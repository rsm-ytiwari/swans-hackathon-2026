"""Offline tests for app/core/llm.py using a fake provider."""

import json

import pydantic
import pytest

from app.core import llm


class Out(pydantic.BaseModel):
    label: str
    n: int


@pytest.fixture(autouse=True)
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    monkeypatch.delenv("LLM_FALLBACK", raising=False)
    monkeypatch.delenv("LLM_REPLAY", raising=False)
    yield
    for n in ("fake", "fake2"):
        llm.unregister_provider(n)


def make(replies, calls):
    it = iter(replies)

    def fn(model, system, prompt, schema, max_tokens):
        calls.append(prompt)
        r = next(it)
        if isinstance(r, Exception):
            raise r
        return r, 10, 5

    return fn


def test_cache_hit_no_second_call():
    calls = []
    llm.register_provider("fake", make(['{"label":"a","n":1}'], calls))
    r1 = llm.complete(task="t", system="s", prompt="p", schema=Out)
    r2 = llm.complete(task="t", system="s", prompt="p", schema=Out)
    assert len(calls) == 1
    assert (r1.cached, r2.cached) == (False, True)
    assert r2.data == Out(label="a", n=1) and r2.provider == "fake"


def test_replay_miss_raises_and_hit_works(monkeypatch):
    calls = []
    llm.register_provider("fake", make(["hello"], calls))
    monkeypatch.setenv("LLM_REPLAY", "1")
    with pytest.raises(llm.LLMUnavailable):
        llm.complete(task="t", system="s", prompt="p")
    assert calls == []
    monkeypatch.delenv("LLM_REPLAY")
    llm.complete(task="t", system="s", prompt="p")
    monkeypatch.setenv("LLM_REPLAY", "1")
    assert llm.complete(task="t", system="s", prompt="p").cached


def test_schema_retry_once_then_succeeds():
    calls = []
    llm.register_provider("fake", make(['{"label":"a"}', '{"label":"a","n":2}'], calls))
    r = llm.complete(task="t", system="s", prompt="p", schema=Out)
    assert len(calls) == 2 and "invalid" in calls[1] and r.data.n == 2
    assert r.input_tokens == 20


def test_schema_retry_then_raises():
    calls = []
    llm.register_provider("fake", make(["nope", "still nope"], calls))
    with pytest.raises(llm.LLMBadOutput):
        llm.complete(task="t", system="s", prompt="p", schema=Out)
    assert len(calls) == 2


def test_fallback_order(monkeypatch):
    c1, c2 = [], []
    llm.register_provider("fake", make([RuntimeError("down")], c1))
    llm.register_provider("fake2", make(["ok"], c2))
    monkeypatch.setenv("LLM_FALLBACK", "fake2")
    r = llm.complete(task="t", system="s", prompt="p")
    assert r.provider == "fake2" and len(c1) == 1 and len(c2) == 1


def test_unconfigured_skipped_and_all_fail(monkeypatch):
    c = []
    llm.register_provider("fake", make(["x"], c), configured=lambda: False)
    with pytest.raises(llm.LLMUnavailable, match="not configured"):
        llm.complete(task="t", system="s", prompt="p")
    assert c == []


def test_usage_log_and_cost_report(tmp_path):
    llm.register_provider("fake", make(["a", "b"], []))
    llm.complete(task="triage.x", system="s", prompt="p1")
    llm.complete(task="triage.x", system="s", prompt="p1")  # cached
    llm.complete(task="other", system="s", prompt="p2")
    rows = [json.loads(l) for l in (tmp_path / "usage.jsonl").read_text().splitlines()]
    assert [r["cached"] for r in rows] == [False, True, False]
    assert {"task", "provider", "model", "input_tokens", "output_tokens", "cost_usd", "ts"} <= rows[0].keys()
    rep = llm.cost_report("triage")
    assert rep["calls"] == 2 and rep["cached_calls"] == 1 and rep["input_tokens"] == 10


def test_pricing():
    assert llm._cost("claude-haiku-4-5", "anthropic", 1_000_000, 1_000_000) == pytest.approx(6.0)
    assert llm._cost("gemma4:26b", "ollama", 999, 999) == 0.0
