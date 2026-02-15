
from typing import Dict, Any
import numpy as np

def qubit_phase_damping_choi(lambda_t: float) -> np.ndarray:
    # Phase damping channel: off-diagonals multiplied by lambda_t in density matrix.
    # Choi matrix in computational basis (|00>,|01>,|10>,|11>) for channel E:
    # E(|0><0|)=|0><0|, E(|1><1|)=|1><1|, E(|0><1|)=lambda |0><1|, E(|1><0|)=lambda |1><0|
    lam = float(lambda_t)
    C = np.array([
        [1.0, 0.0, 0.0, lam],
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0],
        [lam, 0.0, 0.0, 1.0],
    ], dtype=float) * 0.5
    return C

def ho_gaussian_channel_matrices(gamma: float, t: float, temperature: float) -> Dict[str, Any]:
    # Single-mode damping channel (approx) with X = e^{-γ t} I, Y = (1-e^{-2γ t}) (2n+1) I /2
    # using units where ħ=1 and Ω = [[0,1],[-1,0]]
    g = float(gamma)
    tt = float(t)
    eta = float(np.exp(-g*tt))
    # thermal occupancy (for ω~1 scale); proxy:
    nbar = 0.0 if temperature <= 0 else 1.0/(np.exp(1.0/max(temperature,1e-12)) - 1.0)
    nu = (2.0*nbar + 1.0)/2.0
    X = eta*np.eye(2)
    Y = (1.0-eta**2)*nu*np.eye(2)
    return {"X": X, "Y": Y, "eta": eta, "nbar": nbar, "nu": nu}
