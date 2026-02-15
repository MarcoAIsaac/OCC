
from typing import Dict, Any
import numpy as np

def check_gaussian_cp(X: np.ndarray, Y: np.ndarray, eps: float) -> Dict[str, Any]:
    # CP condition for single-mode Gaussian channel:
    # Y + i(Ω - X Ω X^T) >= 0
    Omega = np.array([[0.0, 1.0],[-1.0, 0.0]])
    M = Y + 1j*(Omega - X@Omega@X.T)
    eigs = np.linalg.eigvalsh(M)
    mine = float(np.min(np.real(eigs)))
    ok = mine >= -float(eps)
    return {"pass": ok, "min_eig": mine, "eps": float(eps)}
