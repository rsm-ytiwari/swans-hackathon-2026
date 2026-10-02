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


SYSTEM = (
    "You brief a personal-injury attorney who has 10 seconds. Use only the case material given. "
    "Write exactly 3 short sentences (max 25 words each): (1) where the case stands and what it turns "
    "on, (2) what is blocking progress right now, including who it is waiting on, (3) the most important "
    "recent development. Write complete, plain sentences a busy reader understands at a glance: no "
    "abbreviations or jargon (write 'range of motion', not 'ROM'), no semicolons, no lists inside a sentence, "
    "no hedging, no legal citations. For each sentence list the tags "
    "(like Note:123) of the records that support it, copied exactly from the material."
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


def bottom_line(con, mid: int, today: date | None = None) -> list[dict] | None:
    """[{text, sources: [Source]}] or None when no AI provider is available."""
    today = today or date.today()
    material, tags = _material(con, mid, today)
    try:
        res = llm.complete(task="digest.bottom_line", system=SYSTEM, prompt=material, schema=BottomLine,
                           max_tokens=800)
    except (llm.LLMUnavailable, llm.LLMBadOutput):
        return None
    out = []
    for s in res.data.sentences[:3]:
        srcs = []
        for tag in s.sources:
            tag = tag.strip("[] ")
            if tag in tags:
                kind, cid = tag.split(":")
                srcs.append(facts.Source(kind, int(cid)))
        out.append({"text": s.text.strip(), "sources": srcs})
    return out
