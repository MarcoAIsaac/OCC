
from typing import Dict, Any

def check_no_uv_reinject(proj: Dict[str, Any]) -> Dict[str, Any]:
    cutoff = proj.get("cutoff_value", None)
    pol = proj.get("policy", None)
    delta = proj.get("delta_trunc_estimate", None)
    if cutoff is None:
        return {"pass": True, "note": "no cutoff used", "severity": "PASS"}
    if (pol is None) or (delta is None):
        return {"pass": False, "cutoff_value": cutoff, "policy": pol, "delta_trunc_estimate": delta,
                "severity": "NO-EVAL", "note": "cutoff used but missing auditable truncation error/projection"}
    # If truncation error dominates the operational window, treat as NO-EVAL (projection not informative).
    try:
        delta_f = float(delta)
    except Exception:
        delta_f = 1.0
    if delta_f > 1e-2:
        return {"pass": False, "cutoff_value": cutoff, "policy": pol, "delta_trunc_estimate": delta_f,
                "severity": "NO-EVAL", "note": "truncation/projection error too large for ΩI (dominates inference)"}
    return {"pass": True, "cutoff_value": cutoff, "policy": pol, "delta_trunc_estimate": delta_f, "severity": "PASS"}
