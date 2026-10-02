"""Shared web helpers: templates, 'today', formatting filters."""

import os
import re
from datetime import date
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

from app.core import facts

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def today() -> date:
    """Real date by default. APP_TODAY=YYYY-MM-DD pins it, so a recorded demo replays identically."""
    pinned = os.getenv("APP_TODAY")
    return date.fromisoformat(pinned) if pinned else date.today()


def money(v) -> str:
    try:
        return f"${float(v):,.2f}".replace(".00", "")
    except (TypeError, ValueError):
        return "—"


def nice_date(v) -> str:
    if not v:
        return "—"
    d = v if isinstance(v, date) else date.fromisoformat(str(v)[:10])
    return d.strftime("%b %-d, %Y")


def relative(days) -> str:
    if days is None:
        return ""
    if days == 0:
        return "today"
    return f"in {days} days" if days > 0 else f"{-days} days overdue"


def jdate(v) -> str:
    """"Apr 23 ’23" for compact timelines."""
    if not v:
        return "—"
    d = v if isinstance(v, date) else date.fromisoformat(str(v)[:10])
    return d.strftime("%b %-d ’%y")


def kmoney(v) -> str:
    """$375k / $118.4k / $950 for chart labels."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "—"
    if abs(v) >= 1000:
        k = v / 1000
        return f"${k:,.0f}k" if round(k, 1) == int(k) else f"${k:,.1f}k"
    return f"${v:,.0f}"


def doc_label(name) -> str:
    """Readable name for a stored file: "05-medical-bills__created__sportscare-pt-itemized-bill-2023-12-14.pdf"
    -> "Sportscare pt itemized bill". Display only; the source dialog still shows the real file."""
    s = str(name or "")
    s = re.sub(r"\.pdf$", "", s, flags=re.I)
    s = s.split("__")[-1]                          # drop "NN-folder__created__" / "doc-01__"
    s = re.sub(r"[-_ ]?\d{4}-\d{2}-\d{2}$", "", s)  # trailing date
    s = re.sub(r"^doc-\d+[-_ ]?", "", s)
    s = re.sub(r"[-_]+", " ", s).strip()
    return (s[:1].upper() + s[1:]) if s else str(name or "")


templates.env.filters.update(money=money, nice_date=nice_date, relative=relative, jdate=jdate,
                             kmoney=kmoney, doc_label=doc_label)


def serve_document(doc_id: int) -> FileResponse:
    path = facts.document_path(facts.connect(), doc_id)
    if not path or not Path(path).exists():
        raise HTTPException(404, "file not downloaded; run app.ingest")
    return FileResponse(path, media_type="application/pdf", content_disposition_type="inline")
