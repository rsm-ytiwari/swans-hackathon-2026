"""Firm view (owner: Yash). Everything on this page comes from app.core.facts."""

from fastapi import APIRouter, Request

from app.core import facts
from app.web.deps import templates, today

router = APIRouter()


@router.get("/m/{mid}")
def firm_view(request: Request, mid: int):
    con = facts.connect()
    t = today()
    m = facts.matter(con, mid)
    client = facts.client(con, mid)
    ctx = {
        "mid": mid, "m": m, "today": t,
        "client": client,
        "client_contact": facts.contact(con, client.contact_id) if client else None,
        "last_client_contact": facts.last_contact_with(con, mid, client.contact_id) if client else None,
        "stages": facts.stages(con, mid),
        "incident_date": facts.field_value(con, mid, "incident_date"),
        "summary": facts.field_value(con, mid, "summary"),
        "tasks": facts.tasks(con, mid, t),
        "events": facts.calendar(con, mid, t),
        "money": facts.money(con, mid),
        "providers": facts.providers(con, mid, t),
    }
    return templates.TemplateResponse(request, "firm/index.html", ctx)
