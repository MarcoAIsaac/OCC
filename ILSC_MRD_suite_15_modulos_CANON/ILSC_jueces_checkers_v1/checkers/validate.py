import json, sys, pathlib
from jsonschema import Draft202012Validator

SCHEMAS = {
  "PA-CERT": "schemas/pa_cert.schema.json",
  "IO-CERT": "schemas/io_cert.schema.json",
  "RFS-CERT": "schemas/rfs_cert.schema.json",
}

def load_schema(base: pathlib.Path, cert_type: str):
    p = base / SCHEMAS[cert_type]
    return json.loads(p.read_text(encoding="utf-8"))

def verdict_pa(cert: dict):
    # PA3 dominance: if max(delta_proj) >= kappa*sigma_data -> NO-EVAL(PA3)
    try:
        deltas = cert["delta_proj"]["delta"]
        kappa = float(cert["kappa_rule"]["kappa"])
        sigma = float(cert["sigma_data"]["sigma"])
        if max(deltas) >= kappa * sigma:
            return ("NO-EVAL(PA3)", "Projection error dominates data uncertainty")
    except Exception:
        return ("NO-EVAL(PA2)", "Projection error bound not usable")
    return ("PASS(PA)", "PA locks satisfied (basic)")

def verdict_io(cert: dict):
    try:
        v = float(cert["identifiability_metric"]["value"])
        tau = float(cert["threshold_tau"])
        if v < tau:
            return ("NO-EVAL(IO3)", "Identifiability metric below threshold")
    except Exception:
        return ("NO-EVAL(IO1)", "Identifiability metric not usable")
    return ("PASS(IO)", "IO locks satisfied (basic)")

def verdict_rfs(cert: dict):
    if cert.get("pcn_sweep", {}).get("enabled", False) and cert.get("pcn_sweep", {}).get("flips", False):
        return ("NO-EVAL(RFS2)", "Verdict flips under PCN sweep")
    if cert.get("pcd_sweep", {}).get("enabled", False) and cert.get("pcd_sweep", {}).get("flips", False):
        return ("NO-EVAL(RFS3)", "Verdict flips under PCD sweep")
    return ("PASS(RFS)", "RFS locks satisfied (basic)")

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m checkers.validate <cert.json>")
        raise SystemExit(2)
    cert_path = pathlib.Path(sys.argv[1])
    base = pathlib.Path(__file__).resolve().parents[1]
    cert = json.loads(cert_path.read_text(encoding="utf-8"))
    ctype = cert.get("cert_type")
    if ctype not in SCHEMAS:
        print("Unknown cert_type. Expected one of:", ", ".join(SCHEMAS.keys()))
        raise SystemExit(2)
    schema = load_schema(base, ctype)
    v = Draft202012Validator(schema)
    errors = sorted(v.iter_errors(cert), key=lambda e: e.path)
    if errors:
        print("SCHEMA FAIL -> NO-EVAL")
        for e in errors[:20]:
            print("-", "/".join(map(str,e.path)), ":", e.message)
        raise SystemExit(1)
    if ctype == "PA-CERT":
        verdict, note = verdict_pa(cert)
    elif ctype == "IO-CERT":
        verdict, note = verdict_io(cert)
    else:
        verdict, note = verdict_rfs(cert)
    print("SCHEMA PASS")
    print("VERDICT:", verdict)
    print("NOTE:", note)

if __name__ == "__main__":
    main()
