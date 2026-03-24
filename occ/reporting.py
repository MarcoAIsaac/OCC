"""Helpers to summarize OCC compiler-style reports for humans."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping


def summarize_report(report: Mapping[str, Any]) -> Dict[str, Any]:
    diagnostics = report.get("diagnostics", {})
    verdict = str(report.get("verdict", ""))
    first_reason = str(report.get("first_reason", ""))
    reason_catalog = report.get("reason_catalog", [])
    pipeline_trace = report.get("pipeline_trace", {})
    claim_bundle = report.get("claim_bundle", {})
    constraint_ir = report.get("constraint_ir", {})

    pass_counts = diagnostics.get("counts", {}) if isinstance(diagnostics, Mapping) else {}
    by_category = diagnostics.get("by_category", {}) if isinstance(diagnostics, Mapping) else {}
    passes = pipeline_trace.get("passes", []) if isinstance(pipeline_trace, Mapping) else []
    required_checks = (
        constraint_ir.get("required_checks", []) if isinstance(constraint_ir, Mapping) else []
    )

    top_reasons: List[Dict[str, str]] = []
    if isinstance(reason_catalog, list):
        for item in reason_catalog[:5]:
            if not isinstance(item, Mapping):
                continue
            top_reasons.append(
                {
                    "code": str(item.get("code", "")),
                    "category": str(item.get("category", "")),
                    "label": str(item.get("label", "")),
                    "severity": str(item.get("severity", "")),
                }
            )

    return {
        "verdict": verdict,
        "first_reason": first_reason,
        "claim_id": claim_bundle.get("claim_id") if isinstance(claim_bundle, Mapping) else None,
        "title": claim_bundle.get("title") if isinstance(claim_bundle, Mapping) else None,
        "frontend": claim_bundle.get("frontend") if isinstance(claim_bundle, Mapping) else None,
        "counts": {
            "pass": int(pass_counts.get("pass", 0)),
            "fail": int(pass_counts.get("fail", 0)),
            "no_eval": int(pass_counts.get("no_eval", 0)),
        },
        "by_category": dict(by_category) if isinstance(by_category, Mapping) else {},
        "pipeline_passes": [str(item.get("name", "")) for item in passes if isinstance(item, Mapping)],
        "required_checks": [str(x) for x in required_checks] if isinstance(required_checks, list) else [],
        "top_reasons": top_reasons,
    }


def render_report_summary(report: Mapping[str, Any], language: str = "en") -> str:
    summary = summarize_report(report)
    lines: List[str] = []

    if language == "es":
        lines.append(f"Veredicto: {summary['verdict']}")
        if summary.get("first_reason"):
            lines.append(f"Primer reason code: {summary['first_reason']}")
        if summary.get("claim_id"):
            lines.append(f"Claim: {summary['claim_id']}")
        if summary.get("title"):
            lines.append(f"Título: {summary['title']}")
        lines.append(
            "Conteo de jueces: "
            f"PASS={summary['counts']['pass']} "
            f"FAIL={summary['counts']['fail']} "
            f"NO-EVAL={summary['counts']['no_eval']}"
        )
        if summary["pipeline_passes"]:
            lines.append("Pipeline: " + " -> ".join(summary["pipeline_passes"]))
        if summary["required_checks"]:
            lines.append("Checks obligatorios: " + ", ".join(summary["required_checks"]))
        if summary["by_category"]:
            cat_line = ", ".join(
                f"{key}={value}" for key, value in sorted(summary["by_category"].items())
            )
            lines.append("Razones por categoría: " + cat_line)
        if summary["top_reasons"]:
            lines.append("Razones principales:")
            for item in summary["top_reasons"]:
                lines.append(
                    f"- {item['code']} [{item['category']}] {item['label']} ({item['severity']})"
                )
        return "\n".join(lines)

    lines.append(f"Verdict: {summary['verdict']}")
    if summary.get("first_reason"):
        lines.append(f"First reason code: {summary['first_reason']}")
    if summary.get("claim_id"):
        lines.append(f"Claim: {summary['claim_id']}")
    if summary.get("title"):
        lines.append(f"Title: {summary['title']}")
    lines.append(
        "Judge counts: "
        f"PASS={summary['counts']['pass']} "
        f"FAIL={summary['counts']['fail']} "
        f"NO-EVAL={summary['counts']['no_eval']}"
    )
    if summary["pipeline_passes"]:
        lines.append("Pipeline: " + " -> ".join(summary["pipeline_passes"]))
    if summary["required_checks"]:
        lines.append("Required checks: " + ", ".join(summary["required_checks"]))
    if summary["by_category"]:
        cat_line = ", ".join(
            f"{key}={value}" for key, value in sorted(summary["by_category"].items())
        )
        lines.append("Reasons by category: " + cat_line)
    if summary["top_reasons"]:
        lines.append("Top reasons:")
        for item in summary["top_reasons"]:
            lines.append(f"- {item['code']} [{item['category']}] {item['label']} ({item['severity']})")
    return "\n".join(lines)
