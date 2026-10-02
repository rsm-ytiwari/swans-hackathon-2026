"""AI digests for the firm view: the 3-sentence bottom line. Generic: the prompt describes the task, the
case content comes only from the local Clio mirror. Every sentence cites record tags that must exist in
the material we sent; unknown tags are dropped (the model cannot cite what it was not shown).
"""

import re
from datetime import date

import pydantic

from app.core import config, facts, llm

_TAG = re.compile(r"\[(\w+):(\d+)\]")


class Sentence(pydantic.BaseModel):
    text: str
    sources: list[str]  # tags like "Note:123"


class BottomLine(pydantic.BaseModel):
    sentences: list[Sentence]
    injuries: list[str] = []  # short labels, e.g. "Both knees"


# The firm view labels the three sentences in this order (app/web/templates/firm/index.html).
LABELS = ("What happened", "Where it stands", "Biggest risk")

SYSTEM = (
    "You brief a personal-injury attorney who has 10 seconds. Use only the case material given. "
    "Write exactly 3 short sentences (max 20 words each), in this order: (1) WHAT HAPPENED: the incident "
    "and the injuries; (2) WHERE IT STANDS: the procedural stage and the latest concrete step taken (do not "
    "list overdue tasks, the page shows those separately); (3) BIGGEST RISK: the single biggest threat to "
    "the case's value or liability, and why. Write complete, plain sentences a busy reader understands at a "
    "glance: no abbreviations or jargon (write 'range of motion', not 'ROM'), no semicolons, no lists inside "
    "a sentence, no hedging, no legal citations. For each sentence list the tags (like Note:123) of the "
    "records that support it, copied exactly from the material. Also list the client's injuries as at most "
    "4 short labels of 1 to 3 words each (like 'Both knees'), taken from the material."
)


def _material(con, mid: int, today: date) -> tuple[str, set[str]]:
    m = facts.matter(con, mid)
    lines = [f"TODAY: {today.isoformat()}", f"MATTER: {m['description']} | stage: {m['stage_name']}"]
    for key in config.FIELDS:
        f = facts.field_value(con, mid, key)
        if f.value not in (None, "") and f.source:
            lines.append(f"[CustomFieldValue:{f.source.clio_id}] {config.FIELDS[key]}: {f.value}")
    t = facts.tasks(con, mid, today)
    for item in t["overdue"] + t["upcoming"]:
        lines.append(f"[Task:{item.source.clio_id}] OPEN TASK due {item.due} ({item.days_from_today:+d} days): {item.name}")
    recent = [e for e in facts.timeline(con, mid) if e.kind in ("note", "email", "call")][-25:]
    for e in recent:
        lines.append(f"[{e.source.clio_type}:{e.source.clio_id}] {e.when} {e.kind.upper()}: {e.title}. {e.detail[:500]}")
    text = "\n".join(lines)
    return text, {f"{a}:{b}" for a, b in _TAG.findall(text)}


def story(con, mid: int, today: date | None = None) -> dict | None:
    """{"lines": [{label, text, sources: [Source]}], "injuries": [str]} or None when no AI provider is available."""
    today = today or date.today()
    material, tags = _material(con, mid, today)
    try:
        res = llm.complete(task="digest.bottom_line", system=SYSTEM, prompt=material, schema=BottomLine,
                           max_tokens=800)
    except (llm.LLMUnavailable, llm.LLMBadOutput):
        return None
    out = []
    for label, s in zip(LABELS, res.data.sentences[:3]):
        srcs = []
        for tag in s.sources:
            tag = tag.strip("[] ")
            if tag in tags:
                kind, cid = tag.split(":")
                srcs.append(facts.Source(kind, int(cid)))
        out.append({"label": label, "text": s.text.strip(), "sources": srcs})
    return {"lines": out, "injuries": [i.strip() for i in res.data.injuries[:4] if i.strip()]}


def bottom_line(con, mid: int, today: date | None = None) -> list[dict] | None:
    """The three labelled sentences only (same cached model call as story())."""
    st = story(con, mid, today)
    return st["lines"] if st else None
