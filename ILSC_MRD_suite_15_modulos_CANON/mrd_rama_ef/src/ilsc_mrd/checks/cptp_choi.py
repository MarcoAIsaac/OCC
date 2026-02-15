
from typing import Dict, Any
import numpy as np

def check_choi_cptp(C: np.ndarray, eps: float, eps_trace: float) -> Dict[str, Any]:
    # CPTP: Choi matrix PSD and trace-preserving condition Tr_out(C)=I/d
    # For qubit d=2, Tr_out(C) should equal I/2.
    eigs = np.linalg.eigvalsh((C + C.T)/2.0)
    mine = float(np.min(eigs))
    psd_ok = mine >= -float(eps)

    # partial trace over output system:
    # C indices: (i_out,i_in),(j_out,j_in) in 2x2; reshape to (2,2,2,2)
    R = C.reshape(2,2,2,2)
    tr_out = np.zeros((2,2), dtype=float)
    for o in range(2):
        tr_out += R[o,:,o,:]
    target = 0.5*np.eye(2)
    trace_err = float(np.max(np.abs(tr_out - target)))
    tp_ok = trace_err <= float(eps_trace)
    return {
        "pass": bool(psd_ok and tp_ok),
        "psd_ok": bool(psd_ok),
        "tp_ok": bool(tp_ok),
        "min_eig": mine,
        "trace_err": trace_err,
        "eps": float(eps),
        "eps_trace": float(eps_trace)
    }
