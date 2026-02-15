# MRD-1X-SK — Judge Certificates Integration (v2)

This MRD now supports optional **judge certificates** for:
- J1: PA (Auditable Projection)
- J2: IO (Operational Identifiability)
- J3: RFS (Finite Resources & Stability)

## How to use
Add to your YAML case:

judge_certs:
  PA:  { enabled: true, path: "/mnt/data/ILSC-MRD-1X-SK_exec_v2/certs/pa_cert_example.json" }
  IO:  { enabled: true, path: "/mnt/data/ILSC-MRD-1X-SK_exec_v2/certs/io_cert_example.json" }
  RFS: { enabled: true, path: "/mnt/data/ILSC-MRD-1X-SK_exec_v2/certs/rfs_cert_example.json" }

If a certificate is enabled and fails validation, the run will be **downgraded** with a diagnostic entry.
If not enabled, it is skipped (does not affect PASS/FAIL/NO-EVAL).

Certificates examples live in `certs/`.


## PA5 / RFS5 hardening
Certificates may set hashes to `AUTO`. The runner will compute and fill:
- code tree hash
- data object hash (cfg subset)
- env hash (for RFS)
If a non-AUTO hash is provided, it must match or the run downgrades to NO-EVAL.
