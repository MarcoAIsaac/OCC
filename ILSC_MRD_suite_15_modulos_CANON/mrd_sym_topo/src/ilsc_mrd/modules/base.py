from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Protocol, Tuple

@dataclass
class ModuleResult:
    artifact: Dict[str, Any]
    locks: Dict[str, Dict[str, Any]]
    diagnostic: List[str]

class Module(Protocol):
    name: str
    def compile(self, cfg: Dict[str, Any]) -> Dict[str, Any]: ...
    def check(self, artifact: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]: ...
