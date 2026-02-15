
from dataclasses import dataclass
from typing import Dict, Any
import numpy as np

def ohmic_J(omega: np.ndarray, gamma: float, omega_c: float, m: float=1.0) -> np.ndarray:
    # J(ω)=m γ ω exp(-ω/ω_c)
    return m*gamma*omega*np.exp(-omega/omega_c)

def coth(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x)
    out = np.empty_like(x, dtype=float)
    small = np.abs(x) < 1e-6
    out[small] = 1.0/x[small] + x[small]/3.0
    out[~small] = np.cosh(x[~small]) / np.sinh(x[~small])
    return out

@dataclass
class HOCaldeiraLeggett:
    m: float
    omega0: float
    gamma: float
    omega_c: float
    temperature: float

    @staticmethod
    def from_cfg(cfg: Dict[str, Any]) -> "HOCaldeiraLeggett":
        osc = cfg["oscillator"]
        bath = cfg["bath"]["spectral_density"]
        T = cfg["bath"].get("temperature", 0.0)
        return HOCaldeiraLeggett(
            m=float(osc.get("m", 1.0)),
            omega0=float(osc.get("omega0", 1.0)),
            gamma=float(bath.get("gamma", 0.1)),
            omega_c=float(bath.get("omega_c", 30.0)),
            temperature=float(T)
        )

    def spectral_density(self, omega: np.ndarray) -> np.ndarray:
        return ohmic_J(omega, self.gamma, self.omega_c, self.m)

    def noise_spectrum(self, omega: np.ndarray) -> np.ndarray:
        beta = np.inf if self.temperature == 0 else 1.0/self.temperature
        x = 0.5*beta*np.maximum(omega, 1e-12)
        return 0.5*self.spectral_density(omega)*coth(x)

    def retarded_response_time(self) -> float:
        # simple timescale proxy
        return 1.0/max(self.omega_c, 1e-9)
