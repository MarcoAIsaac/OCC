"""Module catalog helpers.

This scans MRD suites and exposes lightweight metadata for UX commands like:

- ``occ list``
- ``occ explain <module>``
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .runner import discover_module_runner
from .suites import SUITE_CANON, SUITE_EXTENSIONS, discover_suite_roots


@dataclass(frozen=True)
class MrdModuleInfo:
    name: str
    suite: str  # "canon" | "extensions"
    path: str
    runner: Optional[str]
    title: str
    summary: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def _read_first_heading(md_text: str) -> str:
    for line in md_text.splitlines():
        s = line.strip()
        if s.startswith("#"):
            return s.lstrip("#").strip()
    return ""


def _read_first_paragraph(md_text: str) -> str:
    lines: List[str] = []
    for line in md_text.splitlines():
        s = line.rstrip()
        if not s:
            if lines:
                break
            continue
        if s.lstrip().startswith("#"):
            continue
        lines.append(s)
        if len(lines) >= 3:
            break
    return " ".join(lines).strip()


def _pick_best_readme(mod_dir: Path) -> Optional[Path]:
    for cand in ("MRD_README.md", "README.md", "README_MODULES.md"):
        p = mod_dir / cand
        if p.is_file():
            return p
    return None


def iter_modules(suite_root: Path) -> Iterable[Path]:
    for p in sorted(suite_root.iterdir()):
        if p.is_dir() and p.name.startswith("mrd_"):
            yield p


def load_module_info(mod_dir: Path, suite: str) -> MrdModuleInfo:
    readme = _pick_best_readme(mod_dir)
    title = mod_dir.name
    summary = ""
    if readme:
        txt = readme.read_text(encoding="utf-8", errors="replace")
        title = _read_first_heading(txt) or title
        summary = _read_first_paragraph(txt)

    runner = discover_module_runner(mod_dir)
    return MrdModuleInfo(
        name=mod_dir.name,
        suite=suite,
        path=str(mod_dir),
        runner=str(runner) if runner else None,
        title=title,
        summary=summary,
    )


def build_catalog(start: Path, which: str = "all") -> List[MrdModuleInfo]:
    """Return a list of MRD module metadata.

    Args:
        start: any path within the repo.
        which: "canon", "extensions", or "all".
    """

    roots = discover_suite_roots(start)
    out: List[MrdModuleInfo] = []

    if which in ("canon", "all") and roots.canon:
        for m in iter_modules(roots.canon):
            out.append(load_module_info(m, "canon"))

    if which in ("extensions", "all") and roots.extensions:
        for m in iter_modules(roots.extensions):
            out.append(load_module_info(m, "extensions"))

    return out


def suite_dir_name(which: str) -> str:
    if which == "canon":
        return SUITE_CANON
    if which == "extensions":
        return SUITE_EXTENSIONS
    raise ValueError(f"Unknown suite: {which}")
