"""Red flags for the firm view (D-011).

Two engines, both generic (nothing here knows about one matter; firm naming lives in app.core.config):
  * rule_flags: deterministic checks over app.core.facts (dates and money are always code).
  * contradiction_flags: an LLM reads the case file (notes, emails, text fields) and the medical documents
    and proposes contradictions. A contradiction is kept ONLY if both quoted claims are found in the
    sources they cite; anything else is dropped and counted.
Results are stored in app/data/app.db (table `flags`) keyed by a hash of the case corpus.
CLI: uv run python -m app.core.flags --matter <id>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import date
from typing import Literal

import pydantic
from rapidfuzz import fuzz

from app import store
from app.core import config, facts, llm
from app.core.facts import Source

APP_DB = store.DATA_DIR / "app.db"
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


# ---------------------------------------------------------------- types
@dataclass
class Evidence:
    source: Source
    quote: str
    page: int | None = None


@dataclass
class Flag:
    key: str
    kind: Literal["rule", "contradiction"]
    severity: Literal["high", "medium", "low"]
    title: str  # <= 90 chars, one line
    detail: str  # <= 2 sentences
    evidence: list[Evidence] = field(default_factory=list)


def _title(s: str) -> str:
    s = " ".join(s.split())
    return s if len(s) <= 90 else s[:87].rstrip() + "..."


def _flag_to_dict(f: Flag) -> dict:
    return {
        "key": f.key, "kind": f.kind, "severity": f.severity, "title": f.title, "detail": f.detail,
        "evidence": [{"source": {"clio_type": e.source.clio_type, "clio_id": e.source.clio_id,
                                 "label": e.source.label}, "quote": e.quote, "page": e.page}
                     for e in f.evidence],
    }


def _flag_from_dict(d: dict) -> Flag:
    return Flag(d["key"], d["kind"], d["severity"], d["title"], d["detail"],
                [Evidence(Source(**e["source"]), e["quote"], e["page"]) for e in d["evidence"]])


def _snip(text, n: int = 160) -> str:
    t = " ".join(str(text or "").split())
    return t if len(t) <= n else t[: n - 3] + "..."


def _money(x: float) -> str:
    return f"${x:,.0f}" if abs(x - round(x)) < 0.005 else f"${x:,.2f}"


def _sorted(flags: list[Flag]) -> list[Flag]:
    return sorted(flags, key=lambda f: SEVERITY_ORDER[f.severity])


# ---------------------------------------------------------------- rule flags
_AMOUNT = re.compile(r"\$\s?(\d[\d,]*(?:\.\d+)?)\s*(million|thousand|m|k)?\b", re.I)


_SPLIT = re.compile(r"\$\s?(\d[\d,]*)\s*/\s*\$\s?(\d[\d,]*)")


def _amounts(text: str) -> list[float]:
    out = []
    for num, unit in _AMOUNT.findall(text or ""):
        try:
            v = float(num.replace(",", ""))
        except ValueError:
            continue
        mult = {"million": 1e6, "m": 1e6, "thousand": 1e3, "k": 1e3}.get((unit or "").lower(), 1)
        out.append(v * mult)
    return out


def rule_flags(con, mid: int, today: date) -> list[Flag]:
    flags: list[Flag] = []
    m = facts.matter(con, mid)

    # 1. Medical bills total vs the specials custom field.
    money = facts.money(con, mid)
    specials = money["specials_field"]
    if money["specials_mismatch"]:
        billed, claimed = money["provider_billed_total"], facts.number(specials.value)
        diff = abs(claimed - billed)
        top = sorted((c for p in facts.providers(con, mid, today) for c in p.charges),
                     key=lambda c: -c.amount)[:3]
        flags.append(Flag(
            "rule:specials_mismatch", "rule", "high" if diff >= 0.1 * max(claimed, billed) else "medium",
            _title(f"Specials field {_money(claimed)} does not match provider charges {_money(billed)}"),
            f"The specials custom field and the sum of provider charges on file differ by {_money(diff)}. "
            "Whichever figure goes into a demand needs to be reconciled first.",
            [Evidence(specials.source, _snip(f"{specials.source.label}: {specials.value}"))]
            + [Evidence(c.source, _snip(f"{c.note} ({_money(c.amount)})")) for c in top],
        ))

    # 2. Overdue tasks (one flag, worst first).
    overdue = sorted(facts.tasks(con, mid, today)["overdue"], key=lambda t: t.days_from_today)
    if overdue:
        worst = overdue[0]
        late = -worst.days_from_today
        flags.append(Flag(
            "rule:overdue_tasks", "rule", "high" if late > config.OVERDUE_HIGH_DAYS else "medium",
            _title(f"{len(overdue)} overdue task{'s' if len(overdue) != 1 else ''}; worst: {worst.name} ({late}d late)"),
            f"{len(overdue)} open task(s) are past due, the oldest by {late} days. "
            "Items waiting on outside parties are listed in the evidence.",
            [Evidence(t.source, _snip(f"{t.name}, due {t.due}, {-t.days_from_today}d overdue")) for t in overdue[:5]],
        ))

    # 3. Limitations date near or passed while the matter is still before suit.
    stage_names = facts.stages(con, mid)
    before_suit = (m["stage_name"] not in config.SUIT_STAGES) and (not stage_names or m["stage_name"] in stage_names)
    sol = facts.statute_of_limitations(con, mid)
    if sol and sol.due and before_suit:
        left = (sol.due - today).days
        if left <= config.SOL_WARN_DAYS:
            msg = (f"Limitations date {sol.due} passed {-left} days ago" if left < 0
                   else f"Limitations date {sol.due} is {left} days away")
            flags.append(Flag(
                "rule:statute_of_limitations", "rule", "high" if left <= config.SOL_HIGH_DAYS else "medium",
                _title(f"{msg} and no suit filed yet"),
                f"The matter is in stage '{m['stage_name']}', before suit. "
                + ("Confirm whether the claim is still viable." if left < 0 else "A complaint must be filed before this date."),
                [Evidence(sol.source, _snip(f"{sol.name}, due {sol.due}, status {sol.status}"))],
            ))

    # 4. No client contact for too long.
    cl = facts.client(con, mid)
    if cl and (m["status"] or "").lower() != "closed":
        last = facts.last_contact_with(con, mid, cl.contact_id)
        gap = (today - last.when).days if last and last.when else None
        if last is None or (gap is not None and gap > config.NO_CLIENT_CONTACT_DAYS):
            flags.append(Flag(
                "rule:no_client_contact", "rule",
                "high" if last is None or gap > 2 * config.NO_CLIENT_CONTACT_DAYS else "medium",
                _title("No email or call with the client on record" if last is None
                       else f"No client contact for {gap} days (last: {last.kind} on {last.when})"),
                f"The threshold for staying in touch with the client is {config.NO_CLIENT_CONTACT_DAYS} days. "
                "Clients who hear nothing tend to complain or leave.",
                [Evidence(last.source if last else cl.source,
                          _snip(last.title if last else f"No communication with {cl.name}"))],
            ))

    # 5. Gap between consecutive dated treatment items for a provider (calendar entries + charge dates).
    provs = facts.providers(con, mid, today)
    cal = facts.calendar(con, mid, today, future_only=False)
    gaps = []
    for p in provs:
        items = {}
        for c in p.charges:
            d = facts._d(c.date)
            if d and d <= today:
                items.setdefault(d, (c.source, c.note))
        for e in cal:
            if e.when <= today and facts._mentions(p.party.name, p.party.kind, f"{e.title} {e.detail}"):
                items.setdefault(e.when, (e.source, e.title))
        if len(items) < config.TREATMENT_MIN_ITEMS:
            continue
        ds = sorted(items)
        a, b = max(zip(ds, ds[1:]), key=lambda ab: (ab[1] - ab[0]).days)
        if (b - a).days > config.TREATMENT_GAP_DAYS:
            gaps.append((p, a, b, items[a], items[b]))
    if gaps:
        gaps.sort(key=lambda g: -(g[2] - g[1]).days)
        p, a, b, ia, ib = gaps[0]
        flags.append(Flag(
            "rule:treatment_gaps", "rule", "medium",
            _title(f"Treatment gap of {(b - a).days} days with {p.party.name}"
                   + (f" (+{len(gaps) - 1} more provider{'s' if len(gaps) > 2 else ''})" if len(gaps) > 1 else "")),
            f"Dated calendar entries and charges show no activity between {a} and {b}, "
            f"over the {config.TREATMENT_GAP_DAYS}-day threshold. Insurers use gaps in care to argue the injury resolved.",
            [Evidence(src, _snip(f"{d}: {txt}")) for g in gaps[:3] for d, (src, txt) in ((g[1], g[3]), (g[2], g[4]))],
        ))

    # 6. Provider with charges but no records, or records but no charges or bills.
    no_rec = [p for p in provs if p.charges and not p.records]
    if no_rec:
        flags.append(Flag(
            "rule:charges_without_records", "rule", "medium",
            _title(f"Charges but no medical records on file: {', '.join(p.party.name for p in no_rec[:3])}"
                   + (f" +{len(no_rec) - 3}" if len(no_rec) > 3 else "")),
            "These providers billed the case but no record from them is in the document folders. "
            "Bills without records are easy for an insurer to discount.",
            [Evidence(c.source, _snip(f"{p.party.name}: {c.note} ({_money(c.amount)})"))
             for p in no_rec for c in p.charges[:1]][:5],
        ))
    no_chg = [p for p in provs if p.records and not p.charges and not p.bills]
    if no_chg:
        flags.append(Flag(
            "rule:records_without_charges", "rule", "low",
            _title(f"Records but no charges or bills: {', '.join(p.party.name for p in no_chg[:3])}"
                   + (f" +{len(no_chg) - 3}" if len(no_chg) > 3 else "")),
            "Treatment is documented but nothing was billed, so these providers' costs may be missing from the specials.",
            [Evidence(r.source, _snip(r.name)) for p in no_chg for r in p.records[:1]][:5],
        ))

    # 7. Every dollar amount in the coverage text is below the case value.
    limits, value = money["policy_limits"], money["case_value"]
    if limits.value and value.value:
        # Split limits "$A / $B" are per-person / per-accident; one claimant can reach only A.
        split = _SPLIT.findall(str(limits.value))
        amts = [float(a.replace(",", "")) for a, _ in split] or _amounts(str(limits.value))
        try:
            val = float(value.value)
        except (TypeError, ValueError):
            val = None
        if amts and val and max(amts) < val:
            flags.append(Flag(
                "rule:coverage_below_value", "rule", "high",
                _title(f"Coverage reachable by the client ({_money(max(amts))} max) is below the case value ({_money(val)})"),
                "Every amount in the policy-limits field is lower than the estimated case value, "
                "so recovery may be capped by available coverage. Look for other policies or assets.",
                [Evidence(limits.source, _snip(f"{limits.source.label}: {limits.value}", 220)),
                 Evidence(value.source, _snip(f"{value.source.label}: {value.value}"))],
            ))
    return _sorted(flags)


# ---------------------------------------------------------------- contradiction flags
Sev = Literal["high", "medium", "low"]


class Claim(pydantic.BaseModel):
    tag: str
    quote: str


class Contradiction(pydantic.BaseModel):
    title: str
    why_it_matters: str
    claim_a: Claim
    claim_b: Claim
    severity: Sev


class CaseFileOut(pydantic.BaseModel):
    contradictions: list[Contradiction]
    assertions: list[Claim]


class DocOut(pydantic.BaseModel):
    contradictions: list[Contradiction]


_TAG = re.compile(r"\[\s*(Note|Communication|CustomFieldValue|Document)\s*:\s*(\d+)(?:\s+p\.?\s*(\d+))?\s*\]")

SYSTEM = (
    "You are a careful paralegal auditing a personal-injury case file for inconsistencies. "
    "Report only real conflicts between two specific statements that cannot both be true. "
    "Typical kinds: the same event or place described differently; a status, coverage or amount stated "
    "differently in two places; a statement that something did or did not happen versus a record showing the opposite; "
    "a person's denial versus a record. Do not report differences of emphasis, missing information, or opinions. "
    "Every quote must be copied verbatim (at most 200 characters) from the text that follows the tag you cite; "
    "never paraphrase or combine passages. Cite each claim with the exact tag shown, for example [Note:123]."
)


def _norm(s: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9$%.]+", " ", (s or "").lower()).split())


def _quote_in(quote: str, text: str) -> bool:
    q, t = _norm(quote), _norm(text)
    if len(q) < 12:
        return False
    return q in t or fuzz.partial_ratio(q, t) >= config.FLAG_QUOTE_MATCH


class _Corpus:
    """Everything the model may cite, with the text each tag resolves to."""

    def __init__(self, con, mid: int):
        self.con, self.mid = con, mid
        self.items: dict[tuple[str, int], tuple[Source, str]] = {}
        self._pages: dict[int, list[str]] = {}
        for r in con.execute("SELECT * FROM notes WHERE matter_id = ? ORDER BY date, clio_id", (mid,)):
            self.items[("Note", r["clio_id"])] = (
                Source("Note", r["clio_id"], r["subject"] or ""),
                f"{r['date'] or ''} {r['subject'] or ''}\n{r['detail'] or ''}".strip())
        for r in con.execute("SELECT * FROM communications WHERE matter_id = ? ORDER BY date, clio_id", (mid,)):
            self.items[("Communication", r["clio_id"])] = (
                Source("Communication", r["clio_id"], r["subject"] or ""),
                f"{r['date'] or ''} {r['subject'] or ''}\n{r['body'] or ''}".strip())
        for r in con.execute("SELECT * FROM custom_field_values WHERE matter_id = ? ORDER BY clio_id", (mid,)):
            if isinstance(r["value"], str) and str(r["field_type"] or "").startswith("text"):
                self.items[("CustomFieldValue", r["clio_id"])] = (
                    Source("CustomFieldValue", r["clio_id"], r["field_name"]), f"{r['field_name']}: {r['value']}")
        self.docs = [d for d in facts.documents(con, mid)
                     if d.has_text and any(k in d.folder.lower() for k in config.PROVIDER_DOC_FOLDERS)]

    def case_text(self) -> str:
        return "\n\n".join(f"[{t}:{i}]\n{text}" for (t, i), (_, text) in self.items.items())

    def pages(self, doc_id: int) -> list[str]:
        if doc_id not in self._pages:
            import pymupdf
            path = facts.document_path(self.con, doc_id)
            try:
                self._pages[doc_id] = [p.get_text() for p in pymupdf.open(path)] if path else []
            except Exception:  # missing or unreadable file: nothing to cite
                self._pages[doc_id] = []
        return self._pages[doc_id]

    def hash(self) -> str:
        h = hashlib.sha256(self.case_text().encode())
        for d in self.docs:
            h.update(f"|{d.doc_id}:{d.name}:{d.pages}".encode())
        return h.hexdigest()

    def resolve(self, tag: str) -> tuple[Source, str, int | None] | None:
        """Tag text -> (Source, text of the cited place, page) or None if it cites nothing real."""
        mt = _TAG.search(tag or "")
        if not mt:
            return None
        typ, cid, page = mt.group(1), int(mt.group(2)), mt.group(3)
        if typ != "Document":
            hit = self.items.get((typ, cid))
            return (hit[0], hit[1], None) if hit else None
        doc = next((d for d in self.docs if d.doc_id == cid), None)
        pages = self.pages(cid) if doc else []
        if not pages:
            return None
        if page:
            n = int(page)
            return (doc.source, pages[n - 1], n) if 1 <= n <= len(pages) else None
        return doc.source, "\n".join(pages), None

    def doc_chunks(self) -> list[str]:
        """Tagged page text, packed into chunks of at most FLAG_DOC_CHUNK_CHARS."""
        limit, chunks, cur, size = config.FLAG_DOC_CHUNK_CHARS, [], [], 0
        for d in self.docs:
            for n, text in enumerate(self.pages(d.doc_id), 1):
                text = text.strip()
                while text:
                    block = f"[Document:{d.doc_id} p.{n}] ({d.name})\n{text[: limit - 200]}"
                    text = text[limit - 200:]
                    if size + len(block) > limit and cur:
                        chunks.append("\n\n".join(cur))
                        cur, size = [], 0
                    cur.append(block)
                    size += len(block)
        if cur:
            chunks.append("\n\n".join(cur))
        return chunks


def _to_flag(c: Contradiction, a, b) -> Flag:
    tags = sorted(f"{s.clio_type}:{s.clio_id}:{p}" for s, _, p in (a, b))
    key = "ctr:" + hashlib.sha1("|".join(tags).encode()).hexdigest()[:12]
    why = " ".join(c.why_it_matters.split())
    sentences = re.split(r"(?<=[.!?])\s+", why)
    return Flag(key, "contradiction", c.severity, _title(c.title), " ".join(sentences[:2]),
                [Evidence(a[0], _snip(c.claim_a.quote, 220), a[2]), Evidence(b[0], _snip(c.claim_b.quote, 220), b[2])])


def _verified(c: Contradiction, corpus: _Corpus) -> Flag | None:
    a, b = corpus.resolve(c.claim_a.tag), corpus.resolve(c.claim_b.tag)
    if not a or not b or (a[0], a[2]) == (b[0], b[2]):
        return None
    if not _quote_in(c.claim_a.quote, a[1]) or not _quote_in(c.claim_b.quote, b[1]):
        return None
    return _to_flag(c, a, b)


def _run(con, mid: int, corpus: _Corpus) -> tuple[list[Flag], int, str, int]:
    """Returns (flags, dropped_unverified, ai, failed_calls)."""
    raw: list[Contradiction] = []
    try:
        r = llm.complete(
            task="flags.contradictions.casefile", system=SYSTEM, schema=CaseFileOut, max_tokens=6000,
            prompt=(
                "Below is the case file: notes, emails and text fields, each introduced by a tag.\n"
                "1. Find contradictions WITHIN the case file (claim_a and claim_b must cite different tags).\n"
                f"2. List up to {config.FLAG_MAX_ASSERTIONS} key factual assertions the case file makes that a "
                "medical record could confirm or contradict (what happened, where, injuries, treatment status, "
                "prior history, dates). Give each as a tag and a verbatim quote.\n\n" + corpus.case_text()))
    except (llm.LLMUnavailable, llm.LLMBadOutput):
        return [], 0, "off", 0
    raw += r.data.contradictions
    assertions = [x for x in r.data.assertions if corpus.resolve(x.tag) and _quote_in(x.quote, corpus.resolve(x.tag)[1])]
    assertions = assertions[: config.FLAG_MAX_ASSERTIONS]

    failed = 0
    if assertions:
        listing = "\n".join(f"{x.tag} {x.quote}" for x in assertions)
        for chunk in corpus.doc_chunks():
            try:
                d = llm.complete(
                    task="flags.contradictions.documents", system=SYSTEM, schema=DocOut, max_tokens=4000,
                    prompt=("Assertions made by the case file:\n" + listing +
                            "\n\nBelow are pages of medical documents, each introduced by a [Document:<id> p.<n>] tag. "
                            "Report where a document contradicts an assertion above. claim_a is the case-file "
                            "assertion (its tag and its verbatim quote); claim_b is the document (its page tag and a "
                            "verbatim quote from that page). Report nothing if there is no real conflict.\n\n" + chunk))
            except (llm.LLMUnavailable, llm.LLMBadOutput):
                failed += 1
                continue
            raw += d.data.contradictions

    kept, dropped, seen = [], 0, []
    for c in raw:
        f = _verified(c, corpus)
        if f is None:
            dropped += 1
            continue
        if any(f.key == k.key or fuzz.token_set_ratio(f.title.lower(), k.title.lower()) >= 85 for k in kept):
            continue  # same finding seen in another chunk
        kept.append(f)
    return _sorted(kept), dropped, "ok", failed


def contradiction_flags(con, mid: int) -> list[Flag]:
    """Verified contradictions only; [] when no LLM is available (caller shows 'AI off')."""
    return _run(con, mid, _Corpus(con, mid))[0]


# ---------------------------------------------------------------- store
def _db(path=None) -> sqlite3.Connection:
    db = sqlite3.connect(path or APP_DB)
    db.execute("CREATE TABLE IF NOT EXISTS flags (matter_id INTEGER, content_hash TEXT, computed_at TEXT, json TEXT)")
    return db


def _pack(res: dict) -> str:
    return json.dumps({**res, "rules": [_flag_to_dict(f) for f in res["rules"]],
                       "contradictions": [_flag_to_dict(f) for f in res["contradictions"]]})


def _unpack(blob: str) -> dict:
    d = json.loads(blob)
    d["rules"] = [_flag_from_dict(x) for x in d["rules"]]
    d["contradictions"] = [_flag_from_dict(x) for x in d["contradictions"]]
    return d


def load(mid: int, db_path=None) -> dict | None:
    """Latest stored result for the matter, or None."""
    with _db(db_path) as db:
        row = db.execute("SELECT json FROM flags WHERE matter_id = ? ORDER BY rowid DESC LIMIT 1", (mid,)).fetchone()
    return _unpack(row[0]) if row else None


def compute(con, mid: int, today: date, db_path=None) -> dict:
    """Rules always recompute (they depend on today). The AI part is reused while the case corpus is unchanged."""
    corpus = _Corpus(con, mid)
    chash = corpus.hash()
    rules = rule_flags(con, mid, today)
    with _db(db_path) as db:
        row = db.execute("SELECT json FROM flags WHERE matter_id = ? AND content_hash = ? ORDER BY rowid DESC LIMIT 1",
                         (mid, chash)).fetchone()
    prev = _unpack(row[0]) if row else None
    if prev and prev["ai"] == "ok":
        ctr, dropped, ai, failed = prev["contradictions"], prev["dropped_unverified"], "ok", prev.get("failed_calls", 0)
    else:
        ctr, dropped, ai, failed = _run(con, mid, corpus)
    res = {"rules": rules, "contradictions": ctr, "dropped_unverified": dropped, "ai": ai, "failed_calls": failed}
    with _db(db_path) as db:
        db.execute("INSERT INTO flags VALUES (?, ?, ?, ?)", (mid, chash, store.now(), _pack(res)))
    return res


# ---------------------------------------------------------------- CLI
def main() -> None:
    ap = argparse.ArgumentParser(description="Compute and print red flags for a matter.")
    ap.add_argument("--matter", type=int, required=True)
    ap.add_argument("--today", help="YYYY-MM-DD (default: today)")
    args = ap.parse_args()
    today = date.fromisoformat(args.today) if args.today else date.today()
    con = facts.connect()
    before = llm.cost_report("flags")
    t = time.perf_counter()
    res = compute(con, args.matter, today)
    took = time.perf_counter() - t
    for f in res["rules"] + res["contradictions"]:
        srcs = ", ".join(f"{e.source.clio_type}:{e.source.clio_id}" + (f" p.{e.page}" if e.page else "") for e in f.evidence)
        print(f"{f.kind:13} {f.severity:6} {f.title}  [{srcs}]")
    print(f"\nai={res['ai']} dropped_unverified={res['dropped_unverified']} failed_calls={res.get('failed_calls', 0)} "
          f"rules={len(res['rules'])} contradictions={len(res['contradictions'])}")
    after = llm.cost_report("flags")
    print(f"time {took:.1f}s | this run: live_calls={after['calls'] - after['cached_calls'] - (before['calls'] - before['cached_calls'])} "
          f"cached_calls={after['cached_calls'] - before['cached_calls']}")
    print("cost_report(flags):", after)


if __name__ == "__main__":
    main()
