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
def console(request: Request, mid: int, provider: int | None = None):
    """Attorney side: pick a provider (left), set what they can see, live preview (right)."""
    con, app_con = facts.connect(), sharing.connect()
    t = today()
    rows = []
    for p in facts.providers(con, mid, t):
        if not (p.charges or p.records or p.bills or p.requests):
            continue  # an individual clinician with nothing of their own on file
        pid = p.party.contact_id
        sent = sharing.publications_for(app_con, mid, pid)
        rows.append({"p": p, "pid": pid, "sent": sent, "views": sum(s["views"] for s in sent),
                     "last_sent": sent[0]["approved_at"] if sent else None})
    selected = next((r for r in rows if r["pid"] == provider), rows[0] if rows else None)
    ctx = {"mid": mid, "m": facts.matter(con, mid), "rows": rows, "selected": selected,
           "sections": sharing.SECTIONS, "never": sharing.NEVER_SHARED}
    if selected:
        policy = sharing.get_policy(app_con, mid, selected["pid"])
        ctx.update(policy=policy, pkt=sharing.build_packet(con, mid, selected["pid"], policy, t).__dict__,
                   hidden=sharing.hidden_sections(policy))
    return templates.TemplateResponse(request, "provider/console.html", ctx)


@router.post("/m/{mid}/share/{pid}/policy")
async def save_policy(request: Request, mid: int, pid: int):
    form = await request.form()
    policy = sharing.Policy({k for k in sharing.SECTIONS if form.get(k)},
                            {int(v) for v in form.getlist("doc")})
    sharing.save_policy(sharing.connect(), mid, pid, policy)
    return RedirectResponse(f"/m/{mid}/share?provider={pid}", status_code=303)


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
    return RedirectResponse(f"/m/{mid}/share?provider={pid}", status_code=303)


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
