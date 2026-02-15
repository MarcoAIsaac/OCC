
from typing import Dict, Any

def enforce_no_uv_reinject(cfg: Dict[str, Any]) -> Dict[str, Any]:
    # MRD-1X v0: validate that if cutoff is used, an error estimate is present.
    trunc = cfg.get("compile", {}).get("truncate", {})
    cutoff = trunc.get("cutoff_value", None)
    delta = trunc.get("delta_trunc_estimate", None)
    return {"cutoff_value": cutoff, "delta_trunc_estimate": delta, "policy": trunc.get("cutoff_policy")}
