"""Command-line interface for the OCC runtime.

The CLI focuses on two goals:

1) Make the canonical MRD suite *runnable* and *auditable*.
2) Make OCC concepts *discoverable* (catalog, predictions registry, claim judges).
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ModuleNotFoundError:
    from .util import simple_yaml as yaml

from . import get_version
from .catalog import build_catalog
from .judges.pipeline import default_judges, run_pipeline
from .predictions.registry import find_registry_path, load_registry
from .runner import extract_verdict_from_report, run_bundle, run_verify
from .suites import SUITE_CANON, SUITE_EXTENSIONS, discover_suite_roots


def _maybe_rich_print() -> Any:
    """Return a print-like function.

    If the optional ``rich`` extra is installed, this improves CLI readability.
    """

    try:
        from rich import print as rprint  # type: ignore

        return rprint
    except Exception:
        return print


RPRINT = _maybe_rich_print()


def cmd_run(args: argparse.Namespace) -> int:
    res = run_bundle(
        Path(args.bundle),
        module=args.module,
        out_dir=Path(args.out) if args.out else None,
        strict=args.include_outputs,
        suite=args.suite,
    )
    if res.report_path and Path(res.report_path).is_file():
        verdict = extract_verdict_from_report(Path(res.report_path))
        if verdict:
            RPRINT(verdict)
        else:
            RPRINT(f"Report written: {res.report_path}")
    else:
        print("No report produced (or could not be found).", file=sys.stderr)
    return res.returncode


def cmd_verify(args: argparse.Namespace) -> int:
    roots = discover_suite_roots(Path.cwd())
    wanted = args.suite
    strict = bool(args.strict)

    summaries: List[str] = []
    rc = 0

    def _one(suite_name: str, root: Optional[Path]) -> None:
        nonlocal rc
        if root is None:
            raise SystemExit(
                f"Suite '{suite_name}' not found. Expected folder: "
                f"{SUITE_CANON if suite_name=='canon' else SUITE_EXTENSIONS}"
            )
        code, summary = run_verify(root, strict=strict, timeout=int(args.timeout))
        rc = max(rc, code)
        if summary:
            summaries.append(f"{suite_name}: {summary}")

    if wanted in ("canon", "all"):
        _one("canon", roots.canon)
    if wanted in ("extensions", "all"):
        _one("extensions", roots.extensions)

    for s in summaries:
        RPRINT(f"Summary: {s}")
    return rc


def cmd_list(args: argparse.Namespace) -> int:
    items = build_catalog(Path.cwd(), which=args.suite)
    if args.json:
        print(json.dumps([x.to_dict() for x in items], indent=2, ensure_ascii=False))
        return 0

    if not items:
        RPRINT("No MRD modules found.")
        return 0

    # Compact table-like output without extra deps
    for it in items:
        runner = "yes" if it.runner else "no"
        RPRINT(f"- [{it.suite}] {it.name} (runner: {runner})")
    return 0


def cmd_explain(args: argparse.Namespace) -> int:
    items = build_catalog(Path.cwd(), which="all")
    match = next((x for x in items if x.name == args.module), None)
    if not match:
        raise SystemExit(f"Unknown module: {args.module}. Try: occ list")

    mod_dir = Path(match.path)
    # Prefer MRD_README
    for cand in ("MRD_README.md", "README.md", "README_MODULES.md"):
        p = mod_dir / cand
        if p.is_file():
            RPRINT(f"# {match.name}  [{match.suite}]")
            RPRINT(p.read_text(encoding="utf-8", errors="replace"))
            return 0

    RPRINT(f"No README found for {match.name}.")
    return 0


def cmd_predict_list(args: argparse.Namespace) -> int:
    reg_path = find_registry_path(Path.cwd())
    if not reg_path:
        raise SystemExit("Predictions registry not found (expected predictions/registry.yaml)")
    reg = load_registry(reg_path)
    rows = reg.predictions
    if args.json:
        print(
            json.dumps(
                [
                    {
                        "id": p.id,
                        "title": p.title,
                        "status": p.status,
                        "summary": p.summary,
                    }
                    for p in rows
                ],
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    for p in rows:
        star = "★" if p.status == "featured" else " "
        RPRINT(f"{star} {p.id}: {p.title}  ({p.status})")
    return 0


def cmd_predict_show(args: argparse.Namespace) -> int:
    reg_path = find_registry_path(Path.cwd())
    if not reg_path:
        raise SystemExit("Predictions registry not found (expected predictions/registry.yaml)")
    reg = load_registry(reg_path)
    pred = reg.by_id().get(args.id)
    if not pred:
        raise SystemExit(f"Unknown prediction id: {args.id}")

    out: Dict[str, Any] = {
        "id": pred.id,
        "title": pred.title,
        "status": pred.status,
        "summary": pred.summary,
        "domain": pred.domain,
        "observables": pred.observables,
        "tests": pred.tests,
        "timeframe": pred.timeframe,
        "references": pred.references,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def cmd_judge(args: argparse.Namespace) -> int:
    claim_path = Path(args.claim).resolve()
    if not claim_path.is_file():
        raise SystemExit(f"Claim spec not found: {claim_path}")

    claim = yaml.safe_load(claim_path.read_text(encoding="utf-8"))
    if not isinstance(claim, dict):
        raise SystemExit("Claim spec must be a YAML mapping")

    pipeline = default_judges(strict_trace=bool(args.strict_trace))
    report = run_pipeline(claim, pipeline)
    verdict = report.get("verdict")
    if isinstance(verdict, str):
        RPRINT(verdict)

    if args.out:
        outp = Path(args.out)
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        RPRINT(f"Report: {outp}")

    if isinstance(verdict, str) and verdict.startswith("PASS"):
        return 0
    return 1


def cmd_doctor(args: argparse.Namespace) -> int:
    roots = discover_suite_roots(Path.cwd())
    reg = find_registry_path(Path.cwd())
    info: Dict[str, Any] = {
        "occ_version": get_version(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "suite_roots": {
            "canon": str(roots.canon) if roots.canon else None,
            "extensions": str(roots.extensions) if roots.extensions else None,
        },
        "predictions_registry": str(reg) if reg else None,
    }

    if args.json:
        print(json.dumps(info, indent=2, ensure_ascii=False))
        return 0

    RPRINT(f"OCC: {info['occ_version']}")
    RPRINT(f"Python: {info['python']}")
    RPRINT(f"Platform: {info['platform']}")
    RPRINT(f"Canon suite: {info['suite_roots']['canon']}")
    RPRINT(f"Extensions suite: {info['suite_roots']['extensions']}")
    RPRINT(f"Predictions registry: {info['predictions_registry']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="occ",
        description="OCC runtime CLI (MRD suite runner + catalogs)",
    )
    p.add_argument(
        "--version",
        action="version",
        version=f"occ-mrd-runner {get_version()}",
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
        "--suite",
        default="auto",
        choices=["auto", "canon", "extensions"],
        help="Which suite to search (default: auto).",
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

    pv = sub.add_parser(
        "verify",
        help="Run a full MRD suite verification (canonical/extensions)",
    )
    pv.add_argument(
        "--suite",
        default="canon",
        choices=["canon", "extensions", "all"],
        help="Which suite to verify (default: canon).",
    )
    pv.add_argument("--strict", action="store_true", help="Fail if any expectation fails")
    pv.add_argument(
        "--timeout",
        default=180,
        type=int,
        help="Timeout per MRD case (seconds).",
    )
    pv.set_defaults(func=cmd_verify)

    pl = sub.add_parser("list", help="List available MRD modules")
    pl.add_argument(
        "--suite",
        default="all",
        choices=["canon", "extensions", "all"],
        help="Which suite to list (default: all).",
    )
    pl.add_argument("--json", action="store_true", help="Emit JSON")
    pl.set_defaults(func=cmd_list)

    pe = sub.add_parser("explain", help="Print a module README to stdout")
    pe.add_argument("module", help="Module folder name (e.g. mrd_obs_isaac)")
    pe.set_defaults(func=cmd_explain)

    pj = sub.add_parser("judge", help="Run built-in operational judges on a claim spec YAML")
    pj.add_argument("claim", help="Path to claim spec YAML")
    pj.add_argument(
        "--strict-trace",
        action="store_true",
        help="Require all declared source paths to exist.",
    )
    pj.add_argument("--out", help="Write report JSON to this path")
    pj.set_defaults(func=cmd_judge)

    pd = sub.add_parser("doctor", help="Environment & repo diagnostics")
    pd.add_argument("--json", action="store_true", help="Emit JSON")
    pd.set_defaults(func=cmd_doctor)

    pp = sub.add_parser("predict", help="Predictions registry commands")
    pp_sub = pp.add_subparsers(dest="pred_cmd", required=True)

    ppl = pp_sub.add_parser("list", help="List predictions")
    ppl.add_argument("--json", action="store_true", help="Emit JSON")
    ppl.set_defaults(func=cmd_predict_list)

    pps = pp_sub.add_parser("show", help="Show a prediction")
    pps.add_argument("id", help="Prediction id (e.g. P-0003)")
    pps.set_defaults(func=cmd_predict_show)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
