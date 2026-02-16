"""Batch experiment lab for OCC claim evaluation.

The lab runs multiple claim specs across one or more judge profiles and
generates auditable comparative artifacts (JSON/CSV/Markdown).
"""

from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from .judges.pipeline import default_judges, run_pipeline
from .module_autogen import load_claim_file
from .version import get_version

LAB_REPORT_SCHEMA = "occ.lab_report.v1"


@dataclass(frozen=True)
class LabConfig:
    claim_paths: List[Path]
    profiles: List[str]
    strict_trace: bool
    out_dir: Path


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _verdict_class(raw: str) -> str:
    upper = str(raw or "").upper()
    if upper.startswith("PASS"):
        return "PASS"
    if upper.startswith("FAIL"):
        return "FAIL"
    if upper.startswith("NO-EVAL"):
        return "NO-EVAL"
    return "UNKNOWN"


def discover_claim_files(claims_dir: Path, recursive: bool = False) -> List[Path]:
    if not claims_dir.is_dir():
        raise FileNotFoundError(f"Claims directory not found: {claims_dir}")

    patterns = ("*.yaml", "*.yml", "*.json")
    discovered: List[Path] = []
    for pattern in patterns:
        if recursive:
            discovered.extend(claims_dir.rglob(pattern))
        else:
            discovered.extend(claims_dir.glob(pattern))

    files = sorted(x.resolve() for x in discovered if x.is_file())
    if not files:
        raise FileNotFoundError(f"No claim files found in: {claims_dir}")
    return files


def _profile_to_include_nuclear(profile: str) -> bool:
    return str(profile).strip().lower() == "nuclear"


def _claim_label(claim: Mapping[str, Any], path: Path) -> str:
    claim_id = claim.get("claim_id")
    if isinstance(claim_id, str) and claim_id.strip():
        return claim_id.strip()
    return path.stem


def _claim_title(claim: Mapping[str, Any], path: Path) -> str:
    title = claim.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    return path.stem


def _profile_stats(rows: Iterable[Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    stats: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        profile = str(row.get("profile") or "unknown")
        cls = _verdict_class(str(row.get("verdict") or ""))
        item = stats.setdefault(
            profile,
            {
                "profile": profile,
                "runs": 0,
                "pass": 0,
                "fail": 0,
                "no_eval": 0,
                "unknown": 0,
                "pass_rate": 0.0,
            },
        )
        item["runs"] += 1
        if cls == "PASS":
            item["pass"] += 1
        elif cls == "FAIL":
            item["fail"] += 1
        elif cls == "NO-EVAL":
            item["no_eval"] += 1
        else:
            item["unknown"] += 1

    for item in stats.values():
        runs = int(item["runs"])
        item["pass_rate"] = round((float(item["pass"]) / runs) if runs > 0 else 0.0, 4)
    return stats


def _matrix(
    rows: Sequence[Mapping[str, Any]],
    profiles: Sequence[str],
) -> Dict[str, Dict[str, str]]:
    table: Dict[str, Dict[str, str]] = {}
    for row in rows:
        claim_label = str(row.get("claim_id") or "unknown")
        profile = str(row.get("profile") or "unknown")
        verdict = str(row.get("verdict") or "UNKNOWN")
        claim_row = table.setdefault(claim_label, {})
        claim_row[profile] = verdict

    for claim_row in table.values():
        for profile in profiles:
            claim_row.setdefault(profile, "-")
    return table


def _divergence(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    by_claim: Dict[str, List[Mapping[str, Any]]] = {}
    for row in rows:
        key = str(row.get("claim_id") or "unknown")
        by_claim.setdefault(key, []).append(row)

    out: List[Dict[str, Any]] = []
    for claim_id, claim_rows in by_claim.items():
        classes = {_verdict_class(str(x.get("verdict") or "")) for x in claim_rows}
        if len(classes) <= 1:
            continue
        out.append(
            {
                "claim_id": claim_id,
                "profiles": [
                    {
                        "profile": str(x.get("profile") or ""),
                        "verdict": str(x.get("verdict") or ""),
                        "first_reason": str(x.get("first_reason") or ""),
                    }
                    for x in claim_rows
                ],
            }
        )
    return sorted(out, key=lambda x: str(x["claim_id"]))


def _write_rows_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "claim_id",
                "title",
                "claim_path",
                "profile",
                "verdict",
                "first_reason",
                "duration_ms",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    str(row.get("claim_id") or ""),
                    str(row.get("title") or ""),
                    str(row.get("claim_path") or ""),
                    str(row.get("profile") or ""),
                    str(row.get("verdict") or ""),
                    str(row.get("first_reason") or ""),
                    str(row.get("duration_ms") or ""),
                ]
            )


def _write_profile_csv(path: Path, stats: Mapping[str, Mapping[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["profile", "runs", "pass", "fail", "no_eval", "unknown", "pass_rate"])
        for profile in sorted(stats):
            row = stats[profile]
            writer.writerow(
                [
                    row.get("profile", profile),
                    row.get("runs", 0),
                    row.get("pass", 0),
                    row.get("fail", 0),
                    row.get("no_eval", 0),
                    row.get("unknown", 0),
                    row.get("pass_rate", 0.0),
                ]
            )


def _write_matrix_markdown(
    path: Path,
    matrix: Mapping[str, Mapping[str, str]],
    profiles: Sequence[str],
) -> None:
    headers = ["Claim"] + [str(p) for p in profiles]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for claim_id in sorted(matrix):
        row = [claim_id] + [str(matrix[claim_id].get(p, "-")) for p in profiles]
        lines.append("| " + " | ".join(row) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_experiment_lab(cfg: LabConfig) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for claim_path in cfg.claim_paths:
        claim = load_claim_file(claim_path)
        if not isinstance(claim, Mapping):
            raise ValueError(f"Claim must be a mapping: {claim_path}")
        claim_id = _claim_label(claim, claim_path)
        title = _claim_title(claim, claim_path)

        for profile in cfg.profiles:
            judges = default_judges(
                strict_trace=cfg.strict_trace,
                include_nuclear=_profile_to_include_nuclear(profile),
            )
            started = time.perf_counter()
            report = run_pipeline(claim, judges)
            duration_ms = int((time.perf_counter() - started) * 1000)

            verdict = str(report.get("verdict") or "UNKNOWN")
            rows.append(
                {
                    "claim_id": claim_id,
                    "title": title,
                    "claim_path": str(claim_path),
                    "profile": profile,
                    "verdict": verdict,
                    "verdict_class": _verdict_class(verdict),
                    "first_reason": str(report.get("first_reason") or ""),
                    "duration_ms": duration_ms,
                }
            )

    totals = {
        "runs": len(rows),
        "pass": sum(1 for x in rows if x["verdict_class"] == "PASS"),
        "fail": sum(1 for x in rows if x["verdict_class"] == "FAIL"),
        "no_eval": sum(1 for x in rows if x["verdict_class"] == "NO-EVAL"),
        "unknown": sum(1 for x in rows if x["verdict_class"] == "UNKNOWN"),
    }
    stats = _profile_stats(rows)
    matrix = _matrix(rows, cfg.profiles)
    divergence = _divergence(rows)

    payload: Dict[str, Any] = {
        "schema": LAB_REPORT_SCHEMA,
        "occ_version": get_version(),
        "generated_at": _now_iso(),
        "config": {
            "profiles": cfg.profiles,
            "strict_trace": cfg.strict_trace,
            "claim_count": len(cfg.claim_paths),
            "out_dir": str(cfg.out_dir),
        },
        "totals": totals,
        "profile_stats": [stats[p] for p in sorted(stats)],
        "divergence_count": len(divergence),
        "divergence": divergence,
        "results": rows,
    }

    cfg.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = cfg.out_dir / "lab_report.json"
    rows_csv = cfg.out_dir / "lab_results.csv"
    profile_csv = cfg.out_dir / "lab_profile_summary.csv"
    matrix_md = cfg.out_dir / "lab_verdict_matrix.md"

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_rows_csv(rows_csv, rows)
    _write_profile_csv(profile_csv, stats)
    _write_matrix_markdown(matrix_md, matrix, cfg.profiles)

    payload["artifacts"] = {
        "json": str(json_path),
        "results_csv": str(rows_csv),
        "profile_csv": str(profile_csv),
        "matrix_md": str(matrix_md),
    }
    return payload
