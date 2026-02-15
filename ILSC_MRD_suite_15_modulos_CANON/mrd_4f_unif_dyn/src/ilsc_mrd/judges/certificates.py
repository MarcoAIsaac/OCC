from __future__ import annotations
import json
import pathlib
from jsonschema import Draft202012Validator

_SCHEMA_FILES = {
    "PA-CERT": "pa_cert.schema.json",
    "IO-CERT": "io_cert.schema.json",
    "RFS-CERT": "rfs_cert.schema.json",
}

def _schema_error(cert: Dict[str, Any]) -> "Optional[str]":
    """Return a compact schema error string, or None if valid."""
    ctype = cert.get("cert_type")
    if ctype not in _SCHEMA_FILES:
        return f"Unknown cert_type: {ctype}"
    base = pathlib.Path(__file__).resolve().parent / "schemas"
    schema_path = base / _SCHEMA_FILES[ctype]
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except Exception as e:
        return f"Cannot load schema for {ctype}: {e}"
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(cert), key=lambda e: list(e.path))
    if not errors:
        return None
    parts = []
    for e in errors[:5]:
        p = ".".join(str(x) for x in e.path)
        parts.append(f"{p or '<root>'}: {e.message}")
    extra = "" if len(errors) <= 5 else f" (+{len(errors)-5} more)"
    return "; ".join(parts) + extra

from dataclasses import dataclass
from typing import Any, Dict, List
from ilsc_mrd.audit import env_hash, tree_hash, sha256_json, now_utc_iso

PA_REQUIRED = ["cert_type","cert_version","projection_version","Pi_signature","assumptions",
               "delta_proj_method","delta_proj","kappa_rule","hashes","seeds","run_log","sigma_data"]
IO_REQUIRED = ["cert_type","cert_version","map_O_theta","theta_effective_list","observables_list",
               "identifiability_metric","threshold_tau","degeneracies_list","dataset_equivalence"]
RFS_REQUIRED = ["cert_type","cert_version","resource_budget","isaac_link","pcn_sweep","pcd_sweep","idealizations","audit_hashes"]

@dataclass
class CertVerdict:
    verdict: str
    note: str

def _missing(cert: Dict[str, Any], required: List[str]) -> List[str]:
    return [k for k in required if k not in cert]

def load_cert(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _ensure_runlog(cert: Dict[str, Any]) -> None:
    rl = cert.get("run_log") or {}
    rl.setdefault("validated_at_utc", now_utc_iso())
    cert["run_log"] = rl

def _compute_code_hash(repo_root: str) -> str:
    return "sha256:" + tree_hash(repo_root)["tree_sha256"]

def _compute_data_hash(obj: Any) -> str:
    return "sha256:" + sha256_json(obj)

def _check_or_fill_hash(field: str, current: str, expected: str) -> str:
    # If current is AUTO or placeholder, replace. Otherwise compare.
    if not current or current.strip().upper() == "AUTO" or current.startswith("sha256:..."):
        return expected
    if current != expected:
        raise ValueError(f"{field} mismatch: cert has {current}, expected {expected}")
    return current

def validate_pa(cert: Dict[str, Any], *, repo_root: str, data_obj: Any) -> CertVerdict:
    miss = _missing(cert, PA_REQUIRED)
    if miss:
        return CertVerdict("NO-EVAL(PA1)", f"Missing required fields: {', '.join(miss)}")
    if cert.get("cert_type") != "PA-CERT":
        return CertVerdict("NO-EVAL(PA1)", "cert_type must be PA-CERT")
    _ensure_runlog(cert)

    # PA5: hashes (code/data) should be present and match, allow AUTO
    try:
        hashes = cert.get("hashes", {})
        expected_code = _compute_code_hash(repo_root)
        expected_data = _compute_data_hash(data_obj)
        hashes["code"] = _check_or_fill_hash("hashes.code", hashes.get("code",""), expected_code)
        hashes["data"] = _check_or_fill_hash("hashes.data", hashes.get("data",""), expected_data)
        cert["hashes"] = hashes
    except Exception as e:
        return CertVerdict("NO-EVAL(PA5)", f"Hash audit failed: {e}")

    # PA3: dominance check
    try:
        deltas = list(cert["delta_proj"]["delta"])
        kappa = float(cert["kappa_rule"]["kappa"])
        sigma = float(cert["sigma_data"]["sigma"])
        if max(deltas) >= kappa * sigma:
            return CertVerdict("NO-EVAL(PA3)", "Projection error dominates data uncertainty")
    except Exception as e:
        return CertVerdict("NO-EVAL(PA2)", f"Projection error bound not usable: {e}")
    return CertVerdict("PASS(PA)", "PA certificate checks passed (incl. PA5)")

def validate_io(cert: Dict[str, Any]) -> CertVerdict:
    miss = _missing(cert, IO_REQUIRED)
    if miss:
        return CertVerdict("NO-EVAL(IO1)", f"Missing required fields: {', '.join(miss)}")
    if cert.get("cert_type") != "IO-CERT":
        return CertVerdict("NO-EVAL(IO1)", "cert_type must be IO-CERT")
    try:
        v = float(cert["identifiability_metric"]["value"])
        tau = float(cert["threshold_tau"])
        if v < tau:
            return CertVerdict("NO-EVAL(IO3)", "Identifiability metric below threshold")
    except Exception as e:
        return CertVerdict("NO-EVAL(IO1)", f"Identifiability metric not usable: {e}")
    return CertVerdict("PASS(IO)", "IO certificate checks passed")

def validate_rfs(cert: Dict[str, Any], *, repo_root: str, data_obj: Any) -> CertVerdict:
    miss = _missing(cert, RFS_REQUIRED)
    if miss:
        return CertVerdict("NO-EVAL(RFS1)", f"Missing required fields: {', '.join(miss)}")
    if cert.get("cert_type") != "RFS-CERT":
        return CertVerdict("NO-EVAL(RFS1)", "cert_type must be RFS-CERT")

    # RFS5: end-to-end audit hashes (code/data/env) allow AUTO
    try:
        ah = cert.get("audit_hashes", {})
        expected_code = _compute_code_hash(repo_root)
        expected_data = _compute_data_hash(data_obj)
        expected_env  = "sha256:" + env_hash()
        ah["code"] = _check_or_fill_hash("audit_hashes.code", ah.get("code",""), expected_code)
        ah["data"] = _check_or_fill_hash("audit_hashes.data", ah.get("data",""), expected_data)
        ah["env"]  = _check_or_fill_hash("audit_hashes.env",  ah.get("env",""),  expected_env)
        cert["audit_hashes"] = ah
    except Exception as e:
        return CertVerdict("NO-EVAL(RFS5)", f"End-to-end audit failed: {e}")

    if cert.get("pcn_sweep", {}).get("enabled", False) and cert.get("pcn_sweep", {}).get("flips", False):
        return CertVerdict("NO-EVAL(RFS2)", "Verdict flips under PCN sweep")
    if cert.get("pcd_sweep", {}).get("enabled", False) and cert.get("pcd_sweep", {}).get("flips", False):
        return CertVerdict("NO-EVAL(RFS3)", "Verdict flips under PCD sweep")
    return CertVerdict("PASS(RFS)", "RFS certificate checks passed (incl. RFS5)")