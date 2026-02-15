# MRD — Rama efectiva / Decoherencia / Objetividad (Ejecutable) / Effective Branching (Executable)

Locks:
- RE0 pointer basis declared (NO-EVAL)
- RE1 decoherence fast enough (FAIL)
- RE2 stability (FAIL)
- RE3 redundancy >= R_min (FAIL)
- RE4 no-backflow policy (FAIL)

Dataset:
- `data/mrd_rama_ef_times_v1.csv`
- `data/mrd_rama_ef_times_v1.meta.json`

Run:
```bash
python scripts/run_mrd_rama_ef.py inputs/mrd_rama_ef/pass.yaml
python scripts/run_mrd_rama_ef.py inputs/mrd_rama_ef/fail_RE3_redundancy.yaml
python scripts/run_mrd_rama_ef.py inputs/mrd_rama_ef/noeval_RE0_pointer_missing.yaml
```
