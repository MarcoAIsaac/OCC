#!/usr/bin/env python3
"""Audit EN/ES documentation consistency and local links."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


@dataclass
class Issue:
    level: str  # ERROR | WARN
    file: str
    message: str


LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^(#{2,3})\s+(.+?)\s*$")
CODE_BLOCK_RE = re.compile(r"```(?:bash|sh|powershell|pwsh|console|text)?\n(.*?)\n```", re.DOTALL)
CMD_RE = re.compile(r"^\s*(occ|make|python|pytest|ruff|mypy|mkdocs)\b")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _heading_profile(text: str) -> Dict[int, int]:
    out: Dict[int, int] = {2: 0, 3: 0}
    for line in text.splitlines():
        m = HEADING_RE.match(line)
        if not m:
            continue
        level = len(m.group(1))
        if level in out:
            out[level] += 1
    return out


def _command_count(text: str) -> int:
    total = 0
    for block in CODE_BLOCK_RE.findall(text):
        for line in block.splitlines():
            if CMD_RE.match(line):
                total += 1
    return total


def _local_links(path: Path, text: str) -> Iterable[Tuple[str, Path]]:
    for target in LINK_RE.findall(text):
        t = target.strip()
        if not t or t.startswith(("http://", "https://", "mailto:", "#")):
            continue
        clean = t.split("#", 1)[0].split("?", 1)[0].strip()
        if not clean:
            continue
        yield clean, (path.parent / clean).resolve()


def _pair_files(root: Path) -> List[Tuple[Path, Path]]:
    pairs: List[Tuple[Path, Path]] = []

    readme_en = root / "README.md"
    readme_es = root / "README.es.md"
    if readme_en.is_file():
        pairs.append((readme_en, readme_es))

    docs = root / "docs"
    for en in sorted(docs.glob("*.md")):
        name = en.name
        if name.endswith(".es.md"):
            continue
        stem = name[:-3]
        es = docs / f"{stem}.es.md"
        pairs.append((en, es))
    return pairs


def run_audit(root: Path) -> List[Issue]:
    issues: List[Issue] = []
    pairs = _pair_files(root)

    for en, es in pairs:
        if not en.is_file():
            continue
        if not es.is_file():
            issues.append(Issue("ERROR", str(en.relative_to(root)), f"Missing pair file: {es.name}"))
            continue

        en_text = _read(en)
        es_text = _read(es)

        en_head = _heading_profile(en_text)
        es_head = _heading_profile(es_text)
        for level in (2, 3):
            if abs(en_head[level] - es_head[level]) > 1:
                issues.append(
                    Issue(
                        "WARN",
                        str(en.relative_to(root)),
                        f"H{level} count mismatch EN={en_head[level]} ES={es_head[level]}",
                    )
                )

        en_cmds = _command_count(en_text)
        es_cmds = _command_count(es_text)
        if abs(en_cmds - es_cmds) > 2:
            issues.append(
                Issue(
                    "WARN",
                    str(en.relative_to(root)),
                    f"Command examples mismatch EN={en_cmds} ES={es_cmds}",
                )
            )

    for md in [p for p in [root / "README.md", root / "README.es.md"] if p.is_file()] + sorted(
        (root / "docs").glob("*.md")
    ):
        text = _read(md)
        for raw, resolved in _local_links(md, text):
            if not resolved.exists():
                issues.append(
                    Issue(
                        "ERROR",
                        str(md.relative_to(root)),
                        f"Broken local link: {raw}",
                    )
                )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit EN/ES docs consistency and local links.")
    parser.add_argument("--strict", action="store_true", help="Treat WARN as failure")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    issues = run_audit(root)
    errors = [x for x in issues if x.level == "ERROR"]
    warns = [x for x in issues if x.level == "WARN"]

    if args.json:
        print(
            json.dumps(
                {
                    "schema": "occ.docs_i18n_audit.v1",
                    "issues": [asdict(x) for x in issues],
                    "summary": {"errors": len(errors), "warnings": len(warns)},
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        for it in issues:
            print(f"[{it.level}] {it.file}: {it.message}")
        print(f"\nSummary: errors={len(errors)} warnings={len(warns)}")

    if errors:
        return 1
    if args.strict and warns:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
