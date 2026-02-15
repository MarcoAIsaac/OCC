
from typing import Any, Dict, List, Tuple

class SchemaError(ValueError):
    pass

def require(d: Dict[str, Any], key: str) -> Any:
    if key not in d:
        raise SchemaError(f"Missing required key: {key}")
    return d[key]

def validate_case(cfg: Dict[str, Any]) -> None:
    require(cfg, "mrd")
    require(cfg, "isaac_omegaI")
    require(cfg, "numerics")
    require(cfg, "model")
    require(cfg, "compile")
    require(cfg, "checks")
    require(cfg, "audit")

    m = cfg["model"]
    if "type" not in m:
        raise SchemaError("model.type is required")
    if m["type"] not in ("qubit_spinboson","ho_caldeira_leggett"):
        raise SchemaError(f"Unsupported model.type: {m['type']}")

    tol = cfg["numerics"].get("tolerances", {})
    for k in ["eps_causal","eps_psd","eps_cptp","eps_fdt","eps_trace"]:
        if k not in tol:
            raise SchemaError(f"numerics.tolerances.{k} is required")

    grid = cfg["numerics"].get("grid", {})
    og = grid.get("omega_grid", {})
    tg = grid.get("time_grid", {})
    for gname, g in [("omega_grid", og), ("time_grid", tg)]:
        for k in ["type","n","min","max"]:
            if k not in g:
                raise SchemaError(f"numerics.grid.{gname}.{k} is required")
        if g["type"] != "lin":
            raise SchemaError("Only linear grids supported in MRD-1X v0")

    # ISAAC-0 policy presence
    pol = cfg["isaac_omegaI"].get("ISAAC0_policy", {})
    if pol.get("principle") != "operational_closure_backreaction":
        raise SchemaError("ISAAC0_policy.principle must be 'operational_closure_backreaction'")
