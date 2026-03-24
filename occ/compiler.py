"""Claim normalization and compiler-style report helpers for OCC."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Mapping, Sequence

from .reason_codes import lookup_reason
from .version import get_version

CLAIM_BUNDLE_SCHEMA = "occ.claim_bundle.v1"
OCC_IR_SCHEMA = "occ.ir.v1"
CONSTRAINT_IR_SCHEMA = "occ.constraint_ir.v1"
VERDICT_BUNDLE_SCHEMA = "occ.verdict_bundle.v2"


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _normalize_sources(raw: Any) -> List[str]:
    if not isinstance(raw, list):
        return []
    return [str(x) for x in raw]


def _normalize_parameters(raw: Any) -> List[Dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        out.append(
            {
                "name": name,
                "accessible": item.get("accessible"),
                "affects_observables": item.get("affects_observables"),
            }
        )
    return out


def build_claim_bundle(claim: Mapping[str, Any]) -> Dict[str, Any]:
    domain = claim.get("domain")
    domain_map = dict(domain) if isinstance(domain, Mapping) else {}
    observables = domain_map.get("observables")
    sources = _normalize_sources(claim.get("sources"))
    parameters = _normalize_parameters(claim.get("parameters"))
    assumptions = claim.get("assumptions")
    if not isinstance(assumptions, list):
        assumptions = []

    normalized: Dict[str, Any] = {
        "schema": CLAIM_BUNDLE_SCHEMA,
        "schema_version": "1.0",
        "claim_id": str(claim.get("claim_id") or "").strip() or None,
        "title": str(claim.get("title") or "").strip() or None,
        "frontend": "claim_spec",
        "domain": {
            "omega_I": domain_map.get("omega_I"),
            "observables": [str(x) for x in observables] if isinstance(observables, list) else [],
            "anchors": [str(x) for x in domain_map.get("anchors", [])]
            if isinstance(domain_map.get("anchors"), list)
            else [],
        },
        "parameters": parameters,
        "sources": sources,
        "assumptions": [str(x) for x in assumptions],
        "raw_claim": dict(claim),
    }
    normalized["content_hash"] = "sha256:" + _sha256_json(normalized["raw_claim"])
    return normalized


def _profile_hints(bundle: Mapping[str, Any]) -> List[str]:
    domain = bundle.get("domain", {})
    texts: List[str] = []
    if isinstance(domain, Mapping):
        for key in ("omega_I", "sector", "field", "discipline", "domain_type"):
            raw = domain.get(key)
            if isinstance(raw, str):
                texts.append(raw.lower())
        observables = domain.get("observables")
        if isinstance(observables, list):
            texts.extend(str(x).lower() for x in observables)
    merged = " ".join(texts)
    hints: List[str] = []
    if any(token in merged for token in ("nuclear", "reactor", "fission", "fusion", "neutron", "isotope")):
        hints.append("nuclear")
    if not hints:
        hints.append("core")
    return hints


def build_occ_ir(bundle: Mapping[str, Any]) -> Dict[str, Any]:
    parameters = bundle.get("parameters", [])
    if not isinstance(parameters, list):
        parameters = []

    domain = bundle.get("domain", {})
    if not isinstance(domain, Mapping):
        domain = {}

    observables = domain.get("observables", [])
    if not isinstance(observables, list):
        observables = []

    uv_sensitive = [
        str(p.get("name"))
        for p in parameters
        if isinstance(p, Mapping)
        and p.get("affects_observables") is True
        and p.get("accessible") is not True
    ]

    occ_ir: Dict[str, Any] = {
        "schema": OCC_IR_SCHEMA,
        "schema_version": "1.0",
        "dialect": "occ.claim",
        "claim_ref": bundle.get("claim_id") or bundle.get("content_hash"),
        "domain": {
            "omega_I": domain.get("omega_I"),
            "observables": [str(x) for x in observables],
            "anchor_count": len(domain.get("anchors", [])) if isinstance(domain.get("anchors"), list) else 0,
        },
        "parameter_table": parameters,
        "assumptions": bundle.get("assumptions", []),
        "source_count": len(bundle.get("sources", [])) if isinstance(bundle.get("sources"), list) else 0,
        "profile_hints": _profile_hints(bundle),
        "uv_sensitive_parameters": uv_sensitive,
    }
    occ_ir["ir_hash"] = "sha256:" + _sha256_json(occ_ir)
    return occ_ir


def build_constraint_ir(bundle: Mapping[str, Any], occ_ir: Mapping[str, Any]) -> Dict[str, Any]:
    domain = occ_ir.get("domain", {})
    observables = domain.get("observables", []) if isinstance(domain, Mapping) else []
    required_checks: List[str] = ["domain_declared", "omega_declared", "observables_non_empty"]
    optional_checks: List[str] = []

    if occ_ir.get("uv_sensitive_parameters"):
        required_checks.append("uv_reinjection_guard")
    else:
        optional_checks.append("uv_reinjection_guard")

    sources = bundle.get("sources", [])
    if isinstance(sources, list) and sources:
        optional_checks.append("traceability_witness")

    if "nuclear" in occ_ir.get("profile_hints", []):
        required_checks.extend(["nuclear_domain_guard", "evidence_anchor"])

    return {
        "schema": CONSTRAINT_IR_SCHEMA,
        "schema_version": "1.0",
        "claim_ref": bundle.get("claim_id") or bundle.get("content_hash"),
        "required_checks": required_checks,
        "optional_checks": optional_checks,
        "observable_count": len(observables) if isinstance(observables, list) else 0,
        "source_count": len(sources) if isinstance(sources, list) else 0,
        "constraint_hash": "sha256:" + _sha256_json(
            {
                "required_checks": required_checks,
                "optional_checks": optional_checks,
                "profile_hints": occ_ir.get("profile_hints", []),
            }
        ),
    }


def severity_from_verdict(verdict: str, default_severity: str) -> str:
    if verdict.startswith("FAIL"):
        return "error"
    if verdict.startswith("NO-EVAL"):
        return "warning"
    if verdict.startswith("PASS"):
        return "info"
    return default_severity


def build_reason_catalog(judge_payloads: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    catalog: List[Dict[str, Any]] = []
    for entry in judge_payloads:
        code = str(entry.get("code", ""))
        verdict = str(entry.get("verdict", ""))
        meta = lookup_reason(code)
        catalog.append(
            {
                "judge": str(entry.get("judge", "")),
                "code": code,
                "category": meta["category"],
                "label": meta["label"],
                "severity": severity_from_verdict(verdict, meta["default_severity"]),
                "verdict": verdict,
                "message": str(entry.get("message", "")),
            }
        )
    return catalog


def build_diagnostics(
    judge_payloads: Sequence[Mapping[str, Any]],
    reason_catalog: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    counts = {"pass": 0, "fail": 0, "no_eval": 0}
    for entry in judge_payloads:
        verdict = str(entry.get("verdict", ""))
        if verdict.startswith("FAIL"):
            counts["fail"] += 1
        elif verdict.startswith("NO-EVAL"):
            counts["no_eval"] += 1
        else:
            counts["pass"] += 1

    by_category: Dict[str, int] = {}
    for entry in reason_catalog:
        cat = str(entry.get("category", "general"))
        by_category[cat] = by_category.get(cat, 0) + 1

    return {"counts": counts, "by_category": by_category}


def build_pipeline_trace(
    judge_names: Sequence[str],
    bundle: Mapping[str, Any],
    occ_ir: Mapping[str, Any],
    constraint_ir: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "compiler": "occ.claim_compiler",
        "passes": [
            {"name": "parse_claim", "kind": "frontend", "status": "ok"},
            {"name": "normalize_claim", "kind": "normalization", "status": "ok"},
            {"name": "lower_to_occ_ir", "kind": "lowering", "status": "ok"},
            {"name": "lower_to_constraint_ir", "kind": "lowering", "status": "ok"},
            {"name": "run_judges", "kind": "analysis", "status": "ok", "judges": list(judge_names)},
            {"name": "emit_verdict_bundle", "kind": "emission", "status": "ok"},
        ],
        "artifacts": {
            "claim_bundle": bundle.get("content_hash"),
            "occ_ir": occ_ir.get("ir_hash"),
            "constraint_ir": constraint_ir.get("constraint_hash"),
        },
    }


def build_verdict_bundle(
    claim: Mapping[str, Any],
    judge_names: Sequence[str],
    judge_payloads: Sequence[Mapping[str, Any]],
    final_verdict: str,
    first_reason: str,
) -> Dict[str, Any]:
    bundle = build_claim_bundle(claim)
    occ_ir = build_occ_ir(bundle)
    constraint_ir = build_constraint_ir(bundle, occ_ir)
    reason_catalog = build_reason_catalog(judge_payloads)
    diagnostics = build_diagnostics(judge_payloads, reason_catalog)

    return {
        "schema": VERDICT_BUNDLE_SCHEMA,
        "schema_version": "2.0",
        "occ_version": get_version(),
        "claim_bundle": bundle,
        "occ_ir": occ_ir,
        "constraint_ir": constraint_ir,
        "pipeline_trace": build_pipeline_trace(judge_names, bundle, occ_ir, constraint_ir),
        "diagnostics": diagnostics,
        "reason_catalog": reason_catalog,
        "provenance": {
            "compiler": "occ.claim_compiler",
            "frontend": bundle.get("frontend"),
            "judge_set": list(judge_names),
            "content_hash": bundle.get("content_hash"),
        },
        "verdict_summary": {
            "verdict": final_verdict,
            "first_reason": first_reason,
            "judge_count": len(judge_payloads),
        },
    }
