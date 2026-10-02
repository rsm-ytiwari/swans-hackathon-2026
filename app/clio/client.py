"""Read-only Clio Manage API v4 client (D-001).

Every request goes through ReadOnlySession, which refuses anything except GET/HEAD before any network
I/O. Handles cursor pagination (meta.paging.next), the 600 req / 60 s per-token limit, 429 Retry-After,
and one token refresh on 401.
"""

import time
from collections import deque
from collections.abc import Callable, Iterator
from pathlib import Path

import requests

from app.clio import auth

API_BASE = f"{auth.BASE_URL}/api/v4"
ALLOWED_METHODS = frozenset({"GET", "HEAD"})
RATE_LIMIT_PER_MIN = 600
RATE_LIMIT_BUDGET = 550  # stay under Clio's limit with a margin
MAX_RETRIES = 6


class ReadOnlyViolation(RuntimeError):
    """Raised when code tries to send a non-GET request to Clio."""


class ReadOnlySession(requests.Session):
    """A requests.Session that cannot write. Covers .post/.put/.patch/.delete too, since they all
    route through .request()."""

    def request(self, method, url, *args, **kwargs):
        if str(method).upper() not in ALLOWED_METHODS:
            raise ReadOnlyViolation(f"Clio is read-only for this app: refused {method} {url}")
        return super().request(method, url, *args, **kwargs)


class ClioError(RuntimeError):
    pass


class ClioClient:
    def __init__(
        self,
        token_provider: Callable[[bool], str] | None = None,
        session: requests.Session | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._token_provider = token_provider or (lambda force: auth.get_access_token(force_refresh=force))
        self._session = session or ReadOnlySession()
        if not isinstance(self._session, ReadOnlySession):
            raise ReadOnlyViolation("ClioClient only accepts a ReadOnlySession")
        self._sleep, self._clock = sleep, clock
        self._sent: deque[float] = deque()
        self.request_count = 0
        self.api_version: str | None = None

    # -- core -------------------------------------------------------------------------------
    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        if method.upper() not in ALLOWED_METHODS:  # fail before touching tokens or the network
            raise ReadOnlyViolation(f"Clio is read-only for this app: refused {method} {url}")
        if not url.startswith("http"):
            url = f"{API_BASE}/{url.lstrip('/')}"
        extra_headers = kwargs.pop("headers", {})
        refreshed = False
        for attempt in range(MAX_RETRIES):
            self._throttle()
            headers = {"Authorization": f"Bearer {self._token_provider(False)}", **extra_headers}
            resp = self._session.request(method, url, headers=headers, timeout=60, **kwargs)
            self.request_count += 1
            self.api_version = resp.headers.get("X-API-VERSION", self.api_version)
            if resp.status_code == 401 and not refreshed:
                self._token_provider(True)
                refreshed = True
                continue
            if resp.status_code == 429 or resp.status_code >= 500:
                wait = resp.headers.get("Retry-After")
                self._sleep(float(wait) if wait else min(2**attempt, 60))
                continue
            if resp.headers.get("X-RateLimit-Remaining") == "0" and resp.headers.get("X-RateLimit-Reset"):
                self._sleep(max(0.0, float(resp.headers["X-RateLimit-Reset"]) - time.time()) + 1)
            if resp.status_code >= 400:
                raise ClioError(f"GET {url} -> {resp.status_code}: {resp.text[:500]}")
            return resp
        raise ClioError(f"GET {url} failed after {MAX_RETRIES} attempts (last {resp.status_code})")

    def _throttle(self) -> None:
        """Client-side sliding window so we never hit the per-minute limit."""
        now = self._clock()
        while self._sent and now - self._sent[0] >= 60:
            self._sent.popleft()
        if len(self._sent) >= RATE_LIMIT_BUDGET:
            self._sleep(60 - (now - self._sent[0]) + 0.05)
            return self._throttle()
        self._sent.append(now)

    def get(self, path: str, **params) -> dict:
        return self.request("GET", path, params=params).json()

    def paginate(self, path: str, **params) -> Iterator[dict]:
        """Yield every record of a list endpoint, following meta.paging.next until absent."""
        params.setdefault("limit", 200)
        body = self.get(path, **params)
        while True:
            data = body.get("data", [])
            yield from data if isinstance(data, list) else [data]
            nxt = (body.get("meta") or {}).get("paging", {}).get("next")
            if not nxt:
                return
            body = self.request("GET", nxt).json()  # next URL already carries every param

    def list(self, path: str, **params) -> list[dict]:
        return list(self.paginate(path, **params))

    def download(self, document_id: int, dest: Path) -> int:
        """Stream a document's latest version to dest. Clio answers with a 303 to a signed URL;
        requests drops our Authorization header on the cross-host redirect."""
        resp = self.request("GET", f"documents/{document_id}/download.json", stream=True)
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        size = 0
        with tmp.open("wb") as fh:
            for chunk in resp.iter_content(1 << 16):
                fh.write(chunk)
                size += len(chunk)
        tmp.replace(dest)
        return size
