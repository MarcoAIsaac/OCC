
from typing import Dict, Any, Tuple
import numpy as np

def make_lin_grid(n: int, vmin: float, vmax: float) -> np.ndarray:
    return np.linspace(vmin, vmax, int(n), dtype=float)

def build_kernels_from_spectra(omega: np.ndarray, J: np.ndarray, Nw: np.ndarray) -> Dict[str, Any]:
    # For MRD-1X v0, we represent:
    # - noise spectrum N(ω) (non-negative required)
    # - a simple retarded response D_R(t) constructed to be causal by construction:
    #   D_R(t) = θ(t) * ∫ dω J(ω) sin(ω t) e^{-ω/ω_max}  (scaled)
    wmax = float(np.max(omega)) if len(omega)>0 else 1.0
    return {"omega": omega, "J": J, "Nw": Nw, "wmax": wmax}

def retarded_time_kernel(omega: np.ndarray, J: np.ndarray, t: np.ndarray) -> np.ndarray:
    # Construct D_R(t) with explicit θ(t)
    # D_R(t) = θ(t) * sum J(ω) sin(ω t) Δω / (wmax+ε)
    domega = float(omega[1]-omega[0]) if len(omega)>1 else 1.0
    wmax = float(np.max(omega)) if len(omega)>0 else 1.0
    # broadcasting: (T, W)
    sinwt = np.sin(np.outer(t, omega))
    dr = (sinwt @ (J*domega)) / (wmax + 1e-12)
    dr = np.where(t[:,None] >= 0, dr[:,None], 0.0).reshape(-1)
    return dr

def noise_time_kernel(omega: np.ndarray, Nw: np.ndarray, t: np.ndarray) -> np.ndarray:
    # N(t) = ∫ dω N(ω) cos(ω t) Δω / (wmax+ε)
    domega = float(omega[1]-omega[0]) if len(omega)>1 else 1.0
    wmax = float(np.max(omega)) if len(omega)>0 else 1.0
    coswt = np.cos(np.outer(t, omega))
    nt = (coswt @ (Nw*domega)) / (wmax + 1e-12)
    return nt
