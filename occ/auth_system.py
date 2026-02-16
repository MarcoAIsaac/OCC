"""Authentication backends for OCC CLI.

Supports two modes:

- local: metadata/session state stored in a local JSON file.
- remote: session state managed by an external HTTP auth service.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Protocol

SUPPORTED_PROVIDERS = {"google", "github", "arxiv"}
SUPPORTED_BACKENDS = {"auto", "local", "remote"}
DEFAULT_REMOTE_TIMEOUT = 15
USER_AGENT = "occ-mrd-runner"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _token_preview(token: str) -> str:
    if len(token) <= 8:
        return "*" * len(token)
    return f"{token[:4]}...{token[-4:]}"


def default_auth_store_path() -> Path:
    env = os.getenv("OCC_AUTH_STORE")
    if env:
        return Path(env).expanduser().resolve()
    return (Path.home() / ".occ" / "auth.json").resolve()


def default_remote_auth_url() -> Optional[str]:
    raw = os.getenv("OCC_AUTH_REMOTE_URL")
    if not raw:
        return None
    return raw.strip() or None


def default_remote_auth_token() -> Optional[str]:
    raw = os.getenv("OCC_AUTH_REMOTE_TOKEN")
    if not raw:
        return None
    return raw.strip() or None


def _github_login_from_token(token: str) -> Optional[str]:
    req = urllib.request.Request(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read()
    except Exception:
        return None
    obj = json.loads(body.decode("utf-8", errors="replace"))
    login = obj.get("login")
    return str(login) if isinstance(login, str) and login else None


def _google_email_from_token(token: str) -> Optional[str]:
    url = f"https://oauth2.googleapis.com/tokeninfo?access_token={token}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read()
    except Exception:
        return None
    obj = json.loads(body.decode("utf-8", errors="replace"))
    email = obj.get("email")
    return str(email) if isinstance(email, str) and email else None


def best_effort_gh_token() -> Optional[str]:
    try:
        proc = subprocess.run(
            ["gh", "auth", "token"],
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    if proc.returncode != 0:
        return None
    tok = proc.stdout.strip()
    return tok if tok else None


def _json_or_empty(raw: bytes) -> Dict[str, Any]:
    try:
        obj = json.loads(raw.decode("utf-8", errors="replace"))
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


class _LocalAuthBackend:
    def __init__(self, path: Path) -> None:
        self.path = path.resolve()

    def _empty(self) -> Dict[str, Any]:
        return {
            "version": 1,
            "active_provider": None,
            "accounts": {},
            "events": [],
            "updated_at": _utcnow(),
        }

    def load(self) -> Dict[str, Any]:
        if not self.path.is_file():
            return self._empty()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return self._empty()
        if not isinstance(data, dict):
            return self._empty()
        if "accounts" not in data or not isinstance(data.get("accounts"), dict):
            data["accounts"] = {}
        if "events" not in data or not isinstance(data.get("events"), list):
            data["events"] = []
        if "active_provider" not in data:
            data["active_provider"] = None
        if "version" not in data:
            data["version"] = 1
        return data

    def save(self, data: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        try:
            os.chmod(self.path, 0o600)
        except Exception:
            pass

    def _append_event(self, data: Dict[str, Any], event: Dict[str, Any]) -> None:
        events = data.setdefault("events", [])
        if not isinstance(events, list):
            events = []
            data["events"] = events
        events.append(event)
        if len(events) > 500:
            del events[:-500]

    def login(
        self,
        provider: str,
        username: Optional[str],
        token: Optional[str],
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        provider = provider.strip().lower()
        if provider not in SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")

        inferred = username
        if (not inferred) and token:
            if provider == "github":
                inferred = _github_login_from_token(token)
            elif provider == "google":
                inferred = _google_email_from_token(token)

        if not inferred:
            raise ValueError(
                "Username/email is required for this provider. Pass --username "
                "(or provide a valid token for auto-detection where supported)."
            )

        now = _utcnow()
        data = self.load()
        accounts = data.setdefault("accounts", {})
        if not isinstance(accounts, dict):
            accounts = {}
            data["accounts"] = accounts

        prev = accounts.get(provider)
        created_at = prev.get("created_at") if isinstance(prev, dict) else now
        account: Dict[str, Any] = {
            "provider": provider,
            "username": inferred,
            "created_at": created_at,
            "last_login_at": now,
            "metadata": metadata or {},
        }
        if token:
            account["token_hash"] = _sha256_text(token)
            account["token_preview"] = _token_preview(token)

        accounts[provider] = account
        data["active_provider"] = provider
        data["updated_at"] = now
        self._append_event(
            data,
            {
                "ts": now,
                "action": "login",
                "provider": provider,
                "username": inferred,
            },
        )
        self.save(data)
        return account

    def logout(self, provider: Optional[str]) -> Dict[str, Any]:
        data = self.load()
        accounts = data.get("accounts", {})
        if not isinstance(accounts, dict):
            accounts = {}
            data["accounts"] = accounts

        target = (provider or data.get("active_provider") or "").strip().lower()
        if not target:
            return {"ok": True, "message": "No active session"}

        now = _utcnow()
        removed = accounts.pop(target, None)
        if data.get("active_provider") == target:
            data["active_provider"] = None
        data["updated_at"] = now
        self._append_event(
            data,
            {"ts": now, "action": "logout", "provider": target, "had_account": bool(removed)},
        )
        self.save(data)
        return {"ok": True, "provider": target, "had_account": bool(removed)}

    def status(self) -> Dict[str, Any]:
        data = self.load()
        accounts = data.get("accounts", {})
        if not isinstance(accounts, dict):
            accounts = {}

        public_accounts: Dict[str, Any] = {}
        for provider, raw in accounts.items():
            if not isinstance(raw, dict):
                continue
            public_accounts[provider] = {
                "provider": raw.get("provider"),
                "username": raw.get("username"),
                "created_at": raw.get("created_at"),
                "last_login_at": raw.get("last_login_at"),
                "token_preview": raw.get("token_preview"),
                "metadata": raw.get("metadata", {}),
            }

        events = data.get("events", [])
        if not isinstance(events, list):
            events = []

        return {
            "backend": "local",
            "version": data.get("version", 1),
            "store_path": str(self.path),
            "active_provider": data.get("active_provider"),
            "accounts": public_accounts,
            "events_count": len(events),
            "updated_at": data.get("updated_at"),
        }

    def events(self, limit: int) -> list[Dict[str, Any]]:
        data = self.load()
        events = data.get("events", [])
        if not isinstance(events, list):
            return []
        out: list[Dict[str, Any]] = []
        for e in events[-max(1, int(limit)) :]:
            if isinstance(e, dict):
                out.append(e)
        return out


class _RemoteAuthBackend:
    def __init__(self, base_url: str, token: Optional[str] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        if params:
            qs = urllib.parse.urlencode({k: str(v) for k, v in params.items()})
            url = f"{url}?{qs}"

        body: Optional[bytes] = None
        headers: Dict[str, str] = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=DEFAULT_REMOTE_TIMEOUT) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Remote auth HTTP {e.code}: {msg}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Remote auth unreachable: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Remote auth request failed: {e}") from e

        out = _json_or_empty(raw)
        if out:
            return out
        return {"ok": True}

    def login(
        self,
        provider: str,
        username: Optional[str],
        token: Optional[str],
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/auth/login",
            payload={
                "provider": provider,
                "username": username,
                "token": token,
                "metadata": metadata or {},
            },
        )

    def logout(self, provider: Optional[str]) -> Dict[str, Any]:
        return self._request("POST", "/auth/logout", payload={"provider": provider})

    def status(self) -> Dict[str, Any]:
        out = self._request("GET", "/auth/status")
        out.setdefault("backend", "remote")
        out.setdefault("remote_url", self.base_url)
        return out

    def events(self, limit: int) -> list[Dict[str, Any]]:
        out = self._request("GET", "/auth/events", params={"limit": max(1, int(limit))})
        if "events" in out and isinstance(out["events"], list):
            return [e for e in out["events"] if isinstance(e, dict)]
        if isinstance(out, dict):
            return [out]
        return []


class _AuthBackend(Protocol):
    def login(
        self,
        provider: str,
        username: Optional[str],
        token: Optional[str],
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        ...

    def logout(self, provider: Optional[str]) -> Dict[str, Any]:
        ...

    def status(self) -> Dict[str, Any]:
        ...

    def events(self, limit: int) -> list[Dict[str, Any]]:
        ...


class AuthStore:
    def __init__(
        self,
        path: Optional[Path] = None,
        backend: str = "auto",
        remote_url: Optional[str] = None,
        remote_token: Optional[str] = None,
    ) -> None:
        backend = backend.strip().lower()
        if backend not in SUPPORTED_BACKENDS:
            raise ValueError(
                f"Unsupported auth backend: {backend}. "
                f"Expected one of {sorted(SUPPORTED_BACKENDS)}"
            )

        self.path = (path or default_auth_store_path()).resolve()
        self.remote_url = (remote_url or default_remote_auth_url() or "").strip()
        self.remote_token = (remote_token or default_remote_auth_token() or "").strip() or None

        if backend == "auto":
            backend = "remote" if self.remote_url else "local"
        if backend == "remote" and not self.remote_url:
            raise ValueError(
                "Remote auth backend requires URL. Set --remote-url or OCC_AUTH_REMOTE_URL."
            )

        self.backend = backend
        self._impl: _AuthBackend
        if backend == "remote":
            self._impl = _RemoteAuthBackend(base_url=self.remote_url, token=self.remote_token)
        else:
            self._impl = _LocalAuthBackend(path=self.path)

    def login(
        self,
        provider: str,
        username: Optional[str],
        token: Optional[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self._impl.login(
            provider=provider,
            username=username,
            token=token,
            metadata=metadata,
        )

    def logout(self, provider: Optional[str] = None) -> Dict[str, Any]:
        return self._impl.logout(provider=provider)

    def status(self) -> Dict[str, Any]:
        out = self._impl.status()
        if not isinstance(out, dict):
            return {"backend": self.backend}
        out.setdefault("backend", self.backend)
        return out

    def events(self, limit: int = 20) -> list[Dict[str, Any]]:
        return self._impl.events(limit=limit)
