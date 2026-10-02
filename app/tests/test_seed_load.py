"""Offline tests for app/seed_load.py: deterministic ids, minimal seed, missing sections, idempotence."""

from app import seed_load, store
from app.core import facts

MINIMAL = {
    "matter_stages": {"stages_in_order": ["Open", "Closed"]},
    "contacts": {"items": [{"ref": "client", "body": {"type": "Person", "first_name": "Ann", "last_name": "Lee"}}]},
    "matter": {"body": {"client": {"id": "{{contact:client}}"}, "status": "Open", "open_date": "2024-01-02",
                        "matter_stage": {"id": "{{stage:Open}}"}, "description": "Lee v. Co"}},
    "notes": {"items": [{"body": {"type": "Matter", "matter": {"id": "{{matter_id}}"}, "date": "2024-01-03",
                                  "subject": "Hello", "detail": "Body text"}}]},
}


def _con(tmp_path):
    return store.connect(tmp_path / "t.db")


def test_synth_id_deterministic_positive_and_file_scoped():
    a = seed_load.synth_id("a.json", "{{contact:x}}")
    assert a == seed_load.synth_id("a.json", "{{contact:x}}")
    assert a != seed_load.synth_id("b.json", "{{contact:x}}")
    assert a != seed_load.synth_id("a.json", "{{contact:y}}")
    assert 0 < a < 2**53


def test_placeholders_resolve_to_ints_recursively():
    ld = seed_load.Loader(MINIMAL, "m.json")
    out = ld.resolve({"a": ["{{matter_id}}", {"id": "{{contact:client}}"}], "b": "plain {{not_whole}}"})
    assert out["a"][0] == ld.matter_id and isinstance(out["a"][1]["id"], int)
    assert out["a"][1]["id"] == ld.sid("{{contact:client}}")
    assert out["b"] == "plain {{not_whole}}"


def test_minimal_seed_loads_and_facts_read_it(tmp_path):
    con = _con(tmp_path)
    mid, counts = seed_load.load_seed(MINIMAL, "m.json", None, con)
    assert counts["notes"] == 1 and counts["contacts"] == 1
    m = facts.matter(con, mid)
    assert m["client_name"] == "Ann Lee" and m["stage_name"] == "Open"
    assert facts.client(con, mid).name == "Ann Lee"
    assert "seed:m.json" in con.execute("SELECT json FROM raw WHERE clio_type='Matter'").fetchone()[0]
    # idempotent: second load changes no row counts
    seed_load.load_seed(MINIMAL, "m.json", None, con)
    assert con.execute("SELECT count(*) FROM notes").fetchone()[0] == 1
    assert con.execute("SELECT count(*) FROM matters").fetchone()[0] == 1


def test_missing_sections_and_junk_items_do_not_crash(tmp_path, capsys):
    seed = {**MINIMAL, "notes": {"items": [{"nobody": 1}, "junk"]}, "tasks": None, "documents": {"items": "x"},
            "expenses": {"items": [{"body": {"type": "ExpenseEntry"}}]}, "extra_section": {"x": 1}}
    mid, counts = seed_load.load_seed(seed, "j.json", None, _con(tmp_path))
    assert counts["notes"] == 0 and counts["activities"] == 0 and counts["tasks"] == 0
    assert "warning" in capsys.readouterr().err
