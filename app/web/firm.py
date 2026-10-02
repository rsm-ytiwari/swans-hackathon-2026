"""Firm view (owner: Yash). First screen = 5 blocks (plan/v1.md): header, bottom line, do next,
worth vs coverage, red flags. Everything else is in the second layer, opened on demand."""

import re
from datetime import date, timedelta

from fastapi import APIRouter, Request

from app.core import digest, facts, jobs, status
from app.web.deps import templates, today

router = APIRouter()


def _first_line(text) -> str | None:
    if not text:
        return None
    return re.split(r"(?<=[.;])\s|\n", str(text).strip(), maxsplit=1)[0].rstrip(".;")


def _short_task(name: str, waiting_on: str | None) -> str:
    """Drop a leading "By <who>: <party> -" prefix; the 'waiting on' line already says who."""
    name = re.sub(r"^By [^:]{1,40}:\s*", "", name)
    if waiting_on and name.startswith(waiting_on):
        name = name[len(waiting_on):].lstrip(" -–:")
    return name[:1].upper() + name[1:]


def _needs_answer(overdue, upcoming) -> str:
    """One answer line for 'what needs me now', computed from the task list (never a count alone)."""
    if overdue:
        worst = min(overdue, key=lambda x: x.days_from_today)
        who = f", waiting on {worst.waiting_on}" if worst.waiting_on else ""
        n = len(overdue)
        lead = "1 thing is overdue" if n == 1 else f"{n} things are overdue"
        return f"{lead}; the worst is {-worst.days_from_today} days late{who}."
    if upcoming:
        nxt = upcoming[0]
        return f"Nothing overdue. Next: {_short_task(nxt.name, nxt.waiting_on)} {('in ' + str(nxt.days_from_today) + ' days') if nxt.days_from_today else 'today'}."
    return "Nothing open on this case."


def _money_bar(money) -> dict:
    """The four numbers for the worth-vs-coverage visual, all computed in code."""
    value = float(money["case_value"].value) if money["case_value"].value else None
    liens = facts.dollars(money["liens"].value)
    return {
        "value": value,
        "reachable": facts.reachable_coverage(money["policy_limits"].value),
        "billed": money["provider_billed_total"] or None,
        "liens": liens[0] if liens else None,
    }


def _flags(con, mid: int, t: date):
    """Stored flags if computed (app.core.flags), else rule flags live; None if the module is unavailable."""
    try:
        from app.core import flags
    except ImportError:
        return None
    # Rules depend on today, so they run live (fast, code). Contradictions come from the last AI run.
    stored = flags.load(mid) if hasattr(flags, "load") else None
    # Two findings on the same case-file record about the same subject (shared title word) are one problem,
    # e.g. the same claim contradicted by two documents. Keep the first (stored order = stronger first).
    ctr, seen = [], []
    for f in (stored["contradictions"] if stored else []):
        anchor = f.evidence[0].source if f.evidence else None
        words = {w for w in re.findall(r"[a-z]+", f.title.lower()) if len(w) > 5}
        if any(anchor == a and words & w for a, w in seen):
            continue
        seen.append((anchor, words))
        ctr.append(f)
    ai = stored["ai"] if stored else "not run"
    # The overdue-task rule repeats the "Do next" block on this screen, so it is not shown twice.
    rules = [f for f in flags.rule_flags(con, mid, t) if f.key != "rule:overdue_tasks"]
    items = sorted(ctr + rules,
                   key=lambda f: (flags.SEVERITY_ORDER.get(f.severity, 9), f.kind != "contradiction"))
    return {"items": items, "ai": ai}


@router.get("/m/{mid}")
def firm_view(request: Request, mid: int, since: str | None = None):
    con = facts.connect()
    t = today()
    m = facts.matter(con, mid)
    client = facts.client(con, mid)
    tasks = facts.tasks(con, mid, t)
    do_next = sorted(tasks["overdue"], key=lambda x: x.days_from_today) + tasks["upcoming"]
    money = facts.money(con, mid)
    since_d = date.fromisoformat(since) if since else t - timedelta(days=14)
    stages = facts.stages(con, mid)
    ctx = {
        "mid": mid, "m": m, "today": t, "client": client,
        "last_client_contact": facts.last_contact_with(con, mid, client.contact_id) if client else None,
        "stages": stages, "stage_index": stages.index(m["stage_name"]) if m["stage_name"] in stages else None,
        "incident_date": facts.field_value(con, mid, "incident_date"),
        "summary": facts.field_value(con, mid, "summary"),
        # AI blocks come from the background job; until it finishes the page shows "running".
        "ai_status": (ai := jobs.ensure(mid, t)),
        "ai_check": status.ai(),
        "bottom_line": digest.bottom_line(con, mid, t) if ai["status"] == "done" else None,
        "do_next": [(x, _short_task(x.name, x.waiting_on)) for x in do_next[:5]], "do_next_more": max(0, len(do_next) - 5),
        "money": money,
        "money_bar": _money_bar(money),
        "needs_answer": _needs_answer(tasks["overdue"], tasks["upcoming"]),
        "journey": facts.milestones(con, mid, t),
        "case_age": facts.age(facts._d(facts.field_value(con, mid, "incident_date").value) or facts._d(m["open_date"]), t),
        "coverage_line": _first_line(money["policy_limits"].value),
        "liens_line": _first_line(money["liens"].value),
        "flags": _flags(con, mid, t),
        # second layer
        "since": since_d, "changes": facts.events_since(con, mid, since_d)[::-1],
        "providers": [p for p in facts.providers(con, mid, t) if p.charges or p.records or p.bills],
        "events": facts.calendar(con, mid, t),
    }
    return templates.TemplateResponse(request, "firm/index.html", ctx)
