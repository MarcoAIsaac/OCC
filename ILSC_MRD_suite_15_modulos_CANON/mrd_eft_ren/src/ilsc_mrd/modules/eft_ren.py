from __future__ import annotations
from typing import Any, Dict, List, Tuple
import math

name = "eft_ren"

def _run_c6(c6_0: float, gamma: float, mu0: float, mu: float) -> float:
    # Toy: C6(mu) = C6(mu0) + gamma * ln(mu/mu0)
    return c6_0 + gamma * math.log(mu/mu0)

def _observable(E: float, *, c6_E: float, Lambda: float) -> float:
    # Toy observable: O(E) = 1 + C6(E) * (E/L)^2
    x2 = (E/Lambda)**2
    return 1.0 + c6_E * x2

def compile(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Compile a toy EFT+RG module with explicit truncation bound ΔΠ.

    cfg keys:
      - eft: {Lambda_GeV, c6_mu0, gamma, c8_max_abs}
      - scales: {mu0_GeV, mu_mid_GeV, mu1_GeV, E_probe_GeV}
      - kappa: float
    """
    eft = cfg.get("eft", {}) or {}
    sc = cfg.get("scales", {}) or {}

    Lambda = float(eft.get("Lambda_GeV", float("nan")))
    c6_0 = float(eft.get("c6_mu0", float("nan")))
    gamma = float(eft.get("gamma", float("nan")))
    c8_max = float(eft.get("c8_max_abs", 1.0))

    mu0 = float(sc.get("mu0_GeV", float("nan")))
    mu_mid = float(sc.get("mu_mid_GeV", float("nan")))
    mu1 = float(sc.get("mu1_GeV", float("nan")))
    E = float(sc.get("E_probe_GeV", mu0))

    c6_1_direct = _run_c6(c6_0, gamma, mu0, mu1)
    c6_mid = _run_c6(c6_0, gamma, mu0, mu_mid)
    # allow optional inconsistent gamma_mid for testing
    gamma_mid = float((cfg.get("scheme", {}) or {}).get("gamma_mid_override", gamma))
    c6_1_step = _run_c6(c6_mid, gamma_mid, mu_mid, mu1)

    # truncation bound from neglected dim-8 term: |ΔO| <= |c8| (E/L)^4
    delta_O = abs(c8_max) * (E/Lambda)**4
    kappa = float(cfg.get("kappa", 1.0))

    artifact = {
        "module": name,
        "eft": {"Lambda_GeV": Lambda, "c6_mu0": c6_0, "gamma": gamma, "c8_max_abs": c8_max},
        "scales": {"mu0_GeV": mu0, "mu_mid_GeV": mu_mid, "mu1_GeV": mu1, "E_probe_GeV": E},
        "running": {"c6_mu1_direct": c6_1_direct, "c6_mu1_step": c6_1_step, "c6_mu_mid": c6_mid, "gamma_mid_used": gamma_mid},
        "observable": {"O_pred": _observable(E, c6_E=c6_1_direct, Lambda=Lambda), "delta_O_bound": delta_O},
        "kappa": kappa,
        "notes": "Toy EFT running + truncation bound; illustrates PA/IO/RFS integration.",
    }
    return artifact

def check(artifact: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    locks: Dict[str, Dict[str, Any]] = {}
    diag: List[str] = []
    eft = artifact.get("eft", {}) or {}
    sc = artifact.get("scales", {}) or {}

    Lambda = float(eft.get("Lambda_GeV", float("nan")))
    if not (Lambda == Lambda) or Lambda <= 0:
        locks["EFT1_CUTOFF_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(EFT1)", "note": "Lambda_GeV missing/invalid"}
        diag.append("Missing cutoff -> NO-EVAL(EFT1)")
        return locks, diag
    locks["EFT1_CUTOFF_DECLARED"] = {"pass": True, "verdict": "PASS", "note": "cutoff declared"}

    # EFT2 / PA3: truncation does not dominate sigma_data
    sigma = cfg.get("sigma_data", None)
    if sigma is None:
        locks["EFT2_SIGMA_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(EFT2)", "note": "sigma_data missing"}
        diag.append("sigma_data missing -> NO-EVAL(EFT2)")
    else:
        locks["EFT2_SIGMA_DECLARED"] = {"pass": True, "verdict": "PASS", "note": "sigma_data declared"}
        delta_O = float(artifact.get("observable", {}).get("delta_O_bound", 0.0))
        kappa = float(artifact.get("kappa", 1.0))
        if delta_O >= kappa*float(sigma):
            locks["EFT2_TRUNC_INFORMATIVE"] = {"pass": False, "verdict": "NO-EVAL(EFT2)", "note": f"ΔO={delta_O:.3g} >= κσ={kappa*float(sigma):.3g}"}
            diag.append("Truncation dominates -> NO-EVAL(EFT2)")
        else:
            locks["EFT2_TRUNC_INFORMATIVE"] = {"pass": True, "verdict": "PASS", "note": "ΔO below κσ"}

    # EFT3: RG consistency (two-step == direct)
    run = artifact.get("running", {}) or {}
    c_dir = float(run.get("c6_mu1_direct", float("nan")))
    c_stp = float(run.get("c6_mu1_step", float("nan")))
    tol = float((cfg.get("tolerances", {}) or {}).get("rg_tol", 1e-10))
    if abs(c_dir - c_stp) <= tol:
        locks["EFT3_RG_CONSISTENCY"] = {"pass": True, "verdict": "PASS", "note": f"|Δ|={abs(c_dir-c_stp):.3e} <= {tol:.1e}"}
    else:
        locks["EFT3_RG_CONSISTENCY"] = {"pass": False, "verdict": "FAIL(EFT3)", "note": f"|Δ|={abs(c_dir-c_stp):.3e} > {tol:.1e}"}
        diag.append("RG inconsistency -> FAIL(EFT3)")

    # EFT4: ΩI validity vs cutoff fraction (E_probe below frac*Lambda)
    frac = float((cfg.get("omegaI", {}) or {}).get("frac_cutoff_max", 0.5))
    E = float(sc.get("E_probe_GeV", float("nan")))
    if not (E == E):
        locks["EFT4_E_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(EFT4)", "note": "E_probe missing"}
        diag.append("E_probe missing -> NO-EVAL(EFT4)")
    elif E > frac*Lambda:
        locks["EFT4_OMEGAI_VALID"] = {"pass": False, "verdict": "NO-EVAL(EFT4)", "note": f"E={E:.3g} > frac*Lambda={frac*Lambda:.3g}"}
        diag.append("E outside ΩI -> NO-EVAL(EFT4)")
    else:
        locks["EFT4_OMEGAI_VALID"] = {"pass": True, "verdict": "PASS", "note": "E within ΩI"}

    return locks, diag
