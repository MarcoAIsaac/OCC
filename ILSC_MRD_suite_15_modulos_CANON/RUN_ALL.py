#!/usr/bin/env python3
import argparse, subprocess, json, time
from pathlib import Path

from jsonschema import Draft202012Validator

def first(lst):
    return lst[0] if lst else None

def find_script(mod: Path):
    return first(sorted((mod/'scripts').glob('run_*.py'))) or first(sorted((mod/'scripts').glob('*.py')))

def pick_kind(ymls, kind):
    kind=kind.lower()
    for p in ymls:
        if p.name.lower().startswith(kind):
            return p
    for p in ymls:
        if kind in p.stem.lower():
            return p
    return None

def pick_inputs(mod: Path):
    base=mod/'inputs'
    spec=base/mod.name
    if spec.exists():
        ymls=sorted(spec.glob('*.yaml'))
    else:
        # legacy fallback
        ymls=sorted(base.rglob('*.yaml'))
    return {
        'pass': pick_kind(ymls,'pass'),
        'fail': pick_kind(ymls,'fail'),
        'noeval': pick_kind(ymls,'noeval') or pick_kind(ymls,'no-eval') or pick_kind(ymls,'no_eval'),
    }

def newest_json(mod: Path):
    out=mod/'outputs'
    if not out.exists():
        return None
    cand=sorted(out.rglob('*.report.json'), key=lambda p:p.stat().st_mtime, reverse=True)
    if cand: return cand[0]
    cand=sorted(out.rglob('result.json'), key=lambda p:p.stat().st_mtime, reverse=True)
    if cand: return cand[0]
    return None

def read_verdict(p: Path):
    j=json.loads(p.read_text(encoding='utf-8'))
    return j.get('verdict')

def expected_prefix(kind: str):
    if kind=='pass': return 'PASS'
    if kind=='fail': return 'FAIL'
    if kind=='noeval': return 'NO-EVAL'
    return None

def load_schema(checkers_root: Path, cert_type: str) -> dict:
    schemas = {
        "PA-CERT": "schemas/pa_cert.schema.json",
        "IO-CERT": "schemas/io_cert.schema.json",
        "RFS-CERT": "schemas/rfs_cert.schema.json",
    }
    p = checkers_root / schemas[cert_type]
    return json.loads(p.read_text(encoding='utf-8'))

def validate_cert_schema(checkers_root: Path, cert_path: Path) -> list[str]:
    cert = json.loads(cert_path.read_text(encoding='utf-8'))
    ctype = cert.get('cert_type')
    if ctype not in ("PA-CERT","IO-CERT","RFS-CERT"):
        return []  # ignore unknown
    schema = load_schema(checkers_root, ctype)
    v = Draft202012Validator(schema)
    errs = sorted(v.iter_errors(cert), key=lambda e: list(e.path))
    out=[]
    for e in errs[:8]:
        p = ".".join(str(x) for x in e.path) or "<root>"
        out.append(f"{p}: {e.message}")
    if len(errs) > 8:
        out.append(f"... (+{len(errs)-8} more)")
    return out

def validate_module_certs(checkers_root: Path, mod: Path) -> dict:
    certs_dir = mod/'certs'
    res = {"ok": True, "checked": 0, "errors": {}}
    if not certs_dir.exists():
        return res
    for p in sorted(certs_dir.glob("*.json")):
        try:
            errs = validate_cert_schema(checkers_root, p)
        except Exception as e:
            res["ok"] = False
            res["errors"][p.name] = [f"Exception while validating: {e}"]
            continue
        if errs:
            res["ok"] = False
            res["errors"][p.name] = errs
        res["checked"] += 1
    return res

def run_one(mod: Path, script: Path, inp: Path, timeout:int):
    t0=time.time()
    try:
        script_arg = str(script.relative_to(mod))
    except Exception:
        script_arg = str(script.resolve())
    try:
        inp_arg = str(inp.relative_to(mod))
    except Exception:
        inp_arg = str(inp.resolve())

    proc=subprocess.run(['python', script_arg, inp_arg], cwd=mod, capture_output=True, text=True, timeout=timeout)
    dt=round(time.time()-t0,3)

    cand = mod/'outputs'/(inp.stem + '.report.json')
    rj = cand if cand.exists() else newest_json(mod)
    verdict=read_verdict(rj) if rj else None

    return {
        'input': str(inp.relative_to(mod)),
        'rc': proc.returncode,
        'seconds': dt,
        'verdict': verdict,
        'report': str(rj.relative_to(mod)) if rj else None,
        'stdout_tail': proc.stdout[-200:],
        'stderr_tail': proc.stderr[-200:],
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--summary', required=True)
    ap.add_argument('--timeout', type=int, default=180)
    ap.add_argument('--strict', action='store_true', help="Nonzero exit if any expectation fails")
    args=ap.parse_args()

    root=Path(args.root).resolve()
    checkers_root = (root/'ILSC_jueces_checkers_v1').resolve()
    if not checkers_root.exists():
        raise SystemExit("Missing ILSC_jueces_checkers_v1 in suite root")

    mods=sorted([p for p in root.iterdir() if p.is_dir() and p.name.startswith('mrd_')])

    out={}
    ok_all = True

    for m in mods:
        script=find_script(m)
        if not script:
            out[m.name]={'error':'missing script'}
            ok_all = False
            continue

        cert_check = validate_module_certs(checkers_root, m)

        inputs=pick_inputs(m)
        res={'cert_schema': cert_check, 'cases': {}}

        if not cert_check["ok"]:
            # do not run module if certs are invalid in strict mode
            res['error'] = 'CERT_SCHEMA_INVALID'
            ok_all = False
        else:
            for kind,inp in inputs.items():
                if not inp:
                    continue
                r = run_one(m, script, inp, args.timeout)
                pref = expected_prefix(kind)
                exp_ok = (r['verdict'] or '').startswith(pref) if pref else True
                r['expected_prefix'] = pref
                r['expectation_ok'] = exp_ok
                if not exp_ok:
                    ok_all = False
                res['cases'][kind] = r

        out[m.name]=res

    Path(args.summary).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')

    if args.strict and (not ok_all):
        raise SystemExit(1)

if __name__=='__main__':
    main()
