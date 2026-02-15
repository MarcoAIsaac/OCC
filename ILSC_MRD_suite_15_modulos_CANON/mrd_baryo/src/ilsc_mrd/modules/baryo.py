from __future__ import annotations
from typing import Any, Dict, List, Tuple
import math

name = "baryo"

def compile(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Compile a toy baryogenesis module (EWBG / Leptogenesis umbrella).

    cfg:
      - mode: "EWBG" or "LEP"
      - params: depending on mode
          EWBG: {Lambda_CPV_GeV, sin_delta, vc_over_Tc, beta_over_H, alpha_PT}
          LEP:  {epsilon1, kappa_L}
      - constants: {kappa_Y, kappa_EDM, kappa_f, kappa_Omega}
      - obs: {Y_obs, sigma_Y, edm_limit, gw_threshold}
    """
    mode = (cfg.get("mode") or "").upper()
    p = cfg.get("params", {}) or {}
    c = cfg.get("constants", {}) or {}
    obs = cfg.get("obs", {}) or {}

    kY = float(c.get("kappa_Y", 1e-10))
    kE = float(c.get("kappa_EDM", 1e-29))
    kf = float(c.get("kappa_f_mHz", 1.0))
    kO = float(c.get("kappa_Omega", 1e-10))

    if mode == "EWBG":
        Lam = float(p.get("Lambda_CPV_GeV", float("nan")))
        sd = float(p.get("sin_delta", float("nan")))
        vcTc = float(p.get("vc_over_Tc", float("nan")))
        betaH = float(p.get("beta_over_H", float("nan")))
        alpha = float(p.get("alpha_PT", float("nan")))
        theta = sd * (1000.0/Lam)**2 if (Lam==Lam and Lam>0) else float("nan")
        strength = max(vcTc-1.0, 0.0) if (vcTc==vcTc) else float("nan")
        Y = kY * theta * strength
        dEDM = kE * theta
        f_peak = kf * (betaH/100.0) if (betaH==betaH) else float("nan")
        Omega = kO * (alpha/(1+alpha))**2 * (100.0/betaH)**2 if (alpha==alpha and betaH==betaH and betaH>0) else float("nan")
        pred = {"Y_B": Y, "d_e": dEDM, "f_peak_mHz": f_peak, "Omega_GW": Omega}
    elif mode == "LEP":
        eps1 = float(p.get("epsilon1", float("nan")))
        kL = float(p.get("kappa_L", 1e-10))
        Y = kL * eps1
        pred = {"Y_B": Y, "d_e": 0.0, "f_peak_mHz": float("nan"), "Omega_GW": float("nan")}
    else:
        pred = {"Y_B": float("nan"), "d_e": float("nan"), "f_peak_mHz": float("nan"), "Omega_GW": float("nan")}

    artifact = {
        "module": name,
        "mode": mode,
        "params": p,
        "pred": pred,
        "obs": obs,
        "notes": "Toy umbrella for baryogenesis; demonstrates how ILSC forces correlated predictions (EDM/GW) in ΩI.",
    }
    return artifact

def check(artifact: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    locks: Dict[str, Dict[str, Any]] = {}
    diag: List[str] = []

    mode = artifact.get("mode","")
    if mode not in ("EWBG","LEP"):
        locks["B0_MODE"] = {"pass": False, "verdict": "NO-EVAL(B0)", "note": "mode must be EWBG or LEP"}
        diag.append("Unknown mode -> NO-EVAL(B0)")
        return locks, diag
    locks["B0_MODE"] = {"pass": True, "verdict": "PASS", "note": f"mode={mode}"}

    obs = artifact.get("obs", {}) or {}
    if "Y_obs" not in obs or "sigma_Y" not in obs:
        locks["B1_OBS_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(B1)", "note": "Need obs.Y_obs and obs.sigma_Y"}
        diag.append("Missing observational target -> NO-EVAL(B1)")
        return locks, diag
    locks["B1_OBS_DECLARED"] = {"pass": True, "verdict": "PASS", "note": "Y_obs declared"}

    pred = artifact.get("pred", {}) or {}
    Y = float(pred.get("Y_B", float("nan")))
    Yobs = float(obs["Y_obs"]); sig = float(obs["sigma_Y"])
    if not (Y==Y):
        locks["B2_Y_PRED"] = {"pass": False, "verdict": "NO-EVAL(B2)", "note": "Y_B not computable"}
        diag.append("Y_B NaN -> NO-EVAL(B2)")
    else:
        n_sigma = float((cfg.get("tolerances", {}) or {}).get("n_sigma", 3.0))
        if abs(Y - Yobs) <= n_sigma*sig:
            locks["B2_MATCH_Y"] = {"pass": True, "verdict": "PASS", "note": f"|Y-Yobs|<= {n_sigma}σ"}
        else:
            locks["B2_MATCH_Y"] = {"pass": False, "verdict": "FAIL(B2)", "note": f"|Y-Yobs|={abs(Y-Yobs):.3g} > {n_sigma}σ={n_sigma*sig:.3g}"}
            diag.append("Baryon asymmetry mismatch -> FAIL(B2)")

    # B3: Sakharov minimal checks depend on mode
    if mode == "EWBG":
        p = artifact.get("params", {}) or {}
        if "vc_over_Tc" not in p:
            locks["B3_SAKHAROV"] = {"pass": False, "verdict": "NO-EVAL(B3)", "note": "Need vc_over_Tc (strong PT) declared"}
            diag.append("Missing vc_over_Tc -> NO-EVAL(B3)")
        else:
            vcTc = float(p.get("vc_over_Tc", float("nan")))
            if vcTc > 1.0:
                locks["B3_SAKHAROV"] = {"pass": True, "verdict": "PASS", "note": "strong first-order proxy vc/Tc>1"}
            else:
                locks["B3_SAKHAROV"] = {"pass": False, "verdict": "FAIL(B3)", "note": "vc/Tc<=1 (no strong PT)"}
                diag.append("No strong PT -> FAIL(B3)")
        # B4: EDM constraint
        if "edm_limit" not in obs:
            locks["B4_EDM_LIMIT_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(B4)", "note": "Need obs.edm_limit"}
            diag.append("Missing EDM limit -> NO-EVAL(B4)")
        else:
            d = float(pred.get("d_e", float("nan")))
            lim = float(obs["edm_limit"])
            if not (d==d):
                locks["B4_EDM"] = {"pass": False, "verdict": "NO-EVAL(B4)", "note": "d_e not computable"}
                diag.append("d_e NaN -> NO-EVAL(B4)")
            elif abs(d) <= lim:
                locks["B4_EDM"] = {"pass": True, "verdict": "PASS", "note": "EDM below limit"}
            else:
                locks["B4_EDM"] = {"pass": False, "verdict": "FAIL(B4)", "note": "EDM exceeds limit"}
                diag.append("EDM constraint violated -> FAIL(B4)")
    else:
        # LEP: require epsilon1 declared and nonzero
        p = artifact.get("params", {}) or {}
        eps1 = p.get("epsilon1", None)
        if eps1 is None:
            locks["B3_SAKHAROV"] = {"pass": False, "verdict": "NO-EVAL(B3)", "note": "Need epsilon1 declared"}
            diag.append("Missing epsilon1 -> NO-EVAL(B3)")
        else:
            if abs(float(eps1)) > 0:
                locks["B3_SAKHAROV"] = {"pass": True, "verdict": "PASS", "note": "CPV epsilon1 nonzero (toy)"}
            else:
                locks["B3_SAKHAROV"] = {"pass": False, "verdict": "FAIL(B3)", "note": "epsilon1=0"}
                diag.append("No CPV -> FAIL(B3)")

    return locks, diag
