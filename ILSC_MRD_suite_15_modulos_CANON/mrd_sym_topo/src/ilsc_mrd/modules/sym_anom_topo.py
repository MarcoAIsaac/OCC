from __future__ import annotations
from typing import Any, Dict, List, Tuple
import math

name = "sym_anom_topo"

def compile(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Compile a Symmetry/Anomaly/Topology operational module (toy).

    This MRD focuses on:
      - A declared gauge symmetry group (toy: U(1))
      - Anomaly cancellation (toy conditions):
          * sum_i q_i   = 0
          * sum_i q_i^3 = 0
      - A topological quantization condition (toy):
          * a Chern-number-like integer k must be integer within tolerance

    Operational rule:
      - SYM1 (group declared) is checked against the *theory spec* in cfg.
        The dataset may provide example charges/k for reproducibility, but it
        must not silently "repair" missing declarations.
      - If cfg.fermions is absent/empty, we fall back to the dataset fermions
        purely as a reproducible toy input (PASS case).
      - If cfg.fermions is provided, it overrides the dataset (FAIL case).

    Expected cfg:
      - symmetry: {group: "U1", notes}
      - dataset: {csv_path, meta_path} (optional but recommended for audit)
      - fermions: [{name, charge_q}] (optional; overrides dataset)
      - topology: {chern_k: float (optional), tol_integer: float}
    """
    sym_cfg = cfg.get("symmetry", {}) or {}
    topo_cfg = cfg.get("topology", {}) or {}
    ferm_cfg = cfg.get("fermions", None)

    # Dataset fallback (toy): provides reproducible charges/k, but must not set group.
    ds = cfg.get("dataset", {}) or {}
    data_fermions: List[Dict[str, Any]] = []
    data_k = float("nan")
    if ds.get("csv_path") and ds.get("meta_path"):
        try:
            from ilsc_mrd.utils.data_sym_topo import load_sym_topo
            d = load_sym_topo(ds["csv_path"], ds["meta_path"])
            data_fermions = d.fermions
            data_k = float(d.chern_k)
        except Exception:
            # Dataset is optional for logic; audit handles missing files elsewhere.
            pass

    fermions = ferm_cfg if (ferm_cfg is not None and len(ferm_cfg) > 0) else data_fermions

    charges: List[float] = []
    for f in fermions:
        if "charge_q" in f:
            charges.append(float(f["charge_q"]))

    s1 = sum(charges)
    s3 = sum(q**3 for q in charges)

    artifact = {
        "module": name,
        "symmetry": {
            # IMPORTANT: do NOT default group here; missing group must trigger NO-EVAL(SYM1)
            "group": sym_cfg.get("group", None),
            "notes": sym_cfg.get("notes", ""),
        },
        "charges": charges,
        "anomaly_sums": {"sum_q": s1, "sum_q3": s3},
        "topology": {
            "chern_k": float(topo_cfg.get("chern_k", data_k)),
            "tol_integer": float(topo_cfg.get("tol_integer", 1e-8)),
        },
        "dataset": {
            "dataset_id": ds.get("dataset_id"),
            "csv_path": ds.get("csv_path"),
            "meta_path": ds.get("meta_path"),
        },
        "notes": "Toy symmetry/anomaly/topology module with dataset fallback (charges/k only).",
    }
    return artifact


def check(artifact: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    locks: Dict[str, Dict[str, Any]] = {}
    diagnostic: List[str] = []

    sym = artifact.get("symmetry", {}) or {}
    group = sym.get("group", None)
    if not group:
        locks["SYM1_GROUP_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(SYM1)", "note": "symmetry.group missing"}
        diagnostic.append("Missing symmetry.group -> NO-EVAL(SYM1)")
        return locks, diagnostic
    locks["SYM1_GROUP_DECLARED"] = {"pass": True, "verdict": "PASS", "note": f"group={group}"}

    charges = artifact.get("charges", None)
    if not charges:
        locks["AN1_CHARGES_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(AN1)", "note": "no fermion charges provided"}
        diagnostic.append("No fermion charges -> NO-EVAL(AN1)")
        return locks, diagnostic
    locks["AN1_CHARGES_DECLARED"] = {"pass": True, "verdict": "PASS", "note": f"N={len(charges)} charges"}

    sums = artifact.get("anomaly_sums", {}) or {}
    s1 = float(sums.get("sum_q", float("nan")))
    s3 = float(sums.get("sum_q3", float("nan")))
    # anomaly tolerances
    tol = float((cfg.get("tolerances", {}) or {}).get("anom_tol", 1e-12))
    if abs(s1) <= tol:
        locks["AN2_LINEAR_CANCEL"] = {"pass": True, "verdict": "PASS", "note": f"|sum q|={abs(s1):.3e} <= {tol:.1e}"}
    else:
        locks["AN2_LINEAR_CANCEL"] = {"pass": False, "verdict": "FAIL(AN2)", "note": f"|sum q|={abs(s1):.3e} > {tol:.1e}"}
        diagnostic.append("Linear anomaly condition violated -> FAIL(AN2)")
    if abs(s3) <= tol:
        locks["AN3_CUBIC_CANCEL"] = {"pass": True, "verdict": "PASS", "note": f"|sum q^3|={abs(s3):.3e} <= {tol:.1e}"}
    else:
        locks["AN3_CUBIC_CANCEL"] = {"pass": False, "verdict": "FAIL(AN3)", "note": f"|sum q^3|={abs(s3):.3e} > {tol:.1e}"}
        diagnostic.append("Cubic anomaly condition violated -> FAIL(AN3)")

    topo = artifact.get("topology", {}) or {}
    k = topo.get("chern_k", float("nan"))
    tol_int = float(topo.get("tol_integer", 1e-8))
    if not (k == k):
        locks["TOPO1_K_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(TOPO1)", "note": "chern_k missing/NaN"}
        diagnostic.append("chern_k missing -> NO-EVAL(TOPO1)")
    else:
        locks["TOPO1_K_DECLARED"] = {"pass": True, "verdict": "PASS", "note": "chern_k declared"}
        nearest = round(float(k))
        if abs(float(k) - nearest) <= tol_int:
            locks["TOPO2_QUANTIZED"] = {"pass": True, "verdict": "PASS", "note": f"k≈{nearest} within {tol_int:.1e}"}
        else:
            locks["TOPO2_QUANTIZED"] = {"pass": False, "verdict": "FAIL(TOPO2)", "note": f"k={k} not integer within {tol_int:.1e}"}
            diagnostic.append("Topological quantization violated -> FAIL(TOPO2)")

    return locks, diagnostic
