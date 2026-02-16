"""Automatic module generation from user claims."""

from __future__ import annotations

import json
import re
import shutil
import textwrap
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from .catalog import build_catalog
from .judges.nuclear_guard import claim_is_nuclear
from .judges.pipeline import default_judges, run_pipeline
from .science_research import research_claim
from .suites import SUITE_EXTENSIONS, discover_suite_roots, find_repo_root
from .util import simple_yaml
from .version import get_version

try:
    import yaml as _pyyaml  # type: ignore[import-untyped]
except ModuleNotFoundError:
    _pyyaml = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(text: str) -> str:
    low = text.strip().lower()
    low = re.sub(r"[^a-z0-9]+", "_", low)
    low = low.strip("_")
    return low or f"generated_{int(time.time())}"


def _load_yaml_text(text: str) -> Any:
    if _pyyaml is not None:
        return _pyyaml.safe_load(text)
    return simple_yaml.safe_load(text)


def _dump_yaml_text(data: Any) -> str:
    if _pyyaml is not None:
        return str(_pyyaml.safe_dump(data, sort_keys=False, allow_unicode=True))
    raise RuntimeError("YAML dump requires PyYAML in this environment")


def load_claim_file(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        obj = json.loads(text)
    else:
        obj = _load_yaml_text(text)
    if not isinstance(obj, dict):
        raise ValueError("Claim must be a mapping (YAML/JSON object)")
    return obj


def _validate_claim_for_autogen(claim: Mapping[str, Any]) -> None:
    errors: list[str] = []

    title = claim.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append("Missing required string field: title")

    domain = claim.get("domain")
    if not isinstance(domain, Mapping):
        errors.append("Missing required mapping field: domain")
    else:
        omega = domain.get("omega_I")
        if not isinstance(omega, (str, Mapping)):
            errors.append("Missing required domain field: domain.omega_I")

        observables = domain.get("observables")
        if not isinstance(observables, list) or not observables:
            errors.append("Missing required domain field: domain.observables[] (non-empty list)")

    params = claim.get("parameters")
    if params is not None:
        if not isinstance(params, list):
            errors.append("Invalid field: parameters must be a list when provided")
        else:
            for i, p in enumerate(params):
                if not isinstance(p, Mapping):
                    errors.append(f"Invalid parameters[{i}]: expected mapping")
                    continue
                name = p.get("name")
                if not isinstance(name, str) or not name.strip():
                    errors.append(f"Invalid parameters[{i}]: missing string name")

    if errors:
        raise ValueError(
            "Claim is not valid for module auto-generation:\n- " + "\n- ".join(errors)
        )


def _verdict_prefix(verdict: str) -> str:
    if verdict.startswith("PASS"):
        return "PASS"
    if verdict.startswith("FAIL"):
        return "FAIL"
    if verdict.startswith("NO-EVAL"):
        return "NO-EVAL"
    return verdict or "PASS"


def _extensions_root(start: Path) -> Path:
    roots = discover_suite_roots(start)
    if roots.extensions:
        return roots.extensions.resolve()

    repo = find_repo_root(start)
    if not repo:
        raise RuntimeError("Could not locate repo root (pyproject.toml not found)")

    ext = (repo / SUITE_EXTENSIONS).resolve()
    ext.mkdir(parents=True, exist_ok=True)
    manifest = ext / "manifest.yaml"
    if not manifest.is_file():
        manifest.write_text("version: 1\n\nmodules: []\n", encoding="utf-8")
    return ext


def _find_existing_module(
    claim: Mapping[str, Any],
    start: Path,
    requested_name: Optional[str],
) -> Optional[str]:
    catalog = build_catalog(start, which="all")
    names = {x.name for x in catalog}

    if requested_name and requested_name in names:
        return requested_name

    for key in ("module", "mrd_module", "target_module"):
        val = claim.get(key)
        if isinstance(val, str) and val in names:
            return val

    return None


def _module_readme(
    module_name: str,
    claim: Mapping[str, Any],
    verdict: str,
    locks_applied: list[str],
    research: Dict[str, Any],
) -> str:
    title = str(claim.get("title") or module_name)
    query = str(research.get("query") or "")
    refs: list[str] = []
    sources = research.get("sources", {})
    if isinstance(sources, dict):
        for src in ("arxiv", "crossref"):
            items = sources.get(src)
            if not isinstance(items, list):
                continue
            for item in items[:3]:
                if not isinstance(item, dict):
                    continue
                t = str(item.get("title") or "").strip()
                u = str(item.get("url") or "").strip()
                if t and u:
                    refs.append(f"- {t} ({u})")

    refs_block = "\n".join(refs) if refs else "- No external references captured."
    locks_block = "\n".join(f"- {x}" for x in locks_applied) if locks_applied else "- none"

    return (
        f"# {module_name}\n\n"
        "Auto-generated extension module.\n\n"
        f"## Source claim\n\n- Title: {title}\n- Initial verdict: {verdict}\n\n"
        "## Applied judges/locks\n\n"
        f"{locks_block}\n\n"
        "## Research context query\n\n"
        f"`{query}`\n\n"
        "## Research references (best effort)\n\n"
        f"{refs_block}\n"
    )


def _runner_script(module_name: str) -> str:
    return textwrap.dedent(
        f"""\
        #!/usr/bin/env python3
        \"\"\"Auto-generated MRD runner.\"\"\"

        from __future__ import annotations

        import json
        import sys
        import time
        from pathlib import Path
        from typing import Any, Dict

        try:
            import yaml
        except ModuleNotFoundError:
            repo_root = Path(__file__).resolve().parents[3]
            if str(repo_root) not in sys.path:
                sys.path.insert(0, str(repo_root))
            from occ.util import simple_yaml as yaml


        def _repo_root() -> Path:
            return Path(__file__).resolve().parents[3]


        def main() -> int:
            if len(sys.argv) != 2:
                print("Usage: run_{module_name}.py <input.yaml>")
                return 2

            inp = Path(sys.argv[1]).resolve()
            claim = yaml.safe_load(inp.read_text(encoding="utf-8"))
            if not isinstance(claim, dict):
                raise SystemExit("Input must be a YAML mapping")

            sys.path.insert(0, str(_repo_root()))
            from occ.judges.pipeline import default_judges, run_pipeline

            ctx_path = Path(__file__).resolve().parents[1] / "module_context.json"
            ctx: Dict[str, Any] = {{}}
            if ctx_path.is_file():
                try:
                    ctx = json.loads(ctx_path.read_text(encoding="utf-8"))
                except Exception:
                    ctx = {{}}

            include_nuclear = bool(ctx.get("include_nuclear_profile", False))
            report = run_pipeline(
                claim,
                default_judges(
                    strict_trace=False,
                    include_nuclear=include_nuclear,
                ),
            )
            verdict = str(report.get("verdict"))

            out: Dict[str, Any] = {{
                "module": "{module_name}",
                "input": str(inp.name),
                "verdict": verdict,
                "report": report,
                "module_context": {{
                    "generated_from": ctx.get("source_claim"),
                    "locks_applied": ctx.get("locks_applied", []),
                    "research": ctx.get("research", {{}}),
                }},
                "timestamp": time.time(),
            }}

            outputs = Path(__file__).resolve().parents[1] / "outputs"
            outputs.mkdir(exist_ok=True)
            outpath = outputs / f"{module_name}.{{inp.stem}}.{{int(time.time())}}.report.json"
            outpath.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
            return 0


        if __name__ == "__main__":
            raise SystemExit(main())
        """
    )


def _manual_manifest_dump(modules: list[Dict[str, Any]]) -> str:
    lines = ["version: 1", "", "modules:"]
    for mod in modules:
        name = str(mod.get("name", "")).strip()
        if not name:
            continue
        lines.append(f"  - name: {name}")
        lines.append("    cases:")
        cases = mod.get("cases")
        if not isinstance(cases, list):
            cases = []
        for case in cases:
            if not isinstance(case, dict):
                continue
            inp = str(case.get("input", "pass.yaml"))
            exp = str(case.get("expect", "PASS"))
            lines.append(f"      - input: {inp}")
            lines.append(f"        expect: \"{exp}\"")
        if not cases:
            lines.append("      - input: pass.yaml")
            lines.append("        expect: \"PASS\"")
    return "\n".join(lines) + "\n"


def _update_manifest(ext_root: Path, module_name: str, expect_prefix: str) -> None:
    manifest = ext_root / "manifest.yaml"
    obj: Dict[str, Any]
    if manifest.is_file():
        obj_raw = _load_yaml_text(manifest.read_text(encoding="utf-8"))
        obj = obj_raw if isinstance(obj_raw, dict) else {"version": 1, "modules": []}
    else:
        obj = {"version": 1, "modules": []}

    modules = obj.get("modules")
    if not isinstance(modules, list):
        modules = []
        obj["modules"] = modules

    found = False
    for mod in modules:
        if not isinstance(mod, dict):
            continue
        if str(mod.get("name")) != module_name:
            continue
        mod["cases"] = [{"input": "pass.yaml", "expect": expect_prefix}]
        found = True
        break

    if not found:
        modules.append(
            {
                "name": module_name,
                "cases": [{"input": "pass.yaml", "expect": expect_prefix}],
            }
        )

    if _pyyaml is not None:
        txt = _dump_yaml_text(obj)
    else:
        txt = _manual_manifest_dump([m for m in modules if isinstance(m, dict)])
    manifest.write_text(txt, encoding="utf-8")


def _next_prediction_id(predictions_root: Path) -> str:
    reg = predictions_root / "registry.yaml"
    if not reg.is_file():
        return "P-0001"
    raw = _load_yaml_text(reg.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return "P-0001"
    preds = raw.get("predictions")
    if not isinstance(preds, list):
        return "P-0001"

    max_n = 0
    for p in preds:
        if not isinstance(p, dict):
            continue
        pid = str(p.get("id", ""))
        m = re.fullmatch(r"P-(\d+)", pid)
        if not m:
            continue
        max_n = max(max_n, int(m.group(1)))
    return f"P-{max_n + 1:04d}"


def _build_prediction(
    claim: Mapping[str, Any],
    module_name: str,
    research: Dict[str, Any],
) -> Dict[str, Any]:
    domain = claim.get("domain")
    domain_label = ""
    observables: list[str] = []
    if isinstance(domain, Mapping):
        omega = domain.get("omega_I")
        if isinstance(omega, str):
            domain_label = omega
        obs = domain.get("observables")
        if isinstance(obs, list):
            observables = [str(x) for x in obs]

    refs: list[str] = [f"module:{module_name}"]
    sources = research.get("sources", {})
    if isinstance(sources, dict):
        for src in ("arxiv", "crossref"):
            items = sources.get(src)
            if not isinstance(items, list):
                continue
            for item in items[:2]:
                if not isinstance(item, dict):
                    continue
                url = str(item.get("url") or "").strip()
                if url:
                    refs.append(url)

    title = str(claim.get("title") or f"Auto prediction from {module_name}")
    summary = (
        "Auto-generated prediction candidate derived from claim-spec auditing, "
        "applied judges/locks, and current scientific source scan."
    )
    return {
        "id": "",
        "title": title,
        "status": "draft",
        "summary": summary,
        "domain": domain_label or "Unspecified",
        "observables": observables,
        "tests": ["Validate claim under OCC judges and MRD reproducibility constraints"],
        "timeframe": "To be refined",
        "references": refs,
    }


def _manual_prediction_dump(pred: Mapping[str, Any]) -> str:
    def q(value: Any) -> str:
        return str(value).replace('"', "'")

    lines = [
        f"id: {pred.get('id', '')}",
        f"title: \"{q(pred.get('title', ''))}\"",
        f"status: {pred.get('status', 'draft')}",
        "summary: >-",
        f"  {pred.get('summary', '')}",
        f"domain: \"{q(pred.get('domain', ''))}\"",
        "observables:",
    ]
    for x in pred.get("observables", []):
        lines.append(f"  - \"{q(x)}\"")
    lines.append("tests:")
    for x in pred.get("tests", []):
        lines.append(f"  - \"{q(x)}\"")
    lines.append(f"timeframe: \"{q(pred.get('timeframe', ''))}\"")
    lines.append("references:")
    for x in pred.get("references", []):
        lines.append(f"  - \"{q(x)}\"")
    return "\n".join(lines) + "\n"


def _write_prediction_draft(predictions_root: Path, pred: Mapping[str, Any]) -> Path:
    drafts = predictions_root / "drafts"
    drafts.mkdir(parents=True, exist_ok=True)
    out = drafts / f"{pred['id']}.yaml"
    if _pyyaml is not None:
        out.write_text(_dump_yaml_text(dict(pred)), encoding="utf-8")
    else:
        out.write_text(_manual_prediction_dump(pred), encoding="utf-8")
    return out


def _publish_prediction(predictions_root: Path, pred: Mapping[str, Any]) -> Path:
    if _pyyaml is None:
        raise RuntimeError("Publishing prediction to registry requires PyYAML")
    registry = predictions_root / "registry.yaml"
    if registry.is_file():
        raw = _load_yaml_text(registry.read_text(encoding="utf-8"))
        obj = raw if isinstance(raw, dict) else {"version": 1, "predictions": []}
    else:
        obj = {"version": 1, "predictions": []}
    preds = obj.get("predictions")
    if not isinstance(preds, list):
        preds = []
        obj["predictions"] = preds
    preds.append(dict(pred))
    registry.write_text(_dump_yaml_text(obj), encoding="utf-8")
    return registry


def auto_generate_module(
    claim_path: Path,
    start: Path,
    module_name: Optional[str] = None,
    with_research: bool = True,
    max_sources: int = 5,
    create_prediction: bool = False,
    publish_prediction: bool = False,
    register_manifest: bool = True,
    force: bool = False,
) -> Dict[str, Any]:
    claim_path = claim_path.resolve()
    if not claim_path.is_file():
        raise FileNotFoundError(f"Claim file not found: {claim_path}")

    claim = load_claim_file(claim_path)
    _validate_claim_for_autogen(claim)
    existing = _find_existing_module(claim, start=start, requested_name=module_name)
    include_nuclear_profile = claim_is_nuclear(claim)
    report = run_pipeline(
        claim,
        default_judges(
            strict_trace=False,
            include_nuclear=include_nuclear_profile,
        ),
    )
    verdict = str(report.get("verdict") or "")

    if existing and not force:
        return {
            "schema": "occ.module_autogen.result.v1",
            "schema_version": "1.0",
            "occ_version": get_version(),
            "generated_at": _now_iso(),
            "created": False,
            "matched_existing": True,
            "module": existing,
            "verdict": verdict,
            "message": "Claim appears to map to an existing module",
        }

    hint = module_name or str(claim.get("claim_id") or claim.get("title") or claim_path.stem)
    normalized = _slugify(hint)
    if not normalized.startswith("mrd_"):
        normalized = f"mrd_auto_{normalized}"
    module_name = normalized

    ext_root = _extensions_root(start)
    module_dir = ext_root / module_name
    if module_dir.exists():
        if not force:
            raise RuntimeError(
                "Target module already exists: "
                f"{module_name}. Use --force to create a timestamped variant."
            )
        module_name = f"{module_name}_{int(time.time())}"
        module_dir = ext_root / module_name

    inputs = module_dir / "inputs"
    outputs = module_dir / "outputs"
    scripts = module_dir / "scripts"
    inputs.mkdir(parents=True, exist_ok=True)
    outputs.mkdir(parents=True, exist_ok=True)
    scripts.mkdir(parents=True, exist_ok=True)

    shutil.copy2(claim_path, inputs / "pass.yaml")
    (outputs / ".gitkeep").write_text("", encoding="utf-8")
    (outputs / ".gitignore").write_text("*.report.json\n!.gitkeep\n", encoding="utf-8")

    research = (
        research_claim(claim, max_results=max(1, int(max_sources)))
        if with_research
        else {"generated_at": _now_iso(), "query": "", "sources": {}, "errors": []}
    )

    judges = report.get("judges")
    locks_applied: list[str] = []
    if isinstance(judges, list):
        for j in judges:
            if isinstance(j, Mapping):
                code = j.get("code")
                if isinstance(code, str):
                    locks_applied.append(code)

    context = {
        "schema": "occ.module_context.v1",
        "schema_version": "1.0",
        "occ_version": get_version(),
        "module_name": module_name,
        "generated_at": _now_iso(),
        "source_claim": str(claim_path),
        "baseline_verdict": verdict,
        "include_nuclear_profile": include_nuclear_profile,
        "locks_applied": locks_applied,
        "judge_report": report,
        "research": research,
    }
    (module_dir / "module_context.json").write_text(
        json.dumps(context, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    (module_dir / "MRD_README.md").write_text(
        _module_readme(module_name, claim, verdict, locks_applied, research),
        encoding="utf-8",
    )
    runner_name = f"run_{module_name}.py"
    runner_path = scripts / runner_name
    runner_path.write_text(_runner_script(module_name), encoding="utf-8")

    if register_manifest:
        _update_manifest(ext_root, module_name=module_name, expect_prefix=_verdict_prefix(verdict))

    prediction_draft: Optional[Path] = None
    prediction_registry: Optional[Path] = None
    prediction_id: Optional[str] = None
    if create_prediction or publish_prediction:
        repo = find_repo_root(start) or start.resolve()
        pred_root = repo / "predictions"
        pred_root.mkdir(parents=True, exist_ok=True)
        pred = _build_prediction(claim, module_name=module_name, research=research)
        pred["id"] = _next_prediction_id(pred_root)
        prediction_id = str(pred["id"])
        prediction_draft = _write_prediction_draft(pred_root, pred)
        if publish_prediction:
            prediction_registry = _publish_prediction(pred_root, pred)

    return {
        "schema": "occ.module_autogen.result.v1",
        "schema_version": "1.0",
        "occ_version": get_version(),
        "generated_at": _now_iso(),
        "created": True,
        "matched_existing": False,
        "module": module_name,
        "module_dir": str(module_dir),
        "verdict": verdict,
        "locks_applied": locks_applied,
        "research_query": research.get("query"),
        "prediction_id": prediction_id,
        "prediction_draft": str(prediction_draft) if prediction_draft else None,
        "prediction_registry": str(prediction_registry) if prediction_registry else None,
    }
