from __future__ import annotations
from typing import Any, Dict, List, Tuple
import numpy as np

name = "fourf_dict"

def _su2_from_axis_angle(axis: np.ndarray, angle: float) -> np.ndarray:
    """Return SU(2) matrix for rotation about axis by angle."""
    axis = axis / (np.linalg.norm(axis) + 1e-30)
    a = np.cos(angle/2.0)
    b = -1j*np.sin(angle/2.0)*(axis[0])
    c = -1j*np.sin(angle/2.0)*(axis[1])
    d = -1j*np.sin(angle/2.0)*(axis[2])
    # Using Pauli matrices representation
    # U = a I - i sin(angle/2) (axis·sigma)
    U = np.array([[a + d, b - 1j*c],
                  [b + 1j*c, a - d]], dtype=complex)
    # Numerical cleanup: enforce det=1
    det = np.linalg.det(U)
    U = U / np.sqrt(det)
    return U

def _conjugate(U: np.ndarray, V: np.ndarray) -> np.ndarray:
    # V U V^{-1}
    Vinv = np.linalg.inv(V)
    return V @ U @ Vinv

def compile(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Compile a minimal 4F operational dictionary (CUI/HUI style) into an auditable artifact.

    This MRD uses a toy SU(2) gauge sector:
      - Each 'path' is represented by an SU(2) holonomy U(path).
      - Observables are gauge-invariant class functions, here: Tr(U)/2.

    Expected cfg keys:
      - dict:
          group: "SU2"
          paths: list of {path_id, axis (3), angle}
          loops: list of {loop_id, path_ids: [..]}
          observables: list of {name, type: "trace", loop_id}
      - gauge:
          mode: "conjugation"
          V: {axis (3), angle}   # gauge transform used for tests
      - tolerances: {unitary_eps, closure_eps}
    """
    d = cfg.get("dict", {}) or {}
    group = d.get("group", "SU2")
    if group != "SU2":
        return {"module": name, "error": "Only SU2 supported in MRD", "dict": d}

    # Build path holonomies
    paths = {}
    for p in d.get("paths", []) or []:
        axis = np.array(p.get("axis", [1.0,0.0,0.0]), dtype=float)
        angle = float(p.get("angle", 0.0))
        U = _su2_from_axis_angle(axis, angle)
        if (cfg.get('corrupt_path') == p['path_id']):
            U = 1.001 * U  # break unitarity/det=1
        paths[p["path_id"]] = U

    # Compose loops
    loops = {}
    for L in d.get("loops", []) or []:
        U = np.eye(2, dtype=complex)
        for pid in L.get("path_ids", []):
            U = U @ paths[pid]
        loops[L["loop_id"]] = U

    # Build observables (gauge-invariant)
    obs = {}
    for o in d.get("observables", []) or []:
        if o.get("type") == "trace":
            U = loops[o["loop_id"]]
            obs[o["name"]] = float(np.real(np.trace(U) / 2.0))
        else:
            obs[o["name"]] = None

    artifact = {
        "module": name,
        "dictionary": {
            "group": group,
            "paths": {k: paths[k] for k in paths},
            "loops": {k: loops[k] for k in loops},
            "observables": obs,
            "rules": [
                "Composition: U(loop)=Π U(path_i)",
                "Gauge: U -> V U V^{-1}; Tr(U) invariant"
            ],
        },
        "notes": "Toy SU(2) dictionary; demonstrates gauge-invariant observable extraction.",
    }
    return artifact

def check(artifact: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    locks: Dict[str, Dict[str, Any]] = {}
    diagnostic: List[str] = []
    tol = cfg.get("tolerances", {}) or {}
    unitary_eps = float(tol.get("unitary_eps", 1e-10))
    closure_eps = float(tol.get("closure_eps", 1e-10))

    D = artifact.get("dictionary", None)
    if not D or "paths" not in D or "loops" not in D or "observables" not in D:
        locks["4F1_DICT_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(4F1)", "note": "Dictionary not declared or incomplete"}
        diagnostic.append("Missing dictionary components -> NO-EVAL(4F1)")
        return locks, diagnostic
    locks["4F1_DICT_DECLARED"] = {"pass": True, "verdict": "PASS", "note": "Dictionary declared"}

    # 4F2: unitarity of holonomies (toy stand-in for group validity)
    bad = []
    for k, U in D["paths"].items():
        U = np.array(U)
        I = np.eye(U.shape[0], dtype=complex)
        err = np.linalg.norm(U.conj().T @ U - I)
        if err > unitary_eps:
            bad.append((k, err))
    if bad:
        locks["4F2_GROUP_VALID"] = {"pass": False, "verdict": "FAIL(4F2)", "note": f"Non-unitary path holonomies: {bad[:3]}..."}
        diagnostic.append("Some path holonomies violate unitarity -> FAIL(4F2)")
    else:
        locks["4F2_GROUP_VALID"] = {"pass": True, "verdict": "PASS", "note": "All path holonomies unitary within eps"}

    # 4F3: gauge invariance of declared observables under conjugation
    g = cfg.get("gauge", {}) or {}
    Vspec = g.get("V", {}) or {"axis":[0.0,0.0,1.0],"angle":0.123}
    axis = np.array(Vspec.get("axis",[0,0,1]), dtype=float)
    angle = float(Vspec.get("angle", 0.0))
    V = _su2_from_axis_angle(axis, angle)

    # recompute observables after conjugation
    diffs = []
    for loop_id, U in D["loops"].items():
        Uc = _conjugate(np.array(U), V)
        tr0 = float(np.real(np.trace(np.array(U))/2.0))
        tr1 = float(np.real(np.trace(Uc)/2.0))
        diffs.append(abs(tr0-tr1))
    maxdiff = max(diffs) if diffs else 0.0
    if maxdiff > closure_eps:
        locks["4F3_GAUGE_INVARIANCE"] = {"pass": False, "verdict": "FAIL(4F3)", "note": f"max |Δ Tr(U)/2| = {maxdiff:.3e} > eps"}
        diagnostic.append("Gauge invariance violated for trace observable -> FAIL(4F3)")
    else:
        locks["4F3_GAUGE_INVARIANCE"] = {"pass": True, "verdict": "PASS", "note": "Observables invariant under conjugation within eps"}

    # 4F4: closure under loop composition (consistency check)
    # Here: each loop is defined as product of paths; we verify determinants ~1
    det_bad = []
    for loop_id, U in D["loops"].items():
        det = np.linalg.det(np.array(U))
        if abs(det - 1.0) > 1e-8:
            det_bad.append((loop_id, det))
    if det_bad:
        locks["4F4_CLOSURE"] = {"pass": False, "verdict": "FAIL(4F4)", "note": f"det(U(loop))!=1 for {det_bad[:3]}..."}
        diagnostic.append("Loop holonomy not in SU(2) (det!=1) -> FAIL(4F4)")
    else:
        locks["4F4_CLOSURE"] = {"pass": True, "verdict": "PASS", "note": "Loop holonomies in SU(2) within tolerance"}

    return locks, diagnostic
