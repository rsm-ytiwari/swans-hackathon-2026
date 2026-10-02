"""Plain-language system status: what works, what's missing, and exactly how to fix it.
Shown on the home page and wherever an AI block is off, so a missing key never looks like a bug."""

import os

from app.clio import auth
from app.core import facts, llm


def ai() -> dict:
    """Which AI providers are usable right now, in the order the app will try them."""
    usable = [n for n in llm._chain() if n in llm._PROVIDERS and llm._PROVIDERS[n][2]()]
    if usable:
        return {"ok": True, "message": f"AI provider: {usable[0]}" + (f" (fallback: {', '.join(usable[1:])})" if usable[1:] else "")}
    return {"ok": False, "message": (
        "AI analysis is off because no AI provider is configured. Add GEMINI_API_KEY (or ANTHROPIC_API_KEY) "
        "to .env, or log in to Claude Code, or run Ollama, then restart the app. Everything else works without it.")}


def clio() -> dict:
    if not (os.getenv("CLIO_CLIENT_ID") and os.getenv("CLIO_CLIENT_SECRET")):
        return {"ok": False, "message": "Clio is not connected: CLIO_CLIENT_ID / CLIO_CLIENT_SECRET are missing from .env. "
                                         "You can still load a case from a seed file (see README)."}
    if auth.load_token() is None:
        return {"ok": False, "message": "Clio credentials are set but not authorized yet: run `uv run python -m app.clio.auth` and click Allow."}
    return {"ok": True, "message": "Clio connected (read-only)."}


def matters() -> dict:
    n = len(facts.matters(facts.connect()))
    if n:
        return {"ok": True, "message": f"{n} matter{'s' if n != 1 else ''} loaded."}
    return {"ok": False, "message": "No matters loaded yet. Click 'Sync from Clio', or run `uv run python -m app.ingest --all`, "
                                    "or load a seed file with `uv run python -m app.seed_load <file.json>`."}


def all_checks() -> list[dict]:
    return [{"name": "Case data", **matters()}, {"name": "Clio", **clio()}, {"name": "AI", **ai()}]
