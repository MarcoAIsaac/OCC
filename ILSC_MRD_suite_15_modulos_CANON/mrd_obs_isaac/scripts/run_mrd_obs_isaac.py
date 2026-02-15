#!/usr/bin/env python3
"""MRD — Observabilidad/Instrumentación ISAAC (Executable).

Usage:
  python scripts/run_mrd_obs_isaac.py <inputs/mrd_obs_isaac/*.yaml>

Writes:
  outputs/<input_stem>.report.json
"""

import sys
import pathlib
import json
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ilsc_mrd.audit import sha256_file
from ilsc_mrd.judges.certificates import load_cert, validate_io, validate_rfs
from ilsc_mrd.modules import observability_isaac


def _resolve(p: str) -> str:
    pp = pathlib.Path(p)
    if pp.is_absolute():
        return str(pp)
    return str((REPO_ROOT / pp).resolve())

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
        print("Usage: python scripts/run_mrd_obs_isaac.py <inputs/mrd_obs_isaac/*.yaml>")
        raise SystemExit(2)

    yml = pathlib.Path(sys.argv[1])
    cfg = yaml.safe_load(yml.read_text(encoding="utf-8"))

    ds = cfg.get("dataset") or {}
    # Minimal dataset hashes if provided; this MRD can run without external datasets.
    dataset_hashes = {}
    if "meta_path" in ds:
        dataset_hashes["meta"] = "sha256:" + sha256_file(_resolve(ds["meta_path"]))

    artifact = observability_isaac.compile(cfg)
    locks, diagnostic = observability_isaac.check(artifact, cfg)

    jc = cfg.get("judge_certs", {}) or {}
    certs = {}
    if jc.get("IO", {}).get("enabled", False):
        certs["IO"] = validate_io(load_cert(_resolve(jc["IO"]["path"]))).__dict__
    if jc.get("RFS", {}).get("enabled", False):
        certs["RFS"] = validate_rfs(load_cert(_resolve(jc["RFS"]["path"])), repo_root=str(REPO_ROOT), data_obj={"case": cfg.get("case", {}), "artifact": artifact}).__dict__

    final_verdict, first_reason = compute_final_verdict(locks, certs)


    report = {
        "module": "OBS_ISAAC",
        "verdict": final_verdict,
        "first_reason": first_reason,
        "artifact": artifact,
        "locks": locks,
        "diagnostic": diagnostic,
        "certificates": certs,
        "dataset_hashes": dataset_hashes,
    }

    outdir = REPO_ROOT / "outputs"
    outdir.mkdir(exist_ok=True)
    outpath = outdir / f"{yml.stem}.report.json"
    outpath.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote: {outpath}")


if __name__ == "__main__":
    main()
