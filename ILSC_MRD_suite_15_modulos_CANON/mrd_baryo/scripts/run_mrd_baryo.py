#!/usr/bin/env python3
"""MRD — Bariogénesis (Umbrella EWBG/Leptogénesis) (Executable)."""
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
from ilsc_mrd.judges.certificates import load_cert, validate_rfs, validate_io, validate_pa
from ilsc_mrd.modules import baryo
from ilsc_mrd.utils.data_baryo import load_baryo_obs

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
        print("Usage: python scripts/run_mrd_baryo.py <inputs/mrd_baryo/*.yaml>")
        raise SystemExit(2)
    yml = pathlib.Path(sys.argv[1])
    cfg = yaml.safe_load(yml.read_text(encoding="utf-8"))

    ds = cfg.get("dataset") or {}
    ob = load_baryo_obs(_resolve(ds["csv_path"]), _resolve(ds["meta_path"]))
    cfg["obs"] = ob.row

    data_obj = {
        "case": cfg.get("case",{}),
        "mode": cfg.get("mode"),
        "params": cfg.get("params",{}),
        "constants": cfg.get("constants",{}),
        "tolerances": cfg.get("tolerances",{}),
        "obs": cfg.get("obs",{}),
        "dataset_id": ob.dataset_id,
        "dataset_hashes": {
            "csv": "sha256:" + sha256_file(_resolve(ds["csv_path"])),
            "meta": "sha256:" + sha256_file(_resolve(ds["meta_path"])),
        }
    }
    repo_root = str(REPO_ROOT)

    artifact = baryo.compile(cfg)
    locks, diag = baryo.check(artifact, cfg)

    jc = cfg.get("judge_certs",{}) or {}
    cert_out = {}
    if (jc.get("PA",{}) or {}).get("enabled", False):
        cert = load_cert(_resolve(jc["PA"]["path"]))
        cv = validate_pa(cert, repo_root=repo_root, data_obj=data_obj)
        cert_out["PA"] = {"verdict": cv.verdict, "note": cv.note, "cert": cert}
    else:
        cert_out["PA"] = {"verdict":"SKIP","note":"not enabled"}
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
        "artifact": artifact,
        "locks": locks,
        "diagnostic": diag,
        "verdict": final_verdict,
        "first_reason": first_reason,
        "certificates": cert_out,
    }
    outdir = pathlib.Path("outputs"); outdir.mkdir(exist_ok=True)
    out = outdir / (yml.stem + ".report.json")
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Wrote:", out)

if __name__ == "__main__":
    main()
