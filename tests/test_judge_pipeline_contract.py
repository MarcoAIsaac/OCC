from __future__ import annotations

from typing import Any, Dict

from occ.judges.pipeline import default_judges, run_pipeline


def _claim_minimal() -> Dict[str, Any]:
    return {
        "claim_id": "CLAIM-MIN-001",
        "title": "Minimal claim",
        "domain": {"omega_I": "demo", "observables": ["O1"]},
        "parameters": [
            {
                "name": "theta",
                "accessible": True,
                "affects_observables": True,
            }
        ],
    }


def test_run_pipeline_contract_fields() -> None:
    report = run_pipeline(_claim_minimal(), default_judges(strict_trace=False))
    assert report["schema"] == "occ.judge_report.v1"
    assert report["schema_version"] == "1.0"
    assert isinstance(report["occ_version"], str)
    assert isinstance(report["generated_at"], str)
    assert report["claim_id"] == "CLAIM-MIN-001"
    assert isinstance(report["judges"], list)


def test_nuclear_guard_pass() -> None:
    claim: Dict[str, Any] = {
        "claim_id": "CLAIM-NUC-001",
        "title": "Nuclear pass claim",
        "domain": {
            "sector": "Nuclear Physics",
            "omega_I": "Neutron capture setup",
            "observables": ["Capture cross section", "Prompt gamma yield"],
            "energy_range_mev": {"min_mev": 0.01, "max_mev": 8.0},
            "isotopes": ["U-235"],
            "reaction_channel": "(n,gamma)",
            "detectors": ["HPGe spectrometer"],
        },
        "model": {"predicted_cross_section_barns": 2.11},
        "evidence": {
            "observed_cross_section_barns": 2.05,
            "sigma_cross_section_barns": 0.05,
            "max_sigma": 2.0,
            "dataset_ref": "Sample evaluated dataset",
            "source_url": "https://example.org/dataset",
        },
    }
    report = run_pipeline(claim, default_judges(strict_trace=False, include_nuclear=True))
    assert str(report["verdict"]).startswith("PASS")
    nuclear = next(j for j in report["judges"] if j["judge"] == "j4_nuclear_guard")
    assert nuclear["verdict"] == "PASS(J4)"
    assert nuclear["code"] == "J4"
    assert nuclear["details"]["lock_id"] == "L4"


def test_nuclear_guard_missing_reaction_channel() -> None:
    claim: Dict[str, Any] = {
        "claim_id": "CLAIM-NUC-002",
        "title": "Nuclear missing reaction",
        "domain": {
            "sector": "nuclear",
            "omega_I": "Fast-neutron setup",
            "observables": ["Differential cross section"],
            "energy_range_mev": {"min_mev": 1.0, "max_mev": 14.0},
            "isotopes": ["Fe-56"],
            "detectors": ["TOF spectrometer"],
        },
    }
    report = run_pipeline(claim, default_judges(strict_trace=False, include_nuclear=True))
    assert report["verdict"] == "NO-EVAL(L4C6)"
    nuclear = next(j for j in report["judges"] if j["judge"] == "j4_nuclear_guard")
    assert nuclear["verdict"] == "NO-EVAL(L4C6)"
    assert nuclear["code"] == "L4C6"
    assert nuclear["details"]["legacy_code"] == "NUC6"


def test_nuclear_guard_requires_provenance_locator() -> None:
    claim: Dict[str, Any] = {
        "claim_id": "CLAIM-NUC-003",
        "title": "Nuclear evidence without locator",
        "domain": {
            "sector": "Nuclear Physics",
            "omega_I": "Neutron capture setup",
            "observables": ["Capture cross section"],
            "energy_range_mev": {"min_mev": 0.01, "max_mev": 8.0},
            "isotopes": ["U-235"],
            "reaction_channel": "(n,gamma)",
            "detectors": ["HPGe spectrometer"],
        },
        "model": {"predicted_cross_section_barns": 2.11},
        "evidence": {
            "observed_cross_section_barns": 2.05,
            "sigma_cross_section_barns": 0.05,
            "max_sigma": 2.0,
            "dataset_ref": "Sample evaluated dataset",
        },
    }
    report = run_pipeline(claim, default_judges(strict_trace=False, include_nuclear=True))
    assert report["verdict"] == "NO-EVAL(L4E7)"
