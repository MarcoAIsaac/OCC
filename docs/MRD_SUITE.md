# Suite MRD (15 módulos)

La suite canónica vive en:

- `ILSC_MRD_suite_15_modulos_CANON/`

Cada módulo suele contener:

- `inputs/` → bundles YAML de prueba (PASS/FAIL/NO‑EVAL)
- `scripts/` → runner(s) Python (`run_mrd_*.py` o `run_*.py`)
- `outputs/` → reportes `.report.json` canónicos (útiles para regresión)

## Ejecutar un módulo

Forma recomendada:

```bash
occ run ILSC_MRD_suite_15_modulos_CANON/<modulo>/inputs/<modulo>/<bundle>.yaml --out out/
```

## Verificar todo

```bash
occ verify
```

Esto ejecuta `ILSC_MRD_suite_15_modulos_CANON/RUN_ALL.py` y genera un resumen en
`verification_summary.json`.
