from __future__ import annotations
from typing import Any, Dict, List, Tuple
import math

name = "g0_dm"

G_kpc_kms2_Msun = 4.302e-6  # kpc (km/s)^2 / Msun
c_kms = 299792.458

def _M_baryon(r_kpc: float, M0: float, r0: float) -> float:
    # Toy baryon mass profile: M_b(r)=M0 * r^3/(r^3+r0^3)
    return M0 * (r_kpc**3)/(r_kpc**3 + r0**3)

def _M_NFW(r_kpc: float, rho0: float, rs: float) -> float:
    # Toy NFW mass enclosed (up to constant 4π rho0 rs^3)
    x = r_kpc/rs
    return 4.0*math.pi*rho0*rs**3*(math.log(1+x) - x/(1+x))

def compile(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Compile a toy G0 effective DM module: fit rotation + lensing with one DM profile.

    cfg:
      - baryons: {M0_Msun, r0_kpc}
      - dm_profile: {rho0_Msun_kpc3, rs_kpc}
      - dataset_rows: [{r_kpc, v_obs_kms, sigma_v, alpha_obs_arcsec, sigma_alpha}]
    """
    b = cfg.get("baryons", {}) or {}
    dm = cfg.get("dm_profile", {}) or {}
    M0 = float(b.get("M0_Msun", float("nan")))
    r0 = float(b.get("r0_kpc", float("nan")))
    rho0 = float(dm.get("rho0_Msun_kpc3", float("nan")))
    rs = float(dm.get("rs_kpc", float("nan")))

    rows = cfg.get("dataset_rows", []) or []
    preds = []
    for r in rows:
        rk = float(r["r_kpc"])
        Mb = _M_baryon(rk, M0, r0)
        Mdm = _M_NFW(rk, rho0, rs)
        Mtot = Mb + Mdm
        v = math.sqrt(G_kpc_kms2_Msun * Mtot / rk)  # km/s
        # lensing deflection (toy thin lens): alpha_rad ~ 4GM/(c^2 R)
        alpha_rad = 4.0 * (G_kpc_kms2_Msun * Mtot) / (c_kms**2 * rk)
        alpha_arcsec = alpha_rad * (180.0/math.pi) * 3600.0
        preds.append({"r_kpc": rk, "v_pred_kms": v, "alpha_pred_arcsec": alpha_arcsec, "Mb": Mb, "Mdm": Mdm})

    artifact = {
        "module": name,
        "baryons": {"M0_Msun": M0, "r0_kpc": r0},
        "dm_profile": {"rho0_Msun_kpc3": rho0, "rs_kpc": rs},
        "predictions": preds,
        "notes": "Toy: single DM profile must fit both rotation and lensing simultaneously (multi-scale consistency).",
    }
    return artifact

def check(artifact: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    locks: Dict[str, Dict[str, Any]] = {}
    diag: List[str] = []

    # G0-1: baryon model declared
    b = artifact.get("baryons", {}) or {}
    if any(k not in b or not (float(b[k])==float(b[k])) for k in ["M0_Msun","r0_kpc"]):
        locks["G01_BARYONS_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(G01)", "note": "baryon params missing"}
        diag.append("Missing baryon model -> NO-EVAL(G01)")
        return locks, diag
    locks["G01_BARYONS_DECLARED"] = {"pass": True, "verdict": "PASS", "note": "baryon model declared"}

    # G0-2: DM density parameter rho0 positive
    dm = artifact.get("dm_profile", {}) or {}
    rho0 = float(dm.get("rho0_Msun_kpc3", float("nan")))
    if not (rho0==rho0) or rho0 <= 0:
        locks["G02_RHO_POS"] = {"pass": False, "verdict": "FAIL(G02)", "note": "rho0 must be >0"}
        diag.append("rho0<=0 -> FAIL(G02)")
    else:
        locks["G02_RHO_POS"] = {"pass": True, "verdict": "PASS", "note": "rho0>0"}

    # G0-3: rotation fit
    rows = cfg.get("dataset_rows", []) or []
    preds = artifact.get("predictions", []) or []
    if not rows:
        locks["G03_DATA_PRESENT"] = {"pass": False, "verdict": "NO-EVAL(G03)", "note": "dataset_rows missing"}
        diag.append("Missing dataset -> NO-EVAL(G03)")
        return locks, diag
    chi2_v = 0.0
    chi2_a = 0.0
    for r,p in zip(rows, preds):
        vobs = float(r["v_obs_kms"]); sigv = float(r["sigma_v"]); vp = float(p["v_pred_kms"])
        chi2_v += ((vp - vobs)/sigv)**2
        if "alpha_obs_arcsec" in r:
            aobs = float(r["alpha_obs_arcsec"]); siga = float(r["sigma_alpha"]); ap = float(p["alpha_pred_arcsec"])
            chi2_a += ((ap - aobs)/siga)**2
    thr_v = float((cfg.get("tolerances", {}) or {}).get("chi2_v_max", 50.0))
    thr_a = float((cfg.get("tolerances", {}) or {}).get("chi2_a_max", 50.0))
    if chi2_v <= thr_v:
        locks["G03_ROTATION_FIT"] = {"pass": True, "verdict": "PASS", "note": f"chi2_v={chi2_v:.3g} <= {thr_v:.3g}"}
    else:
        locks["G03_ROTATION_FIT"] = {"pass": False, "verdict": "FAIL(G03)", "note": f"chi2_v={chi2_v:.3g} > {thr_v:.3g}"}
        diag.append("Rotation fit failed -> FAIL(G03)")
    # G0-4: lensing fit
    if any("alpha_obs_arcsec" not in r for r in rows):
        locks["G04_LENSING_PRESENT"] = {"pass": False, "verdict": "NO-EVAL(G04)", "note": "lensing column missing"}
        diag.append("Missing lensing observables -> NO-EVAL(G04)")
    else:
        if chi2_a <= thr_a:
            locks["G04_LENSING_FIT"] = {"pass": True, "verdict": "PASS", "note": f"chi2_a={chi2_a:.3g} <= {thr_a:.3g}"}
        else:
            locks["G04_LENSING_FIT"] = {"pass": False, "verdict": "FAIL(G04)", "note": f"chi2_a={chi2_a:.3g} > {thr_a:.3g}"}
            diag.append("Lensing fit failed -> FAIL(G04)")

    return locks, diag
