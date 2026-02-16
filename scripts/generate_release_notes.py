#!/usr/bin/env python3
"""Generate release notes from CHANGELOG and recent commits."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path
from typing import List, Optional

try:
    import yaml  # type: ignore[import-untyped]
except ModuleNotFoundError:
    import sys

    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from occ.util import simple_yaml as yaml


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _project_version(pyproject: Path) -> str:
    text = _read(pyproject)
    m = re.search(r'^\s*version\s*=\s*"([^"]+)"\s*$', text, flags=re.MULTILINE)
    if not m:
        raise RuntimeError("Could not parse version from pyproject.toml")
    return m.group(1).strip()


def _citation_doi(cff: Path) -> str:
    raw = yaml.safe_load(_read(cff))
    if not isinstance(raw, dict):
        return ""
    return str(raw.get("doi") or "").strip()


def _extract_changelog_section(changelog: Path, version: str) -> str:
    text = _read(changelog)
    start_re = re.compile(rf"^## \[{re.escape(version)}\].*$", flags=re.MULTILINE)
    m = start_re.search(text)
    if not m:
        return ""
    start = m.end()
    end_m = re.search(r"^## \[", text[start:], flags=re.MULTILINE)
    end = start + end_m.start() if end_m else len(text)
    return text[start:end].strip()


def _git(args: List[str], cwd: Path) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True)
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def _previous_tag(cwd: Path) -> str:
    tags = _git(["tag", "--sort=-creatordate"], cwd).splitlines()
    return tags[0].strip() if tags else ""


def _commit_highlights(cwd: Path, since_ref: Optional[str], max_items: int) -> List[str]:
    range_expr = "HEAD"
    if since_ref:
        range_expr = f"{since_ref}..HEAD"
    out = _git(["log", range_expr, "--pretty=format:%s"], cwd)
    lines = [x.strip() for x in out.splitlines() if x.strip()]
    clean: List[str] = []
    low_signal = {"up", "wip", "fix", "update", "changes"}
    for line in lines:
        low = line.lower()
        if low.startswith("merge "):
            continue
        if low in low_signal:
            continue
        clean.append(line)
        if len(clean) >= max(1, max_items):
            break
    return clean


def _build_notes(
    version: str,
    doi: str,
    changelog_section: str,
    commits: List[str],
    since_ref: str,
) -> str:
    parts: List[str] = [f"## OCC v{version}", ""]
    if doi:
        parts.append(f"DOI (Zenodo): https://doi.org/{doi}")
        parts.append("")

    if changelog_section:
        parts.append(changelog_section)
        parts.append("")
    else:
        parts.append("_No explicit changelog section found for this version._")
        parts.append("")

    if commits:
        title = "### Commit highlights"
        if since_ref:
            title += f" ({since_ref}..HEAD)"
        parts.append(title)
        parts.append("")
        for c in commits:
            parts.append(f"- {c}")
        parts.append("")

    return "\n".join(parts).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate release notes from repo metadata.")
    parser.add_argument("--version", help="Release version (defaults to pyproject)")
    parser.add_argument(
        "--since-ref",
        help="Git reference to build commit highlights from (defaults to most recent tag)",
    )
    parser.add_argument("--max-commits", type=int, default=12, help="Max commit highlights")
    parser.add_argument("--output", help="Write notes to file instead of stdout")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    version = (
        str(args.version).strip()
        if args.version
        else _project_version(root / "pyproject.toml")
    )
    doi = _citation_doi(root / "CITATION.cff")
    changelog_section = _extract_changelog_section(root / "CHANGELOG.md", version)
    since_ref = str(args.since_ref).strip() if args.since_ref else _previous_tag(root)
    commits = _commit_highlights(root, since_ref=since_ref or None, max_items=int(args.max_commits))

    notes = _build_notes(version, doi, changelog_section, commits, since_ref)
    if args.output:
        Path(args.output).write_text(notes, encoding="utf-8")
    else:
        print(notes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
