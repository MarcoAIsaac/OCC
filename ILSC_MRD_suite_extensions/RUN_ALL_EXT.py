#!/usr/bin/env python3
"""Run all extension MRDs.

This is a *meta* suite runner and intentionally small.

It reads ``manifest.yaml`` and executes each module runner for each listed case.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ModuleNotFoundError:
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from occ.util import simple_yaml as yaml


def newest_report(outputs_dir: Path) -> Optional[Path]:
    reports = list(outputs_dir.glob("*.report.json"))
    if not reports:
        return None
    reports.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return reports[0]


def report_snapshot(outputs_dir: Path) -> dict[Path, int]:
    snap: dict[Path, int] = {}
    for p in outputs_dir.glob("*.report.json"):
        try:
            snap[p] = p.stat().st_mtime_ns
        except OSError:
            continue
    return snap


def newest_updated_report(outputs_dir: Path, before: dict[Path, int]) -> Optional[Path]:
    changed: list[Path] = []
    for p in outputs_dir.glob("*.report.json"):
        try:
            now_ns = p.stat().st_mtime_ns
        except OSError:
            continue
        prev = before.get(p)
        if prev is None or now_ns > prev:
            changed.append(p)
    if not changed:
        return None
    changed.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return changed[0]


def extract_verdict(report_path: Path) -> str:
    data = json.loads(report_path.read_text(encoding="utf-8"))
    for key in ("verdict", "VERDICT", "result"):
        if key in data:
            return str(data[key])
    return ""


def run_case(module_dir: Path, input_yaml: Path, timeout_s: int) -> Dict[str, Any]:
    runner = None
    scripts = module_dir / "scripts"
    if scripts.is_dir():
        cands = sorted(scripts.glob("run_mrd_*.py"))
        runner = cands[0] if cands else None
    if not runner:
        raise RuntimeError(f"No runner found in {module_dir}")

    outputs_dir = module_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    before = report_snapshot(outputs_dir)

    t0 = time.time()
    proc = subprocess.run(
        [sys.executable, str(runner), str(input_yaml)],
        cwd=str(module_dir),
        timeout=timeout_s,
    )
    dt = time.time() - t0

    rep = newest_updated_report(outputs_dir, before)
    if rep is None and proc.returncode == 0:
        rep = newest_report(outputs_dir)
    verdict = extract_verdict(rep) if rep else ""
    return {
        "returncode": proc.returncode,
        "elapsed_s": dt,
        "report": str(rep) if rep else None,
        "verdict": verdict,
    }


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--timeout", type=int, default=180)
    ns = ap.parse_args(argv)

    root = Path(ns.root).resolve()
    manifest = root / "manifest.yaml"
    if not manifest.is_file():
        raise SystemExit(f"manifest.yaml not found at {manifest}")

    mobj = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    modules = mobj.get("modules") if isinstance(mobj, dict) else None
    if not isinstance(modules, list):
        raise SystemExit("manifest.yaml must contain 'modules' list")

    results: List[Dict[str, Any]] = []
    ok = True

    for mod in modules:
        if not isinstance(mod, dict):
            continue
        name = str(mod.get("name", "")).strip()
        if not name:
            continue
        cases = mod.get("cases")
        if not isinstance(cases, list):
            continue

        module_dir = root / name
        for case in cases:
            inp = str(case.get("input"))
            expect = str(case.get("expect"))
            input_yaml = module_dir / "inputs" / inp

            entry: Dict[str, Any] = {
                "module": name,
                "input": str(input_yaml),
                "expect": expect,
            }
            try:
                out = run_case(module_dir, input_yaml, timeout_s=int(ns.timeout))
                entry.update(out)
            except subprocess.TimeoutExpired:
                ok = False
                entry.update({"error": "timeout"})
            except Exception as e:
                ok = False
                entry.update({"error": str(e)})

            verdict = str(entry.get("verdict") or "")
            # Normalise: treat PASS(...) as PASS
            verdict_norm = "PASS" if verdict.startswith("PASS") else verdict
            expect_norm = "PASS" if expect.startswith("PASS") else expect

            match = verdict_norm == expect_norm
            entry["match"] = match
            if not match:
                ok = False

            results.append(entry)

    summary_obj = {
        "suite": "extensions",
        "ok": ok,
        "results": results,
    }
    Path(ns.summary).write_text(
        json.dumps(summary_obj, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    if ok:
        return 0
    return 1 if ns.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
