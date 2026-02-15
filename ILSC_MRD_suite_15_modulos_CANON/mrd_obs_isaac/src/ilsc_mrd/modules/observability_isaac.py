from __future__ import annotations
from typing import Any, Dict, List, Tuple
import math

name = "observability_isaac"

# Fundamental constants (CODATA values may update; concept does not depend on the exact numeric instantiation)
C = 299_792_458.0                     # m/s
HBAR = 1.054_571_817e-34              # J·s
G = 6.674_30e-11                      # m^3/(kg·s^2)

def isaac_scale_LI() -> float:
    """Operational resolution floor implied by SR + QM + GR (conceptual ISAAC).
    Numeric instantiation uses sqrt(hbar*G/c^3); if constants update, LI updates.
    """
    return math.sqrt(HBAR * G / (C**3))

def compile(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Compile observability assumptions into an auditable artifact.

    Expected cfg keys (minimal):
      - obs.instrument: {type, aperture_m, wavelength_m, baseline_m (optional), note}
      - obs.requested_resolution_m: float (target operational resolution)
      - obs.safety_factor: float (>=1). Recommended >1.
      - obs.domain: {OmegaI: {E_max, L_min_declared, notes}}
    """
    obs = cfg.get("obs", {}) or {}
    inst = obs.get("instrument", {}) or {}
    requested = float(obs.get("requested_resolution_m", float("nan")))
    safety = float(obs.get("safety_factor", 10.0))
    LI = isaac_scale_LI()

    # A crude diffraction-limited estimate for declared resolution (for audit):
    # delta_x ~ lambda / D or lambda / baseline; we record both if present.
    lam = float(inst.get("wavelength_m", float("nan")))
    D = float(inst.get("aperture_m", float("nan")))
    B = inst.get("baseline_m", None)
    est = {}
    if lam == lam and D == D and D > 0:
        est["diffraction_lambda_over_D_m"] = lam / D
    if B is not None:
        B = float(B)
        if lam == lam and B > 0:
            est["interferometer_lambda_over_B_m"] = lam / B

    artifact = {
        "module": name,
        "ISAAC": {
            "concept": "SR causal limit + QM E~hbar/λ + GR backreaction of probe energy-momentum",
            "LI_m": LI,
            "constants": {"c": C, "hbar": HBAR, "G": G},
        },
        "instrument": inst,
        "declared_resolution_estimates": est,
        "requested_resolution_m": requested,
        "safety_factor": safety,
        "operational_floor_m": safety * LI,
        "OmegaI_decl": (obs.get("domain", {}) or {}).get("OmegaI", {}),
    }
    return artifact

def check(artifact: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    locks: Dict[str, Dict[str, Any]] = {}
    diagnostic: List[str] = []

    LI = float(artifact["ISAAC"]["LI_m"])
    floor = float(artifact["operational_floor_m"])
    requested = float(artifact.get("requested_resolution_m", float("nan")))

    # ISAAC0: concept vs equation separation (concept must be declared; equation is instantiation)
    if "concept" not in artifact.get("ISAAC", {}):
        locks["ISAAC0_CONCEPT_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(ISAAC0)", "note": "ISAAC concept not declared"}
        diagnostic.append("Missing ISAAC concept -> NO-EVAL(ISAAC0)")
    else:
        locks["ISAAC0_CONCEPT_DECLARED"] = {"pass": True, "verdict": "PASS", "note": "ISAAC concept declared (equation is instantiation)"}

    # ISAAC1: operational ceiling / floor respected
    if not (requested == requested):
        locks["ISAAC1_REQUESTED_RESOLUTION_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(ISAAC1)", "note": "requested_resolution_m missing/NaN"}
        diagnostic.append("requested_resolution_m not provided -> NO-EVAL(ISAAC1)")
    else:
        locks["ISAAC1_REQUESTED_RESOLUTION_DECLARED"] = {"pass": True, "verdict": "PASS", "note": "requested_resolution_m declared"}
        if requested < floor:
            locks["ISAAC1_FLOOR_RESPECTED"] = {"pass": False, "verdict": "NO-EVAL(ISAAC1)", "note": f"requested_resolution_m={requested:.3e} < safety*LI={floor:.3e}"}
            diagnostic.append("Requested resolution below ISAAC operational floor -> NO-EVAL(ISAAC1)")
        else:
            locks["ISAAC1_FLOOR_RESPECTED"] = {"pass": True, "verdict": "PASS", "note": "Requested resolution respects ISAAC operational floor"}

    # ISAAC2: ΩI declaration
    OmegaI = artifact.get("OmegaI_decl", {}) or {}
    if not OmegaI:
        locks["ISAAC2_OMEGAI_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(ISAAC2)", "note": "OmegaI not declared"}
        diagnostic.append("OmegaI not declared -> NO-EVAL(ISAAC2)")
    else:
        locks["ISAAC2_OMEGAI_DECLARED"] = {"pass": True, "verdict": "PASS", "note": "OmegaI declared"}
        # Optional check: declared L_min should not undercut floor if provided
        Lmin = OmegaI.get("L_min_declared_m", None)
        if Lmin is not None:
            try:
                Lmin = float(Lmin)
                if Lmin < floor:
                    locks["ISAAC2_OMEGAI_LMIN_RESPECTS_FLOOR"] = {"pass": False, "verdict": "NO-EVAL(ISAAC2)", "note": "OmegaI L_min undercuts ISAAC floor"}
                    diagnostic.append("OmegaI L_min undercuts ISAAC floor -> NO-EVAL(ISAAC2)")
                else:
                    locks["ISAAC2_OMEGAI_LMIN_RESPECTS_FLOOR"] = {"pass": True, "verdict": "PASS", "note": "OmegaI L_min respects ISAAC floor"}
            except Exception:
                locks["ISAAC2_OMEGAI_LMIN_RESPECTS_FLOOR"] = {"pass": False, "verdict": "NO-EVAL(ISAAC2)", "note": "OmegaI L_min not parseable"}
                diagnostic.append("OmegaI L_min not parseable -> NO-EVAL(ISAAC2)")

    # RFS1 minimal: resources budget must be finite (we read from judge cert RFS or cfg)
    rb = (cfg.get("resources", {}) or {}).get("budget", None)
    if rb is None:
        locks["RFS1_RESOURCE_BUDGET_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(RFS1)", "note": "resources.budget missing (or rely on RFS cert)"}
        diagnostic.append("resources.budget missing -> recommend enabling RFS cert for hard audit")
    else:
        locks["RFS1_RESOURCE_BUDGET_DECLARED"] = {"pass": True, "verdict": "PASS", "note": "resources.budget declared"}

    return locks, diagnostic
