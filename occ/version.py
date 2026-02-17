"""Version helpers.

We intentionally keep version lookup robust for:
- editable installs
- direct script execution from repo
- frozen desktop binaries
"""

from __future__ import annotations

import os
import re
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

PACKAGE_NAME = "occ-mrd-runner"
_VERSION_RE = re.compile(r'^\s*version\s*=\s*"([^"]+)"\s*$')


def _read_pyproject_version() -> str | None:
    meipass = getattr(sys, "_MEIPASS", "")
    candidates = [
        Path(__file__).resolve().parents[1] / "pyproject.toml",
        Path.cwd() / "pyproject.toml",
    ]
    if meipass:
        candidates.insert(0, Path(str(meipass)) / "pyproject.toml")
    for candidate in candidates:
        try:
            if not candidate.is_file():
                continue
            for line in candidate.read_text(encoding="utf-8").splitlines():
                match = _VERSION_RE.match(line)
                if match:
                    return match.group(1).strip()
        except Exception:
            continue
    return None


def get_version(fallback: str = "") -> str:
    """Return package version with practical fallbacks."""

    env_version = str(os.getenv("OCC_APP_VERSION") or "").strip()
    if env_version:
        return env_version

    pyproject_version = _read_pyproject_version()
    if pyproject_version:
        return pyproject_version

    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        pass

    clean_fallback = fallback.strip()
    return clean_fallback if clean_fallback else "0.0.0"
