"""Offline tests for the read-only Clio client (D-001). A fake transport adapter records every request
that would hit the network, so we can prove refused writes never leave the process."""

import json

import pytest
import requests
from requests.adapters import BaseAdapter

from app.clio.client import ClioClient, ReadOnlySession, ReadOnlyViolation


class FakeAdapter(BaseAdapter):
    def __init__(self, responses):
        super().__init__()
        self.responses = list(responses)  # (status, body, headers)
        self.sent: list[requests.PreparedRequest] = []

    def send(self, request, **kwargs):
        self.sent.append(request)
        status, body, headers = self.responses.pop(0)
        resp = requests.Response()
        resp.status_code, resp.url, resp.request = status, request.url, request
        resp.headers.update(headers or {})
        resp._content = json.dumps(body).encode()
        return resp

    def close(self):
        pass


def make_client(responses, sleeps=None):
    session = ReadOnlySession()
    adapter = FakeAdapter(responses)
    session.mount("https://", adapter)
    refreshes = []
    client = ClioClient(
        token_provider=lambda force: refreshes.append(force) or "tok",
        session=session,
        sleep=(sleeps.append if sleeps is not None else lambda s: None),
    )
    return client, adapter, refreshes


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "post", "OPTIONS"])
def test_client_refuses_non_get_without_network(method):
    client, adapter, refreshes = make_client([])
    with pytest.raises(ReadOnlyViolation):
        client.request(method, "matters.json")
    assert adapter.sent == [] and refreshes == []


@pytest.mark.parametrize("call", ["post", "put", "patch", "delete"])
def test_session_helpers_refuse_writes(call):
    session = ReadOnlySession()
    adapter = FakeAdapter([])
    session.mount("https://", adapter)
    with pytest.raises(ReadOnlyViolation):
        getattr(session, call)("https://app.clio.com/api/v4/notes.json", json={"data": {}})
    assert adapter.sent == []


def test_client_rejects_writable_session():
    with pytest.raises(ReadOnlyViolation):
        ClioClient(token_provider=lambda f: "tok", session=requests.Session())


def test_get_is_allowed_and_sends_bearer():
    client, adapter, _ = make_client([(200, {"data": {"id": 1}}, {"X-API-VERSION": "4.0.13"})])
    assert client.get("matters/1.json", fields="id") == {"data": {"id": 1}}
    assert adapter.sent[0].method == "GET"
    assert adapter.sent[0].headers["Authorization"] == "Bearer tok"
    assert client.api_version == "4.0.13"


def test_paginate_follows_next_until_absent():
    nxt = "https://app.clio.com/api/v4/notes.json?page_token=abc&limit=200"
    client, adapter, _ = make_client([
        (200, {"data": [{"id": 1}, {"id": 2}], "meta": {"paging": {"next": nxt}}}, {}),
        (200, {"data": [{"id": 3}], "meta": {"paging": {}}}, {}),
    ])
    assert [r["id"] for r in client.paginate("notes.json", matter_id=9)] == [1, 2, 3]
    assert "matter_id=9" in adapter.sent[0].url and "limit=200" in adapter.sent[0].url
    assert adapter.sent[1].url == nxt


def test_429_waits_retry_after_then_succeeds():
    sleeps = []
    client, adapter, _ = make_client(
        [(429, {"error": {}}, {"Retry-After": "7"}), (200, {"data": []}, {})], sleeps=sleeps
    )
    assert client.get("tasks.json") == {"data": []}
    assert sleeps == [7.0] and len(adapter.sent) == 2


def test_401_refreshes_token_once():
    client, adapter, refreshes = make_client([(401, {}, {}), (200, {"data": []}, {})])
    client.get("tasks.json")
    assert True in refreshes and len(adapter.sent) == 2


def test_throttle_sleeps_before_exceeding_budget(monkeypatch):
    import app.clio.client as mod

    monkeypatch.setattr(mod, "RATE_LIMIT_BUDGET", 3)
    sleeps, t = [], [0.0]
    client = ClioClient(token_provider=lambda f: "tok", session=ReadOnlySession(),
                        sleep=lambda s: (sleeps.append(s), t.__setitem__(0, t[0] + s)), clock=lambda: t[0])
    for _ in range(4):
        client._throttle()
    assert len(sleeps) == 1 and sleeps[0] == pytest.approx(60.05)
