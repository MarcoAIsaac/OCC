
from typing import Dict, Any
import numpy as np

def check_causality(t: np.ndarray, D_R: np.ndarray, eps: float) -> Dict[str, Any]:
    # t includes negative times; require D_R(t<0) ~ 0
    neg = t < 0
    if not np.any(neg):
        return {"pass": True, "max_violation": 0.0, "note": "no negative-time samples"}
    maxv = float(np.max(np.abs(D_R[neg]))) if np.any(neg) else 0.0
    ok = maxv <= float(eps)
    return {"pass": ok, "max_violation": maxv, "eps": float(eps)}
