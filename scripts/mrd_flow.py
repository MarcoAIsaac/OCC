#!/usr/bin/env python3
"""Guided pipeline for claim -> judges -> module generation.

Safe defaults:
- evaluates claim with judges
- does NOT run MRD module execution unless explicitly requested
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]


def _judge_claim(claim: Dict[str, Any]) -> Dict[str, Any]:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from occ.judges.nuclear_guard import claim_is_nuclear
    from occ.judges.pipeline import default_judges, run_pipeline

    include_nuclear = claim_is_nuclear(claim)
    judges = default_judges(strict_trace=False, include_nuclear=include_nuclear)
    report = run_pipeline(claim, judges)
    return {
        "verdict": report.get("verdict"),
        "judge_set": report.get("judge_set"),
        "report": report,
        "include_nuclear_profile": include_nuclear,
    }


def main() -> int:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from occ.module_autogen import auto_generate_module, load_claim_file
    from occ.runner import extract_verdict_from_report, run_bundle

    parser = argparse.ArgumentParser(description="Run OCC guided pipeline for new claims.")
    parser.add_argument("claim", help="Path to claim YAML/JSON")
    parser.add_argument("--module-name", help="Target module name for auto-generation")
    parser.add_argument("--start", default=".", help="Workspace root (default: current dir)")
    parser.add_argument(
        "--no-research",
        action="store_true",
        help="Disable web research enrichment",
    )
    parser.add_argument("--max-sources", type=int, default=5, help="Max external references")
    parser.add_argument(
        "--create-prediction",
        action="store_true",
        help="Create prediction draft",
    )
    parser.add_argument(
        "--publish-prediction",
        action="store_true",
        help="Publish draft to registry",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force module creation when name exists",
    )
    parser.add_argument(
        "--generate-module",
        action="store_true",
        help="Create/resolve extension module after judge evaluation",
    )
    parser.add_argument(
        "--verify-generated",
        action="store_true",
        help=(
            "Execute generated module pass case once. "
            "Disabled by default to avoid writing MRD outputs automatically."
        ),
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    args = parser.parse_args()

    claim_path = Path(args.claim).resolve()
    claim = load_claim_file(claim_path)
    if not isinstance(claim, dict):
        raise SystemExit("Claim must be a mapping")

    start = Path(args.start).resolve()
    judge = _judge_claim(claim)
    out: Dict[str, Any] = {
        "schema": "occ.mrd_flow.v1",
        "claim": str(claim_path),
        "judge": judge,
        "module": None,
        "verify_generated": None,
    }

    if args.generate_module:
        result = auto_generate_module(
            claim_path=claim_path,
            start=start,
            module_name=str(args.module_name).strip() if args.module_name else None,
            with_research=not bool(args.no_research),
            max_sources=max(1, int(args.max_sources)),
            create_prediction=bool(args.create_prediction),
            publish_prediction=bool(args.publish_prediction),
            force=bool(args.force),
        )
        out["module"] = result

        if args.verify_generated and bool(result.get("created")):
            module_name = str(result.get("module") or "").strip()
            bundle = Path(str(result.get("module_dir"))) / "inputs" / "pass.yaml"
            run = run_bundle(bundle, module=module_name, suite="extensions")
            verdict = ""
            if run.report_path:
                verdict = extract_verdict_from_report(Path(run.report_path)) or ""
            out["verify_generated"] = {
                "returncode": run.returncode,
                "report_path": run.report_path,
                "verdict": verdict,
            }

    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print(f"claim: {out['claim']}")
        print(f"judge verdict: {judge.get('verdict')}")
        print(f"nuclear profile: {judge.get('include_nuclear_profile')}")
        if out["module"] is None:
            print("module: skipped (use --generate-module)")
        else:
            mod = out["module"]
            print(f"module: {mod.get('module')} (created={mod.get('created')})")
            if mod.get("prediction_draft"):
                print(f"prediction draft: {mod.get('prediction_draft')}")
            if out.get("verify_generated"):
                vr = out["verify_generated"]
                print(f"verify generated: rc={vr.get('returncode')} verdict={vr.get('verdict')}")
                print(f"report: {vr.get('report_path')}")
            elif args.generate_module:
                print("verify generated: skipped (use --verify-generated)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
