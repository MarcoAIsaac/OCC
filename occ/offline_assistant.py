"""Deterministic offline assistant for OCC workflows.

This assistant does not call external services. It provides actionable
guidance using rule-based intent detection over user prompts/context.
"""

from __future__ import annotations

import re
from typing import List


def _contains_any(text: str, tokens: List[str]) -> bool:
    low = text.lower()
    return any(token in low for token in tokens)


def _extract_verdict(text: str) -> str:
    match = re.search(r"\b(PASS|FAIL|NO-EVAL)(?:\([^)]+\))?\b", text.upper())
    if not match:
        return ""
    return match.group(0)


def ask_offline(prompt: str, context: str = "") -> str:
    full = f"{prompt}\n{context}".strip()
    if not full:
        return "Offline assistant: empty prompt."

    verdict = _extract_verdict(full)
    tips: List[str] = []

    if verdict.startswith("NO-EVAL"):
        tips.append(
            "Your latest state is NO-EVAL. Prioritize missing operational anchors "
            "(domain.omega_I, observables, traceability, or profile-specific fields)."
        )
    elif verdict.startswith("FAIL"):
        tips.append(
            "Your latest state is FAIL. Inspect first_reason and violating judge details "
            "to isolate the non-negotiable inconsistency."
        )
    elif verdict.startswith("PASS"):
        tips.append(
            "Your latest state is PASS. Next step: promote reproducibility "
            "(verify suite + prediction draft + release notes)."
        )

    if _contains_any(full, ["nuclear", "isotope", "reaction_channel", "nuc"]):
        tips.append(
            "Nuclear profile checklist: domain.energy_range_mev, isotopes, "
            "reaction_channel, detectors, and evidence anchor "
            "(observed_cross_section_barns, sigma, dataset_ref + source_url/dataset_doi)."
        )

    if _contains_any(full, ["module", "autogen", "generate"]):
        tips.append(
            "Module generation path: `occ module auto <claim.yaml> --create-prediction` "
            "then verify with `occ verify --suite extensions --strict`."
        )

    if _contains_any(full, ["ci", "github actions", "workflow", "lint"]):
        tips.append(
            "CI triage sequence: `python -m ruff check occ scripts tests`, "
            "`python -m mypy occ`, `pytest -q`, then "
            "`python scripts/ci_doctor.py --workflow CI --limit 12`."
        )

    if _contains_any(full, ["release", "zenodo", "doi", "version"]):
        tips.append(
            "Release hygiene: sync version across `pyproject.toml`, `CITATION.cff`, "
            "`.zenodo.json`, `CHANGELOG.md`, then run "
            "`python scripts/release_doctor.py --strict --no-resolve-doi`."
        )

    if _contains_any(full, ["batch", "matrix", "compare", "lab"]):
        tips.append(
            "Use the new Experiment Lab: "
            "`occ lab run --claims-dir examples/claim_specs --profiles core nuclear "
            "--out .occ_lab/latest`."
        )

    if not tips:
        tips.extend(
            [
                "Recommended OCC sequence:",
                "1) `occ judge <claim.yaml> --json`",
                "2) `occ module auto <claim.yaml> --create-prediction` (if needed)",
                "3) `occ verify --suite extensions --strict`",
                "4) `occ lab run --claims-dir examples/claim_specs --profiles core nuclear`",
            ]
        )

    return "Offline OCC Assistant\n\n" + "\n- ".join([""] + tips)
