"""Server-side deny-by-default for the provider side: a crafted POST can never widen what a provider sees."""

import json
import re

import pytest
from fastapi.testclient import TestClient

from app.core import config, facts, sharing
from app.web.main import app

con = facts.connect()


def _pick():
    """A matter + provider that has own bills and records on file."""
    for m in facts.matters(con):
        for p in facts.providers(con, m["clio_id"], None):
            if p.bills and p.records:
                return m["clio_id"], p.party.contact_id
    return None


PICK = _pick()
pytestmark = pytest.mark.skipif(PICK is None, reason="no ingested matter with a provider")


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.delenv("APP_PASSWORD", raising=False)
    monkeypatch.setattr(sharing, "APP_DB", tmp_path / "app.db")  # never touch the real publications
    return TestClient(app, follow_redirects=False)


def _publish(client, mid, pid) -> str:
    assert client.post(f"/m/{mid}/share/{pid}/publish").status_code == 303
    return sharing.publications_for(sharing.connect(), mid, pid)[0]["token"]


def test_forged_keys_ignored(client):
    mid, pid = PICK
    non_clinical = next(d.doc_id for d in facts.documents(con, mid)
                        if not any(k in d.folder.lower() for k in config.PROVIDER_DOC_FOLDERS))
    r = client.post(f"/m/{mid}/share/{pid}/policy", data={
        "notes": "1", "emails": "1", "communications": "1", "case_value": "1", "liability": "1",
        "status": "1", "doc": [str(non_clinical), "999999999", "abc"]})
    assert r.status_code == 303
    policy = sharing.get_policy(sharing.connect(), mid, pid)
    assert policy.sections == {"status"}  # only the known key survived
    assert policy.shared_doc_ids == set()  # non-clinical, unknown and malformed doc ids dropped
    pkt = sharing.build_packet(con, mid, pid, policy)
    assert pkt.bills is None and pkt.records is None and pkt.shared_documents is None
    assert set(json.loads(pkt.to_json())) == set(sharing.ProviderPacket.__dataclass_fields__)  # no extra keys


def test_bad_token_404(client):
    assert client.get("/p/not-a-real-token").status_code == 404
    assert client.get("/p/not-a-real-token/files/1").status_code == 404


def test_file_outside_packet_403(client):
    mid, pid = PICK
    token = _publish(client, mid, pid)
    outside = next(d.doc_id for d in facts.documents(con, mid)
                   if d.doc_id not in {x.doc_id for p in facts.providers(con, mid, None)
                                       if p.party.contact_id == pid for x in p.records + p.bills})
    assert client.get(f"/p/{token}/files/{outside}").status_code == 403


def test_publish_unknown_provider_404(client):
    mid, _ = PICK
    assert client.post(f"/m/{mid}/share/1/publish").status_code == 404


def test_published_page_has_no_strategy_values(client):
    mid, pid = PICK
    client.post(f"/m/{mid}/share/{pid}/policy", data={k: "1" for k in sharing.SECTIONS})
    token = _publish(client, mid, pid)
    r = client.get(f"/p/{token}")
    assert r.status_code == 200
    html = re.sub(r"\s+", " ", r.text).lower()
    values = [str(facts.field_value(con, mid, k).value).strip().lower() for k in config.STRATEGY_FIELDS]
    values = [v for v in values if len(v) >= 6 and v != "none"]
    assert values, "matter has no strategy values to check against"
    assert not [v for v in values if v in html]
