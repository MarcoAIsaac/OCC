# MRD Suite (15 modules)

The canonical suite lives in:

- `ILSC_MRD_suite_15_modulos_CANON/`

Each module typically contains:

- `inputs/`: YAML bundles (PASS/FAIL/NO-EVAL cases)
- `scripts/`: Python runners (`run_mrd_*.py` or `run_*.py`)
- `outputs/`: canonical `.report.json` outputs for regression

## Run one module

Recommended form:

```bash
occ run ILSC_MRD_suite_15_modulos_CANON/<module>/inputs/<module>/<bundle>.yaml --out out/
```

## Verify all

```bash
occ verify
```

This executes `ILSC_MRD_suite_15_modulos_CANON/RUN_ALL.py` and writes
`verification_summary.json`.
