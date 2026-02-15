from __future__ import annotations
from typing import Any, Dict, List, Tuple

name = "grav_ir"

def compile(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Compile a toy IR gravity consistency module (PPN + GW propagation).

    cfg:
      - params: {gamma_ppn, beta_ppn, cT_over_c}
      - omegaI: {v_over_c_max}
      - bounds: {dgamma_max, dbeta_max, dcT_max, v_over_c_dataset}
    """
    p = cfg.get("params", {}) or {}
    b = cfg.get("bounds", {}) or {}

    gamma = float(p.get("gamma_ppn", 1.0))
    beta  = float(p.get("beta_ppn", 1.0))
    cT    = float(p.get("cT_over_c", 1.0))

    artifact = {
        "module": name,
        "params": {"gamma_ppn": gamma, "beta_ppn": beta, "cT_over_c": cT},
        "deviations": {"dgamma": gamma-1.0, "dbeta": beta-1.0, "dcT": cT-1.0},
        "bounds": {
            "dgamma_max": float(b.get("dgamma_max", 1e-3)),
            "dbeta_max": float(b.get("dbeta_max", 1e-3)),
            "dcT_max": float(b.get("dcT_max", 1e-3)),
            "v_over_c_dataset": float(b.get("v_over_c_dataset", 0.1)),
        },
        "omegaI": {"v_over_c_max": float((cfg.get("omegaI", {}) or {}).get("v_over_c_max", 0.3))},
        "notes": "Toy PPN & GW-propagation checks. Replace with full PPN+GW likelihoods and IR handling.",
    }
    return artifact

def check(artifact: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    locks: Dict[str, Dict[str, Any]] = {}
    diag: List[str] = []

    # GR0: parameters declared
    p = artifact.get("params", {}) or {}
    if "gamma_ppn" not in p or "beta_ppn" not in p or "cT_over_c" not in p:
        locks["GR0_PARAMS_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(GR0)", "note": "params missing"}
        diag.append("params missing -> NO-EVAL(GR0)")
        return locks, diag
    locks["GR0_PARAMS_DECLARED"] = {"pass": True, "verdict": "PASS", "note": "params declared"}

    # GR1: IR domain validity (PPN expansion) via v/c
    bnd = artifact.get("bounds", {}) or {}
    vdat = float(bnd.get("v_over_c_dataset", 0.0))
    vmax = float((artifact.get("omegaI", {}) or {}).get("v_over_c_max", 0.3))
    if vdat > vmax:
        locks["GR1_IR_DOMAIN"] = {"pass": False, "verdict": "NO-EVAL(GR1)", "note": f"v/c={vdat} > vmax={vmax}"}
        diag.append("PPN domain exceeded -> NO-EVAL(GR1)")
    else:
        locks["GR1_IR_DOMAIN"] = {"pass": True, "verdict": "PASS", "note": "v/c within IR domain"}

    # GR2: PPN bounds
    dev = artifact.get("deviations", {}) or {}
    dgamma = abs(float(dev.get("dgamma", 0.0)))
    dbeta  = abs(float(dev.get("dbeta", 0.0)))
    dgamma_max = float(bnd.get("dgamma_max", 1e-3))
    dbeta_max  = float(bnd.get("dbeta_max", 1e-3))
    if dgamma <= dgamma_max and dbeta <= dbeta_max:
        locks["GR2_PPN"] = {"pass": True, "verdict": "PASS", "note": f"|dgamma|={dgamma:.3g}, |dbeta|={dbeta:.3g}"}
    else:
        locks["GR2_PPN"] = {"pass": False, "verdict": "FAIL(GR2)", "note": "PPN bounds violated"}
        diag.append("PPN bounds violated -> FAIL(GR2)")

    # GR3: GW speed bound
    dcT = abs(float(dev.get("dcT", 0.0)))
    dcT_max = float(bnd.get("dcT_max", 1e-3))
    if dcT <= dcT_max:
        locks["GR3_GW_SPEED"] = {"pass": True, "verdict": "PASS", "note": f"|dcT|={dcT:.3g} <= {dcT_max:.3g}"}
    else:
        locks["GR3_GW_SPEED"] = {"pass": False, "verdict": "FAIL(GR3)", "note": f"|dcT|={dcT:.3g} > {dcT_max:.3g}"}
        diag.append("GW speed bound violated -> FAIL(GR3)")

    return locks, diag
