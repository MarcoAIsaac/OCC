# CLI (`occ`)

El CLI está pensado para dos casos:

1. Ejecutar MRDs (suite canónica y extensiones).
2. Hacer *discoverability* (listar módulos, predicciones, diagnosticar el repo).

## Comandos principales

### Listar módulos

```bash
occ list
occ list --suite canon
occ list --suite extensions
occ list --json
```

### Ejecutar un bundle

```bash
occ run ILSC_MRD_suite_15_modulos_CANON/mrd_4f_dict/inputs/mrd_4f_dict/pass.yaml
occ run ... --out out/
```

### Verificar una suite completa

```bash
occ verify
occ verify --suite extensions
occ verify --suite all
```

### Predicciones

```bash
occ predict list
occ predict show P-0003
```

### Judges (claim spec)

```bash
occ judge examples/claim_specs/minimal_pass.yaml
occ judge examples/claim_specs/trace_noeval.yaml --strict-trace --out out/judge.json
```
