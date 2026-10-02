"""What a treating provider may see (D-003). Deny by default.

A provider page is rendered ONLY from a `ProviderPacket`. The packet builder reads nothing but the
sections the attorney switched on, and it can never include notes, communications or strategy fields
(config.STRATEGY_FIELDS), whatever the policy says. `check_firewall` proves that on the finished packet.

Our own state (policies, approved publications, view receipts) lives in app/data/app.db, never in Clio
(D-001).
"""

import json
import secrets
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime

from app import store
from app.core import config, facts

APP_DB = store.DATA_DIR / "app.db"

# section key -> (label shown to the attorney, on by default)
SECTIONS: dict[str, tuple[str, bool]] = {
    "status": ("Case stage, in plain language", True),
    "own_bills": ("Their own charges and bills on file", True),
    "own_records": ("Their own records on file", True),
    "requests": ("What the firm needs from their office", True),
    "treatment_status": ("Treatment status", False),
    "coverage": ("Insurance coverage / policy limits", False),
    "shared_documents": ("Selected documents from other providers", False),
}

NEVER_SHARED = ("Notes", "Emails and calls", "Case value and strategy fields")


@dataclass
class Policy:
    sections: set[str]
    shared_doc_ids: set[int] = field(default_factory=set)

    @classmethod
    def default(cls) -> "Policy":
        return cls({k for k, (_, on) in SECTIONS.items() if on})


@dataclass
class ProviderPacket:
    provider_name: str
    patient_name: str
    matter_number: str
    generated_at: str
    status: dict | None = None  # {stage, plain, index, stages}
    bills: dict | None = None  # {total, charges: [...], documents: [...]}
    records: list[dict] | None = None
    requests: list[dict] | None = None
    treatment_status: str | None = None
    coverage: str | None = None
    shared_documents: list[dict] | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str, sort_keys=True)


# ---------- our own state ----------

def connect() -> sqlite3.Connection:
    con = sqlite3.connect(APP_DB)
    con.row_factory = sqlite3.Row
    con.executescript("""
        CREATE TABLE IF NOT EXISTS share_policy (matter_id INTEGER, provider_id INTEGER, sections TEXT,
            shared_doc_ids TEXT, updated_at TEXT, PRIMARY KEY (matter_id, provider_id));
        CREATE TABLE IF NOT EXISTS publication (token TEXT PRIMARY KEY, matter_id INTEGER, provider_id INTEGER,
            packet TEXT, approved_by TEXT, approved_at TEXT);
        CREATE TABLE IF NOT EXISTS publication_view (token TEXT, viewed_at TEXT, user_agent TEXT);
    """)
    return con


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def get_policy(app_con, mid: int, provider_id: int) -> Policy:
    row = app_con.execute("SELECT * FROM share_policy WHERE matter_id = ? AND provider_id = ?",
                          (mid, provider_id)).fetchone()
    if row is None:
        return Policy.default()
    return Policy(set(json.loads(row["sections"])) & SECTIONS.keys(), set(json.loads(row["shared_doc_ids"])))


def save_policy(app_con, mid: int, provider_id: int, policy: Policy) -> None:
    app_con.execute("INSERT OR REPLACE INTO share_policy VALUES (?, ?, ?, ?, ?)", (
        mid, provider_id, json.dumps(sorted(policy.sections & SECTIONS.keys())),
        json.dumps(sorted(policy.shared_doc_ids)), _now()))
    app_con.commit()


# ---------- packet ----------

def _doc(d: facts.Doc) -> dict:
    return {"doc_id": d.doc_id, "name": d.name, "received": d.received, "pages": d.pages}


def build_packet(con, mid: int, provider_id: int, policy: Policy, today: date | None = None) -> ProviderPacket:
    """Everything the provider will see, and nothing else."""
    prov = next((p for p in facts.providers(con, mid, today) if p.party.contact_id == provider_id), None)
    if prov is None:
        raise KeyError(f"contact {provider_id} is not a treating provider on matter {mid}")
    m = facts.matter(con, mid)
    on = policy.sections
    pkt = ProviderPacket(provider_name=prov.party.name, patient_name=m["client_name"],
                         matter_number=m["display_number"], generated_at=_now())
    if "status" in on:
        stages = facts.stages(con, mid)
        stage = m["stage_name"]
        pkt.status = {"stage": stage, "plain": config.STAGE_PLAIN.get(stage, stage), "stages": stages,
                      "index": stages.index(stage) if stage in stages else None}
    if "own_bills" in on:
        pkt.bills = {"total": prov.billed_total,
                     "charges": [{"date": c.date, "amount": c.amount} for c in prov.charges],
                     "documents": [_doc(d) for d in prov.bills]}
    if "own_records" in on:
        pkt.records = [_doc(d) for d in prov.records]
    if "requests" in on:
        pkt.requests = [{"what": t.name, "due": t.due, "days_from_today": t.days_from_today}
                        for t in prov.requests]
    if "treatment_status" in on:
        pkt.treatment_status = facts.field_value(con, mid, "treatment_status").value
    if "coverage" in on:
        pkt.coverage = facts.field_value(con, mid, "policy_limits").value
    if "shared_documents" in on and policy.shared_doc_ids:
        # Only clinical documents can be shared across providers; pleadings, experts etc. never.
        pkt.shared_documents = [_doc(d) for d in facts.documents(con, mid) if d.doc_id in policy.shared_doc_ids
                                and any(k in d.folder.lower() for k in config.PROVIDER_DOC_FOLDERS)]
    check_firewall(con, mid, pkt)
    return pkt


class FirewallBreach(Exception):
    pass


def check_firewall(con, mid: int, pkt: ProviderPacket) -> None:
    """Refuse any packet containing note text, email/call text, or a strategy field value."""
    blob = pkt.to_json().lower()
    secret = [r["detail"] for r in con.execute("SELECT detail FROM notes WHERE matter_id = ?", (mid,))]
    secret += [r["body"] for r in con.execute("SELECT body FROM communications WHERE matter_id = ?", (mid,))]
    secret += [str(facts.field_value(con, mid, k).value) for k in config.STRATEGY_FIELDS]
    for text in secret:
        text = (text or "").strip().lower()
        if len(text) >= 40 and text[:40] in blob:
            raise FirewallBreach(f"packet contains restricted text: {text[:40]!r}")


# ---------- publish + receipts ----------

def publish(app_con, mid: int, provider_id: int, pkt: ProviderPacket, approved_by: str) -> str:
    """Freeze an attorney-approved packet behind an unguessable link token."""
    token = secrets.token_urlsafe(16)
    app_con.execute("INSERT INTO publication VALUES (?, ?, ?, ?, ?, ?)",
                    (token, mid, provider_id, pkt.to_json(), approved_by, _now()))
    app_con.commit()
    return token


def published(app_con, token: str) -> dict | None:
    row = app_con.execute("SELECT * FROM publication WHERE token = ?", (token,)).fetchone()
    return {**dict(row), "packet": json.loads(row["packet"])} if row else None


def record_view(app_con, token: str, user_agent: str = "") -> None:
    app_con.execute("INSERT INTO publication_view VALUES (?, ?, ?)", (token, _now(), user_agent[:200]))
    app_con.commit()


def publications_for(app_con, mid: int, provider_id: int) -> list[dict]:
    rows = app_con.execute(
        "SELECT p.token, p.approved_by, p.approved_at, COUNT(v.token) AS views, MAX(v.viewed_at) AS last_viewed"
        " FROM publication p LEFT JOIN publication_view v ON v.token = p.token"
        " WHERE p.matter_id = ? AND p.provider_id = ? GROUP BY p.token ORDER BY p.approved_at DESC",
        (mid, provider_id)).fetchall()
    return [dict(r) for r in rows]
