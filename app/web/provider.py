"""Provider view + sharing controls.

Rule: provider-facing pages render ONLY a sharing.ProviderPacket, never app.core.facts directly (D-003).
The attorney console may use facts (it is firm-side).
"""

import re
from datetime import date

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.core import config, facts, sharing
from app.web.deps import serve_document, templates, today

router = APIRouter()

_DATE_TAIL = re.compile(r"[-_ ]*\d{4}[-_]\d{2}[-_]\d{2}$")


def doc_title(name: str | None) -> str:
    """Clean label for a document row: never the raw filename.
    '05-medical-bills__created__<who>-itemized-bill-2023-12-14.pdf' -> 'Itemized bill'."""
    stem = re.sub(r"\.[A-Za-z0-9]{2,4}$", "", name or "")
    cat, sep, rest = stem.partition("__")
    slug = _DATE_TAIL.sub("", rest.split("__")[-1] if sep else cat)
    cat = re.sub(r"^\d+[-_ ]*", "", cat) if sep else ""
    if "itemized" in slug and "bill" in slug:
        return "Itemized bill"
    words = re.sub(r"[-_]+", " ", cat or re.sub(r"^\d+[-_ ]*", "", slug)).strip()
    return words[:1].upper() + words[1:] if words else "Document"


def request_text(what: str | None) -> str:
    """Task names look like 'By medical provider: <name> - <what we need>'; the provider only needs the last part."""
    return (what or "").rsplit(" - ", 1)[-1].strip()


def short_date(v) -> str:
    if not v:
        return ""
    d = v if isinstance(v, date) else date.fromisoformat(str(v)[:10])
    return d.strftime("%b %-d")


templates.env.filters.update(doc_title=doc_title, request_text=request_text, short_date=short_date)


def _hidden(policy: "sharing.Policy") -> dict[str, str]:
    """section key -> label, for sections the provider will NOT see (grey placeholders in the preview)."""
    return {k: label for k, (label, _) in sharing.SECTIONS.items() if k not in policy.sections}


def _shareable_docs(con, mid: int, provider_id: int, own: set[int]) -> list:
    """Clinical documents of OTHER providers the attorney may choose to share (never pleadings, experts, etc.)."""
    return [d for d in facts.documents(con, mid) if d.doc_id not in own
            and any(k in d.folder.lower() for k in config.PROVIDER_DOC_FOLDERS)]


@router.get("/m/{mid}/share")
def console(request: Request, mid: int, provider: int | None = None):
    """Attorney side: pick a provider (left), set what they can see, live preview (right)."""
    con, app_con = facts.connect(), sharing.connect()
    t = today()
    if not facts.matter(con, mid):
        raise HTTPException(404, "matter not found")
    rows = []
    for p in facts.providers(con, mid, t):
        pid = p.party.contact_id
        sent = sharing.publications_for(app_con, mid, pid)
        rows.append({"p": p, "pid": pid, "sent": sent, "views": sum(s["views"] for s in sent),
                     "last_sent": sent[0]["approved_at"] if sent else None})
    # Open requests first, then by amount billed; providers with nothing on file yet stay pickable at the end.
    rows.sort(key=lambda r: (not r["p"].requests, -r["p"].billed_total))
    selected = next((r for r in rows if r["pid"] == provider), rows[0] if rows else None)
    ctx = {"mid": mid, "m": facts.matter(con, mid), "rows": rows, "selected": selected,
           "sections": sharing.SECTIONS, "never": sharing.NEVER_SHARED}
    if selected:
        policy = sharing.get_policy(app_con, mid, selected["pid"])
        sp = selected["p"]
        own = {d.doc_id for d in sp.records + sp.bills}
        ctx.update(policy=policy, pkt=sharing.build_packet(con, mid, selected["pid"], policy, t).__dict__,
                   hidden=_hidden(policy), preview=True,
                   other_docs=_shareable_docs(con, mid, selected["pid"], own))
    return templates.TemplateResponse(request, "provider/console.html", ctx)


@router.post("/m/{mid}/share/{pid}/policy")
async def save_policy(request: Request, mid: int, pid: int):
    form = await request.form()
    con = facts.connect()
    if not any(p.party.contact_id == pid for p in facts.providers(con, mid, today())):
        raise HTTPException(404, "provider not on this matter")
    # Deny by default: only known section keys count; any other form key (notes, emails, case_value...) is ignored.
    sections = {k for k in sharing.SECTIONS if form.get(k)}
    ok_docs = {d.doc_id for d in _shareable_docs(con, mid, pid, set())}
    docs = set()
    for v in form.getlist("doc"):
        try:
            if int(v) in ok_docs:  # must belong to this matter and be a clinical document
                docs.add(int(v))
        except (TypeError, ValueError):
            continue
    sharing.save_policy(sharing.connect(), mid, pid, sharing.Policy(sections, docs))
    return RedirectResponse(f"/m/{mid}/share?provider={pid}", status_code=303)


@router.get("/m/{mid}/share/{pid}/preview")
def preview(request: Request, mid: int, pid: int):
    """Exactly what the provider would see, before the attorney approves it."""
    con = facts.connect()
    policy = sharing.get_policy(sharing.connect(), mid, pid)
    try:
        pkt = sharing.build_packet(con, mid, pid, policy, today())
    except KeyError:
        raise HTTPException(404, "provider not on this matter")
    return templates.TemplateResponse(request, "provider/page.html",
                                      {"pkt": pkt.__dict__, "preview": True, "mid": mid, "pid": pid})


@router.post("/m/{mid}/share/{pid}/publish")
def publish(mid: int, pid: int, approved_by: str = Form("Attorney")):
    con, app_con = facts.connect(), sharing.connect()
    try:
        pkt = sharing.build_packet(con, mid, pid, sharing.get_policy(app_con, mid, pid), today())
        sharing.check_firewall(con, mid, pkt)  # refuse to publish anything that fails the firewall
    except KeyError:
        raise HTTPException(404, "provider not on this matter")
    except sharing.FirewallBreach as e:
        raise HTTPException(422, f"not published: {e}")
    sharing.publish(app_con, mid, pid, pkt, approved_by.strip()[:80] or "Attorney")
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
