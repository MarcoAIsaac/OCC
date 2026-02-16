"""Version helpers.

We intentionally keep the version lookup lightweight and robust for editable installs.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

PACKAGE_NAME = "occ-mrd-runner"


def get_version(fallback: str = "0.0.0") -> str:
    """Return installed package version (or fallback).

    This uses importlib.metadata which works for normal installs and editable installs.
    """

    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        return fallback
