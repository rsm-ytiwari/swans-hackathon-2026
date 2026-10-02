"""Provider-agnostic LLM wrapper (D-009, CLAUDE.md rules 3 and 5).

Every AI feature calls `complete(...)`. Nothing here knows about any case.
Providers: claude_cli (local Claude Code login, no key), anthropic, gemini, ollama (env-configured). Every call is cached on disk
(app/cache/llm/) and logged to usage.jsonl. LLM_REPLAY=1 serves the cache only (offline demo).
Callers catch LLMUnavailable and show "AI off"; deterministic features must never depend on this.

Env: LLM_PROVIDER (primary), LLM_FALLBACK (comma list), LLM_REPLAY=1,
     ANTHROPIC_API_KEY/ANTHROPIC_MODEL, GEMINI_API_KEY/GEMINI_MODEL, OLLAMA_MODEL/OLLAMA_URL.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pydantic
import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_CACHE_DIR = Path(__file__).resolve().parents[1] / "cache" / "llm"
AUTO_ORDER = ["claude_cli", "anthropic", "gemini", "ollama"]

# USD per million (input, output) tokens. Ollama is local = 0.
PRICING: dict[str, tuple[float, float]] = {
    # Anthropic public pricing page (claude.com/pricing): Haiku 4.5 $1 in / $5 out.
    "claude-haiku-4-5": (1.00, 5.00),
    # Anthropic public pricing: Sonnet class $3 / $15. ASSUMED for any Sonnet id used here.
    "claude-sonnet-5-5": (3.00, 15.00),  # ASSUMED
    # Google public pricing for Flash-class models; exact figure for this id not confirmed. ASSUMED
    "gemini-3.8-flash": (0.30, 2.50),  # ASSUMED
    # claude_cli runs on the user's Claude subscription (not billed per token). We still report the
    # API-equivalent cost so "cost per case" is comparable: haiku alias = Haiku 4.5 pricing above.
    "haiku": (1.00, 5.00),
}
DEFAULT_GEMINI_PRICE = (0.30, 2.50)  # ASSUMED, used for unlisted gemini models


class LLMUnavailable(RuntimeError):
    """No provider configured, all failed, or replay mode with a cache miss."""


class LLMBadOutput(RuntimeError):
    """Model output failed schema validation after one retry."""


@dataclass
class LLMResult:
    text: str
    data: pydantic.BaseModel | None
    provider: str
    model: str
    cached: bool
    input_tokens: int
    output_tokens: int
    cost_usd: float


# ---------------------------------------------------------------- providers
# A provider fn: (model, system, prompt, json_schema | None, max_tokens) -> (text, in_tokens, out_tokens)
ProviderFn = Callable[[str, str, str, "dict | None", int], "tuple[str, int, int]"]


def _anthropic(model, system, prompt, schema, max_tokens):
    import anthropic

    client = anthropic.Anthropic(timeout=120)
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text")
    return text, resp.usage.input_tokens, resp.usage.output_tokens


def _claude_cli(model, system, prompt, schema, max_tokens):
    """Headless Claude Code (`claude -p`) on the logged-in user's subscription: no API key needed.
    Runs in a temp dir with no tools, settings, MCP or skills, so the prompt is all the model sees."""
    import subprocess
    import tempfile

    cmd = ["claude", "-p", "--model", model, "--output-format", "json", "--tools", "",
           "--system-prompt", system or "You are a careful assistant.", "--setting-sources", "",
           "--strict-mcp-config", "--disable-slash-commands"]
    if schema is not None:
        cmd += ["--json-schema", json.dumps(schema)]
    with tempfile.TemporaryDirectory() as cwd:
        out = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=600, cwd=cwd)
    if out.returncode != 0:
        raise RuntimeError(f"claude -p exited {out.returncode}: {out.stderr[:300]}")
    j = json.loads(out.stdout)
    if j.get("is_error"):
        raise RuntimeError(f"claude -p error: {str(j.get('result'))[:300]}")
    text = json.dumps(j["structured_output"]) if j.get("structured_output") is not None else j.get("result", "")
    u = j.get("usage", {})
    tin = u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
    return text, tin, u.get("output_tokens", 0)


def _gemini(model, system, prompt, schema, max_tokens):
    body: dict = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0},
    }
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    if schema is not None:
        body["generationConfig"]["responseMimeType"] = "application/json"
    # Gemini returns intermittent 503/429 under load; retry with backoff before falling through.
    for attempt in range(4):
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"].strip()},
            json=body,
            timeout=180,
        )
        if resp.status_code not in (429, 500, 502, 503, 504) or attempt == 3:
            break
        time.sleep(2 * 2**attempt)
    resp.raise_for_status()
    j = resp.json()
    text = "".join(p.get("text", "") for p in j["candidates"][0]["content"]["parts"])
    u = j.get("usageMetadata", {})
    return text, u.get("promptTokenCount", 0), u.get("candidatesTokenCount", 0)


def _ollama(model, system, prompt, schema, max_tokens):
    # Native API (not /v1): allows num_ctx, JSON-schema `format`, keep_alive. Same shape as
    # scripts/check_providers.py. think=False because Gemma 4 thinks by default (slow).
    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": prompt}
    ]
    body: dict = {
        "model": model,
        "messages": messages,
        "stream": False,
        "keep_alive": "2h",
        "think": False,
        "options": {"temperature": 0, "num_ctx": 32768, "num_predict": max_tokens},
    }
    if schema is not None:
        body["format"] = schema
    resp = requests.post(
        os.getenv("OLLAMA_URL", "http://localhost:11434") + "/api/chat", json=body, timeout=600
    )
    resp.raise_for_status()
    j = resp.json()
    return j["message"]["content"], j.get("prompt_eval_count", 0), j.get("eval_count", 0)


# name -> (fn, model_getter, configured_getter)
_PROVIDERS: dict[str, tuple[ProviderFn, Callable[[], str], Callable[[], bool]]] = {
    # Local default: the Claude Code CLI the user is logged into. Configured when `claude` is on PATH.
    "claude_cli": (
        _claude_cli,
        lambda: os.getenv("CLAUDE_CLI_MODEL") or "haiku",
        lambda: __import__("shutil").which("claude") is not None and os.getenv("CLAUDE_CLI_DISABLED") != "1",
    ),
    "anthropic": (
        _anthropic,
        lambda: os.getenv("ANTHROPIC_MODEL") or "claude-haiku-4-5",
        lambda: bool((os.getenv("ANTHROPIC_API_KEY") or "").strip()),
    ),
    "gemini": (
        _gemini,
        lambda: os.getenv("GEMINI_MODEL") or "gemini-3.8-flash",
        lambda: bool(os.getenv("GEMINI_API_KEY")),
    ),
    # Ollama has no key; it counts as configured only if OLLAMA_MODEL is set (failure falls through).
    "ollama": (
        _ollama,
        lambda: os.getenv("OLLAMA_MODEL") or "gemma4:26b",
        lambda: bool(os.getenv("OLLAMA_MODEL")),
    ),
}


def register_provider(
    name: str,
    fn: ProviderFn,
    model: str = "fake-model",
    configured: Callable[[], bool] = lambda: True,
) -> None:
    """Add or replace a provider (used by tests and for custom backends)."""
    _PROVIDERS[name] = (fn, lambda: model, configured)


def unregister_provider(name: str) -> None:
    _PROVIDERS.pop(name, None)


# ---------------------------------------------------------------- cache / usage
def _cache_dir() -> Path:
    d = Path(os.getenv("LLM_CACHE_DIR") or DEFAULT_CACHE_DIR)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _key(provider, model, system, prompt, schema_json, max_tokens) -> str:
    blob = json.dumps([provider, model, system, prompt, schema_json, max_tokens], sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def _cost(model: str, provider: str, tin: int, tout: int) -> float:
    if provider == "ollama":
        return 0.0
    pin, pout = PRICING.get(model) or (DEFAULT_GEMINI_PRICE if provider == "gemini" else (0.0, 0.0))
    return (tin * pin + tout * pout) / 1_000_000


def _log_usage(task, provider, model, tin, tout, cost, cached) -> None:
    row = {
        "task": task, "provider": provider, "model": model, "input_tokens": tin,
        "output_tokens": tout, "cost_usd": cost, "cached": cached,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    with open(_cache_dir() / "usage.jsonl", "a") as f:
        f.write(json.dumps(row) + "\n")


def cost_report(task_prefix: str | None = None) -> dict:
    """Sum usage.jsonl. cost_usd counts only real (non-cached) calls."""
    out = {"calls": 0, "cached_calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
    path = _cache_dir() / "usage.jsonl"
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if task_prefix and not r["task"].startswith(task_prefix):
            continue
        out["calls"] += 1
        if r["cached"]:
            out["cached_calls"] += 1
            continue
        out["input_tokens"] += r["input_tokens"]
        out["output_tokens"] += r["output_tokens"]
        out["cost_usd"] += r["cost_usd"]
    return out


# ---------------------------------------------------------------- core
def _chain() -> list[str]:
    primary = (os.getenv("LLM_PROVIDER") or "").strip()
    fallback = [p.strip() for p in (os.getenv("LLM_FALLBACK") or "").split(",") if p.strip()]
    names = ([primary] if primary else []) + fallback
    if not names:
        names = list(AUTO_ORDER)
    seen: list[str] = []
    for n in names:
        if n not in seen:
            seen.append(n)
    return seen


def _parse_json(text: str) -> object:
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        a, b = t.find("{"), t.rfind("}")
        if a != -1 and b > a:
            return json.loads(t[a : b + 1])
        raise


def _call_structured(fn, model, system, prompt, schema, schema_dict, max_tokens):
    """Call provider; validate against schema; one retry with the error appended."""
    sys_full = (
        f"{system}\n\nRespond with ONLY a JSON object matching this JSON Schema, no prose:\n"
        f"{json.dumps(schema_dict)}"
    )
    text, tin, tout = fn(model, sys_full, prompt, schema_dict, max_tokens)
    try:
        return text, schema.model_validate(_parse_json(text)), tin, tout
    except (ValueError, pydantic.ValidationError) as e:
        err = str(e)[:800]
    retry_prompt = (
        f"{prompt}\n\nYour previous reply was invalid:\n{text[:1500]}\n\nError: {err}\n"
        "Reply again with ONLY valid JSON matching the schema."
    )
    text2, tin2, tout2 = fn(model, sys_full, retry_prompt, schema_dict, max_tokens)
    try:
        data = schema.model_validate(_parse_json(text2))
    except (ValueError, pydantic.ValidationError) as e:
        raise LLMBadOutput(f"Output failed {schema.__name__} validation after retry: {str(e)[:300]}")
    return text2, data, tin + tin2, tout + tout2


def complete(
    *,
    task: str,
    system: str,
    prompt: str,
    schema: type[pydantic.BaseModel] | None = None,
    max_tokens: int = 2000,
) -> LLMResult:
    replay = os.getenv("LLM_REPLAY") == "1"
    schema_dict = schema.model_json_schema() if schema else None
    schema_json = json.dumps(schema_dict, sort_keys=True) if schema_dict else ""
    errors: list[str] = []
    bad_output = False

    # Any provider's cached answer first: if an earlier call fell back to a later provider, a page view
    # must not wait on a live retry of the first one.
    for name in _chain():
        if name in _PROVIDERS:
            model = _PROVIDERS[name][1]()
            path = _cache_dir() / f"{_key(name, model, system, prompt, schema_json, max_tokens)}.json"
            if path.exists():
                c = json.loads(path.read_text())
                data = schema.model_validate(json.loads(c["text"])) if schema else None
                _log_usage(task, name, model, c["input_tokens"], c["output_tokens"], 0.0, True)
                return LLMResult(c["text"], data, name, model, True, c["input_tokens"], c["output_tokens"], 0.0)

    for name in _chain():
        if name not in _PROVIDERS:
            errors.append(f"{name}: unknown provider")
            continue
        fn, model_get, configured = _PROVIDERS[name]
        model = model_get()
        key = _key(name, model, system, prompt, schema_json, max_tokens)
        path = _cache_dir() / f"{key}.json"

        if path.exists():
            c = json.loads(path.read_text())
            data = schema.model_validate(json.loads(c["text"])) if schema else None
            _log_usage(task, name, model, c["input_tokens"], c["output_tokens"], 0.0, True)
            return LLMResult(c["text"], data, name, model, True, c["input_tokens"], c["output_tokens"], 0.0)
        if replay:
            errors.append(f"{name}: not in cache")
            continue
        if not configured():
            errors.append(f"{name}: not configured")
            continue
        try:
            if schema:
                text, data, tin, tout = _call_structured(
                    fn, model, system, prompt, schema, schema_dict, max_tokens
                )
                text = data.model_dump_json()
            else:
                text, tin, tout = fn(model, system, prompt, None, max_tokens)
                data = None
        except LLMBadOutput as e:
            bad_output = True
            errors.append(f"{name}: {e}")
            continue
        except Exception as e:  # network, auth, rate limit: try the next provider
            errors.append(f"{name}: {type(e).__name__}: {str(e)[:200]}")
            continue
        cost = _cost(model, name, tin, tout)
        path.write_text(json.dumps({
            "provider": name, "model": model, "task": task, "text": text,
            "input_tokens": tin, "output_tokens": tout,
        }))
        _log_usage(task, name, model, tin, tout, cost, False)
        return LLMResult(text, data, name, model, False, tin, tout, cost)

    msg = "; ".join(errors) or "no providers"
    if bad_output:
        raise LLMBadOutput(msg)
    if replay:
        raise LLMUnavailable(f"LLM_REPLAY=1 and no cached response for task '{task}' ({msg})")
    raise LLMUnavailable(f"No LLM provider available ({msg})")


# ---------------------------------------------------------------- smoke
class _Smoke(pydantic.BaseModel):
    animal: str
    legs: int


def _smoke() -> int:
    ok = 0
    for name in AUTO_ORDER:
        _, _, configured = _PROVIDERS[name]
        if not configured():
            print(f"[skip] {name}: not configured")
            continue
        os.environ["LLM_PROVIDER"], os.environ["LLM_FALLBACK"] = name, ""
        for attempt in ("live  ", "repeat"):
            t = time.perf_counter()
            try:
                r = complete(
                    task="smoke", system="You answer in JSON.",
                    prompt="Name one common house pet and give its number of legs.", schema=_Smoke,
                    max_tokens=200,
                )
            except (LLMUnavailable, LLMBadOutput) as e:
                print(f"[fail] {name} {attempt}: {e}")
                break
            print(
                f"[ok] {name} {attempt} model={r.model} {time.perf_counter() - t:.2f}s "
                f"in={r.input_tokens} out={r.output_tokens} cost=${r.cost_usd:.6f} "
                f"cached={r.cached} data={r.data}"
            )
            if attempt == "repeat":
                ok += 1
    print("cost_report:", cost_report("smoke"))
    return 0 if ok else 1


if __name__ == "__main__":
    if "--smoke" in sys.argv:
        sys.exit(_smoke())
    print(__doc__)
