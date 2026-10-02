"""Shared web helpers: templates, 'today', formatting filters."""

import os
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


templates.env.filters.update(money=money, nice_date=nice_date, relative=relative)


def serve_document(doc_id: int) -> FileResponse:
    path = facts.document_path(facts.connect(), doc_id)
    if not path or not Path(path).exists():
        raise HTTPException(404, "file not downloaded; run app.ingest")
    return FileResponse(path, media_type="application/pdf", content_disposition_type="inline")
