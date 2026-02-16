"""Judge pipelines."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Tuple

from ..version import get_version
from .base import Judge, JudgeResult
from .domain import DomainJudge
from .nuclear_guard import NuclearGuardJudge
from .trace import TraceConfig, TraceJudge
from .uv_guard import UVGuardJudge

JUDGE_REPORT_SCHEMA = "occ.judge_report.v1"
JUDGE_REPORT_SCHEMA_VERSION = "1.0"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_judges(
    strict_trace: bool = False,
    include_nuclear: bool = False,
) -> List[Judge]:
    judges: List[Judge] = [
        DomainJudge(),
        UVGuardJudge(),
        TraceJudge(TraceConfig(strict=strict_trace)),
    ]
    if include_nuclear:
        judges.insert(1, NuclearGuardJudge())
    return judges


def combine(results: Iterable[JudgeResult]) -> Tuple[str, str]:
    """Return (final_verdict, first_reason_code)."""

    # Priority: NO-EVAL > FAIL > PASS
    first_reason = ""
    for r in results:
        if r.verdict.startswith("NO-EVAL"):
            return (r.verdict, r.code)
    for r in results:
        if r.verdict.startswith("FAIL"):
            return (r.verdict, r.code)
    return ("PASS", first_reason)


def run_pipeline(
    claim: Mapping[str, Any],
    judges: List[Judge],
) -> Dict[str, Any]:
    results: List[JudgeResult] = [j.evaluate(claim) for j in judges]
    final_verdict, first_reason = combine(results)
    claim_id = claim.get("claim_id")
    claim_id_text = str(claim_id) if isinstance(claim_id, str) else None
    return {
        "schema": JUDGE_REPORT_SCHEMA,
        "schema_version": JUDGE_REPORT_SCHEMA_VERSION,
        "occ_version": get_version(),
        "generated_at": _now_iso(),
        "claim_id": claim_id_text,
        "judge_set": [str(getattr(j, "name", "unknown")) for j in judges],
        "verdict": final_verdict,
        "first_reason": first_reason,
        "judges": [asdict(r) for r in results],
    }
