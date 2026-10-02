"""Web app: one FastAPI process, Jinja templates, Tailwind + HTMX + Alpine served locally (works offline).

Run:  uv run uvicorn app.web.main:app --reload --port 8000

Routes owned here are shared by both views: matter picker, click-to-source, document files.
Firm view routes live in app/web/firm.py, provider view routes in app/web/provider.py.
"""

import base64
import os
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from app.core import facts, status
from app.web import firm, provider
from app.web.deps import serve_document, templates

app = FastAPI(title="Case digest")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.middleware("http")
async def firm_password(request: Request, call_next):
    """Optional: when APP_PASSWORD is set (public demo link), firm pages need it via HTTP basic auth.
    Provider links (/p/...) stay open: their unguessable token is their access control."""
    pw = os.getenv("APP_PASSWORD")
    path = request.url.path
    if pw and not path.startswith(("/p/", "/static/")):
        header = request.headers.get("authorization", "")
        ok = False
        if header.startswith("Basic "):
            try:
                ok = base64.b64decode(header[6:]).decode().split(":", 1)[1] == pw
            except (ValueError, IndexError):
                ok = False
        if not ok:
            return Response("Password required", status_code=401, headers={"WWW-Authenticate": 'Basic realm="case brief"'})
    return await call_next(request)


app.include_router(firm.router)
app.include_router(provider.router)


_sync: dict = {"status": "idle", "message": ""}


def _run_sync() -> None:
    """Pull every open matter from Clio (read-only) into the local store, then reset AI jobs."""
    from app.clio.client import ClioClient
    from app.ingest import ingest_all
    try:
        ids = ingest_all(ClioClient())
        _sync.update(status="done", message=f"Synced {len(ids)} matter(s) from Clio.")
    except Exception as e:  # show the real reason (missing credentials, not authorized, network)
        _sync.update(status="error", message=f"Sync failed: {type(e).__name__}: {str(e)[:300]}")


@app.get("/")
def home(request: Request):
    """Every loaded matter, plus a plain-language status of Clio, data and AI (what's missing and how to fix it)."""
    con = facts.connect()
    return templates.TemplateResponse(request, "home.html", {
        "matters": facts.matters(con), "checks": status.all_checks(), "sync": _sync})


@app.post("/sync")
def sync():
    if _sync["status"] != "running":
        _sync.update(status="running", message="Syncing from Clio…")
        threading.Thread(target=_run_sync, daemon=True).start()
    return RedirectResponse("/", status_code=303)


@app.get("/source/{clio_type}/{clio_id}")
def source(request: Request, clio_type: str, clio_id: int):
    """The record behind any fact on screen; rendered into the shared source dialog."""
    con = facts.connect()
    rec = facts.source_record(con, clio_type, clio_id)
    if rec is None:
        raise HTTPException(404, "source not found")
    return templates.TemplateResponse(request, "source.html", {"type": clio_type, "rec": rec})


@app.get("/files/{doc_id}")
def file(doc_id: int):
    """Firm-side document access. MOCK: no login in this demo; in production this sits behind firm auth."""
    return serve_document(doc_id)
