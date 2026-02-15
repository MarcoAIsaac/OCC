from __future__ import annotations
from typing import Any, Dict, List, Tuple
import math

name = "rama_ef"

def compile(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Compile a toy Effective Branching / Decoherence / Objectivity module.

    cfg:
      - params: {Gamma_decoh, N_fragments}
      - times: {tau_read, tau_stab}
      - thresholds: {R_min}
      - policy: {no_backflow: bool}
    """
    p = cfg.get("params", {}) or {}
    t = cfg.get("times", {}) or {}
    th = cfg.get("thresholds", {}) or {}

    Gamma = float(p.get("Gamma_decoh", float("nan")))
    Nf = int(p.get("N_fragments", 0))
    tau_read = float(t.get("tau_read", float("nan")))
    tau_stab = float(t.get("tau_stab", float("nan")))
    Rmin = float(th.get("R_min", 1.0))

    # Toy decoherence factor D(t)=exp(-Gamma t). Redundancy proxy R = Nf*(1-D(tau_read)).
    D_read = math.exp(-Gamma*tau_read) if (Gamma==Gamma and tau_read==tau_read) else float("nan")
    R = Nf*(1.0-D_read) if (D_read==D_read) else float("nan")
    tau_dec = (1.0/Gamma) if (Gamma==Gamma and Gamma>0) else float("nan")

    artifact = {
        "module": name,
        "params": {"Gamma_decoh": Gamma, "N_fragments": Nf},
        "times": {"tau_read": tau_read, "tau_stab": tau_stab, "tau_dec": tau_dec},
        "redundancy": {"D_read": D_read, "R": R, "R_min": Rmin},
        "policy": cfg.get("policy", {}) or {},
        "pointer_basis": cfg.get("pointer_basis", None),
        "notes": "Toy decoherence/objectivity checks. Replace with SK-derived kernels and mutual information computations.",
    }
    return artifact

def check(artifact: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    locks: Dict[str, Dict[str, Any]] = {}
    diag: List[str] = []

    # RE0: pointer basis declared
    pb = artifact.get("pointer_basis", None)
    if not pb:
        locks["RE0_POINTER_BASIS"] = {"pass": False, "verdict": "NO-EVAL(RE0)", "note": "pointer_basis missing"}
        diag.append("Missing pointer basis -> NO-EVAL(RE0)")
        return locks, diag
    locks["RE0_POINTER_BASIS"] = {"pass": True, "verdict": "PASS", "note": f"pointer_basis={pb}"}

    times = artifact.get("times", {}) or {}
    tau_dec = float(times.get("tau_dec", float("nan")))
    tau_read = float(times.get("tau_read", float("nan")))
    tau_stab = float(times.get("tau_stab", float("nan")))

    # RE1: decoherence fast enough: tau_dec < tau_read
    if not (tau_dec==tau_dec and tau_read==tau_read):
        locks["RE1_TIMES_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(RE1)", "note": "times missing"}
        diag.append("Times missing -> NO-EVAL(RE1)")
    else:
        if tau_dec < tau_read:
            locks["RE1_DECOH_FAST"] = {"pass": True, "verdict": "PASS", "note": f"tau_dec={tau_dec:.3g} < tau_read={tau_read:.3g}"}
        else:
            locks["RE1_DECOH_FAST"] = {"pass": False, "verdict": "FAIL(RE1)", "note": "decoherence too slow"}
            diag.append("Decoherence too slow -> FAIL(RE1)")

    # RE2: stability: tau_stab > tau_read
    if not (tau_stab==tau_stab and tau_read==tau_read):
        locks["RE2_STABILITY_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(RE2)", "note": "tau_stab/tau_read missing"}
        diag.append("Stability times missing -> NO-EVAL(RE2)")
    else:
        if tau_stab > tau_read:
            locks["RE2_STABLE"] = {"pass": True, "verdict": "PASS", "note": "tau_stab>tau_read"}
        else:
            locks["RE2_STABLE"] = {"pass": False, "verdict": "FAIL(RE2)", "note": "tau_stab<=tau_read"}
            diag.append("Branch not stable -> FAIL(RE2)")

    # RE3: redundancy threshold
    red = artifact.get("redundancy", {}) or {}
    R = float(red.get("R", float("nan")))
    Rmin = float(red.get("R_min", 1.0))
    if not (R==R):
        locks["RE3_REDUNDANCY_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(RE3)", "note": "redundancy missing"}
        diag.append("Redundancy missing -> NO-EVAL(RE3)")
    else:
        if R >= Rmin:
            locks["RE3_REDUNDANCY"] = {"pass": True, "verdict": "PASS", "note": f"R={R:.3g} >= Rmin={Rmin:.3g}"}
        else:
            locks["RE3_REDUNDANCY"] = {"pass": False, "verdict": "FAIL(RE3)", "note": f"R={R:.3g} < Rmin={Rmin:.3g}"}
            diag.append("Insufficient redundancy -> FAIL(RE3)")

    # RE4: no-backflow policy (if required)
    pol = artifact.get("policy", {}) or {}
    if bool(pol.get("require_no_backflow", True)) and bool(pol.get("no_backflow", True)) is not True:
        locks["RE4_NO_BACKFLOW"] = {"pass": False, "verdict": "FAIL(RE4)", "note": "backflow detected/declared"}
        diag.append("No-backflow violated -> FAIL(RE4)")
    else:
        locks["RE4_NO_BACKFLOW"] = {"pass": True, "verdict": "PASS", "note": "no-backflow satisfied (declared)"}

    return locks, diag
