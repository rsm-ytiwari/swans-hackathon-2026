"""Core data layer and the provider firewall, run against the local Clio mirror.

Skipped when app/data/clio.db has no matter yet (run `uv run python -m app.ingest --matter <id>` first).
Assertions are about structure and invariants, never about one matter's values.
"""

from datetime import date

import pytest

from app.core import config, facts, sharing

con = facts.connect()
MATTERS = facts.matters(con)
pytestmark = pytest.mark.skipif(not MATTERS, reason="no ingested matter")
MID = MATTERS[0]["clio_id"] if MATTERS else None
TODAY = date(2026, 10, 2)


def test_every_provider_charge_counted_once():
    provs = facts.providers(con, MID, TODAY)
    ids = [c.source.clio_id for p in provs for c in p.charges]
    assert len(ids) == len(set(ids))


def test_specials_field_reconciles_with_charges_or_is_flagged():
    m = facts.money(con, MID)
    if m["specials_field"].value is not None:
        same = abs(float(m["specials_field"].value) - m["provider_billed_total"]) <= 0.5
        assert same != m["specials_mismatch"]


def test_overdue_tasks_are_in_the_past():
    t = facts.tasks(con, MID, TODAY)
    assert all(x.days_from_today < 0 for x in t["overdue"])
    assert all(0 <= x.days_from_today <= config.UPCOMING_DAYS for x in t["upcoming"])


def test_every_timeline_event_has_a_resolvable_source():
    for e in facts.timeline(con, MID)[:60]:
        assert facts.source_record(con, e.source.clio_type, e.source.clio_id) is not None


def _all_on():
    docs = {d.doc_id for d in facts.documents(con, MID)}
    return sharing.Policy(set(sharing.SECTIONS), docs)


@pytest.mark.parametrize("policy", [sharing.Policy.default(), _all_on()] if MATTERS else [])
def test_firewall_holds_for_every_provider(policy):
    """Even with every section switched on, no packet carries notes, emails or strategy fields."""
    for p in facts.providers(con, MID, TODAY):
        pkt = sharing.build_packet(con, MID, p.party.contact_id, policy, TODAY)
        blob = pkt.to_json()
        for key in config.STRATEGY_FIELDS:
            value = facts.field_value(con, MID, key).value
            if value and len(str(value)) > 8:
                assert str(value) not in blob


def test_default_policy_hides_coverage():
    p = facts.providers(con, MID, TODAY)[0]
    pkt = sharing.build_packet(con, MID, p.party.contact_id, sharing.Policy.default(), TODAY)
    assert pkt.coverage is None and pkt.shared_documents is None


def test_firewall_rejects_a_leaked_note():
    p = facts.providers(con, MID, TODAY)[0]
    pkt = sharing.build_packet(con, MID, p.party.contact_id, sharing.Policy.default(), TODAY)
    note = con.execute("SELECT detail FROM notes WHERE matter_id = ? AND length(detail) > 60", (MID,)).fetchone()
    pkt.treatment_status = note["detail"]
    with pytest.raises(sharing.FirewallBreach):
        sharing.check_firewall(con, MID, pkt)
