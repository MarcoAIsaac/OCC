#!/usr/bin/env python3
"""MRD — 4F Dictionary (CUI/HUI) Executable."""
import sys, pathlib
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
import json, pathlib, sys
import yaml

def _resolve(p: str) -> str:
    """Resolve a repo-relative path against REPO_ROOT."""
    pp = pathlib.Path(p)
    if pp.is_absolute():
        return str(pp)
    return str(REPO_ROOT / pp)
from ilsc_mrd.audit import sha256_file
from ilsc_mrd.judges.certificates import load_cert, validate_rfs, validate_io
from ilsc_mrd.modules import fourf_dict
from ilsc_mrd.utils.data_4f import load_4f_spec

def compute_final_verdict(locks: dict, certificates: dict):
    """Return (verdict, first_reason). Verdict is PASS / FAIL(<LOCK>) / NO-EVAL(<LOCK>)."""
    # Certificates gate
    if certificates:
        for k, v in certificates.items():
            if not isinstance(v, dict):
                continue
            cv = v.get('verdict')
            if isinstance(cv, str) and (cv.startswith('NO-EVAL') or cv.startswith('FAIL')):
                reason = f"CERTS_{k}"
                if isinstance(cv, str) and cv.startswith('NO-EVAL'):
                    return (f"NO-EVAL({reason})", reason)
                return (f"FAIL({reason})", reason)
    # Locks
    for k, v in locks.items():
        if isinstance(v, dict) and (not v.get('pass', False)):
            lv = v.get('verdict','FAIL')
            if isinstance(lv, str) and lv.startswith('NO-EVAL'):
                return (f"NO-EVAL({k})", k)
            return (f"FAIL({k})", k)
    return ('PASS','')


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_mrd_4f_dict.py <inputs/mrd_4f_dict/*.yaml>")
        raise SystemExit(2)
    yml = pathlib.Path(sys.argv[1])
    cfg = yaml.safe_load(yml.read_text(encoding="utf-8"))

    ds = cfg.get("dataset") or {}
    if ("csv_path" not in ds) or ("meta_path" not in ds):
        artifact = {"module":"4F_DICT","verdict":"NO-EVAL"}
        locks = {"4D3_DATASET": {"pass": False, "verdict": "NO-EVAL", "note": "missing dataset (csv_path/meta_path)"}}
        diag = ["Dataset not provided; cannot validate 4F dictionary spec."]
        data_obj = {"case": cfg.get("case",{}), "dataset_hashes": {}}
        repo_root = str(REPO_ROOT)
    else:
        spec = load_4f_spec(_resolve(ds["csv_path"]), _resolve(ds["meta_path"]))
    
        # build dict section from dataset unless overridden
        cfg.setdefault("dict", {})
        cfg["dict"]["group"] = "SU2"
        cfg["dict"]["paths"] = spec.paths
        cfg["dict"]["loops"] = spec.loops
        cfg["dict"]["observables"] = spec.observables
        
        data_obj = {
            "case": cfg.get("case",{}),
            "dict": cfg.get("dict",{}),
            "tolerances": cfg.get("tolerances",{}),
            "dataset_id": spec.dataset_id,
            "dataset_hashes": {
                "csv": "sha256:" + sha256_file(_resolve(ds["csv_path"])),
                "meta": "sha256:" + sha256_file(_resolve(ds["meta_path"])),
            }
        }
        repo_root = str(pathlib.Path(__file__).resolve().parents[1])
    
        artifact = fourf_dict.compile(cfg)
        locks, diag = fourf_dict.check(artifact, cfg)
    
    jc = cfg.get("judge_certs",{}) or {}
    cert_out = {}

    if (jc.get("RFS",{}) or {}).get("enabled", False):
        cert = load_cert(_resolve(jc["RFS"]["path"]))
        cv = validate_rfs(cert, repo_root=repo_root, data_obj=data_obj)
        cert_out["RFS"] = {"verdict": cv.verdict, "note": cv.note, "cert": cert}
    else:
        cert_out["RFS"] = {"verdict":"SKIP","note":"not enabled"}

    if (jc.get("IO",{}) or {}).get("enabled", False):
        cert = load_cert(_resolve(jc["IO"]["path"]))
        cv = validate_io(cert)
        cert_out["IO"] = {"verdict": cv.verdict, "note": cv.note, "cert": cert}
    else:
        cert_out["IO"] = {"verdict":"SKIP","note":"not enabled"}

    final_verdict, first_reason = compute_final_verdict(locks, cert_out)


    report = {
        "input": str(yml),
        "artifact": {
            "observables": artifact.get("dictionary",{}).get("observables",{}),
            "rules": artifact.get("dictionary",{}).get("rules",[]),
        },
        "locks": locks,
        "diagnostic": diag,
        "verdict": final_verdict,
        "first_reason": first_reason,
        "certificates": cert_out,
    }
    outdir = REPO_ROOT / "outputs"
    outdir.mkdir(exist_ok=True)
    out = outdir / (yml.stem + ".report.json")
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Wrote:", out)

if __name__ == "__main__":
    main()
