"""Clio OAuth 2.0 (authorization code grant) for a local, single-user tool.

`python -m app.clio.auth` opens the browser once; the user clicks Allow; the token is saved to
app/data/clio_token.json (gitignored). Access tokens last 30 days and are refreshed automatically.

The only POSTs this project ever sends go to Clio's OAuth token endpoint below, to obtain or refresh
our own token. No Clio record is ever written: data calls go through ReadOnlySession (client.py).
"""

import json
import os
import secrets
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from dotenv import load_dotenv

BASE_URL = "https://app.clio.com"  # US region
AUTHORIZE_URL = f"{BASE_URL}/oauth/authorize"
TOKEN_URL = f"{BASE_URL}/oauth/token"
REDIRECT_HOST, REDIRECT_PORT = "127.0.0.1", 8765
REDIRECT_URI = f"http://{REDIRECT_HOST}:{REDIRECT_PORT}/callback"
TOKEN_PATH = Path(__file__).resolve().parents[1] / "data" / "clio_token.json"
REFRESH_MARGIN_S = 24 * 3600  # refresh when less than a day of validity is left


class ClioAuthError(RuntimeError):
    pass


def _credentials() -> tuple[str, str]:
    load_dotenv()
    cid, secret = os.getenv("CLIO_CLIENT_ID"), os.getenv("CLIO_CLIENT_SECRET")
    if not cid or not secret:
        raise ClioAuthError("CLIO_CLIENT_ID / CLIO_CLIENT_SECRET missing from .env")
    return cid, secret


def _token_request(data: dict) -> dict:
    cid, secret = _credentials()
    resp = requests.post(TOKEN_URL, data={**data, "client_id": cid, "client_secret": secret}, timeout=30)
    if resp.status_code != 200:
        raise ClioAuthError(f"token endpoint returned {resp.status_code}: {resp.text[:300]}")
    token = resp.json()
    token["obtained_at"] = int(time.time())
    return token


def _save(token: dict, path: Path = TOKEN_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(token, indent=2))
    path.chmod(0o600)


def load_token(path: Path = TOKEN_PATH) -> dict | None:
    return json.loads(path.read_text()) if path.exists() else None


def _expires_at(token: dict) -> int:
    return int(token.get("obtained_at", 0)) + int(token.get("expires_in", 0))


def refresh(token: dict, path: Path = TOKEN_PATH) -> dict:
    if not token.get("refresh_token"):
        raise ClioAuthError("no refresh_token stored; run `uv run python -m app.clio.auth`")
    new = _token_request({"grant_type": "refresh_token", "refresh_token": token["refresh_token"]})
    new.setdefault("refresh_token", token["refresh_token"])  # Clio keeps the same refresh token
    _save(new, path)
    return new


def get_access_token(force_refresh: bool = False, path: Path = TOKEN_PATH) -> str:
    token = load_token(path)
    if token is None:
        raise ClioAuthError("not authorized yet; run `uv run python -m app.clio.auth` and click Allow")
    if force_refresh or _expires_at(token) - time.time() < REFRESH_MARGIN_S:
        token = refresh(token, path)
    return token["access_token"]


def login(open_browser: bool = True) -> dict:
    """Run the browser flow once and store the token."""
    cid, _ = _credentials()
    state = secrets.token_urlsafe(24)
    result: dict = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 (http.server API)
            url = urlparse(self.path)
            if url.path != "/callback":
                self.send_response(404)
                self.end_headers()
                return
            q = {k: v[0] for k, v in parse_qs(url.query).items()}
            result.update(q)
            ok = q.get("state") == state and "code" in q
            self.send_response(200 if ok else 400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            msg = "Clio authorized. You can close this tab." if ok else f"Authorization failed: {q}"
            self.wfile.write(msg.encode())

        def log_message(self, *args):
            pass

    server = HTTPServer((REDIRECT_HOST, REDIRECT_PORT), Handler)
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    url = AUTHORIZE_URL + "?" + urlencode(
        {"response_type": "code", "client_id": cid, "redirect_uri": REDIRECT_URI, "state": state}
    )
    print(f"Open this URL and click Allow:\n{url}\n")
    if open_browser:
        webbrowser.open(url)
    thread.join(timeout=300)
    server.server_close()

    if result.get("state") != state:
        raise ClioAuthError(f"state mismatch or no callback within 5 min: {result}")
    if "code" not in result:
        raise ClioAuthError(f"Clio did not return a code: {result}")
    token = _token_request(
        {"grant_type": "authorization_code", "code": result["code"], "redirect_uri": REDIRECT_URI}
    )
    _save(token)
    return token


if __name__ == "__main__":
    tok = login()
    print(f"Saved token to {TOKEN_PATH} (expires in {tok.get('expires_in')} s)")
