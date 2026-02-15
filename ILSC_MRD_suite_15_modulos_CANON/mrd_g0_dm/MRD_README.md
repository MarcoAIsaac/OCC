# MRD — G0: Materia oscura efectiva (Ejecutable) / G0: Effective Dark Matter (Executable)

Candados/Locks:
- G01: baryon model declared (NO-EVAL)
- G02: rho0>0 (FAIL)
- G03: rotation fit chi2 (PASS/FAIL)
- G04: lensing fit chi2 (PASS/FAIL or NO-EVAL if missing)

Dataset:
- `data/mrd_g0_dm_galaxy_v1.csv`
- `data/mrd_g0_dm_galaxy_v1.meta.json`

Run:
```bash
python scripts/run_mrd_g0_dm.py inputs/mrd_g0_dm/pass.yaml
python scripts/run_mrd_g0_dm.py inputs/mrd_g0_dm/fail_G03_fit.yaml
python scripts/run_mrd_g0_dm.py inputs/mrd_g0_dm/noeval_G03_missing_dataset.yaml
```
