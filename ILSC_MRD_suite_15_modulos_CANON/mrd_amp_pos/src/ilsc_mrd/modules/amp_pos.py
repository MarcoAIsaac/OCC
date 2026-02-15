from __future__ import annotations
from typing import Any, Dict, List, Tuple
import math

name = "amp_pos"

# ---------------------------------------------------------------------------
# aQGC positivity + observational anchor (real-data minimal harness)
# ---------------------------------------------------------------------------

_AQGC_POS_TABLE4_GE0 = {
    # Table 4-style sign constraints (representative subset used in this MRD)
    # Keys use the EFT naming f_{X}/Λ^4 where X ∈ {S0,S1,M0..M5,T0,T1,T2,T8,T9}.
    "FS0": ">=0",
    "FS1": ">=0",
    "FM0": ">=0",
    "FM1": ">=0",
    "FM2": ">=0",
    "FM3": ">=0",
    "FM4": ">=0",
    "FM5": ">=0",
    "FT0": ">=0",
    "FT1": ">=0",
    "FT2": ">=0",
    "FT8": ">=0",
    "FT9": ">=0",
}

def _norm_aqgc_op(op: str) -> str:
    op = (op or "").strip().upper()
    op = op.replace("F_", "F").replace("F", "F")  # idempotent
    op = op.replace("LAMBDA^4","").replace("/","").replace("Λ^4","").replace("^4","")
    # Accept T0 or FT0 or F_T0
    if op.startswith("T") and len(op) >= 2 and op[1].isdigit():
        return "F" + op  # T0 -> FT0
    if op.startswith("FT"):
        return op
    if op.startswith("FS") or op.startswith("FM"):
        return op
    # Sometimes people pass fT0
    if op.startswith("F") and len(op) >= 3 and op[1] in ("S","M","T"):
        return op
    return op

def _load_json(path: str) -> Any:
    import json
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _sha256_path(path: str) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _load_aqgc_limits(cfg: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Load observational aQGC limits (if provided) with optional hash check."""
    ds = (cfg.get("exp_dataset", {}) or {})
    json_path = ds.get("json_path", "")
    meta_path = ds.get("meta_path", "")
    if not json_path:
        return {}, {}
    data = _load_json(json_path)
    meta = _load_json(meta_path) if meta_path else {}
    if meta and meta.get("sha256"):
        sha = _sha256_path(json_path)
        if sha != meta.get("sha256"):
            raise RuntimeError(f"Dataset SHA256 mismatch for {json_path}: {sha} != {meta.get('sha256')}")
    return data, meta

def _aqgc_get_coeff(cfg: Dict[str, Any]) -> Tuple[str, float]:
    aq = (cfg.get("aqgc", {}) or {})
    op = _norm_aqgc_op(str(aq.get("operator","")))
    coeff = aq.get("coeff_TeV4", aq.get("coeff", float("nan")))
    return op, float(coeff)

def _aqgc_lock_positivity(cfg: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    op, coeff = _aqgc_get_coeff(cfg)
    if not op or not (coeff == coeff):
        return ({"pass": False, "verdict": "NO-EVAL(AMP5)", "note": "aqgc.operator/coeff missing",
                 "class": "C", "witness": {"op": op, "coeff_TeV4": coeff}}, "Missing aQGC params -> NO-EVAL(AMP5)")
    rule = _AQGC_POS_TABLE4_GE0.get(op)
    if rule is None:
        return ({"pass": False, "verdict": "NO-EVAL(AMP5)", "note": f"no Table4 rule for {op}",
                 "class": "C", "witness": {"op": op, "coeff_TeV4": coeff}}, f"Unknown op {op} -> NO-EVAL(AMP5)")
    ok = (coeff >= 0.0) if rule == ">=0" else False
    if ok:
        return ({"pass": True, "verdict": "PASS", "note": f"{op} satisfies {rule}",
                 "class": "C", "witness": {"op": op, "coeff_TeV4": coeff, "rule": rule, "margin": coeff}}, "")
    return ({"pass": False, "verdict": "FAIL(AMP5)", "note": f"{op} violates {rule}",
             "class": "C", "witness": {"op": op, "coeff_TeV4": coeff, "rule": rule, "margin": coeff}}, f"Positivity violation for {op} -> FAIL(AMP5)")

def _aqgc_lock_data_limits(cfg: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    # This lock is an *observational anchor* for the demo pipeline (post-compile).
    # The compiler verdict remains meaningful without this; this lock is kept separate via class='E'.
    op, coeff = _aqgc_get_coeff(cfg)
    try:
        data, meta = _load_aqgc_limits(cfg)
    except Exception as e:
        return ({"pass": False, "verdict": "NO-EVAL(AMP6)", "note": f"dataset error: {e}",
                 "class": "E", "witness": {"op": op, "coeff_TeV4": coeff}}, f"Dataset load error -> NO-EVAL(AMP6): {e}")
    if not data:
        return ({"pass": False, "verdict": "NO-EVAL(AMP6)", "note": "exp_dataset not provided",
                 "class": "E", "witness": {"op": op, "coeff_TeV4": coeff}}, "No exp_dataset -> NO-EVAL(AMP6)")
    ops = (data.get("operators", {}) or {})
    if op not in ops:
        return ({"pass": False, "verdict": "NO-EVAL(AMP6)", "note": f"no limits for {op}",
                 "class": "E", "witness": {"op": op, "coeff_TeV4": coeff, "dataset_id": data.get("dataset_id","")}}, f"No exp limits for {op} -> NO-EVAL(AMP6)")
    lo = float(ops[op]["low"]); hi = float(ops[op]["high"])
    ok = (lo <= coeff <= hi)
    wid = {
        "op": op,
        "coeff_TeV4": coeff,
        "bounds_95CL": [lo, hi],
        "dataset_id": data.get("dataset_id",""),
        "dataset_sha256": (meta.get("sha256","") if meta else "")
    }
    if ok:
        return ({"pass": True, "verdict": "PASS", "note": "within observed 95% CL interval (anchor)",
                 "class": "E", "witness": wid}, "")
    return ({"pass": False, "verdict": "FAIL(AMP6)", "note": "outside observed 95% CL interval (anchor)",
             "class": "E", "witness": wid}, f"Outside experimental 95% CL interval for {op} -> FAIL(AMP6)")

def _amplitude_forward(s: float, *, c2: float, c3: float, Lambda: float) -> float:
    # Dimensionless toy forward amplitude A(s,0) = c2 (s/L^2)^2 + c3 (s/L^2)^3
    x = s / (Lambda*Lambda)
    return c2 * x*x + c3 * x*x*x

def compile(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Compile a toy amplitude positivity check on an energy grid in ΩI.

    Required cfg:
      - eft: {Lambda_GeV, c2, c3}
      - dispersion: {ir_safe: bool, N_sub: int}
      - omegaI: {Emin_GeV, Emax_GeV, grid_N, frac_cutoff_max}
    """
    eft = cfg.get("eft", {}) or {}
    disp = cfg.get("dispersion", {}) or {}
    omg = cfg.get("omegaI", {}) or {}

    Lambda = float(eft.get("Lambda_GeV", float("nan")))
    c2 = float(eft.get("c2", float("nan")))
    c3 = float(eft.get("c3", 0.0))

    Emin = float(omg.get("Emin_GeV", 50.0))
    Emax = float(omg.get("Emax_GeV", 300.0))
    N = int(omg.get("grid_N", 50))
    frac = float(omg.get("frac_cutoff_max", 0.5))

    Es = [Emin + (Emax-Emin)*i/(N-1) for i in range(N)] if N > 1 else [Emin]
    series = []
    for E in Es:
        s = E*E
        A = _amplitude_forward(s, c2=c2, c3=c3, Lambda=Lambda)
        a0 = A/(16.0*math.pi)  # toy partial-wave proxy
        series.append({"E_GeV": E, "A": A, "a0_proxy": a0})

    artifact = {
        "module": name,
        "eft": {"Lambda_GeV": Lambda, "c2": c2, "c3": c3},
        "dispersion": {"ir_safe": bool(disp.get("ir_safe", False)), "N_sub": disp.get("N_sub", None)},
        "omegaI": {"Emin_GeV": Emin, "Emax_GeV": Emax, "grid_N": N, "frac_cutoff_max": frac},
        "series": series,
        "notes": "Toy positivity + unitarity + crossing gating. Replace by full dispersion/SDP in production.",
    }
    return artifact

def check(artifact: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    locks: Dict[str, Dict[str, Any]] = {}
    diag: List[str] = []

    eft = artifact.get("eft", {}) or {}
    Lambda = float(eft.get("Lambda_GeV", float("nan")))
    c2 = float(eft.get("c2", float("nan")))
    c3 = float(eft.get("c3", 0.0))

    # AMP1: IR-safe dispersion scheme declared
    disp = artifact.get("dispersion", {}) or {}
    if disp.get("ir_safe") is not True or disp.get("N_sub") is None:
        locks["AMP1_IR_SCHEME"] = {"pass": False, "verdict": "NO-EVAL(AMP1)", "note": "Need dispersion.ir_safe=True and N_sub declared"}
        diag.append("Missing IR-safe dispersion scheme -> NO-EVAL(AMP1)")
        return locks, diag
    locks["AMP1_IR_SCHEME"] = {"pass": True, "verdict": "PASS", "note": "IR-safe scheme declared"}

    # AMP2: ΩI within cutoff fraction (no UV reinjection)
    omg = artifact.get("omegaI", {}) or {}
    Emax = float(omg.get("Emax_GeV", float("nan")))
    frac = float(omg.get("frac_cutoff_max", 0.5))
    if not (Lambda == Lambda) or not (Emax == Emax):
        locks["AMP2_OMEGAI_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(AMP2)", "note": "Lambda/Emax not declared"}
        diag.append("Missing Lambda/Emax -> NO-EVAL(AMP2)")
        return locks, diag
    if Emax > frac*Lambda:
        locks["AMP2_OMEGAI_VALID"] = {"pass": False, "verdict": "NO-EVAL(AMP2)", "note": f"Emax={Emax:.3g} > frac*Lambda={frac*Lambda:.3g}"}
        diag.append("ΩI exceeds declared cutoff fraction -> NO-EVAL(AMP2)")
    else:
        locks["AMP2_OMEGAI_VALID"] = {"pass": True, "verdict": "PASS", "note": "ΩI within cutoff fraction"}

    # AMP3: Positivity bound (toy): c2 > 0
    if c2 > 0:
        locks["AMP3_POSITIVITY"] = {"pass": True, "verdict": "PASS", "note": "c2>0"}
    else:
        locks["AMP3_POSITIVITY"] = {"pass": False, "verdict": "FAIL(AMP3)", "note": "c2<=0 violates positivity"}
        diag.append("Positivity violation -> FAIL(AMP3)")

    # AMP4: Crossing (toy forward identical): require odd term zero if crossing_required
    if bool((cfg.get("crossing", {}) or {}).get("required", True)):
        if abs(c3) > float((cfg.get("crossing", {}) or {}).get("tol", 1e-12)):
            locks["AMP4_CROSSING"] = {"pass": False, "verdict": "FAIL(AMP4)", "note": "c3!=0 violates toy crossing-evenness"}
            diag.append("Crossing violation (toy) -> FAIL(AMP4)")
        else:
            locks["AMP4_CROSSING"] = {"pass": True, "verdict": "PASS", "note": "c3≈0"}
    else:
        locks["AMP4_CROSSING"] = {"pass": True, "verdict": "PASS", "note": "crossing not required in cfg"}

    # AMP5: Unitarity proxy: |a0| <= 1/2 on grid
    amax = 0.0
    for r in artifact.get("series", []) or []:
        a0 = abs(float(r["a0_proxy"]))
        amax = max(amax, a0)
    if amax <= 0.5:
        locks["AMP5_UNITARITY"] = {"pass": True, "verdict": "PASS", "note": f"max|a0|={amax:.3g} <= 0.5"}
    else:
        locks["AMP5_UNITARITY"] = {"pass": False, "verdict": "FAIL(AMP5)", "note": f"max|a0|={amax:.3g} > 0.5"}
        diag.append("Unitarity proxy violated -> FAIL(AMP5)")


    # AMP5/AMP6: aQGC sign-positivity + observational anchor (optional)
    if cfg.get("aqgc"):
        lock5, msg5 = _aqgc_lock_positivity(cfg)
        locks["AMP5_AQGC_POSITIVITY_TABLE4"] = lock5
        if msg5:
            diag.append(msg5)
        lock6, msg6 = _aqgc_lock_data_limits(cfg)
        locks["AMP6_AQGC_DATA_95CL_ANCHOR"] = lock6
        if msg6:
            diag.append(msg6)
    return locks, diag
