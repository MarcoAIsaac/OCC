from __future__ import annotations
from typing import Any, Dict, List, Tuple
import numpy as np

name = "fourf_unif_op"

def compile(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Compile operational 4F unification gating.

    Principle:
      Any 'unified 4F' proposal must map its observables to the 4F dictionary invariants.
      Here we use the toy SU(2) dictionary: observables are Tr(U(loop))/2.

    Expected cfg:
      - dict_artifact: produced by fourf_dict.compile or loaded from report
      - proposal:
          claimed_observables: list of {name, expression} or {name, value}
          mapping: list of {name, maps_to}  where maps_to is one of dictionary observables keys
      - tolerances: {match_eps}
    """
    dict_art = cfg.get("dict_artifact", {}) or {}
    D = dict_art.get("dictionary", {}) or {}
    dict_obs = D.get("observables", {}) or {}

    proposal = cfg.get("proposal", {}) or {}
    claimed = proposal.get("claimed_observables", []) or []
    mapping = proposal.get("mapping", []) or []

    # resolve mapped values
    mapped_values = {}
    for m in mapping:
        nm = m.get("name")
        to = m.get("maps_to")
        if nm and to in dict_obs:
            mapped_values[nm] = dict_obs[to]

    artifact = {
        "module": name,
        "dictionary_observables": dict_obs,
        "proposal": {
            "claimed_observables": claimed,
            "mapping": mapping,
            "mapped_values": mapped_values,
        },
        "rule": "All proposal observables must be functions of 4F invariants (here: trace class functions).",
    }
    return artifact

def check(artifact: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    locks: Dict[str, Dict[str, Any]] = {}
    diagnostic: List[str] = []
    eps = float((cfg.get("tolerances", {}) or {}).get("match_eps", 1e-8))

    dict_obs = artifact.get("dictionary_observables", {}) or {}
    prop = artifact.get("proposal", {}) or {}
    claimed = prop.get("claimed_observables", []) or []
    mapping = prop.get("mapping", []) or []
    mapped = prop.get("mapped_values", {}) or {}

    # 4U1: dictionary present
    if not dict_obs:
        locks["4U1_DICT_PRESENT"] = {"pass": False, "verdict": "NO-EVAL(4U1)", "note": "Dictionary observables missing"}
        diagnostic.append("Missing 4F dictionary -> NO-EVAL(4U1)")
        return locks, diagnostic
    locks["4U1_DICT_PRESENT"] = {"pass": True, "verdict": "PASS", "note": "Dictionary present"}

    # 4U2: mapping declared for all claimed observables
    claimed_names = [c.get("name") for c in claimed if c.get("name")]
    mapping_names = [m.get("name") for m in mapping if m.get("name")]
    missing = [n for n in claimed_names if n not in mapping_names]
    if missing:
        locks["4U2_MAPPING_COMPLETE"] = {"pass": False, "verdict": "NO-EVAL(4U2)", "note": f"Missing mapping for: {missing}"}
        diagnostic.append("Proposal missing mapping -> NO-EVAL(4U2)")
    else:
        locks["4U2_MAPPING_COMPLETE"] = {"pass": True, "verdict": "PASS", "note": "Mapping declared for all claimed observables"}

    # 4U3: mapped targets exist in dictionary and are invariant class functions
    bad = []
    for m in mapping:
        nm = m.get("name")
        to = m.get("maps_to")
        if to not in dict_obs:
            bad.append((nm, to))
    if bad:
        locks["4U3_MAPPING_VALID"] = {"pass": False, "verdict": "FAIL(4U3)", "note": f"Maps to non-dictionary targets: {bad[:3]}..."}
        diagnostic.append("Mapping targets not in dictionary -> FAIL(4U3)")
    else:
        locks["4U3_MAPPING_VALID"] = {"pass": True, "verdict": "PASS", "note": "All mapping targets exist in dictionary"}

    # 4U4: consistency check when proposal provides numeric values: must match mapped invariants (within eps)
    mism = []
    for c in claimed:
        nm = c.get("name")
        if nm is None:
            continue
        if "value" in c and nm in mapped:
            v0 = float(c["value"])
            v1 = float(mapped[nm])
            if abs(v0 - v1) > eps:
                mism.append((nm, v0, v1))
    if mism:
        locks["4U4_NUMERIC_MATCH"] = {"pass": False, "verdict": "FAIL(4U4)", "note": f"Mismatches: {mism[:3]}..."}
        diagnostic.append("Numeric claimed observables do not match dictionary invariants -> FAIL(4U4)")
    else:
        locks["4U4_NUMERIC_MATCH"] = {"pass": True, "verdict": "PASS", "note": "Numeric values (if any) match mapped invariants"}

    # 4U5: non-invariant proposals are rejected (explicit flag)
    if cfg.get("proposal_uses_noninvariant", False):
        locks["4U5_NONINVARIANT_FORBIDDEN"] = {"pass": False, "verdict": "FAIL(4U5)", "note": "Proposal attempts to use non-invariant observable"}
        diagnostic.append("Non-invariant observable used -> FAIL(4U5)")
    else:
        locks["4U5_NONINVARIANT_FORBIDDEN"] = {"pass": True, "verdict": "PASS", "note": "No non-invariant observables used"}

    return locks, diagnostic
