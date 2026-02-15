from __future__ import annotations
from typing import Any, Dict, List, Tuple
import math

name = "vac_de"

def compile(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Compile a toy vacuum/DE effective module.

    cfg:
      - params: {w, rho0, coupling_to_matter}
      - policy: {allow_w_variable: bool, has_exchange_Q: bool}
      - bounds: {w_center, w_halfwidth, coupling_max}
    """
    p = cfg.get("params", {}) or {}
    w = p.get("w", None)
    rho0 = p.get("rho0", None)
    coupling = float(p.get("coupling_to_matter", 0.0))

    artifact = {
        "module": name,
        "params": {"w": w, "rho0": rho0, "coupling_to_matter": coupling},
        "policy": cfg.get("policy", {}) or {},
        "bounds": cfg.get("bounds", {}) or {},
        "notes": "Toy vacuum/DE module: acceleration condition + observational w band + local coupling bound.",
    }
    return artifact

def check(artifact: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    locks: Dict[str, Dict[str, Any]] = {}
    diag: List[str] = []
    p = artifact.get("params", {}) or {}

    # V1: declare rho0 and w
    if p.get("w") is None or p.get("rho0") is None:
        locks["V1_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(V1)", "note": "Need params.w and params.rho0"}
        diag.append("Missing vacuum parameters -> NO-EVAL(V1)")
        return locks, diag
    w = float(p.get("w"))
    rho0 = float(p.get("rho0"))
    locks["V1_DECLARED"] = {"pass": True, "verdict": "PASS", "note": "w and rho0 declared"}

    # V2: variable w requires exchange term declaration (conceptual discipline)
    pol = artifact.get("policy", {}) or {}
    allow_var = bool(pol.get("allow_w_variable", False))
    has_Q = bool(pol.get("has_exchange_Q", False))
    if allow_var and not has_Q:
        locks["V2_WVAR_POLICY"] = {"pass": False, "verdict": "NO-EVAL(V2)", "note": "w(z) variability allowed but no exchange term Q declared"}
        diag.append("Variable w allowed but no Q -> NO-EVAL(V2)")
    else:
        locks["V2_WVAR_POLICY"] = {"pass": True, "verdict": "PASS", "note": "policy consistent"}

    # V3: acceleration requires w < -1/3 (for positive rho)
    if rho0 <= 0:
        locks["V3_RHO_POS"] = {"pass": False, "verdict": "FAIL(V3)", "note": "rho0 must be >0"}
        diag.append("rho0<=0 -> FAIL(V3)")
    else:
        locks["V3_RHO_POS"] = {"pass": True, "verdict": "PASS", "note": "rho0>0"}
    if w < -1.0/3.0:
        locks["V3_ACCEL"] = {"pass": True, "verdict": "PASS", "note": "w<-1/3 gives acceleration (toy)"}
    else:
        locks["V3_ACCEL"] = {"pass": False, "verdict": "FAIL(V3)", "note": "w>=-1/3 not accelerating"}
        diag.append("Not accelerating -> FAIL(V3)")

    # V4: observational band for w (toy)
    b = artifact.get("bounds", {}) or {}
    w0 = float(b.get("w_center", -1.0))
    hw = float(b.get("w_halfwidth", 0.2))
    if abs(w - w0) <= hw:
        locks["V4_W_BAND"] = {"pass": True, "verdict": "PASS", "note": f"w within [{w0-hw},{w0+hw}]"}
    else:
        locks["V4_W_BAND"] = {"pass": False, "verdict": "FAIL(V4)", "note": "w outside observational band (toy)"}
        diag.append("w outside band -> FAIL(V4)")

    # V5: local coupling bound
    coupling = float(p.get("coupling_to_matter", 0.0))
    cmax = float(b.get("coupling_max", 1e-3))
    if abs(coupling) <= cmax:
        locks["V5_LOCAL_COUPLING"] = {"pass": True, "verdict": "PASS", "note": "coupling within bound"}
    else:
        locks["V5_LOCAL_COUPLING"] = {"pass": False, "verdict": "FAIL(V5)", "note": "coupling exceeds bound"}
        diag.append("coupling exceeds local bound -> FAIL(V5)")

    return locks, diag
