#!/usr/bin/env python3
"""Run MRD UV guard."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict

import yaml


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: run_mrd_uv_guard.py <input.yaml>")
        return 2

    inp = Path(sys.argv[1]).resolve()
    claim = yaml.safe_load(inp.read_text(encoding="utf-8"))
    if not isinstance(claim, dict):
        raise SystemExit("Input must be a YAML mapping")

    sys.path.insert(0, str(_repo_root()))
    from occ.judges.pipeline import default_judges, run_pipeline

    report = run_pipeline(claim, default_judges(strict_trace=False))
    verdict = str(report.get("verdict"))

    out: Dict[str, Any] = {
        "module": "mrd_uv_guard",
        "input": str(inp.name),
        "verdict": verdict,
        "report": report,
        "timestamp": time.time(),
    }

    outputs = Path(__file__).resolve().parents[1] / "outputs"
    outputs.mkdir(exist_ok=True)
    outpath = outputs / f"uv_guard.{inp.stem}.{int(time.time())}.report.json"
    outpath.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
