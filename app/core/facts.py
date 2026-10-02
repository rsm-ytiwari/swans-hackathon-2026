"""Case facts read from the local Clio mirror (app/data/clio.db). The one data layer both views use (D-003).

Every value that reaches a screen carries a `Source` (Clio type + id), so the UI can link to the record it
came from (D-006). Dates and money are computed here in code, never by a model. Nothing in this module
knows about one specific matter: firm-specific names live in `app.core.config`.
"""

import json
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from app import store
from app.core import config

# Clio type -> local table, for looking a source record back up.
TABLE_BY_TYPE = {
    "Matter": "matters", "Note": "notes", "Communication": "communications", "Task": "tasks",
    "CalendarEntry": "calendar_entries", "Activity": "activities", "Document": "documents",
    "Contact": "contacts", "MatterContact": "matter_contacts", "CustomFieldValue": "custom_field_values",
}


# ---------- types ----------

@dataclass(frozen=True)
class Source:
    clio_type: str
    clio_id: int
    label: str = ""

    @property
    def url(self) -> str:
        return f"/source/{self.clio_type}/{self.clio_id}"


@dataclass
class Fact:
    value: object
    source: Source | None = None


@dataclass
class Party:
    contact_id: int
    name: str
    kind: str  # Person | Company
    role: str  # client | provider | insurer | adverse | other
    description: str
    source: Source


@dataclass
class Charge:
    date: str
    amount: float
    note: str
    source: Source


@dataclass
class Doc:
    doc_id: int
    name: str
    folder: str
    received: str | None
    pages: int | None
    has_text: bool
    source: Source

    @property
    def file_url(self) -> str:
        return f"/files/{self.doc_id}"


@dataclass
class TaskItem:
    name: str
    due: date | None
    status: str
    days_from_today: int | None  # negative = overdue by that many days
    waiting_on: str | None  # party name when the task waits on someone outside the firm
    source: Source


@dataclass
class Provider:
    party: Party
    charges: list[Charge] = field(default_factory=list)
    records: list[Doc] = field(default_factory=list)
    bills: list[Doc] = field(default_factory=list)
    requests: list[TaskItem] = field(default_factory=list)  # what the firm still needs from this provider

    @property
    def billed_total(self) -> float:
        return round(sum(c.amount for c in self.charges), 2)


@dataclass
class Event:
    when: date
    kind: str  # note | email | call | document | calendar | task
    title: str
    detail: str
    source: Source


# ---------- helpers ----------

def connect() -> sqlite3.Connection:
    return store.connect()


def _d(value) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value)).date()
    except ValueError:
        return date.fromisoformat(str(value)[:10])


def _rows(con, sql, *args):
    return con.execute(sql, args).fetchall()


def _ids(blob) -> set[int]:
    try:
        return {int(p["id"]) for p in json.loads(blob or "[]") if p.get("id") is not None}
    except (ValueError, TypeError):
        return set()


_STOP = {"the", "and", "of", "dr", "inc", "llc", "pllc", "p.c.", "pc", "new", "york"}


def _tokens(name: str) -> list[str]:
    return [t for t in re.findall(r"[a-z]+", name.lower()) if len(t) > 2 and t not in _STOP]


def _unique_tokens(name: str, others: list[str]) -> set[str]:
    """Words of a name that no other provider's name shares; used to match filenames like 'peter-kwan-…'."""
    taken = {t for o in others if o != name for t in _tokens(o)}
    return {t for t in _tokens(name) if t not in taken}


def _mentions(party_name: str, kind: str, text: str) -> bool:
    """True when free text names this party: full name, a person's surname, or a company's first two words."""
    text = text.lower()
    if party_name.lower() in text:
        return True
    toks = _tokens(party_name)
    if kind == "Person" and toks:
        return re.search(rf"\b{re.escape(toks[-1])}\b", text) is not None
    return len(toks) >= 2 and all(t in text for t in toks[:2])


# ---------- matter + fields ----------

def matters(con) -> list[sqlite3.Row]:
    return _rows(con, "SELECT clio_id, display_number, client_name, stage_name, description, open_date FROM matters ORDER BY clio_id")


def matter(con, mid: int) -> sqlite3.Row:
    row = con.execute("SELECT * FROM matters WHERE clio_id = ?", (mid,)).fetchone()
    if row is None:
        raise KeyError(f"matter {mid} not in local store; run app.ingest first")
    return row


def field_value(con, mid: int, key: str) -> Fact:
    """A custom field by our concept name (see config.FIELDS)."""
    row = con.execute(
        "SELECT clio_id, value, field_name FROM custom_field_values WHERE matter_id = ? AND field_name = ?",
        (mid, config.FIELDS[key]),
    ).fetchone()
    if row is None:
        return Fact(None)
    return Fact(row["value"], Source("CustomFieldValue", row["clio_id"], row["field_name"]))


def stages(con, mid: int) -> list[str]:
    pa = con.execute(
        "SELECT practice_area_id FROM matter_stages WHERE clio_id = (SELECT stage_id FROM matters WHERE clio_id = ?)",
        (mid,),
    ).fetchone()
    if pa is None:
        return []
    return [r["name"] for r in _rows(
        con, "SELECT name FROM matter_stages WHERE practice_area_id = ? ORDER BY stage_order", pa["practice_area_id"])]


def statute_of_limitations(con, mid: int) -> TaskItem | None:
    m = matter(con, mid)
    row = con.execute("SELECT * FROM tasks WHERE clio_id = ?", (m["statute_of_limitations_task_id"],)).fetchone()
    return _task(row, date.today(), []) if row else None


# ---------- people ----------

def _role(description: str, is_client: bool) -> str:
    if is_client:
        return "client"
    text = (description or "").lower()
    for role, words in config.ROLE_KEYWORDS:
        if any(w in text for w in words):
            return role
    return "other"


def parties(con, mid: int) -> list[Party]:
    out = []
    for r in _rows(con, "SELECT * FROM matter_contacts WHERE matter_id = ? ORDER BY is_client DESC, clio_id", mid):
        out.append(Party(
            contact_id=r["contact_id"], name=r["name"], kind=r["type"],
            role=_role(r["relationship_name"], bool(r["is_client"])),
            description=r["relationship_name"] or "",
            source=Source("Contact", r["contact_id"], r["name"]),
        ))
    return out


def client(con, mid: int) -> Party | None:
    return next((p for p in parties(con, mid) if p.role == "client"), None)


def contact(con, contact_id: int) -> sqlite3.Row | None:
    return con.execute("SELECT * FROM contacts WHERE clio_id = ?", (contact_id,)).fetchone()


# ---------- documents ----------

def documents(con, mid: int) -> list[Doc]:
    return [Doc(
        doc_id=r["clio_id"], name=r["name"], folder=r["folder_name"] or "", received=r["received_at"],
        pages=r["page_count"], has_text=bool(r["text_pages"]),
        source=Source("Document", r["clio_id"], r["name"]),
    ) for r in _rows(con, "SELECT * FROM documents WHERE matter_id = ? ORDER BY received_at", mid)]


def document_path(con, doc_id: int) -> str | None:
    row = con.execute("SELECT local_path FROM documents WHERE clio_id = ?", (doc_id,)).fetchone()
    if not row or not row["local_path"]:
        return None
    return str(store.DATA_DIR / row["local_path"])  # stored relative to app/data


# ---------- tasks + calendar ----------

def _task(r, today: date, outside: list["Party"]) -> TaskItem:
    due = _d(r["due_at"])
    text = f"{r['name']} {r['description'] or ''}"
    waiting = next((p.name for p in outside if _mentions(p.name, p.kind, text)), None)
    return TaskItem(
        name=r["name"], due=due, status=r["status"] or "",
        days_from_today=(due - today).days if due else None, waiting_on=waiting,
        source=Source("Task", r["clio_id"], r["name"]),
    )


def tasks(con, mid: int, today: date | None = None) -> dict[str, list[TaskItem]]:
    """Open tasks split into overdue / upcoming (config.UPCOMING_DAYS) / later, plus those waiting on others."""
    today = today or date.today()
    outside = [p for p in parties(con, mid) if p.role != "client"]
    items = [_task(r, today, outside) for r in _rows(
        con, "SELECT * FROM tasks WHERE matter_id = ? AND status != 'complete' ORDER BY due_at", mid)]
    return {
        "overdue": [t for t in items if t.days_from_today is not None and t.days_from_today < 0],
        "upcoming": [t for t in items if t.days_from_today is not None and 0 <= t.days_from_today <= config.UPCOMING_DAYS],
        "later": [t for t in items if t.days_from_today is None or t.days_from_today > config.UPCOMING_DAYS],
        "waiting_on_others": [t for t in items if t.waiting_on],
    }


def calendar(con, mid: int, today: date | None = None, future_only: bool = True) -> list[Event]:
    today = today or date.today()
    out = []
    for r in _rows(con, "SELECT * FROM calendar_entries WHERE matter_id = ? ORDER BY start_at", mid):
        when = _d(r["start_at"])
        if when and (not future_only or when >= today):
            out.append(Event(when, "calendar", r["summary"] or "", r["description"] or "",
                             Source("CalendarEntry", r["clio_id"], r["summary"] or "")))
    return out


# ---------- communications ----------

def last_contact_with(con, mid: int, contact_id: int) -> Event | None:
    """Most recent email or call that has this contact as a sender or receiver."""
    for r in _rows(con, "SELECT * FROM communications WHERE matter_id = ? ORDER BY date DESC, clio_id DESC", mid):
        if contact_id in _ids(r["senders"]) | _ids(r["receivers"]):
            kind = "call" if "Phone" in (r["type"] or "") else "email"
            return Event(_d(r["date"]), kind, r["subject"] or "", r["body"] or "",
                         Source("Communication", r["clio_id"], r["subject"] or ""))
    return None


# ---------- providers + money ----------

def providers(con, mid: int, today: date | None = None) -> list[Provider]:
    """Each treating provider with their charges, records, bills and open requests, matched by name."""
    provs = [p for p in parties(con, mid) if p.role == "provider"]
    names = [p.name for p in provs]
    by_name = {p.name: Provider(party=p) for p in provs}

    # Charges: a provider charge is a non-billable expense whose note names the provider. Each charge goes
    # to exactly one provider (the one named earliest in the note), so totals never double count.
    for r in _rows(con, "SELECT * FROM activities WHERE matter_id = ? AND type = 'ExpenseEntry'", mid):
        amount = r["non_billable_total"]
        note = (r["note"] or "").lower()
        hits = [(note.find(n.lower()), n) for n in names if n.lower() in note]
        if amount and hits:
            by_name[min(hits)[1]].charges.append(Charge(
                r["date"], float(amount), r["note"] or "", Source("Activity", r["clio_id"], f"Charge {r['date']}")))

    # Documents in medical folders: matched on words only this provider's name has (filenames are slugs).
    uniq = {n: _unique_tokens(n, names) for n in names}
    for d in documents(con, mid):
        if not any(k in d.folder.lower() for k in config.PROVIDER_DOC_FOLDERS):
            continue
        words = set(re.findall(r"[a-z]+", d.name.lower()))
        best = max(names, key=lambda n: len(uniq[n] & words), default=None)
        if best and uniq[best] & words:
            (by_name[best].bills if "bill" in d.folder.lower() else by_name[best].records).append(d)

    open_tasks = tasks(con, mid, today)
    for t in open_tasks["overdue"] + open_tasks["upcoming"] + open_tasks["later"]:
        if t.waiting_on in by_name:
            by_name[t.waiting_on].requests.append(t)
    return list(by_name.values())


def money(con, mid: int) -> dict:
    """Headline money figures. Totals are summed here, never by a model."""
    provs = providers(con, mid)
    matched = {c.source.clio_id for p in provs for c in p.charges}
    firm_costs = [r for r in _rows(con, "SELECT * FROM activities WHERE matter_id = ? AND type = 'ExpenseEntry'", mid)
                  if r["clio_id"] not in matched and r["total"]]
    billed = round(sum(p.billed_total for p in provs), 2)
    specials = field_value(con, mid, "specials")
    return {
        "case_value": field_value(con, mid, "case_value"),
        "policy_limits": field_value(con, mid, "policy_limits"),
        "policy_limits_confirmed": field_value(con, mid, "policy_limits_confirmed"),
        "specials_field": specials,
        "provider_billed_total": billed,
        "specials_mismatch": specials.value is not None and abs(float(specials.value) - billed) > 0.5,
        "firm_costs_total": round(sum(float(r["total"]) for r in firm_costs), 2),
        "firm_costs": [Charge(r["date"], float(r["total"]), r["note"] or "",
                              Source("Activity", r["clio_id"], f"Cost {r['date']}")) for r in firm_costs],
        "liens": field_value(con, mid, "liens"),
    }


# ---------- timeline ----------

def timeline(con, mid: int) -> list[Event]:
    """Everything dated on the matter, oldest first. Uses each record's own date, not Clio's created_at
    (the seeded matter was created today, so created_at says nothing about when things happened)."""
    ev: list[Event] = []
    for r in _rows(con, "SELECT * FROM notes WHERE matter_id = ?", mid):
        ev.append(Event(_d(r["date"]), "note", r["subject"] or "", r["detail"] or "",
                        Source("Note", r["clio_id"], r["subject"] or "")))
    for r in _rows(con, "SELECT * FROM communications WHERE matter_id = ?", mid):
        kind = "call" if "Phone" in (r["type"] or "") else "email"
        ev.append(Event(_d(r["date"]), kind, r["subject"] or "", r["body"] or "",
                        Source("Communication", r["clio_id"], r["subject"] or "")))
    for d in documents(con, mid):
        if d.received:
            ev.append(Event(_d(d.received), "document", d.name, d.folder, d.source))
    ev += calendar(con, mid, future_only=False)
    return sorted((e for e in ev if e.when), key=lambda e: (e.when, e.kind))


def events_since(con, mid: int, since: date) -> list[Event]:
    return [e for e in timeline(con, mid) if e.when > since]


# ---------- source lookup ----------

def source_record(con, clio_type: str, clio_id: int) -> dict | None:
    """The stored record behind a Source, for the click-to-source view."""
    table = TABLE_BY_TYPE.get(clio_type)
    if not table:
        return None
    row = con.execute(f"SELECT * FROM {table} WHERE clio_id = ?", (clio_id,)).fetchone()
    if row is None and clio_type == "Contact":
        row = contact(con, clio_id)
    return dict(row) if row else None


def days_between(a: date, b: date) -> int:
    return (b - a).days


def add_days(d: date, n: int) -> date:
    return d + timedelta(days=n)


# ---------- view helpers: journey, reachable coverage, age ----------

_DOLLARS = re.compile(r"\$\s?(\d[\d,]*(?:\.\d+)?)")
_SPLIT_LIMIT = re.compile(r"\$\s?(\d[\d,]*)\s*/\s*\$\s?(\d[\d,]*)")


def dollars(text) -> list[float]:
    return [float(a.replace(",", "")) for a in _DOLLARS.findall(str(text or ""))]


def reachable_coverage(text) -> float | None:
    """Most one claimant can reach from a limits text: for split limits "$A / $B" (per person / per
    accident) only A counts; otherwise the largest amount stated."""
    split = [float(a.replace(",", "")) for a, _ in _SPLIT_LIMIT.findall(str(text or ""))]
    amounts = split or dollars(text)
    return max(amounts) if amounts else None


def age(start: date | None, today: date) -> str:
    if not start:
        return ""
    months = (today.year - start.year) * 12 + today.month - start.month - (today.day < start.day)
    y, m = divmod(max(months, 0), 12)
    return " ".join(p for p in (f"{y} yr{'s' if y != 1 else ''}" if y else "", f"{m} mo" if m else "") if p) or "under a month"


def milestones(con, mid: int, today: date | None = None) -> list[Event]:
    """Dated landmarks for the case journey strip: incident, case opened, first treatment, the first
    document in each milestone folder (config.MILESTONE_FOLDERS), and today."""
    today = today or date.today()
    out: list[Event] = []
    inc = field_value(con, mid, "incident_date")
    if inc.value:
        out.append(Event(_d(inc.value), "milestone", "Incident", "", inc.source))
    m = matter(con, mid)
    if m["open_date"]:
        out.append(Event(_d(m["open_date"]), "milestone", "Case opened", "", Source("Matter", mid, m["display_number"])))
    charges = [c for p in providers(con, mid, today) for c in p.charges if c.date]
    if charges:
        first = min(charges, key=lambda c: c.date)
        out.append(Event(_d(first.date), "milestone", "Treatment began", "", first.source))
    docs = documents(con, mid)
    for key, label in config.MILESTONE_FOLDERS:
        hits = [d for d in docs if key in d.folder.lower() and d.received]
        if hits:
            d = min(hits, key=lambda x: x.received)
            out.append(Event(_d(d.received), "milestone", label, d.name, d.source))
    out.append(Event(today, "today", "Today", "", Source("Matter", mid, "today")))
    return sorted(out, key=lambda e: e.when)
