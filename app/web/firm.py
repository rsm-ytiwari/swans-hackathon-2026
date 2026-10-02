"""Firm view (owner: Yash). First screen = 5 blocks (plan/v1.md): header, bottom line, do next,
worth vs coverage, red flags. Everything else is in the second layer, opened on demand."""

import re
from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Request

from app.core import config, digest, facts, jobs, sharing, status
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


def _who(t) -> str:
    """Who a task waits on: the outside party it names, else the client if it mentions them, else us."""
    if t.waiting_on:
        return t.waiting_on
    return "Client" if re.search(r"\bclient\b", t.name, re.I) else "Our team"


def _initials(name: str) -> str:
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z'.-]*", name or "") if w[0].isupper()
             and w.rstrip(".,") not in {"PLLC", "LLC", "P.C", "PC", "Inc", "Of", "The", "And"}]
    return ("".join(w[0] for w in words[:2]) or (name or "?")[:2]).upper()


def _blocker(overdue):
    """The single most important fact: the worst overdue task (prefer one waiting on someone outside)."""
    if not overdue:
        return None
    worst = min(overdue, key=lambda x: (x.waiting_on is None, x.days_from_today))
    who = _who(worst)
    return {"task": worst, "label": _short_task(worst.name, worst.waiting_on), "who": who,
            "blocked": who != "Our team", "days": -worst.days_from_today}


def _flag_view(f) -> dict:
    """Card copy for a flag: a short title (text before ':') and one line under it."""
    head, _, tail = f.title.partition(":")
    sub = tail.strip().rstrip(".") if tail.strip() else re.split(r"(?<=[.!?])\s", f.detail or "", maxsplit=1)[0]
    if sub.endswith("..."):
        sub = re.split(r"(?<=[.!?])\s", f.detail or "", maxsplit=1)[0]
    return {"f": f, "short": head.strip(), "sub": sub}


def _money_view(money) -> dict:
    """Worth vs coverage as one bar: billed + liens as segments of the value, coverage as a marker."""
    b = _money_bar(money)
    value, cov, billed, liens = b["value"], b["reachable"], b["billed"] or 0, b["liens"] or 0
    scale = max(x for x in (value, cov, billed + liens, 1) if x)
    pct = lambda x: round(100 * x / scale, 1) if x else 0
    if cov and billed > cov:
        caption = "Medical bills alone already exceed the coverage."
    elif cov and value and value > cov:
        caption = f"Worth about {value / cov:.1f}× the coverage that can pay it."
    elif cov and value:
        caption = "Coverage is above the estimated value."
    else:
        caption = None
    # Say exactly which Clio field is empty, instead of a dash (config.FIELDS names the field per firm).
    missing = [config.FIELDS[k] for k, v in (("case_value", value), ("policy_limits", cov), ("liens", liens)) if not v]
    if not billed:
        missing.append("provider charges")
    return {**b, "billed": billed or None, "liens": liens or None, "missing": missing, "billed_pct": pct(billed), "liens_pct": pct(liens),
            "cov_pct": pct(cov), "value_pct": pct(value), "caption": caption,
            "assumption": config.COVERAGE_ASSUMPTION if cov else ""}


def _since_tiles(changes) -> list[dict]:
    """Past changes grouped by kind: up to 3 tiles with a count and the latest item's title."""
    groups = [("document", "documents received"), ("email", "emails"), ("call", "calls"), ("note", "case notes")]
    tiles = []
    for kind, label in groups:
        items = [e for e in changes if e.kind == kind]
        if items:
            latest = max(items, key=lambda e: e.when)
            tiles.append({"n": len(items), "label": label if len(items) != 1 else label.rstrip("s"),
                          "latest": latest})
    return tiles[:3]


def _provider_rows(con, mid: int, t: date) -> list[dict]:
    app_con = sharing.connect()
    rows = []
    for p in facts.providers(con, mid, t):
        sent = sharing.publications_for(app_con, mid, p.party.contact_id)
        overdue = [r for r in p.requests if r.days_from_today is not None and r.days_from_today < 0]
        rows.append({"p": p, "pid": p.party.contact_id, "sent": sent[0] if sent else None,
                     "overdue": overdue, "open": p.requests})
    return sorted(rows, key=lambda r: -r["p"].billed_total)


def _ago(ts) -> str | None:
    """"4 min ago" / "3 h ago" / "Oct 2" for the last Clio sync time."""
    if not ts:
        return None
    try:
        then = datetime.fromisoformat(str(ts))
    except ValueError:
        return None
    mins = int((datetime.now(UTC) - then).total_seconds() // 60)
    if mins < 60:
        return f"{max(mins, 0)} min ago"
    return f"{mins // 60} h ago" if mins < 24 * 60 else then.strftime("%b %-d")


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
    do_next = sorted(tasks["overdue"], key=lambda x: x.days_from_today) + tasks["upcoming"] + tasks["later"]
    money = facts.money(con, mid)
    since_d = date.fromisoformat(since) if since else t - timedelta(days=14)
    changes = [e for e in facts.events_since(con, mid, since_d) if e.when <= t][::-1]  # past only
    stages = facts.stages(con, mid)
    ai = jobs.ensure(mid, t)
    story = digest.story(con, mid, t) if ai["status"] == "done" else None
    incident = facts.field_value(con, mid, "incident_date")
    upcoming_cal = facts.calendar(con, mid, t)
    ctx = {
        "mid": mid, "m": m, "today": t, "synced": _ago(m["synced_at"]), "client": client, "initials": _initials(m["client_name"]),
        "last_client_contact": facts.last_contact_with(con, mid, client.contact_id) if client else None,
        "stages": stages, "stage_index": stages.index(m["stage_name"]) if m["stage_name"] in stages else None,
        "incident_date": incident,
        "summary": facts.field_value(con, mid, "summary"),
        "next_date": upcoming_cal[0] if upcoming_cal else None,
        # AI blocks come from the background job; until it finishes the page shows "running".
        "ai_status": ai, "ai_check": status.ai(), "story": story,
        "blocker": _blocker(tasks["overdue"]),
        "do_next": [{"t": x, "label": _short_task(x.name, x.waiting_on), "who": _who(x), "ini": _initials(_who(x))}
                    for x in do_next[:3]],
        "do_next_more": max(0, len(do_next) - 3),
        "do_next_rest": [{"t": x, "label": _short_task(x.name, x.waiting_on), "who": _who(x)} for x in do_next[3:]],
        "money": money, "mv": _money_view(money),
        "journey": [e for e in facts.milestones(con, mid, t) if e.kind != "today"],
        "case_age": facts.age(facts._d(incident.value) or facts._d(m["open_date"]), t),
        "flags": _flags(con, mid, t),
        # second layer
        "since": since_d, "changes": changes, "tiles": _since_tiles(changes),
        "providers": _provider_rows(con, mid, t),
        "timeline": facts.timeline(con, mid)[::-1],
    }
    if ctx["flags"]:
        ctx["flag_cards"] = [_flag_view(f) for f in ctx["flags"]["items"]]
    return templates.TemplateResponse(request, "firm/index.html", ctx)
