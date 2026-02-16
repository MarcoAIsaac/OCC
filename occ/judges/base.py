"""Judge interfaces.

In OCC terminology:

- **Judges** evaluate a claim (or derived artifact) and produce a verdict.
- **Locks** are specific checks inside judges that must hold (PASS) or fail
  (FAIL / NO-EVAL).

This module provides the minimal types used by the built-in judge pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class JudgeResult:
    """Result of a judge evaluation."""

    judge: str
    verdict: str  # PASS / FAIL(<CODE>) / NO-EVAL(<CODE>)
    code: str
    message: str
    details: Mapping[str, Any] = field(default_factory=dict)


class Judge(Protocol):
    name: str

    def evaluate(self, claim: Mapping[str, Any]) -> JudgeResult:  # pragma: no cover
        ...
