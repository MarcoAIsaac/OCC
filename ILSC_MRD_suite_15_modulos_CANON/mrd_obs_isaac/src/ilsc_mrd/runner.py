
import os, json, copy
from datetime import datetime
from typing import Dict, Any, Tuple
import numpy as np
import yaml
from .judges.certificates import load_cert, validate_pa, validate_rfs, validate_io

from .io_schema import validate_case, SchemaError
from .audit import sha256_json, env_fingerprint, versions
from .models.qubit_spinboson import QubitSpinBoson
from .models.ho_caldeira_leggett import HOCaldeiraLeggett
from .compile.kernels import make_lin_grid, build_kernels_from_spectra, retarded_time_kernel, noise_time_kernel
from .compile.map_builders import qubit_phase_damping_choi, ho_gaussian_channel_matrices
from .compile.projections import enforce_no_uv_reinject

from .checks.causality import check_causality
from .checks.psd_noise import check_psd_noise
from .checks.cptp_choi import check_choi_cptp
from .checks.cptp_gaussian import check_gaussian_cp
from .checks.fdt import check_fdt
from .checks.no_uv_reinject import check_no_uv_reinject
from .checks.pcn_pcd import pcn_sweep, pcd_sweep

from .report.report_json import write_json
from .report.report_pdf import write_pdf



def _apply_judge_certificates(cfg: Dict[str, Any], locks: Dict[str, Any], diagnostic: list) -> None:
    """Validate judge certificates (PA/RFS/IO) when provided.

    This is an audit-side check; it does not replace physics locks.
    Results are appended to diagnostic.
    """
    jc = cfg.get("judge_certs", {}) or {}
    if not jc:
        diagnostic.append({"judge_certs": {"verdict": "SKIP", "note": "no judge_certs provided"}})
        return
    repo_root = str(REPO_ROOT)
    data_obj = {"input_hash": sha256_json(cfg)}
    out = {}
    try:
        if (jc.get("PA", {}) or {}).get("enabled", False):
            cert = load_cert(str(REPO_ROOT / jc["PA"]["path"]))
            cv = validate_pa(cert, repo_root=repo_root, data_obj=data_obj)
            out["PA"] = {"verdict": cv.verdict, "note": cv.note}
        else:
            out["PA"] = {"verdict": "SKIP"}
        if (jc.get("RFS", {}) or {}).get("enabled", False):
            cert = load_cert(str(REPO_ROOT / jc["RFS"]["path"]))
            cv = validate_rfs(cert, repo_root=repo_root, data_obj=data_obj)
            out["RFS"] = {"verdict": cv.verdict, "note": cv.note}
        else:
            out["RFS"] = {"verdict": "SKIP"}
        if (jc.get("IO", {}) or {}).get("enabled", False):
            cert = load_cert(str(REPO_ROOT / jc["IO"]["path"]))
            cv = validate_io(cert)
            out["IO"] = {"verdict": cv.verdict, "note": cv.note}
        else:
            out["IO"] = {"verdict": "SKIP"}
    except Exception as e:
        out["verdict"] = "NO-EVAL"
        out["error"] = str(e)
    diagnostic.append({"judge_certs": out})
def _lin_grid(g: Dict[str, Any]) -> np.ndarray:
    return np.linspace(float(g["min"]), float(g["max"]), int(g["n"]), dtype=float)

def _make_time_with_negative(tpos: np.ndarray) -> np.ndarray:
    # mirror to negative times for causality check
    tneg = -tpos[::-1]
    return np.concatenate([tneg[:-1], tpos])

def run_case(cfg: Dict[str, Any], do_meta: bool=True) -> Dict[str, Any]:
    validate_case(cfg)

    input_sha = sha256_json(cfg)
    tol = cfg["numerics"]["tolerances"]
    eps_causal = float(tol["eps_causal"])
    eps_psd = float(tol["eps_psd"])
    eps_cptp = float(tol["eps_cptp"])
    eps_fdt = float(tol["eps_fdt"])
    eps_trace = float(tol["eps_trace"])

    omega = _lin_grid(cfg["numerics"]["grid"]["omega_grid"])
    tpos = _lin_grid(cfg["numerics"]["grid"]["time_grid"])
    t = _make_time_with_negative(tpos)

    model_type = cfg["model"]["type"]
    locks = {}
    diagnostic = []

    _apply_judge_certificates(cfg, locks, diagnostic)

    # Build spectra and kernels
    if model_type == "qubit_spinboson":
        model = QubitSpinBoson.from_cfg(cfg["model"])
        J = model.spectral_density(omega)
        Nw = model.noise_spectrum(omega)

        # engineered injections
        injN = cfg.get("compile", {}).get("inject_nonphysical_noise", {})
        if injN.get("enabled", False):
            # Guarantee PSD violation: enforce a negative patch in N(ω).
            c = float(injN.get("dip_center", 5.0))
            w = float(injN.get("dip_width", 0.5))
            depth = float(injN.get("dip_depth", -0.02))
            g = np.exp(-0.5*((omega-c)/max(w,1e-9))**2)
            scale = max(float(np.max(Nw)), 1e-12)
            # Make the dip go below zero by a margin proportional to |depth|.
            Nw = Nw - (abs(depth)+0.5)*scale*g
            # Ensure at least one point is strictly negative:
            idx = int(np.argmax(g))
            Nw[idx] = -abs(depth)*scale


        injG = cfg.get("compile", {}).get("inject_grid_aliasing", {})
        if injG.get("enabled", False):
            # Introduce a grid-step-dependent artifact to demonstrate PCN instability (MRD NO-EVAL demo).
            # This is *not* physics; it tests that the pipeline correctly downgrades unstable inference.
            domega = float(omega[1]-omega[0]) if len(omega)>1 else 1.0
            amp = float(injG.get("amplitude", 0.02))
            shape = np.sin(np.pi*omega/max(float(np.max(omega)),1e-9))
            Nw = Nw + amp*domega*shape
        kernels = build_kernels_from_spectra(omega, J, Nw)
        D_R = retarded_time_kernel(omega, J, t)
        N_t = noise_time_kernel(omega, Nw, t)

        # checks
        locks["SK_causality"] = check_causality(t, D_R, eps_causal)
        locks["SK_psd_noise"] = check_psd_noise(Nw, eps_psd)
        # CPTP via phase damping channel at target time (choose t= time_max/10)
        t_target = float(cfg["isaac_omegaI"]["omega_window"]["time_max"])*0.1
        lam = model.channel_parameter(t_target)
        C = qubit_phase_damping_choi(lam)

        injC = cfg.get("compile", {}).get("inject_non_cptp_map", {})
        if injC.get("enabled", False):
            # perturb to create a negative eigenvalue
            C = C.copy()
            C[0,0] -= 0.02  # small but can break PSD
            C = (C + C.T)/2.0

        locks["SK_cptp"] = check_choi_cptp(C, eps_cptp, eps_trace)

        eq = cfg["checks"].get("equilibrium", {})
        if bool(eq.get("declared", False)):
            T = float(eq.get("temperature", model.temperature))
            # break FDT injection
            bf = cfg.get("compile", {}).get("break_fdt", {})
            if bf.get("enabled", False):
                T_eff = float(bf.get("effective_temperature_used", T*2))
                # overwrite Nw to violate target of declared T
                # regenerate noise at different temperature
                beta = 1.0/max(T_eff,1e-12)
                x = 0.5*beta*np.maximum(omega,1e-12)
                # use coth from fdt module indirectly by formula approximation
                Nw = 0.5*J*(np.cosh(x)/np.sinh(x))
                kernels["Nw"] = Nw
            locks["SK_fdt_if_equilibrium"] = check_fdt(omega, J, kernels["Nw"], T, eps_fdt)
        else:
            locks["SK_fdt_if_equilibrium"] = {"pass": True, "note": "not declared"}

    elif model_type == "ho_caldeira_leggett":
        model = HOCaldeiraLeggett.from_cfg(cfg["model"])
        J = model.spectral_density(omega)
        Nw = model.noise_spectrum(omega)

        # break FDT injection
        bf = cfg.get("compile", {}).get("break_fdt", {})
        if bf.get("enabled", False):
            T_eff = float(bf.get("effective_temperature_used", model.temperature*2 if model.temperature>0 else 1.0))
            beta = 1.0/max(T_eff,1e-12)
            x = 0.5*beta*np.maximum(omega,1e-12)
            Nw = 0.5*J*(np.cosh(x)/np.sinh(x))

        kernels = build_kernels_from_spectra(omega, J, Nw)

        # Construct retarded response (causal by construction) then inject acausal part if requested
        D_R = retarded_time_kernel(omega, J, t)
        injA = cfg.get("compile", {}).get("inject_acausal_response", {})
        if injA.get("enabled", False):
            amp = float(injA.get("amplitude", 1e-3))
            # add small constant on negative times
            D_R = D_R.copy()
            D_R[t<0] = D_R[t<0] + amp

        locks["SK_causality"] = check_causality(t, D_R, eps_causal)
        locks["SK_psd_noise"] = check_psd_noise(Nw, eps_psd)

        # CPTP via Gaussian CP condition at target time
        t_target = float(cfg["isaac_omegaI"]["omega_window"]["time_max"])*0.1
        mats = ho_gaussian_channel_matrices(model.gamma, t_target, model.temperature)
        locks["SK_cptp"] = check_gaussian_cp(mats["X"], mats["Y"], eps_cptp)

        eq = cfg["checks"].get("equilibrium", {})
        if bool(eq.get("declared", False)):
            Tdecl = float(eq.get("temperature", model.temperature))
            locks["SK_fdt_if_equilibrium"] = check_fdt(omega, J, Nw, Tdecl, eps_fdt)
        else:
            locks["SK_fdt_if_equilibrium"] = {"pass": True, "note": "not declared"}
    else:
        raise SchemaError(f"Unsupported model.type: {model_type}")

    # ISAAC / UV reinjection
    proj = enforce_no_uv_reinject(cfg)
    locks["SK_no_uv_reinject"] = check_no_uv_reinject(proj)

    # Determine verdict
    # Priority:
    # 1) Any failing lock with severity NO-EVAL -> NO-EVAL(reason)
    # 2) Otherwise first failing lock -> FAIL(lock)
    failed = []
    noeval = []
    for k, v in locks.items():
        if isinstance(v, dict) and (not v.get("pass", False)):
            sev = v.get("severity", "FAIL")
            if sev == "NO-EVAL":
                noeval.append(k)
            else:
                failed.append(k)

    verdict = "PASS"
    if noeval:
        verdict = f"NO-EVAL({noeval[0]})"
        diagnostic.append(f"First NO-EVAL lock: {noeval[0]}")
    elif failed:
        verdict = f"FAIL({failed[0]})"
        diagnostic.append(f"First failing lock: {failed[0]}")
# Meta stability sweeps (PCN/PCD) can downgrade to NO-EVAL
    if do_meta:
        def run_once(cfg2):
            return run_case(cfg2, do_meta=False)
        pcn = cfg["numerics"].get("pcn", {})
        ref = pcn.get("refinements", [])
        locks["PCN_stability"] = pcn_sweep(cfg, ref, run_once)
        locks["PCD_stability"] = pcd_sweep(cfg, run_once)
        pcn = locks["PCN_stability"]
        pcd = locks["PCD_stability"]
        unstable = bool(pcn.get("flip", False) or (len(pcn.get("skipped", []))>0) or pcd.get("flip", False))
        inconclusive = (not pcn.get("pass", False)) or (not pcd.get("pass", False))
        if verdict.startswith("NO-EVAL"):
            pass
        elif unstable:
            verdict = "NO-EVAL(unstable_under_PCN_or_PCD)"
            diagnostic.append("Verdict downgraded to NO-EVAL due to stability flip under PCN/PCD sweeps.")
        elif verdict == "PASS" and inconclusive:
            verdict = "NO-EVAL(insufficient_PCN_or_PCD_coverage)"
            diagnostic.append("Verdict downgraded to NO-EVAL due to insufficient PCN/PCD coverage (work cap or missing sweeps).")

    # Compose result
    case_id = cfg["mrd"]["id"]
    result = {
        "case_id": case_id,
        "verdict": verdict,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "input_sha256": input_sha,
        "env": env_fingerprint(),
        "versions": versions(),
        "locks": locks,
        "diagnostic": " ".join(diagnostic) if diagnostic else "(none)"
    }
    return result

def main():
    import argparse
    ap = argparse.ArgumentParser(prog="ilsc-mrd", description="ILSC MRD-1X (SK) runner")
    ap.add_argument("input_yaml", help="Path to YAML case file")
    ap.add_argument("--outdir", default="outputs", help="Output directory (relative to repo root)")
    args = ap.parse_args()

    # Load YAML
    with open(args.input_yaml, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    res = run_case(cfg, do_meta=True)

    # Output
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    outdir = os.path.join(repo_root, args.outdir, res["case_id"])
    os.makedirs(outdir, exist_ok=True)

    write_json(os.path.join(outdir, "result.json"), res)
    write_pdf(os.path.join(outdir, "report.pdf"), res)

    print(res["verdict"])
