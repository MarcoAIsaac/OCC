from __future__ import annotations
from typing import Any, Dict, List, Tuple
import importlib

def run_module(module_name: str, cfg: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], List[str]]:
    mod = importlib.import_module(f"ilsc_mrd.modules.{module_name}")
    artifact = mod.compile(cfg)
    locks, diagnostic = mod.check(artifact, cfg)
    return artifact, locks, diagnostic
