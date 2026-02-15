from __future__ import annotations
from typing import Any, Dict, List, Tuple
import math

name = "cosmo_bridge"

def _H_z(z: float, H0: float, Om: float, w0: float) -> float:
    Ode = 1.0 - Om
    return H0 * math.sqrt(Om*(1+z)**3 + Ode*(1+z)**(3*(1+w0)))

def compile(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Compile a toy Local↔Cosmo bridge.

    cfg:
      - params: {H0, Om, w0, gdot_over_G}
      - dataset_rows: [{z, H_obs, sigma}]
      - projection: {delta_w_bound}  # bound on missing w(z) structure
    """
    p = cfg.get("params", {}) or {}
    H0 = float(p.get("H0", float("nan")))
    Om = float(p.get("Om", float("nan")))
    w0 = float(p.get("w0", float("nan")))
    gdot = float(p.get("gdot_over_G", 0.0))

    rows = cfg.get("dataset_rows", []) or []
    preds = []
    for r in rows:
        z = float(r["z"])
        preds.append({"z": z, "H_pred": _H_z(z, H0, Om, w0)})

    # projection error: missing structure in w(z), bounded by delta_w_bound
    proj = cfg.get("projection", {}) or {}
    dw = float(proj.get("delta_w_bound", float("nan")))
    # crude ΔH bound proportional to |dw| ln(1+z)
    deltaH = []
    for r in rows:
        z = float(r["z"])
        if dw == dw:
            deltaH.append({"z": z, "delta_H_bound": abs(dw) * math.log(1+z) * H0})
        else:
            deltaH.append({"z": z, "delta_H_bound": float("nan")})

    artifact = {
        "module": name,
        "params": {"H0": H0, "Om": Om, "w0": w0, "gdot_over_G": gdot},
        "predictions": preds,
        "DeltaPi": {"delta_w_bound": dw, "delta_H_bound": deltaH},
        "notes": "Toy bridge: requires local bound on gdot and fit to H(z) with projection bound.",
    }
    return artifact

def check(artifact: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    locks: Dict[str, Dict[str, Any]] = {}
    diag: List[str] = []

    p = artifact.get("params", {}) or {}
    if any(k not in p or not (float(p[k])==float(p[k])) for k in ["H0","Om","w0"]):
        locks["COS1_PARAMS_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(COS1)", "note": "H0/Om/w0 missing"}
        diag.append("Missing params -> NO-EVAL(COS1)")
        return locks, diag
    locks["COS1_PARAMS_DECLARED"] = {"pass": True, "verdict": "PASS", "note": "params declared"}

    # COS2: local bound on gdot/G
    gdot = float(p.get("gdot_over_G", 0.0))
    gdot_max = float((cfg.get("local_bounds", {}) or {}).get("gdot_over_G_max", 1e-3))
    if abs(gdot) <= gdot_max:
        locks["COS2_LOCAL_GDOT"] = {"pass": True, "verdict": "PASS", "note": f"|gdot/G|={abs(gdot):.3g} <= {gdot_max:.3g}"}
    else:
        locks["COS2_LOCAL_GDOT"] = {"pass": False, "verdict": "FAIL(COS2)", "note": "local gdot/G bound violated"}
        diag.append("Local gdot/G bound violated -> FAIL(COS2)")

    # COS3: fit H(z) (chi2) ignoring ΔΠ for now
    rows = cfg.get("dataset_rows", []) or []
    preds = artifact.get("predictions", []) or []
    if not rows:
        locks["COS3_DATA_PRESENT"] = {"pass": False, "verdict": "NO-EVAL(COS3)", "note": "dataset_rows missing"}
        diag.append("No H(z) data -> NO-EVAL(COS3)")
        return locks, diag
    chi2 = 0.0
    for r,pred in zip(rows, preds):
        Hobs = float(r["H_obs"]); sig = float(r["sigma"]); Hp = float(pred["H_pred"])
        chi2 += ((Hp - Hobs)/sig)**2
    dof = max(len(rows)-3, 1)
    chi2_red = chi2/dof
    thr = float((cfg.get("tolerances", {}) or {}).get("chi2_red_max", 5.0))
    if chi2_red <= thr:
        locks["COS3_FIT"] = {"pass": True, "verdict": "PASS", "note": f"chi2_red={chi2_red:.3g} <= {thr:.3g}"}
    else:
        locks["COS3_FIT"] = {"pass": False, "verdict": "FAIL(COS3)", "note": f"chi2_red={chi2_red:.3g} > {thr:.3g}"}
        diag.append("Poor fit to H(z) -> FAIL(COS3)")

    # COS4 / PA3: projection error (ΔH) does not dominate sigma
    dp = artifact.get("DeltaPi", {}) or {}
    dw = dp.get("delta_w_bound", float("nan"))
    if not (float(dw)==float(dw)):
        locks["COS4_DW_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(COS4)", "note": "projection.delta_w_bound missing"}
        diag.append("Missing delta_w_bound -> NO-EVAL(COS4)")
    else:
        locks["COS4_DW_DECLARED"] = {"pass": True, "verdict": "PASS", "note": "delta_w_bound declared"}
        kappa = float((cfg.get("kappa_rule", {}) or {}).get("kappa", 1.0))
        ok = True
        for r,db in zip(rows, dp.get("delta_H_bound", []) or []):
            sig = float(r["sigma"])
            dH = float(db["delta_H_bound"])
            if dH >= kappa*sig:
                ok = False
                break
        if ok:
            locks["COS4_INFORMATIVE"] = {"pass": True, "verdict": "PASS", "note": "ΔH below κσ at all z"}
        else:
            locks["COS4_INFORMATIVE"] = {"pass": False, "verdict": "NO-EVAL(COS4)", "note": "ΔH dominates σ_data somewhere"}
            diag.append("Projection error dominates data -> NO-EVAL(COS4)")

    return locks, diag
