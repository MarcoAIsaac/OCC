"""Execution helpers for the OCC CLI.

The runtime is intentionally lightweight:

- ``occ run`` executes a single module runner script based on a bundle YAML.
- ``occ verify`` executes a suite runner script (canonical or extensions).

Suites:

- Canonical suite (15 modules): ``ILSC_MRD_suite_15_modulos_CANON``
- Extensions suite (meta-MRDs/tooling): ``ILSC_MRD_suite_extensions``
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from .suites import SUITE_CANON, SUITE_EXTENSIONS, discover_suite_roots


@dataclass
class RunResult:
    module: str
    input_yaml: Path
    module_dir: Path
    report_path: Optional[Path]
    returncode: int


def _suite_roots(start: Path) -> Tuple[Optional[Path], Optional[Path]]:
    roots = discover_suite_roots(start)
    return roots.canon, roots.extensions


def infer_module_from_yaml_path(yaml_path: Path) -> Optional[str]:
    parts = [p.name for p in yaml_path.resolve().parents]
    for name in parts:
        if name.startswith("mrd_"):
            return name
    return None


def discover_module_runner(module_dir: Path) -> Optional[Path]:
    scripts = module_dir / "scripts"
    if not scripts.is_dir():
        return None
    # Prefer run_mrd_*.py
    candidates = sorted(scripts.glob("run_mrd_*.py"))
    if candidates:
        return candidates[0]
    # Fallback: any run_*.py
    candidates = sorted(scripts.glob("run_*.py"))
    return candidates[0] if candidates else None


def newest_report(outputs_dir: Path) -> Optional[Path]:
    if not outputs_dir.is_dir():
        return None
    reports = list(outputs_dir.glob("*.report.json"))
    if not reports:
        return None
    reports.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return reports[0]


def run_bundle(
    bundle_yaml: Path,
    module: Optional[str] = None,
    out_dir: Optional[Path] = None,
    strict: bool = False,
    suite: str = "auto",  # auto|canon|extensions
) -> RunResult:
    bundle_yaml = bundle_yaml.resolve()
    if not bundle_yaml.is_file():
        raise FileNotFoundError(f"Bundle YAML not found: {bundle_yaml}")

    if module is None:
        module = infer_module_from_yaml_path(bundle_yaml)

    canon_root, ext_root = _suite_roots(bundle_yaml.parent)
    if canon_root is None and ext_root is None:
        # allow running from repo root if cwd has suite
        canon_root, ext_root = _suite_roots(Path.cwd())
    if canon_root is None and ext_root is None:
        raise RuntimeError(
            "Could not find MRD suites. Expected folders: "
            f"{SUITE_CANON} and/or {SUITE_EXTENSIONS}. "
            "Run from the OCC repo root (or any subfolder within it)."
        )

    if module is None:
        raise RuntimeError(
            "Could not infer module from YAML path. Provide --module mrd_xxx."
        )

    module_dir: Optional[Path] = None

    def _try(root: Optional[Path]) -> Optional[Path]:
        if root is None:
            return None
        cand = root / module
        return cand if cand.is_dir() else None

    if suite == "canon":
        module_dir = _try(canon_root)
    elif suite == "extensions":
        module_dir = _try(ext_root)
    else:  # auto
        module_dir = _try(canon_root) or _try(ext_root)

    if module_dir is None:
        raise RuntimeError(
            f"Module not found: {module}. Looked in suites: canon/extensions."
        )

    runner = discover_module_runner(module_dir)
    if runner is None:
        raise RuntimeError(f"No runner script found in {module_dir/'scripts'}")

    # Ensure outputs exists
    outputs_dir = module_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    cmd = [sys.executable, str(runner), str(bundle_yaml)]
    proc = subprocess.run(cmd, cwd=str(module_dir))

    report = newest_report(outputs_dir)

    if out_dir is not None:
        out_dir = out_dir.resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        if report and report.is_file():
            shutil.copy2(report, out_dir / "report.json")
        # Also copy any side artifacts if module produced them
        # Keep it light: copy the entire outputs folder (excluding large files) only if strict
        if strict:
            dst = out_dir / "module_outputs"
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(outputs_dir, dst)

    return RunResult(
        module=module,
        input_yaml=bundle_yaml,
        module_dir=module_dir,
        report_path=(out_dir / "report.json") if (out_dir and report) else report,
        returncode=proc.returncode,
    )


def run_verify(
    suite_root: Path,
    strict: bool = False,
    timeout: int = 180,
) -> Tuple[int, Optional[Path]]:
    suite_root = suite_root.resolve()
    run_all = suite_root / "RUN_ALL.py"
    run_all_ext = suite_root / "RUN_ALL_EXT.py"
    if run_all.is_file():
        runner = run_all
    elif run_all_ext.is_file():
        runner = run_all_ext
    else:
        raise RuntimeError(
            f"No suite runner found at {suite_root} (expected RUN_ALL.py or RUN_ALL_EXT.py)"
        )

    summary = suite_root / "verification_summary.json"
    cmd = [
        sys.executable,
        str(runner),
        "--root",
        str(suite_root),
        "--summary",
        str(summary),
    ]
    cmd += ["--timeout", str(int(timeout))]
    if strict:
        cmd.append("--strict")

    proc = subprocess.run(cmd, cwd=str(suite_root))
    return proc.returncode, (summary if summary.is_file() else None)


def extract_verdict_from_report(report_path: Path) -> Optional[str]:
    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    for key in ("verdict", "VERDICT", "result"):
        if key in data:
            return str(data[key])
    # Some reports may embed under 'summary'
    if isinstance(data, dict) and "summary" in data and isinstance(data["summary"], dict):
        if "verdict" in data["summary"]:
            return str(data["summary"]["verdict"])
    return None
