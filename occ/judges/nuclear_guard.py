"""Nuclear-domain lock package.

This is a *domain lock* set (Class C / Class E), not a foundational J-judge.
Foundational judges remain J0-J3 in the canonical OCC framing.
"""

from __future__ import annotations

from typing import Any, Mapping

from .base import JudgeResult

NUCLEAR_HINTS = (
    "nuclear",
    "reactor",
    "fission",
    "fusion",
    "neutron",
    "isotope",
)


def _as_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def claim_is_nuclear(claim: Mapping[str, Any]) -> bool:
    domain = claim.get("domain")
    if not isinstance(domain, Mapping):
        return False

    for key in ("sector", "field", "discipline", "domain_type"):
        raw = domain.get(key)
        if isinstance(raw, str):
            low = raw.strip().lower()
            if any(hint in low for hint in NUCLEAR_HINTS):
                return True

    observables = domain.get("observables")
    if isinstance(observables, list):
        merged = " ".join(str(x).lower() for x in observables)
        if any(hint in merged for hint in NUCLEAR_HINTS):
            return True
    return False


class NuclearGuardJudge:
    name = "nuclear_guard"

    def evaluate(self, claim: Mapping[str, Any]) -> JudgeResult:
        if not claim_is_nuclear(claim):
            return JudgeResult(
                judge=self.name,
                verdict="PASS(NUC0)",
                code="NUC0",
                message="Nuclear lock package not applicable for this claim.",
            )

        domain = claim.get("domain")
        if not isinstance(domain, Mapping):
            return JudgeResult(
                judge=self.name,
                verdict="NO-EVAL(NUC1)",
                code="NUC1",
                message="Nuclear claims must declare domain mapping.",
            )

        # Class C (consistency / operational closure for nuclear domain)
        energy = domain.get("energy_range_mev")
        if not isinstance(energy, Mapping):
            return JudgeResult(
                judge=self.name,
                verdict="NO-EVAL(NUC2)",
                code="NUC2",
                message="Missing Class-C lock: domain.energy_range_mev.",
                details={"lock_class": "C"},
            )

        min_mev = _as_float(energy.get("min_mev"))
        max_mev = _as_float(energy.get("max_mev"))
        if min_mev is None or max_mev is None:
            return JudgeResult(
                judge=self.name,
                verdict="FAIL(NUC3)",
                code="NUC3",
                message="Class-C lock violation: energy_range_mev bounds must be numeric.",
                details={"lock_class": "C"},
            )
        if min_mev < 0 or max_mev <= min_mev:
            return JudgeResult(
                judge=self.name,
                verdict="FAIL(NUC4)",
                code="NUC4",
                message="Class-C lock violation: expected 0 <= min_mev < max_mev.",
                details={"lock_class": "C"},
            )

        isotopes = domain.get("isotopes")
        if not isinstance(isotopes, list) or not isotopes:
            return JudgeResult(
                judge=self.name,
                verdict="NO-EVAL(NUC5)",
                code="NUC5",
                message="Missing Class-C lock: domain.isotopes[] must be non-empty.",
                details={"lock_class": "C"},
            )

        reaction_channel = domain.get("reaction_channel")
        if not isinstance(reaction_channel, str) or not reaction_channel.strip():
            return JudgeResult(
                judge=self.name,
                verdict="NO-EVAL(NUC6)",
                code="NUC6",
                message="Missing Class-C lock: domain.reaction_channel.",
                details={"lock_class": "C"},
            )

        detectors = domain.get("detectors")
        if not isinstance(detectors, list) or not detectors:
            return JudgeResult(
                judge=self.name,
                verdict="NO-EVAL(NUC7)",
                code="NUC7",
                message="Missing Class-C lock: domain.detectors[] must be non-empty.",
                details={"lock_class": "C"},
            )

        # Class E (evidence anchor): z = |pred-obs|/sigma <= z_max
        evidence = claim.get("evidence")
        if not isinstance(evidence, Mapping):
            return JudgeResult(
                judge=self.name,
                verdict="NO-EVAL(NUC8E)",
                code="NUC8E",
                message="Missing Class-E lock: evidence anchor not declared.",
                details={"lock_class": "E"},
            )

        observed = _as_float(evidence.get("observed_cross_section_barns"))
        sigma = _as_float(evidence.get("sigma_cross_section_barns"))
        if observed is None or sigma is None or sigma <= 0:
            return JudgeResult(
                judge=self.name,
                verdict="NO-EVAL(NUC9E)",
                code="NUC9E",
                message=(
                    "Invalid Class-E anchor: observed_cross_section_barns "
                    "and sigma>0 required."
                ),
                details={"lock_class": "E"},
            )

        model = claim.get("model")
        if not isinstance(model, Mapping):
            return JudgeResult(
                judge=self.name,
                verdict="NO-EVAL(NUC10E)",
                code="NUC10E",
                message="Missing model prediction for Class-E anchor comparison.",
                details={"lock_class": "E"},
            )

        predicted = _as_float(model.get("predicted_cross_section_barns"))
        if predicted is None:
            return JudgeResult(
                judge=self.name,
                verdict="NO-EVAL(NUC11E)",
                code="NUC11E",
                message="Missing model.predicted_cross_section_barns.",
                details={"lock_class": "E"},
            )

        z_max = _as_float(evidence.get("max_sigma"))
        if z_max is None or z_max <= 0:
            z_max = 3.0

        dataset_ref = evidence.get("dataset_ref")
        if not isinstance(dataset_ref, str) or not dataset_ref.strip():
            return JudgeResult(
                judge=self.name,
                verdict="NO-EVAL(NUC13E)",
                code="NUC13E",
                message=(
                    "Missing Class-E provenance: evidence.dataset_ref must cite "
                    "the observational source."
                ),
                details={"lock_class": "E"},
            )

        dataset_doi = evidence.get("dataset_doi")
        source_url = evidence.get("source_url")
        has_doi = isinstance(dataset_doi, str) and bool(dataset_doi.strip())
        has_url = isinstance(source_url, str) and bool(source_url.strip())
        if not (has_doi or has_url):
            return JudgeResult(
                judge=self.name,
                verdict="NO-EVAL(NUC14E)",
                code="NUC14E",
                message=(
                    "Missing Class-E provenance locator: provide evidence.source_url "
                    "or evidence.dataset_doi."
                ),
                details={"lock_class": "E"},
            )

        z_score = abs(predicted - observed) / sigma
        if z_score > z_max:
            return JudgeResult(
                judge=self.name,
                verdict="FAIL(NUC12E)",
                code="NUC12E",
                message=(
                    "Class-E lock violation: prediction inconsistent with "
                    "declared evidence anchor."
                ),
                details={
                    "lock_class": "E",
                    "z_score": z_score,
                    "z_max": z_max,
                    "equation": "z = |sigma_pred - sigma_obs| / sigma_obs_err",
                },
            )

        return JudgeResult(
            judge=self.name,
            verdict="PASS(NUC)",
            code="NUC",
            message="Nuclear lock package satisfied (Class C + Class E).",
            details={
                "lock_classes": ["C", "E"],
                "energy_range_mev": {"min_mev": min_mev, "max_mev": max_mev},
                "isotopes": [str(x) for x in isotopes],
                "reaction_channel": reaction_channel.strip(),
                "detectors": [str(x) for x in detectors],
                "z_score": z_score,
                "z_max": z_max,
                "equation": "z = |sigma_pred - sigma_obs| / sigma_obs_err",
            },
        )
