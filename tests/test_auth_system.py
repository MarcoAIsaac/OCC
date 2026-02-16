from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from occ.auth_system import AuthStore


class _DummyResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> "_DummyResponse":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        return None


def test_local_auth_store_status(tmp_path: Path) -> None:
    store = AuthStore(path=tmp_path / "auth.json", backend="local")
    out = store.status()
    assert out["backend"] == "local"
    assert out["active_provider"] is None


def test_remote_auth_store_status(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_urlopen(req: Any, timeout: int = 0) -> _DummyResponse:
        _ = timeout
        url = req.full_url
        if url.endswith("/auth/status"):
            return _DummyResponse({"active_provider": "github", "accounts": {"github": {}}})
        return _DummyResponse({"ok": True})

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)

    store = AuthStore(
        backend="remote",
        remote_url="https://auth.example.com",
        remote_token="token123",
    )
    out = store.status()
    assert out["backend"] == "remote"
    assert out["active_provider"] == "github"
    assert out["remote_url"] == "https://auth.example.com"


def test_remote_backend_requires_url() -> None:
    with pytest.raises(ValueError, match="requires URL"):
        _ = AuthStore(backend="remote")
