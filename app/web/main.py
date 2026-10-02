"""Web app: one FastAPI process, Jinja templates, Tailwind + HTMX + Alpine served locally (works offline).

Run:  uv run uvicorn app.web.main:app --reload --port 8000

Routes owned here are shared by both views: matter picker, click-to-source, document files.
Firm view routes live in app/web/firm.py, provider view routes in app/web/provider.py.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.core import facts
from app.web import firm, provider
from app.web.deps import serve_document, templates

app = FastAPI(title="Case digest")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.include_router(firm.router)
app.include_router(provider.router)


@app.get("/")
def home(request: Request):
    con = facts.connect()
    ms = facts.matters(con)
    if len(ms) == 1:
        return RedirectResponse(f"/m/{ms[0]['clio_id']}")
    return templates.TemplateResponse(request, "home.html", {"matters": ms})


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
