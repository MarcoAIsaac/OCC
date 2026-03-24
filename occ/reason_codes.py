"""Central reason-code catalog for compiler-style OCC reports."""

from __future__ import annotations

from typing import Dict

_REASON_PREFIXES = {
    "DOM": {"category": "domain", "label": "Domain declaration", "default_severity": "warning"},
    "UV": {"category": "uv_projection", "label": "UV projection", "default_severity": "warning"},
    "TR": {"category": "traceability", "label": "Traceability", "default_severity": "warning"},
    "L4": {"category": "nuclear_domain", "label": "Nuclear domain", "default_severity": "warning"},
    "J4": {"category": "nuclear_domain", "label": "Nuclear domain", "default_severity": "warning"},
    "NUC": {"category": "nuclear_domain", "label": "Nuclear domain", "default_severity": "warning"},
    "MRD": {"category": "mrd_runtime", "label": "MRD runtime", "default_severity": "error"},
}


def lookup_reason(code: str) -> Dict[str, str]:
    clean = str(code or "").strip().upper()
    if not clean:
        return {"category": "none", "label": "No reason code", "default_severity": "info"}
    for prefix, payload in _REASON_PREFIXES.items():
        if clean.startswith(prefix):
            return dict(payload)
    return {"category": "general", "label": "General compiler reason", "default_severity": "info"}
