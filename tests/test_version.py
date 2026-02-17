from __future__ import annotations

from occ import version as version_mod


def test_get_version_prefers_env_override(monkeypatch) -> None:
    monkeypatch.setenv("OCC_APP_VERSION", "9.9.9")
    monkeypatch.setattr(version_mod, "_read_pyproject_version", lambda: "1.2.3")
    monkeypatch.setattr(version_mod, "version", lambda _name: "0.0.1")
    assert version_mod.get_version() == "9.9.9"


def test_get_version_prefers_pyproject_over_metadata(monkeypatch) -> None:
    monkeypatch.delenv("OCC_APP_VERSION", raising=False)
    monkeypatch.setattr(version_mod, "_read_pyproject_version", lambda: "1.2.3")
    monkeypatch.setattr(version_mod, "version", lambda _name: "0.0.1")
    assert version_mod.get_version() == "1.2.3"


def test_read_pyproject_version_from_meipass(tmp_path, monkeypatch) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "\n".join(
            [
                "[project]",
                'name = "occ-mrd-runner"',
                'version = "7.7.7"',
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(version_mod.sys, "_MEIPASS", str(tmp_path), raising=False)
    assert version_mod._read_pyproject_version() == "7.7.7"
