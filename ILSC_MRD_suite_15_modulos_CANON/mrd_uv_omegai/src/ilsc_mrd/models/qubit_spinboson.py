
from dataclasses import dataclass
from typing import Dict, Any, Tuple
import numpy as np

def ohmic_J(omega: np.ndarray, alpha: float, omega_c: float) -> np.ndarray:
    # J(ω)=2α ω exp(-ω/ω_c)
    return 2.0*alpha*omega*np.exp(-omega/omega_c)

def coth(x: np.ndarray) -> np.ndarray:
    # stable coth
    x = np.asarray(x)
    out = np.empty_like(x, dtype=float)
    small = np.abs(x) < 1e-6
    out[small] = 1.0/x[small] + x[small]/3.0  # series
    out[~small] = np.cosh(x[~small]) / np.sinh(x[~small])
    return out

@dataclass
class QubitSpinBoson:
    omega0: float
    bias: float
    alpha: float
    omega_c: float
    temperature: float
    coupling_op: str = "sigma_z"

    @staticmethod
    def from_cfg(cfg: Dict[str, Any]) -> "QubitSpinBoson":
        q = cfg["qubit"]
        bath = cfg["bath"]["spectral_density"]
        T = cfg["bath"].get("temperature", 0.0)
        return QubitSpinBoson(
            omega0=float(q.get("omega0", 1.0)),
            bias=float(q.get("bias", 0.0)),
            alpha=float(bath.get("alpha", 0.05)),
            omega_c=float(bath.get("omega_c", 20.0)),
            temperature=float(T),
            coupling_op=str(cfg.get("coupling", {}).get("operator", "sigma_z"))
        )

    def spectral_density(self, omega: np.ndarray) -> np.ndarray:
        return ohmic_J(omega, self.alpha, self.omega_c)

    def noise_spectrum(self, omega: np.ndarray) -> np.ndarray:
        # N(ω) ~ (1/2) J(ω) coth(β ω /2)
        beta = np.inf if self.temperature == 0 else 1.0/self.temperature
        x = 0.5*beta*np.maximum(omega, 1e-12)
        return 0.5*self.spectral_density(omega)*coth(x)

    def dephasing_rate_markov(self) -> float:
        # crude Markovian dephasing proxy: Γφ ~ π α T (Ohmic)
        # This is a standard scaling; used as MRD proxy (not a full derivation).
        return np.pi*self.alpha*max(self.temperature, 0.0)

    def channel_parameter(self, t: float) -> float:
        # Phase damping channel coherence factor
        Gamma = self.dephasing_rate_markov()
        return float(np.exp(-Gamma*t))
