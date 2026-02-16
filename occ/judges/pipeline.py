"""Judge pipelines."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Iterable, List, Mapping, Tuple

from .base import Judge, JudgeResult
from .domain import DomainJudge
from .trace import TraceConfig, TraceJudge
from .uv_guard import UVGuardJudge


def default_judges(strict_trace: bool = False) -> List[Judge]:
    return [
        DomainJudge(),
        UVGuardJudge(),
        TraceJudge(TraceConfig(strict=strict_trace)),
    ]


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
    return {
        "verdict": final_verdict,
        "first_reason": first_reason,
        "judges": [asdict(r) for r in results],
    }
