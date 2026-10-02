"""Provider view + sharing controls (owner: Jenith).

Rule: provider-facing pages render ONLY a sharing.ProviderPacket, never app.core.facts directly (D-003).
The attorney console may use facts (it is firm-side).
"""

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.core import facts, sharing
from app.web.deps import serve_document, templates, today

router = APIRouter()


@router.get("/m/{mid}/share")
def console(request: Request, mid: int):
    """Attorney side: every provider, what each one can see, and what has been sent."""
    con, app_con = facts.connect(), sharing.connect()
    rows = []
    for p in facts.providers(con, mid, today()):
        pid = p.party.contact_id
        rows.append({"p": p, "policy": sharing.get_policy(app_con, mid, pid),
                     "sent": sharing.publications_for(app_con, mid, pid)})
    return templates.TemplateResponse(request, "provider/console.html", {
        "mid": mid, "m": facts.matter(con, mid), "rows": rows,
        "sections": sharing.SECTIONS, "never": sharing.NEVER_SHARED})


@router.post("/m/{mid}/share/{pid}/policy")
async def save_policy(request: Request, mid: int, pid: int):
    form = await request.form()
    policy = sharing.Policy({k for k in sharing.SECTIONS if form.get(k)},
                            {int(v) for v in form.getlist("doc")})
    sharing.save_policy(sharing.connect(), mid, pid, policy)
    return RedirectResponse(f"/m/{mid}/share/{pid}/preview", status_code=303)


@router.get("/m/{mid}/share/{pid}/preview")
def preview(request: Request, mid: int, pid: int):
    """Exactly what the provider would see, before the attorney approves it."""
    con = facts.connect()
    policy = sharing.get_policy(sharing.connect(), mid, pid)
    pkt = sharing.build_packet(con, mid, pid, policy, today())
    return templates.TemplateResponse(request, "provider/page.html",
                                      {"pkt": pkt.__dict__, "preview": True, "mid": mid, "pid": pid})


@router.post("/m/{mid}/share/{pid}/publish")
def publish(mid: int, pid: int, approved_by: str = Form("Attorney")):
    con, app_con = facts.connect(), sharing.connect()
    pkt = sharing.build_packet(con, mid, pid, sharing.get_policy(app_con, mid, pid), today())
    sharing.publish(app_con, mid, pid, pkt, approved_by)
    return RedirectResponse(f"/m/{mid}/share", status_code=303)


@router.get("/p/{token}")
def provider_page(request: Request, token: str):
    """The provider's read-only link. Renders the frozen, approved packet and records the view."""
    app_con = sharing.connect()
    pub = sharing.published(app_con, token)
    if pub is None:
        raise HTTPException(404, "link not found")
    sharing.record_view(app_con, token, request.headers.get("user-agent", ""))
    return templates.TemplateResponse(request, "provider/page.html",
                                      {"pkt": pub["packet"], "preview": False, "token": token})


@router.get("/p/{token}/files/{doc_id}")
def provider_file(token: str, doc_id: int):
    """A provider can open a document only if it is inside the packet behind their link."""
    pub = sharing.published(sharing.connect(), token)
    if pub is None:
        raise HTTPException(404, "link not found")
    pkt = pub["packet"]
    allowed = {d["doc_id"] for d in (pkt.get("records") or []) + (pkt.get("shared_documents") or [])}
    allowed |= {d["doc_id"] for d in ((pkt.get("bills") or {}).get("documents") or [])}
    if doc_id not in allowed:
        raise HTTPException(403, "not shared with this provider")
    return serve_document(doc_id)
