# MRD — UV → ΩI Proyección Auditable (Ejecutable) / UV → ΩI Auditable Projection (Executable)

Este MRD implementa un ejemplo mínimo pero **auditable** de proyección UV→ΩI:

- Define **Π** (proyección de hipótesis UV a parámetros efectivos en ΩI).
- Define **ΔΠ(E)** (cota conservadora de error de truncación).
- Implementa candados **PA1–PA4** a nivel de módulo y **PA5/RFS5** a nivel de auditoría (hashes hard).
- Incluye dataset pequeño con provenance.

## Archivos clave
- Módulo: `src/ilsc_mrd/modules/uv_omegai.py`
- Runner: `scripts/run_mrd_uv_omegai.py`
- Dataset:
  - `data/mrd_uv_omegai_dataset_v1.csv`
  - `data/mrd_uv_omegai_dataset_v1.meta.json`
- Inputs:
  - `inputs/mrd_uv_omegai/pass.yaml`
  - `inputs/mrd_uv_omegai/noeval_PA3_dominance.yaml`
- Certificados:
  - `certs/pa_cert_uv_omegai_v1.json` (AUTO hashes)
  - `certs/rfs_cert_uv_omegai_v1.json` (AUTO hashes)

## Cómo correr / How to run
```bash
python scripts/run_mrd_uv_omegai.py inputs/mrd_uv_omegai/pass.yaml
python scripts/run_mrd_uv_omegai.py inputs/mrd_uv_omegai/noeval_PA3_dominance.yaml
```

Resultados:
- `outputs/pass.report.json`
- `outputs/noeval_PA3_dominance.report.json`
