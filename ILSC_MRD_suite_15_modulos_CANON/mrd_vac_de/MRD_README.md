# MRD — Vacío / Energía Oscura (Ejecutable) / Vacuum / Dark Energy (Executable)

Candados/Locks:
- V1: w and rho0 declared (NO-EVAL)
- V2: if w(z) variability allowed -> must declare exchange Q (NO-EVAL)
- V3: acceleration requires w<-1/3 and rho0>0 (FAIL)
- V4: w in observational band (toy) (FAIL)
- V5: local coupling bound (FAIL)

Dataset:
- `data/mrd_vac_de_bounds_v1.csv`
- `data/mrd_vac_de_bounds_v1.meta.json`

Run:
```bash
python scripts/run_mrd_vac_de.py inputs/mrd_vac_de/pass.yaml
python scripts/run_mrd_vac_de.py inputs/mrd_vac_de/fail_V4_w_band.yaml
python scripts/run_mrd_vac_de.py inputs/mrd_vac_de/noeval_V1_missing_rho0.yaml
```
