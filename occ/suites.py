"""Suite discovery helpers.

The OCC repository can contain multiple suites:

* Canonical suite (15 modules): ``ILSC_MRD_suite_15_modulos_CANON``
* Extensions suite (meta-MRDs / tooling): ``ILSC_MRD_suite_extensions``

All discovery functions walk up the filesystem from a given start path.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional

SUITE_CANON = "ILSC_MRD_suite_15_modulos_CANON"
SUITE_EXTENSIONS = "ILSC_MRD_suite_extensions"


@dataclass(frozen=True)
class SuiteRoots:
    canon: Optional[Path]
    extensions: Optional[Path]

    def as_dict(self) -> Dict[str, Path]:
        out: Dict[str, Path] = {}
        if self.canon:
            out["canon"] = self.canon
        if self.extensions:
            out["extensions"] = self.extensions
        return out


def _walk_up(start: Path) -> Iterable[Path]:
    p = start.resolve()
    yield p
    yield from p.parents


def find_repo_root(start: Path) -> Optional[Path]:
    """Return repo root (best effort) by looking for ``pyproject.toml``."""

    for parent in _walk_up(start):
        if (parent / "pyproject.toml").is_file():
            return parent
    return None


def find_suite_root(start: Path, suite_dir_name: str) -> Optional[Path]:
    """Find suite root directory by name, walking up from ``start``."""

    for parent in _walk_up(start):
        cand = parent / suite_dir_name
        if cand.is_dir():
            return cand
    return None


def discover_suite_roots(start: Path) -> SuiteRoots:
    """Discover canon/extensions suite roots starting from ``start``."""

    canon = find_suite_root(start, SUITE_CANON)
    ext = find_suite_root(start, SUITE_EXTENSIONS)
    return SuiteRoots(canon=canon, extensions=ext)
