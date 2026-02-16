#!/usr/bin/env python3
"""Run MRD predictions registry validation."""

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
        print("Usage: run_mrd_predictions_registry.py <input.yaml>")
        return 2

    inp = Path(sys.argv[1]).resolve()
    cfg = yaml.safe_load(inp.read_text(encoding="utf-8"))
    if not isinstance(cfg, dict) or "registry_path" not in cfg:
        raise SystemExit("Input must contain registry_path")

    repo_root = _repo_root()
    sys.path.insert(0, str(repo_root))
    from occ.predictions.registry import load_registry

    reg_path = repo_root / Path(str(cfg["registry_path"]))

    verdict = "PASS"
    details: Dict[str, Any] = {"registry_path": str(cfg["registry_path"])}
    try:
        if not reg_path.is_file():
            verdict = "NO-EVAL(REG0)"
            details["missing"] = True
        else:
            _ = load_registry(reg_path)
            verdict = "PASS"
    except ValueError as e:
        msg = str(e)
        if "Duplicate prediction id" in msg:
            verdict = "FAIL(REG2)"
        else:
            verdict = "FAIL(REG1)"
        details["error"] = msg

    out: Dict[str, Any] = {
        "module": "mrd_predictions_registry",
        "input": str(inp.name),
        "verdict": verdict,
        "details": details,
        "timestamp": time.time(),
    }

    outputs = Path(__file__).resolve().parents[1] / "outputs"
    outputs.mkdir(exist_ok=True)
    outpath = outputs / f"pred_registry.{inp.stem}.{int(time.time())}.report.json"
    outpath.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
