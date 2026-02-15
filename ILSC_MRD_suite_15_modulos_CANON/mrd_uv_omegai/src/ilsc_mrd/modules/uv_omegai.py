from __future__ import annotations
from typing import Any, Dict, List, Tuple
import math

name = "uv_omegai"

def _predict_truncated(E: float, Lambda: float, c6: float) -> float:
    # Toy EFT: O(E) = 1 + c6*(E/L)^2 + ...
    x2 = (E / Lambda) ** 2
    return 1.0 + c6 * x2

def _delta_trunc_bound(E: float, Lambda: float, c8_max_abs: float) -> float:
    # Conservative bound from neglected dimension-8 term: |c8|*(E/L)^4 <= c8_max*(E/L)^4
    x4 = (E / Lambda) ** 4
    return abs(c8_max_abs) * x4

def compile(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Compile an auditable UV→ΩI projection Π with an explicit truncation error ΔΠ(E).

    Minimal expected cfg:
      - projection: {Lambda_GeV, c6, c8_max_abs, kappa}
      - dataset: {rows: [{E_GeV, O_obs, sigma}] } OR external dataset in runner
    """
    proj = cfg.get("projection", {}) or {}
    Lambda = float(proj.get("Lambda_GeV", 1000.0))
    c6 = float(proj.get("c6", 0.0))
    c8_max = float(proj.get("c8_max_abs", 1.0))
    kappa = float(proj.get("kappa", 1.0))

    # Collect E points from dataset if present (runner may also supply)
    E_list: List[float] = []
    ds = cfg.get("dataset_rows")
    if isinstance(ds, list):
        for r in ds:
            if "E_GeV" in r:
                E_list.append(float(r["E_GeV"]))
    # fallback: user-specified energy grid
    if not E_list:
        E_list = [100.0, 200.0, 300.0]

    preds = [{"E_GeV": E, "O_pred": _predict_truncated(E, Lambda, c6)} for E in E_list]
    deltas = [{"E_GeV": E, "delta_proj": _delta_trunc_bound(E, Lambda, c8_max)} for E in E_list]

    artifact = {
        "module": name,
        "Pi": {
            "type": "EFT_truncation_toy",
            "Lambda_GeV": Lambda,
            "c6": c6,
            "assumptions": [
                "Local EFT valid in ΩI up to E_max",
                "Neglected higher operators bounded by |c8| <= c8_max_abs",
            ],
        },
        "DeltaPi": {
            "method": "dimension-8 truncation bound",
            "c8_max_abs": c8_max,
            "grid": deltas,
        },
        "predictions": preds,
        "kappa": kappa,
    }
    return artifact

def check(artifact: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    locks: Dict[str, Dict[str, Any]] = {}
    diagnostic: List[str] = []

    # PA1: Π declared
    Pi = artifact.get("Pi")
    if not Pi:
        locks["PA1_Pi_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(PA1)", "note": "Pi missing"}
        diagnostic.append("Missing Pi -> NO-EVAL(PA1)")
        return locks, diagnostic
    locks["PA1_Pi_DECLARED"] = {"pass": True, "verdict": "PASS", "note": "Pi declared"}

    # PA2: ΔΠ(E) declared
    dPi = artifact.get("DeltaPi", {})
    grid = dPi.get("grid", None)
    if not grid:
        locks["PA2_DeltaPi_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(PA2)", "note": "DeltaPi grid missing"}
        diagnostic.append("Missing DeltaPi grid -> NO-EVAL(PA2)")
        return locks, diagnostic
    locks["PA2_DeltaPi_DECLARED"] = {"pass": True, "verdict": "PASS", "note": "DeltaPi grid declared"}

    # PA3: informativeness vs data (dominance)
    # Compare max ΔΠ to kappa * sigma_data (use dataset sigma if provided; else cfg.sigma_data)
    kappa = float(artifact.get("kappa", 1.0))
    sigma_data = None
    if "sigma_data" in cfg:
        sigma_data = float(cfg["sigma_data"])
    # infer typical sigma from dataset rows if present
    ds = cfg.get("dataset_rows")
    if sigma_data is None and isinstance(ds, list) and ds:
        sigma_data = float(ds[0].get("sigma", 0.0))
    if sigma_data is None:
        locks["PA3_SIGMA_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(PA3)", "note": "sigma_data missing"}
        diagnostic.append("sigma_data missing -> NO-EVAL(PA3)")
    else:
        locks["PA3_SIGMA_DECLARED"] = {"pass": True, "verdict": "PASS", "note": "sigma_data declared"}
        max_delta = max(float(r["delta_proj"]) for r in grid)
        if max_delta >= kappa * sigma_data:
            locks["PA3_INFORMATIVE"] = {"pass": False, "verdict": "NO-EVAL(PA3)", "note": f"max ΔΠ={max_delta:.3g} >= κσ={kappa*sigma_data:.3g}"}
            diagnostic.append("Projection not informative (ΔΠ dominates) -> NO-EVAL(PA3)")
        else:
            locks["PA3_INFORMATIVE"] = {"pass": True, "verdict": "PASS", "note": "ΔΠ does not dominate σ_data"}

    # PA4: invariance under allowed reparam (simple scaling check)
    # Allowed: rescale Lambda -> a*Lambda, with c6 -> c6*a^2 (keeps O_pred invariant)
    a = float((cfg.get("reparam", {}) or {}).get("scale_Lambda", 1.0))
    if a <= 0:
        locks["PA4_REPARAM_VALID"] = {"pass": False, "verdict": "NO-EVAL(PA4)", "note": "invalid scale_Lambda"}
        diagnostic.append("Invalid reparam scale -> NO-EVAL(PA4)")
    else:
        locks["PA4_REPARAM_VALID"] = {"pass": True, "verdict": "PASS", "note": "reparam scale valid"}
        if a != 1.0:
            Pi0 = artifact["Pi"]
            Lambda0 = float(Pi0["Lambda_GeV"])
            c60 = float(Pi0["c6"])
            # transformed
            Lambda1 = a * Lambda0
            c61 = c60 * (a*a)
            # compare predictions on grid
            tol = float((cfg.get("reparam", {}) or {}).get("tol", 1e-10))
            ok = True
            for r in artifact["predictions"]:
                E = float(r["E_GeV"])
                o0 = float(r["O_pred"])
                o1 = _predict_truncated(E, Lambda1, c61)
                if abs(o0 - o1) > tol:
                    ok = False
                    break
            if not ok:
                locks["PA4_INVARIANCE"] = {"pass": False, "verdict": "FAIL(PA4)", "note": "predictions change under allowed reparam"}
                diagnostic.append("Predictions not invariant under allowed reparam -> FAIL(PA4)")
            else:
                locks["PA4_INVARIANCE"] = {"pass": True, "verdict": "PASS", "note": "predictions invariant under allowed reparam"}
        else:
            locks["PA4_INVARIANCE"] = {"pass": True, "verdict": "PASS", "note": "no reparam applied"}

    return locks, diagnostic
