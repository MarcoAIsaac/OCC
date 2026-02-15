
from typing import Dict, Any
import numpy as np

def check_psd_noise(Nw: np.ndarray, eps: float) -> Dict[str, Any]:
    # For scalar noise spectrum, PSD reduces to N(ω) >= -eps.
    # Report worst value.
    minv = float(np.min(Nw))
    ok = minv >= -float(eps)
    return {"pass": ok, "min_value": minv, "eps": float(eps)}
