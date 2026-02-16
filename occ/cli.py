"""Command-line interface for the OCC runtime.

The CLI focuses on two goals:

1) Make the canonical MRD suite *runnable* and *auditable*.
2) Make OCC concepts *discoverable* (catalog, predictions registry, claim judges).
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml  # type: ignore[import-untyped]
except ModuleNotFoundError:
    from .util import simple_yaml as yaml

from . import get_version
from .catalog import build_catalog
from .judges.pipeline import default_judges, run_pipeline
from .module_autogen import auto_generate_module, load_claim_file
from .predictions.registry import find_registry_path, load_registry
from .runner import extract_verdict_from_report, run_bundle, run_verify
from .science_research import research_claim
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


def _detect_language() -> str:
    candidates = [
        os.getenv("OCC_LANG"),
        os.getenv("LC_ALL"),
        os.getenv("LC_MESSAGES"),
        os.getenv("LANG"),
    ]
    for raw in candidates:
        norm = str(raw or "").strip().lower()
        if not norm:
            continue
        if norm == "c" or norm.startswith("c.") or norm == "posix":
            continue
        if norm.startswith("es"):
            return "es"
        return "en"
    return "en"


CLI_LANGUAGE = _detect_language()


def _tr(en: str, es: str) -> str:
    return es if CLI_LANGUAGE == "es" else en


def cmd_run(args: argparse.Namespace) -> int:
    try:
        res = run_bundle(
            Path(args.bundle),
            module=args.module,
            out_dir=Path(args.out) if args.out else None,
            strict=args.include_outputs,
            suite=args.suite,
            timeout=int(args.timeout) if args.timeout else None,
        )
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 124

    if res.report_path and Path(res.report_path).is_file():
        verdict = extract_verdict_from_report(Path(res.report_path))
        if verdict:
            RPRINT(verdict)
        else:
            RPRINT(
                _tr(
                    f"Report written: {res.report_path}",
                    f"Reporte escrito: {res.report_path}",
                )
            )
    else:
        print(
            _tr(
                "No report produced (or could not be found).",
                "No se produjo reporte (o no se pudo encontrar).",
            ),
            file=sys.stderr,
        )
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
        RPRINT(_tr(f"Summary: {s}", f"Resumen: {s}"))
    return rc


def cmd_list(args: argparse.Namespace) -> int:
    items = build_catalog(Path.cwd(), which=args.suite)
    if args.json:
        print(json.dumps([x.to_dict() for x in items], indent=2, ensure_ascii=False))
        return 0

    if not items:
        RPRINT(_tr("No MRD modules found.", "No se encontraron módulos MRD."))
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
        raise SystemExit(
            _tr(
                f"Unknown module: {args.module}. Try: occ list",
                f"Módulo desconocido: {args.module}. Prueba: occ list",
            )
        )

    mod_dir = Path(match.path)
    # Prefer MRD_README
    for cand in ("MRD_README.md", "README.md", "README_MODULES.md"):
        p = mod_dir / cand
        if p.is_file():
            RPRINT(f"# {match.name}  [{match.suite}]")
            RPRINT(p.read_text(encoding="utf-8", errors="replace"))
            return 0

    RPRINT(_tr(f"No README found for {match.name}.", f"No se encontró README para {match.name}."))
    return 0


def cmd_predict_list(args: argparse.Namespace) -> int:
    reg_path = find_registry_path(Path.cwd())
    if not reg_path:
        raise SystemExit(
            _tr(
                "Predictions registry not found (expected predictions/registry.yaml)",
                (
                    "No se encontró el registry de predicciones "
                    "(se esperaba predictions/registry.yaml)"
                ),
            )
        )
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
        raise SystemExit(
            _tr(
                "Predictions registry not found (expected predictions/registry.yaml)",
                (
                    "No se encontró el registry de predicciones "
                    "(se esperaba predictions/registry.yaml)"
                ),
            )
        )
    reg = load_registry(reg_path)
    pred = reg.by_id().get(args.id)
    if not pred:
        raise SystemExit(
            _tr(
                f"Unknown prediction id: {args.id}",
                f"ID de predicción desconocido: {args.id}",
            )
        )

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
        raise SystemExit(
            _tr(
                f"Claim spec not found: {claim_path}",
                f"No se encontró claim spec: {claim_path}",
            )
        )

    claim = yaml.safe_load(claim_path.read_text(encoding="utf-8"))
    if not isinstance(claim, dict):
        raise SystemExit(
            _tr(
                "Claim spec must be a YAML mapping",
                "Claim spec debe ser un mapeo YAML",
            )
        )

    pipeline = default_judges(strict_trace=bool(args.strict_trace))
    report = run_pipeline(claim, pipeline)
    verdict = report.get("verdict")
    if isinstance(verdict, str):
        RPRINT(verdict)

    if args.out:
        outp = Path(args.out)
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        RPRINT(_tr(f"Report: {outp}", f"Reporte: {outp}"))

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
    RPRINT(_tr(f"Platform: {info['platform']}", f"Plataforma: {info['platform']}"))
    RPRINT(
        _tr(
            f"Canon suite: {info['suite_roots']['canon']}",
            f"Suite canon: {info['suite_roots']['canon']}",
        )
    )
    RPRINT(
        _tr(
            f"Extensions suite: {info['suite_roots']['extensions']}",
            f"Suite extensiones: {info['suite_roots']['extensions']}",
        )
    )
    RPRINT(
        _tr(
            f"Predictions registry: {info['predictions_registry']}",
            f"Registry de predicciones: {info['predictions_registry']}",
        )
    )
    return 0


def cmd_research(args: argparse.Namespace) -> int:
    claim = load_claim_file(Path(args.claim).resolve())
    res = research_claim(
        claim,
        max_results=max(1, int(args.max_results)),
        timeout_s=max(1, int(args.timeout)),
    )
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0

    RPRINT(f"Query: {res.get('query', '')}")
    sources = res.get("sources", {})
    if isinstance(sources, dict):
        for source_name in ("arxiv", "crossref"):
            rows = sources.get(source_name, [])
            if not isinstance(rows, list):
                continue
            RPRINT(
                _tr(
                    f"\n[{source_name}] {len(rows)} result(s)",
                    f"\n[{source_name}] {len(rows)} resultado(s)",
                )
            )
            for item in rows[: max(1, int(args.show))]:
                if not isinstance(item, dict):
                    continue
                title = str(item.get("title", "")).strip()
                url = str(item.get("url", "")).strip()
                published = str(item.get("published", "")).strip()
                line = f"- {title}"
                if published:
                    line += f" ({published})"
                if url:
                    line += f" -> {url}"
                RPRINT(line)

    errors = res.get("errors", [])
    if isinstance(errors, list) and errors:
        RPRINT(_tr("\nWarnings:", "\nAdvertencias:"))
        for e in errors:
            RPRINT(f"- {e}")
    return 0


def cmd_module_auto(args: argparse.Namespace) -> int:
    res = auto_generate_module(
        claim_path=Path(args.claim),
        start=Path.cwd(),
        module_name=args.module_name,
        with_research=not bool(args.no_research),
        max_sources=max(1, int(args.max_sources)),
        create_prediction=bool(args.create_prediction),
        publish_prediction=bool(args.publish_prediction),
        register_manifest=not bool(args.no_manifest),
        force=bool(args.force),
    )
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0

    if res.get("matched_existing"):
        RPRINT(
            _tr(
                f"Claim maps to an existing module: {res.get('module')}",
                f"El claim mapea a un módulo existente: {res.get('module')}",
            )
        )
        RPRINT(
            _tr(
                "Use `occ run <bundle> --module <module>` to execute it.",
                "Usa `occ run <bundle> --module <módulo>` para ejecutarlo.",
            )
        )
        return 0

    RPRINT(_tr(f"Created module: {res.get('module')}", f"Módulo creado: {res.get('module')}"))
    RPRINT(f"Path: {res.get('module_dir')}")
    RPRINT(_tr(f"Base verdict: {res.get('verdict')}", f"Veredicto base: {res.get('verdict')}"))
    locks = res.get("locks_applied", [])
    if isinstance(locks, list) and locks:
        RPRINT(
            _tr("Applied locks/judges: ", "Locks/jueces aplicados: ")
            + ", ".join(str(x) for x in locks)
        )

    if res.get("prediction_draft"):
        RPRINT(
            _tr(
                f"Prediction draft: {res.get('prediction_draft')}",
                f"Borrador de predicción: {res.get('prediction_draft')}",
            )
        )
    if res.get("prediction_registry"):
        RPRINT(
            _tr(
                f"Prediction published to registry: {res.get('prediction_registry')}",
                f"Predicción publicada en registry: {res.get('prediction_registry')}",
            )
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="occ",
        description=_tr(
            "OCC runtime CLI (MRD suite runner + catalogs)",
            "CLI runtime de OCC (runner de suite MRD + catálogos)",
        ),
    )
    p.add_argument(
        "--version",
        action="version",
        version=f"occ-mrd-runner {get_version()}",
    )

    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser(
        "run",
        help=_tr(
            "Run a single bundle YAML through the appropriate MRD module",
            "Ejecuta un bundle YAML en el módulo MRD correspondiente",
        ),
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
    pr.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="Timeout for the run command in seconds (default: 180).",
    )
    pr.set_defaults(func=cmd_run)

    pv = sub.add_parser(
        "verify",
        help=_tr(
            "Run a full MRD suite verification (canonical/extensions)",
            "Ejecuta verificación completa de suite MRD (canon/extensiones)",
        ),
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

    pl = sub.add_parser(
        "list",
        help=_tr("List available MRD modules", "Lista módulos MRD disponibles"),
    )
    pl.add_argument(
        "--suite",
        default="all",
        choices=["canon", "extensions", "all"],
        help="Which suite to list (default: all).",
    )
    pl.add_argument("--json", action="store_true", help="Emit JSON")
    pl.set_defaults(func=cmd_list)

    pe = sub.add_parser(
        "explain",
        help=_tr("Print a module README to stdout", "Imprime el README de un módulo"),
    )
    pe.add_argument("module", help="Module folder name (e.g. mrd_obs_isaac)")
    pe.set_defaults(func=cmd_explain)

    pj = sub.add_parser(
        "judge",
        help=_tr(
            "Run built-in operational judges on a claim spec YAML",
            "Ejecuta jueces operacionales integrados sobre un claim YAML",
        ),
    )
    pj.add_argument("claim", help="Path to claim spec YAML")
    pj.add_argument(
        "--strict-trace",
        action="store_true",
        help="Require all declared source paths to exist.",
    )
    pj.add_argument("--out", help="Write report JSON to this path")
    pj.set_defaults(func=cmd_judge)

    pd = sub.add_parser(
        "doctor",
        help=_tr("Environment & repo diagnostics", "Diagnóstico de entorno y repositorio"),
    )
    pd.add_argument("--json", action="store_true", help="Emit JSON")
    pd.set_defaults(func=cmd_doctor)

    pp = sub.add_parser(
        "predict",
        help=_tr("Predictions registry commands", "Comandos de registry de predicciones"),
    )
    pp_sub = pp.add_subparsers(dest="pred_cmd", required=True)

    ppl = pp_sub.add_parser("list", help="List predictions")
    ppl.add_argument("--json", action="store_true", help="Emit JSON")
    ppl.set_defaults(func=cmd_predict_list)

    pps = pp_sub.add_parser("show", help="Show a prediction")
    pps.add_argument("id", help="Prediction id (e.g. P-0003)")
    pps.set_defaults(func=cmd_predict_show)

    prc = sub.add_parser(
        "research",
        help=_tr(
            "Run best-effort scientific web research from a claim YAML/JSON",
            "Ejecuta investigación científica web (best effort) desde claim YAML/JSON",
        ),
    )
    prc.add_argument("claim", help="Path to claim YAML/JSON")
    prc.add_argument("--max-results", default=5, type=int, help="Results per source")
    prc.add_argument("--show", default=3, type=int, help="Rows shown per source in text mode")
    prc.add_argument("--timeout", default=15, type=int, help="Network timeout in seconds")
    prc.add_argument("--json", action="store_true", help="Emit JSON")
    prc.set_defaults(func=cmd_research)

    pm = sub.add_parser(
        "module",
        help=_tr(
            "Module engineering commands (auto-generation from claims)",
            "Comandos de ingeniería de módulos (autogeneración desde claims)",
        ),
    )
    pm_sub = pm.add_subparsers(dest="module_cmd", required=True)

    pma = pm_sub.add_parser(
        "auto",
        help=_tr(
            "Create a new extension module from claim data when no module fits",
            "Crea un nuevo módulo de extensiones cuando no hay uno que encaje",
        ),
    )
    pma.add_argument("claim", help="Path to claim YAML/JSON")
    pma.add_argument("--module-name", help="Explicit module name (e.g. mrd_auto_x)")
    pma.add_argument(
        "--no-research",
        action="store_true",
        help="Disable external scientific source scan",
    )
    pma.add_argument("--max-sources", default=5, type=int, help="Max results per source")
    pma.add_argument(
        "--create-prediction",
        action="store_true",
        help="Create prediction draft from generated context",
    )
    pma.add_argument(
        "--publish-prediction",
        action="store_true",
        help="Also append the generated prediction to predictions/registry.yaml",
    )
    pma.add_argument(
        "--no-manifest",
        action="store_true",
        help="Do not register the generated module in extensions manifest",
    )
    pma.add_argument(
        "--force",
        action="store_true",
        help="If module exists, create a timestamped variant",
    )
    pma.add_argument("--json", action="store_true", help="Emit JSON")
    pma.set_defaults(func=cmd_module_auto)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
