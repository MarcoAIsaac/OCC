#!/usr/bin/env python3
"""Validate release metadata consistency for OCC.

Checks:
- version sync across pyproject / CHANGELOG / CITATION / .zenodo.json
- DOI presence in README badges + CITATION
- optional DOI resolution over network
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml  # type: ignore[import-untyped]
except ModuleNotFoundError:
    import sys

    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from occ.util import simple_yaml as yaml


@dataclass
class Check:
    name: str
    status: str  # PASS | WARN | FAIL
    message: str


DOI_RE = re.compile(r"https://doi\.org/(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _pyproject_version(pyproject: Path) -> Optional[str]:
    text = _read_text(pyproject)
    m = re.search(r'^\s*version\s*=\s*"([^"]+)"\s*$', text, flags=re.MULTILINE)
    if not m:
        return None
    return m.group(1).strip()


def _changelog_has_version(changelog: Path, version: str) -> bool:
    text = _read_text(changelog)
    return bool(re.search(rf"^## \[{re.escape(version)}\]\s*-\s*", text, flags=re.MULTILINE))


def _load_yaml(path: Path) -> Dict[str, Any]:
    raw = yaml.safe_load(_read_text(path))
    return raw if isinstance(raw, dict) else {}


def _load_json(path: Path) -> Dict[str, Any]:
    raw = json.loads(_read_text(path))
    return raw if isinstance(raw, dict) else {}


def _extract_readme_doi(text: str) -> Optional[str]:
    m = DOI_RE.search(text)
    if not m:
        return None
    return m.group(1).strip().rstrip(")")


def _resolve_doi(doi: str, timeout_s: int = 12) -> Tuple[bool, str]:
    url = f"https://doi.org/{doi}"
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            return True, str(resp.geturl())
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except Exception as e:  # pragma: no cover - network dependent
        return False, str(e)


def run_checks(root: Path, expected_doi: Optional[str], resolve_doi: bool) -> List[Check]:
    checks: List[Check] = []

    pyproject = root / "pyproject.toml"
    changelog = root / "CHANGELOG.md"
    citation = root / "CITATION.cff"
    zenodo = root / ".zenodo.json"
    readme_en = root / "README.md"
    readme_es = root / "README.es.md"

    version = _pyproject_version(pyproject)
    if not version:
        checks.append(Check("pyproject.version", "FAIL", "Could not parse project version"))
        return checks
    checks.append(Check("pyproject.version", "PASS", f"Version: {version}"))

    if _changelog_has_version(changelog, version):
        checks.append(Check("changelog.version", "PASS", f"CHANGELOG contains [{version}]"))
    else:
        checks.append(
            Check("changelog.version", "FAIL", f"Missing CHANGELOG section for [{version}]")
        )

    cff = _load_yaml(citation)
    cff_version = str(cff.get("version") or "").strip()
    cff_doi = str(cff.get("doi") or "").strip()
    if cff_version == version:
        checks.append(Check("citation.version", "PASS", f"CITATION version matches {version}"))
    else:
        checks.append(
            Check(
                "citation.version",
                "FAIL",
                f"CITATION version mismatch (found '{cff_version}', expected '{version}')",
            )
        )

    z = _load_json(zenodo)
    z_version = str(z.get("version") or "").strip()
    if z_version == version:
        checks.append(Check("zenodo.version", "PASS", f".zenodo.json version matches {version}"))
    else:
        checks.append(
            Check(
                "zenodo.version",
                "FAIL",
                f".zenodo.json version mismatch (found '{z_version}', expected '{version}')",
            )
        )

    en_text = _read_text(readme_en)
    es_text = _read_text(readme_es)
    if "DOI-pending" in en_text or "DOI: pending" in en_text:
        checks.append(Check("readme.en.doi", "FAIL", "README.md still uses DOI pending badge"))
    if "DOI-pending" in es_text or "DOI: pending" in es_text:
        checks.append(Check("readme.es.doi", "FAIL", "README.es.md still uses DOI pending badge"))

    doi_en = _extract_readme_doi(en_text)
    doi_es = _extract_readme_doi(es_text)
    if doi_en:
        checks.append(Check("readme.en.doi", "PASS", f"README.md DOI: {doi_en}"))
    else:
        checks.append(Check("readme.en.doi", "FAIL", "Could not find DOI link in README.md"))
    if doi_es:
        checks.append(Check("readme.es.doi", "PASS", f"README.es.md DOI: {doi_es}"))
    else:
        checks.append(Check("readme.es.doi", "FAIL", "Could not find DOI link in README.es.md"))

    if doi_en and doi_es:
        if doi_en == doi_es:
            checks.append(Check("readme.doi.sync", "PASS", "EN/ES README DOI links match"))
        else:
            checks.append(
                Check(
                    "readme.doi.sync",
                    "FAIL",
                    f"EN/ES README DOI mismatch ({doi_en} vs {doi_es})",
                )
            )

    if cff_doi:
        checks.append(Check("citation.doi", "PASS", f"CITATION DOI: {cff_doi}"))
    else:
        checks.append(Check("citation.doi", "FAIL", "Missing doi in CITATION.cff"))

    target_doi = expected_doi or doi_en or cff_doi
    if expected_doi:
        if doi_en != expected_doi or doi_es != expected_doi or cff_doi != expected_doi:
            checks.append(
                Check(
                    "doi.expected",
                    "FAIL",
                    "Expected DOI does not match README/CITATION values",
                )
            )
        else:
            checks.append(
                Check("doi.expected", "PASS", f"All files match expected DOI {expected_doi}")
            )

    if resolve_doi and target_doi:
        ok, detail = _resolve_doi(target_doi)
        if ok:
            checks.append(Check("doi.resolve", "PASS", f"{target_doi} -> {detail}"))
        else:
            checks.append(
                Check("doi.resolve", "WARN", f"Could not resolve DOI {target_doi}: {detail}")
            )

    return checks


def _summary(checks: List[Check]) -> Dict[str, int]:
    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for c in checks:
        counts[c.status] = counts.get(c.status, 0) + 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate OCC release metadata consistency.")
    parser.add_argument("--expected-doi", help="Expected DOI (e.g., 10.5281/zenodo.1234567)")
    parser.add_argument("--no-resolve-doi", action="store_true", help="Skip DOI network resolution")
    parser.add_argument("--strict", action="store_true", help="Treat WARN as failure")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    checks = run_checks(
        root=root,
        expected_doi=(str(args.expected_doi).strip() if args.expected_doi else None),
        resolve_doi=not bool(args.no_resolve_doi),
    )
    counts = _summary(checks)

    if args.json:
        print(
            json.dumps(
                {
                    "schema": "occ.release_doctor.v1",
                    "checks": [asdict(c) for c in checks],
                    "summary": counts,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        for c in checks:
            print(f"[{c.status}] {c.name}: {c.message}")
        print(f"\nSummary: PASS={counts['PASS']} WARN={counts['WARN']} FAIL={counts['FAIL']}")

    if counts["FAIL"] > 0:
        return 1
    if args.strict and counts["WARN"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
