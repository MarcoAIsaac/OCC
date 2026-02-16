"""Predictions registry.

The registry is a lightweight, versioned YAML catalog of falsifiable predictions.
It exists to make *discoverability* easy (especially from the README and docs).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass(frozen=True)
class Prediction:
    id: str
    title: str
    summary: str
    status: str = "draft"  # draft | featured | deprecated
    domain: Optional[str] = None
    observables: List[str] = field(default_factory=list)
    tests: List[str] = field(default_factory=list)
    timeframe: Optional[str] = None
    references: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class PredictionRegistry:
    version: int
    predictions: List[Prediction]

    def by_id(self) -> Dict[str, Prediction]:
        return {p.id: p for p in self.predictions}


def find_registry_path(start: Path) -> Optional[Path]:
    """Find ``predictions/registry.yaml`` by walking up from ``start``."""

    p = start.resolve()
    for parent in [p] + list(p.parents):
        cand = parent / "predictions" / "registry.yaml"
        if cand.is_file():
            return cand
    return None


def _validate_registry_shape(obj: Any) -> None:
    if not isinstance(obj, dict):
        raise ValueError("Registry must be a YAML mapping")
    if "version" not in obj or "predictions" not in obj:
        raise ValueError("Registry requires keys: version, predictions")
    if not isinstance(obj["predictions"], list):
        raise ValueError("Registry predictions must be a list")


def load_registry(path: Path) -> PredictionRegistry:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    _validate_registry_shape(data)

    preds: List[Prediction] = []
    seen: set[str] = set()
    for raw in data["predictions"]:
        if not isinstance(raw, dict):
            raise ValueError("Each prediction entry must be a mapping")

        pid = str(raw.get("id", "")).strip()
        if not pid:
            raise ValueError("Prediction is missing id")
        if pid in seen:
            raise ValueError(f"Duplicate prediction id: {pid}")
        seen.add(pid)

        title = str(raw.get("title", "")).strip()
        if not title:
            raise ValueError(f"Prediction {pid} is missing title")

        summary = str(raw.get("summary", "")).strip()
        if not summary:
            raise ValueError(f"Prediction {pid} is missing summary")

        preds.append(
            Prediction(
                id=pid,
                title=title,
                summary=summary,
                status=str(raw.get("status", "draft")),
                domain=(str(raw["domain"]).strip() if "domain" in raw else None),
                observables=[str(x) for x in (raw.get("observables") or [])],
                tests=[str(x) for x in (raw.get("tests") or [])],
                timeframe=(str(raw["timeframe"]).strip() if "timeframe" in raw else None),
                references=[str(x) for x in (raw.get("references") or [])],
            )
        )

    return PredictionRegistry(version=int(data["version"]), predictions=preds)
