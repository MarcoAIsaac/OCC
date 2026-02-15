
from typing import Dict, Any
import numpy as np

def coth(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x)
    out = np.empty_like(x, dtype=float)
    small = np.abs(x) < 1e-6
    out[small] = 1.0/x[small] + x[small]/3.0
    out[~small] = np.cosh(x[~small]) / np.sinh(x[~small])
    return out

def check_fdt(omega: np.ndarray, J: np.ndarray, Nw: np.ndarray, temperature: float, eps: float) -> Dict[str, Any]:
    # Proxy FDT: N(ω) ≈ 0.5 J(ω) coth(β ω/2)
    if temperature <= 0:
        # at T=0 coth -> 1, so N ≈ 0.5 J
        target = 0.5*J
    else:
        beta = 1.0/temperature
        target = 0.5*J*coth(0.5*beta*np.maximum(omega,1e-12))
    denom = np.maximum(np.abs(target), 1e-12)
    rel_err = np.max(np.abs(Nw-target)/denom)
    ok = float(rel_err) <= float(eps)
    return {"pass": ok, "max_rel_error": float(rel_err), "eps": float(eps), "temperature": float(temperature)}
