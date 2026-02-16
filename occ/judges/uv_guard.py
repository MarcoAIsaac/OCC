"""UV reinjection guard judge.

This judge is intentionally conservative: it does not try to "solve" UV physics.
It checks that the claim's *parameterization* does not rely on inaccessible knobs
that materially affect the stated observables.

The claim spec format is minimal and pragmatic:

```yaml
parameters:
  - name: theta
    accessible: false
    affects_observables: true
```
"""

from __future__ import annotations

from typing import Any, Mapping

from .base import JudgeResult


class UVGuardJudge:
    name = "uv_guard"

    def evaluate(self, claim: Mapping[str, Any]) -> JudgeResult:
        params = claim.get("parameters")
        if params is None:
            return JudgeResult(
                judge=self.name,
                verdict="PASS(UV0)",
                code="UV0",
                message="No parameters declared (UV-guard not applicable).",
            )

        if not isinstance(params, list):
            return JudgeResult(
                judge=self.name,
                verdict="FAIL(UV4)",
                code="UV4",
                message="'parameters' must be a list.",
            )

        flagged: list[dict[str, Any]] = []
        for i, raw in enumerate(params):
            if not isinstance(raw, dict):
                return JudgeResult(
                    judge=self.name,
                    verdict="FAIL(UV5)",
                    code="UV5",
                    message=f"Parameter entry #{i} must be a mapping.",
                )
            name = str(raw.get("name", "")).strip()
            if not name:
                return JudgeResult(
                    judge=self.name,
                    verdict="FAIL(UV6)",
                    code="UV6",
                    message=f"Parameter entry #{i} missing 'name'.",
                )

            affects = raw.get("affects_observables")
            accessible = raw.get("accessible")

            if affects is True:
                if accessible is False:
                    flagged.append({"name": name, "reason": "inaccessible_affects"})
                elif accessible is None:
                    flagged.append({"name": name, "reason": "unknown_accessibility"})

        if flagged:
            # Conservative: if any inaccessible or unknown knob affects observables -> NO-EVAL
            codes = {
                "inaccessible_affects": "UV1",
                "unknown_accessibility": "UV2",
            }
            first = flagged[0]
            code = codes.get(str(first.get("reason")), "UV1")
            return JudgeResult(
                judge=self.name,
                verdict=f"NO-EVAL({code})",
                code=code,
                message=(
                    "Potential UV reinjection: inaccessible/unknown parameter affects observables."
                ),
                details={"flagged": flagged},
            )

        return JudgeResult(
            judge=self.name,
            verdict="PASS(UV)",
            code="UV",
            message="No obvious UV reinjection via inaccessible parameters.",
            details={"n_parameters": len(params)},
        )
