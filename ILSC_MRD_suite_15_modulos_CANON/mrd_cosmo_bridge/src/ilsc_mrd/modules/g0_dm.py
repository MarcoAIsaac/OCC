from __future__ import annotations
from typing import Any, Dict, List, Tuple

name = "g0_dm"

def compile(cfg: Dict[str, Any]) -> Dict[str, Any]:
    # TODO: implement finite projection Π_g0_dm into ΩI + error budget.
    return {"module":"g0_dm","Pi":"TODO","delta":"TODO","notes":"scaffold"}

def check(artifact: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    locks: Dict[str, Dict[str, Any]] = {}
    diagnostic: List[str] = []
    # TODO: implement module-specific locks.
    locks["SCaffold_ONLY"] = {"pass": True, "verdict":"SKIP", "note":"module scaffold"}
    return locks, diagnostic
