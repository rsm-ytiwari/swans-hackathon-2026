"""A case full of bad data (text in number fields, unparseable dates, unknown stage, nameless contacts, a
task with no due date) must render every page, never crash. Runs on a throwaway database."""

from fastapi.testclient import TestClient

from app import seed_load, store
from app.core import facts, jobs, sharing

M = "{{matter_id}}"


def _cf(name, value):
    return {"custom_field": {"id": "{{field:%s}}" % name}, "value": value}


BAD = {
    "matter_stages": {"stages_in_order": ["Intake", "Treatment", "Litigation", "Closed"]},
    "custom_fields": {"items": [{"body": {"name": n, "parent_type": "Matter", "field_type": "text"}} for n in (
        "Date of Incident", "Estimated Case Value", "Medical Specials To Date", "Policy Limits",
        "Health Insurance or Lien Holder", "Case Summary")]},
    "contacts": {"items": [{"ref": "client", "body": {"type": "Person", "first_name": "Bad"}},
                           {"ref": "prov", "body": {"type": "Company", "name": ""}}]},
    "matter": {"body": {"client": {"id": "{{contact:client}}"}, "description": "", "status": "Open",
                        "open_date": "not-a-date", "matter_stage": {"id": "{{stage:Nonexistent}}"},
                        "custom_field_values": [
                            _cf("Date of Incident", "sometime in 2024"), _cf("Estimated Case Value", "TBD"),
                            _cf("Medical Specials To Date", "n/a"), _cf("Policy Limits", "unknown"),
                            _cf("Health Insurance or Lien Holder", "Medicaid, amount pending"), _cf("Case Summary", "")]}},
    "relationships": {"items": [{"body": {"matter": {"id": M}, "contact": {"id": "{{contact:prov}}"},
                                          "description": "Treating provider"}}]},
    "notes": {"items": [{"body": {"type": "Matter", "matter": {"id": M}, "date": "2099-13-45", "subject": "", "detail": ""}}]},
    "tasks": {"items": [{"body": {"name": "No due date", "status": "pending", "matter": {"id": M}}},
                        {"body": {"name": "Bad due date", "due_at": "yesterday", "status": "pending", "matter": {"id": M}}}]},
    "calendar_entries": {"items": [{"body": {"summary": "", "start_at": "garbage", "matter": {"id": M}}}]},
}


def test_every_page_survives_bad_data(tmp_path, monkeypatch):
    con = store.connect(tmp_path / "bad.db")
    mid, _ = seed_load.load_seed(BAD, "bad.json", None, con)
    monkeypatch.setattr(facts, "connect", lambda: store.connect(tmp_path / "bad.db"))
    monkeypatch.setattr(sharing, "APP_DB", tmp_path / "app.db")
    monkeypatch.setattr(jobs, "ensure", lambda m, t: {"status": "error", "error": "AI off in this test"})
    monkeypatch.delenv("APP_PASSWORD", raising=False)
    from app.web.main import app

    c = TestClient(app)
    provs = facts.providers(facts.connect(), mid)
    pid = provs[0].party.contact_id
    for path in ["/", f"/m/{mid}", f"/m/{mid}?since=2020-01-01", f"/m/{mid}/share", f"/m/{mid}/share/{pid}/preview"]:
        assert c.get(path).status_code == 200, path
    assert c.post(f"/m/{mid}/share/{pid}/publish", follow_redirects=False).status_code == 303
    token = sharing.publications_for(sharing.connect(), mid, pid)[0]["token"]
    assert c.get(f"/p/{token}").status_code == 200
    # Text in a number field is missing data, not a number
    assert facts.number("TBD") is None and facts.number("$375,000.00") == 375000.0
