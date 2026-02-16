"""Traceability judge.

This judge produces a minimal *witness* mapping (path -> sha256) for any declared
source files. The goal is to make reviews auditable and reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from ..suites import find_repo_root
from ..util.hashing import sha256_file
from .base import JudgeResult


@dataclass(frozen=True)
class TraceConfig:
    strict: bool = False


class TraceJudge:
    name = "trace"

    def __init__(self, cfg: Optional[TraceConfig] = None) -> None:
        self.cfg = cfg or TraceConfig()

    def evaluate(self, claim: Mapping[str, Any]) -> JudgeResult:
        sources = claim.get("sources")
        if sources is None:
            return JudgeResult(
                judge=self.name,
                verdict="PASS(TR0)",
                code="TR0",
                message="No sources declared (traceability optional).",
            )

        if not isinstance(sources, list):
            return JudgeResult(
                judge=self.name,
                verdict="FAIL(TR3)",
                code="TR3",
                message="'sources' must be a list of paths.",
            )

        repo_root = find_repo_root(Path.cwd()) or Path.cwd()
        witness: dict[str, str] = {}
        missing: list[str] = []
        for raw in sources:
            p = Path(str(raw))
            abs_p = p if p.is_absolute() else (repo_root / p)
            if not abs_p.exists():
                missing.append(str(p))
                continue
            if abs_p.is_dir():
                # keep it simple: directories are not hashed
                missing.append(str(p))
                continue
            witness[str(p)] = "sha256:" + sha256_file(abs_p)

        if missing and self.cfg.strict:
            return JudgeResult(
                judge=self.name,
                verdict="NO-EVAL(TR1)",
                code="TR1",
                message="Missing source files required for traceability.",
                details={"missing": missing},
            )

        if missing:
            return JudgeResult(
                judge=self.name,
                verdict="NO-EVAL(TR2)",
                code="TR2",
                message="Some sources missing; traceability incomplete.",
                details={"missing": missing, "witness": witness},
            )

        return JudgeResult(
            judge=self.name,
            verdict="PASS(TR)",
            code="TR",
            message="Traceability witness generated.",
            details={"witness": witness},
        )
