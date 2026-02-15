# MRD — EFT & Renormalización operacional (Ejecutable) / EFT & Operational Renormalization (Executable)

Este MRD implementa:
- corrida RG toy de un coeficiente EFT
- chequeo de consistencia por matching (direct vs two-step)
- cota de truncación (dim-8) para disciplinar maleabilidad (PA-like)

This MRD implements:
- toy RG running of one EFT coefficient
- matching/consistency check (direct vs two-step)
- truncation bound (dim-8) to enforce informativeness

Dataset:
- `data/mrd_eft_ren_data_v1.csv`
- `data/mrd_eft_ren_data_v1.meta.json`

Run:
```bash
python scripts/run_mrd_eft_ren.py inputs/mrd_eft_ren/pass.yaml
python scripts/run_mrd_eft_ren.py inputs/mrd_eft_ren/fail_EFT3_rg_inconsistent.yaml
python scripts/run_mrd_eft_ren.py inputs/mrd_eft_ren/noeval_EFT1_missing_cutoff.yaml
```
