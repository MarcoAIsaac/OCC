"""Command-line interface for the OCC runtime.

This CLI is intentionally minimal and designed to be reproducible.

Typical usage:

- ``occ run <bundle.yaml> --out out/``
- ``occ verify``
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .runner import extract_verdict_from_report, run_bundle, run_verify


def _find_suite_root() -> Path:
    here = Path.cwd().resolve()
    for parent in [here] + list(here.parents):
        cand = parent / "ILSC_MRD_suite_15_modulos_CANON"
        if cand.is_dir():
            return cand
    # Also allow running from repo root that contains it
    raise SystemExit(
        "Could not locate ILSC_MRD_suite_15_modulos_CANON. "
        "Run this command from the OCC repo root (or any subfolder within it)."
    )


def cmd_run(args: argparse.Namespace) -> int:
    res = run_bundle(
        Path(args.bundle),
        module=args.module,
        out_dir=Path(args.out) if args.out else None,
        strict=args.include_outputs,
    )
    if res.report_path and Path(res.report_path).is_file():
        verdict = extract_verdict_from_report(Path(res.report_path))
        if verdict:
            print(verdict)
        else:
            print(f"Report written: {res.report_path}")
    else:
        print("No report produced (or could not be found).", file=sys.stderr)
    return res.returncode


def cmd_verify(args: argparse.Namespace) -> int:
    suite_root = _find_suite_root()
    code, summary = run_verify(suite_root, strict=args.strict)
    if summary:
        print(f"Summary: {summary}")
    return code


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="occ",
        description="OCC runtime CLI (MRD suite runner)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser(
        "run",
        help="Run a single bundle YAML through the appropriate MRD module",
    )
    pr.add_argument(
        "bundle",
        help="Path to bundle YAML (usually under a mrd_*/inputs folder)",
    )
    pr.add_argument(
        "--module",
        help="Module folder name (e.g. mrd_obs_isaac). If omitted, inferred from YAML path.",
    )
    pr.add_argument(
        "--out",
        help="Output directory. If provided, report is copied to out/report.json",
    )
    pr.add_argument(
        "--include-outputs",
        action="store_true",
        help="Also copy the module outputs folder into <out>/module_outputs (can be larger).",
    )
    pr.set_defaults(func=cmd_run)

    pv = sub.add_parser("verify", help="Run full MRD regression suite (RUN_ALL.py)")
    pv.add_argument("--strict", action="store_true", help="Pass --strict to RUN_ALL.py")
    pv.set_defaults(func=cmd_verify)

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
