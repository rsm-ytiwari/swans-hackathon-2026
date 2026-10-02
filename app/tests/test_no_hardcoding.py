"""Guard: no matter's data may appear in our code or templates (Swans reads the repo for hardcoding).

The forbidden strings come from the ingested data itself (client, contacts, matter number, document and
custom-field values), so this test holds for whatever matter is loaded and contains no case data itself.
"""

from pathlib import Path

import pytest

from app.core import facts

APP = Path(__file__).resolve().parents[1]
SCAN = [p for p in APP.rglob("*") if p.suffix in {".py", ".html", ".js"}
        and "static" not in p.parts and "tests" not in p.parts and "data" not in p.parts]

con = facts.connect()
pytestmark = pytest.mark.skipif(not facts.matters(con), reason="no ingested matter")


def _case_strings() -> set[str]:
    out = set()
    for m in facts.matters(con):
        out |= {m["display_number"], m["client_name"]}
        mid = m["clio_id"]
        out |= {p.name for p in facts.parties(con, mid)}
        out |= {d.name.rsplit(".", 1)[0] for d in facts.documents(con, mid)}
        for r in con.execute("SELECT value FROM custom_field_values WHERE matter_id = ?", (mid,)):
            if isinstance(r["value"], str):
                out.add(r["value"][:40])
        for r in con.execute("SELECT subject FROM notes WHERE matter_id = ?", (mid,)):
            out.add(r["subject"])
    # Short or generic strings would match innocently; keep the distinctive ones.
    return {s.strip() for s in out if s and len(s.strip()) >= 8}


def test_no_case_data_in_code():
    needles = _case_strings()
    hits = []
    for path in SCAN:
        text = path.read_text(errors="ignore")
        hits += [f"{path.relative_to(APP)}: {n!r}" for n in needles if n in text]
    assert not hits, "case data hardcoded in app code:\n" + "\n".join(hits)
