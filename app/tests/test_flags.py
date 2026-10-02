"""Offline tests for app/core/flags.py: rule flags on the ingested matter, contradiction verification with a fake LLM."""

import json
import re
from datetime import date

import pytest

from app.core import facts, flags, llm

con = facts.connect()
MATTERS = facts.matters(con)
needs_matter = pytest.mark.skipif(not MATTERS, reason="no ingested matter")
TAG = re.compile(r"\[(?:Note|Communication|CustomFieldValue):\d+\]")


@pytest.fixture(autouse=True)
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    monkeypatch.delenv("LLM_FALLBACK", raising=False)
    monkeypatch.delenv("LLM_REPLAY", raising=False)
    yield
    llm.unregister_provider("fake")


def _sections(prompt: str) -> list[tuple[str, str]]:
    """(tag, body) for each case-file item in the prompt."""
    parts = re.split(r"(\[(?:Note|Communication|CustomFieldValue):\d+\])\n", prompt)
    return [(parts[i], parts[i + 1].split("\n\n")[0]) for i in range(1, len(parts) - 1, 2)]


def _fake(fabricate: bool):
    def fn(model, system, prompt, schema, max_tokens):
        if "assertions" not in schema["properties"]:
            return json.dumps({"contradictions": []}), 1, 1
        secs = [s for s in _sections(prompt) if len(s[1]) > 60]
        (ta, ba), (tb, bb) = secs[0], secs[1]
        good = {"title": "Verified conflict", "why_it_matters": "First. Second. Third sentence.",
                "claim_a": {"tag": ta, "quote": ba[10:50]}, "claim_b": {"tag": tb, "quote": bb[10:50]}, "severity": "high"}
        bad = dict(good, title="Invented conflict",
                   claim_b={"tag": tb, "quote": "this sentence was never written anywhere in the file"})
        return json.dumps({"contradictions": [good] + ([bad] if fabricate else []),
                           "assertions": [{"tag": ta, "quote": ba[10:50]}]}), 5, 5
    return fn


@needs_matter
def test_fabricated_quote_dropped_verified_kept(tmp_path):
    mid = MATTERS[0]["clio_id"]
    llm.register_provider("fake", _fake(True))
    res = flags.compute(con, mid, date(2026, 10, 2), db_path=tmp_path / "app.db")
    assert res["ai"] == "ok"
    assert [f.title for f in res["contradictions"]] == ["Verified conflict"]
    assert res["dropped_unverified"] == 1
    f = res["contradictions"][0]
    assert f.kind == "contradiction" and len(f.evidence) == 2
    assert f.detail.count(".") <= 2  # at most two sentences kept
    # stored and reloadable
    again = flags.load(mid, db_path=tmp_path / "app.db")
    assert [x.key for x in again["contradictions"]] == [f.key]


@needs_matter
def test_unavailable_returns_empty_and_ai_off(tmp_path):
    mid = MATTERS[0]["clio_id"]

    def boom(*a):
        raise RuntimeError("down")

    llm.register_provider("fake", boom, configured=lambda: False)
    assert flags.contradiction_flags(con, mid) == []
    res = flags.compute(con, mid, date(2026, 10, 2), db_path=tmp_path / "app.db")
    assert res["ai"] == "off" and res["contradictions"] == [] and res["rules"] is not None


@needs_matter
def test_rule_flags_have_resolvable_sources():
    for m in MATTERS:
        out = flags.rule_flags(con, m["clio_id"], date(2026, 10, 2))
        for f in out:
            assert f.kind == "rule" and f.severity in {"high", "medium", "low"}
            assert f.title and len(f.title) <= 90 and "\n" not in f.title
            assert f.evidence, f.key
            for e in f.evidence:
                assert facts.source_record(con, e.source.clio_type, e.source.clio_id), (f.key, e.source)


def test_quote_check_and_amounts():
    assert flags._quote_in("The  client was\nnever discharged", "x. The client was never discharged from care.")
    assert not flags._quote_in("the client was discharged on the date", "The client was never seen again.")
    assert not flags._quote_in("short", "short text")
    assert flags._amounts("limits $100,000 / $300,000 and $1.5M, $2 million") == [100000, 300000, 1500000, 2000000]


def test_overdue_and_coverage_rules_on_synthetic_matter(tmp_path):
    from app import store
    db = store.connect(tmp_path / "synthetic.db")
    db.execute("INSERT INTO matters (clio_type, clio_id, display_number, status, stage_name, synced_at) VALUES ('Matter', 1, 'X-1', 'Open', 'Intake', 'n')")
    db.execute("INSERT INTO tasks (clio_type, clio_id, matter_id, name, status, due_at, synced_at) VALUES ('Task', 9, 1, 'Send letter', 'pending', '2026-01-01', 'n')")
    for cid, name, val in ((20, "Policy Limits", "$50,000 per person"), (21, "Estimated Case Value", 250000.0)):
        db.execute("INSERT INTO custom_field_values (clio_type, clio_id, matter_id, field_name, field_type, value, synced_at) VALUES ('CustomFieldValue', ?, 1, ?, 'text', ?, 'n')", (cid, name, val))
    out = {f.key: f for f in flags.rule_flags(db, 1, date(2026, 10, 2))}
    assert out["rule:overdue_tasks"].severity == "high" and "Send letter" in out["rule:overdue_tasks"].title
    assert out["rule:coverage_below_value"].severity == "high"
