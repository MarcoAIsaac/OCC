
from typing import Dict, Any, Callable, List
import copy

_MAX_WORK = 5.0e7  # cap for outer-product work ~ n_time*n_omega

def _work(cfg: Dict[str, Any]) -> float:
    n_omega = int(cfg["numerics"]["grid"]["omega_grid"]["n"])
    n_time = int(cfg["numerics"]["grid"]["time_grid"]["n"])
    # causality uses mirrored time -> ~2n_time
    return float(2*n_time*n_omega)

def pcn_sweep(cfg: Dict[str, Any], refinements: List[int], run_once: Callable[[Dict[str, Any]], Dict[str, Any]]) -> Dict[str, Any]:
    base_verdict = None
    runs = []
    flip = False
    skipped = []
    for r in [1] + list(refinements):
        cfg_r = copy.deepcopy(cfg)
        for gname in ["omega_grid","time_grid"]:
            n = int(cfg_r["numerics"]["grid"][gname]["n"])
            cfg_r["numerics"]["grid"][gname]["n"] = int(max(10, n*r))
        w = _work(cfg_r)
        if w > _MAX_WORK:
            skipped.append({"refinement": r, "reason": f"work_cap_exceeded ({w:.2e} > {_MAX_WORK:.2e})"})
            continue
        res = run_once(cfg_r)
        if base_verdict is None:
            base_verdict = res["verdict"]
        else:
            if res["verdict"] != base_verdict:
                flip = True
        runs.append({"refinement": r, "verdict": res["verdict"]})
    # If we had to skip refinements, we conservatively mark as NOT passing PCN (so runner can NO-EVAL)
    pass_pcn = (not flip) and (len(skipped) == 0)
    return {"pass": pass_pcn, "flip": flip, "runs": runs, "skipped": skipped, "work_cap": _MAX_WORK}

def pcd_sweep(cfg: Dict[str, Any], run_once: Callable[[Dict[str, Any]], Dict[str, Any]]) -> Dict[str, Any]:
    import copy
    base = run_once(copy.deepcopy(cfg))["verdict"]
    eps_list = []
    base_eps = float(cfg["numerics"]["tolerances"]["eps_psd"])
    for factor in [0.1, 1.0, 10.0]:
        cfg2 = copy.deepcopy(cfg)
        cfg2["numerics"]["tolerances"]["eps_psd"] = base_eps*factor
        w = _work(cfg2)
        if w > _MAX_WORK:
            eps_list.append({"factor": factor, "verdict": "SKIPPED(work_cap)"})
            continue
        eps_list.append({"factor": factor, "verdict": run_once(cfg2)["verdict"]})
    flip = any((x["verdict"] not in (base, "SKIPPED(work_cap)")) for x in eps_list)
    pass_pcd = (not flip) and all(x["verdict"] != "SKIPPED(work_cap)" for x in eps_list)
    return {"pass": pass_pcd, "flip": flip, "runs": eps_list, "work_cap": _MAX_WORK}
