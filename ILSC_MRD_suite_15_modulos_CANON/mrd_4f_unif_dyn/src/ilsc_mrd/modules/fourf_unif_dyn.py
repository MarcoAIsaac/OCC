from __future__ import annotations
from typing import Any, Dict, List, Tuple
import math

name = "fourf_unif_dyn"

def _run_g(g0: float, b: float, mu0: float, mu: float) -> float:
    """Toy 1-loop running: 1/g^2(mu) = 1/g0^2 + (b/8π^2) ln(mu/mu0)."""
    if g0 <= 0 or mu0 <= 0 or mu <= 0:
        return float("nan")
    inv = 1.0/(g0*g0) + (b/(8.0*math.pi*math.pi))*math.log(mu/mu0)
    if inv <= 0:
        return float("nan")
    return 1.0/math.sqrt(inv)

def compile(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Compile a minimal dynamic unification check (toy).

    Inputs:
      - omegaI: {mu_min_GeV, mu_max_GeV, mu0_GeV}
      - couplings_at_mu0: {g1, g2, g3}
      - betas: {b1, b2, b3}
      - unification: {tol_abs, grid_N}
      - gating: {passed: bool}  # result from 4F_UNIF_OP MRD or external check
    """
    omg = cfg.get("omegaI", {}) or {}
    mu_min = float(omg.get("mu_min_GeV", 1e2))
    mu_max = float(omg.get("mu_max_GeV", 1e5))
    mu0 = float(omg.get("mu0_GeV", 1e2))

    g0 = cfg.get("couplings_at_mu0", {}) or {}
    b = cfg.get("betas", {}) or {}
    g1_0 = float(g0.get("g1", float("nan")))
    g2_0 = float(g0.get("g2", float("nan")))
    g3_0 = float(g0.get("g3", float("nan")))
    b1 = float(b.get("b1", float("nan")))
    b2 = float(b.get("b2", float("nan")))
    b3 = float(b.get("b3", float("nan")))

    uni = cfg.get("unification", {}) or {}
    N = int(uni.get("grid_N", 200))
    tol_abs = float(uni.get("tol_abs", 0.02))

    # scan grid and find best unification point minimizing max pairwise diff
    mus = [mu_min * (mu_max/mu_min)**(i/(N-1)) for i in range(N)]
    best = None
    series = []
    for mu in mus:
        g1 = _run_g(g1_0, b1, mu0, mu)
        g2 = _run_g(g2_0, b2, mu0, mu)
        g3 = _run_g(g3_0, b3, mu0, mu)
        series.append({"mu_GeV": mu, "g1": g1, "g2": g2, "g3": g3})
        if any(math.isnan(x) for x in (g1,g2,g3)):
            continue
        d12 = abs(g1-g2); d13 = abs(g1-g3); d23 = abs(g2-g3)
        score = max(d12,d13,d23)
        if best is None or score < best["score"]:
            best = {"mu_GeV": mu, "gU": (g1+g2+g3)/3.0, "score": score, "d12": d12, "d13": d13, "d23": d23}

    artifact = {
        "module": name,
        "omegaI": {"mu_min_GeV": mu_min, "mu_max_GeV": mu_max, "mu0_GeV": mu0},
        "inputs": {"couplings_at_mu0": {"g1": g1_0, "g2": g2_0, "g3": g3_0}, "betas": {"b1": b1, "b2": b2, "b3": b3}},
        "scan": {"grid_N": N, "series": series[:50], "series_truncated": True},
        "best_unification": best,
        "tol_abs": tol_abs,
        "gating": cfg.get("gating", {}) or {},
        "notes": "Toy one-loop running unification within declared ΩI.",
    }
    return artifact

def check(artifact: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    locks: Dict[str, Dict[str, Any]] = {}
    diagnostic: List[str] = []

    # UD0: gating prerequisite
    gating = artifact.get("gating", {}) or {}
    if gating.get("passed", False) is not True:
        locks["UD0_GATING_4F"] = {"pass": False, "verdict": "NO-EVAL(UD0)", "note": "4F operational gating not satisfied"}
        diagnostic.append("4F gating not satisfied -> NO-EVAL(UD0)")
        return locks, diagnostic
    locks["UD0_GATING_4F"] = {"pass": True, "verdict": "PASS", "note": "4F gating satisfied"}

    best = artifact.get("best_unification", None)
    if not best:
        locks["UD1_UNIFICATION_FOUND"] = {"pass": False, "verdict": "NO-EVAL(UD1)", "note": "no valid scan point (NaNs)"}
        diagnostic.append("No valid scan point -> NO-EVAL(UD1)")
        return locks, diagnostic
    locks["UD1_UNIFICATION_FOUND"] = {"pass": True, "verdict": "PASS", "note": "scan produced a best point"}

    tol = float(artifact.get("tol_abs", 0.02))
    score = float(best.get("score", 1e9))
    if score <= tol:
        locks["UD2_WITHIN_TOL"] = {"pass": True, "verdict": "PASS", "note": f"max|Δg|={score:.3g} <= tol={tol:.3g} at mu={best['mu_GeV']:.3g} GeV"}
    else:
        locks["UD2_WITHIN_TOL"] = {"pass": False, "verdict": "FAIL(UD2)", "note": f"max|Δg|={score:.3g} > tol={tol:.3g} (best at mu={best['mu_GeV']:.3g} GeV)"}
        diagnostic.append("No unification within tolerance -> FAIL(UD2)")

    # UD3: ΩI consistency (mu within declared bounds, and unification scale declared)
    omg = artifact.get("omegaI", {}) or {}
    mu_min = float(omg.get("mu_min_GeV", 0.0))
    mu_max = float(omg.get("mu_max_GeV", 0.0))
    muU = float(best.get("mu_GeV", float("nan")))
    if not (muU == muU) or not (mu_min <= muU <= mu_max):
        locks["UD3_MU_WITHIN_OMEGAI"] = {"pass": False, "verdict": "NO-EVAL(UD3)", "note": "mu_U not within declared ΩI"}
        diagnostic.append("mu_U not within ΩI -> NO-EVAL(UD3)")
    else:
        locks["UD3_MU_WITHIN_OMEGAI"] = {"pass": True, "verdict": "PASS", "note": "mu_U within declared ΩI"}

    # UD4: stability under small perturbations (PCN-style) — optional
    stab = cfg.get("stability", {}) or {}
    eps = float(stab.get("eps_fraction", 0.01))
    if eps <= 0:
        locks["UD4_STABILITY_DECLARED"] = {"pass": False, "verdict": "NO-EVAL(UD4)", "note": "stability eps not positive"}
        diagnostic.append("stability eps invalid -> NO-EVAL(UD4)")
    else:
        locks["UD4_STABILITY_DECLARED"] = {"pass": True, "verdict": "PASS", "note": "stability eps declared"}
        # perturb g0 by ±eps and ensure verdict doesn't flip from PASS to FAIL if already PASS (soft check)
        base_pass = locks["UD2_WITHIN_TOL"]["pass"]
        if base_pass:
            g0 = artifact["inputs"]["couplings_at_mu0"]
            b = artifact["inputs"]["betas"]
            omg = artifact["omegaI"]
            uni = {"grid_N": int((cfg.get("unification",{}) or {}).get("grid_N", 200)), "tol_abs": tol}
            flips = False
            for sgn in (-1, +1):
                cfg2 = {
                    "omegaI": omg,
                    "couplings_at_mu0": {k: float(v)*(1.0+sgn*eps) for k,v in g0.items()},
                    "betas": b,
                    "unification": uni,
                    "gating": {"passed": True},
                }
                art2 = compile(cfg2)
                best2 = art2.get("best_unification", {}) or {}
                if not best2:
                    flips = True
                    break
                if float(best2.get("score", 1e9)) > tol:
                    flips = True
                    break
            if flips:
                locks["UD4_STABILITY"] = {"pass": False, "verdict": "FAIL(UD4)", "note": "PASS not stable under small perturbations"}
                diagnostic.append("Unification PASS unstable under perturbations -> FAIL(UD4)")
            else:
                locks["UD4_STABILITY"] = {"pass": True, "verdict": "PASS", "note": "PASS stable under small perturbations"}
        else:
            locks["UD4_STABILITY"] = {"pass": True, "verdict": "PASS", "note": "Base verdict not PASS; stability check not required"}

    return locks, diagnostic
