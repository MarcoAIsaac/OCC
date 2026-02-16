"""Local authentication/session helpers for OCC CLI.

This is a lightweight account/session system intended for developer workflows.
It stores account metadata locally and keeps an authentication event log.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

SUPPORTED_PROVIDERS = {"google", "github", "arxiv"}


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


def _github_login_from_token(token: str) -> Optional[str]:
    req = urllib.request.Request(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "occ-mrd-runner",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            obj = json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return None
    login = obj.get("login")
    return str(login) if isinstance(login, str) and login else None


def _google_email_from_token(token: str) -> Optional[str]:
    # Public tokeninfo endpoint (best effort).
    url = f"https://oauth2.googleapis.com/tokeninfo?access_token={token}"
    req = urllib.request.Request(url, headers={"User-Agent": "occ-mrd-runner"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            obj = json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return None
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


class AuthStore:
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = (path or default_auth_store_path()).resolve()

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
        metadata: Optional[Dict[str, Any]] = None,
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

        # arXiv does not provide a public OAuth login flow for third-party apps.
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

    def logout(self, provider: Optional[str] = None) -> Dict[str, Any]:
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
            "version": data.get("version", 1),
            "store_path": str(self.path),
            "active_provider": data.get("active_provider"),
            "accounts": public_accounts,
            "events_count": len(events),
            "updated_at": data.get("updated_at"),
        }

    def events(self, limit: int = 20) -> list[Dict[str, Any]]:
        data = self.load()
        events = data.get("events", [])
        if not isinstance(events, list):
            return []
        out: list[Dict[str, Any]] = []
        for e in events[-max(1, int(limit)) :]:
            if isinstance(e, dict):
                out.append(e)
        return out
