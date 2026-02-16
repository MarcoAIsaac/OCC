"""Domain (Ω_I) judge.

This judge enforces a minimal operational domain declaration.
"""

from __future__ import annotations

from typing import Any, Mapping

from .base import JudgeResult


class DomainJudge:
    name = "domain"

    def evaluate(self, claim: Mapping[str, Any]) -> JudgeResult:
        domain = claim.get("domain")
        if not isinstance(domain, dict):
            return JudgeResult(
                judge=self.name,
                verdict="NO-EVAL(DOM1)",
                code="DOM1",
                message="Missing domain declaration (expected mapping under 'domain').",
            )

        omega = domain.get("omega_I")
        if not isinstance(omega, (str, dict)):
            return JudgeResult(
                judge=self.name,
                verdict="NO-EVAL(DOM2)",
                code="DOM2",
                message="Missing omega_I (operational domain) inside 'domain'.",
            )

        observables = domain.get("observables")
        if not isinstance(observables, list) or not observables:
            return JudgeResult(
                judge=self.name,
                verdict="NO-EVAL(DOM3)",
                code="DOM3",
                message="Domain must declare a non-empty list of observables.",
            )

        # Optional: require at least one measurement anchor
        anchors = domain.get("anchors")
        if anchors is not None and not isinstance(anchors, list):
            return JudgeResult(
                judge=self.name,
                verdict="FAIL(DOM4)",
                code="DOM4",
                message="If provided, 'anchors' must be a list.",
            )

        return JudgeResult(
            judge=self.name,
            verdict="PASS(DOM)",
            code="DOM",
            message="Operational domain declaration present.",
            details={
                "observables": [str(x) for x in observables],
            },
        )
