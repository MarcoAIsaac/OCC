# CLI (`occ`)

El CLI está pensado para dos casos:

1. Ejecutar MRDs (suite canónica y extensiones).
2. Mejorar la capacidad de descubrimiento (listar módulos, predicciones y diagnósticos).

## Comandos principales

### Listar módulos

```bash
occ list
occ list --suite canon
occ list --suite extensions
occ list --json
```

### Ejecutar un paquete

```bash
occ run ILSC_MRD_suite_15_modulos_CANON/mrd_4f_dict/inputs/mrd_4f_dict/pass.yaml
occ run ... --out out/
```

### Verificar suites completas

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

### Investigación científica web

```bash
occ research examples/claim_specs/minimal_pass.yaml
occ research examples/claim_specs/minimal_pass.yaml --max-results 8 --show 5 --json
```

### Generación automática de módulos

```bash
occ module auto examples/claim_specs/minimal_pass.yaml
occ module auto examples/claim_specs/minimal_pass.yaml --create-prediction
occ module auto examples/claim_specs/minimal_pass.yaml --create-prediction --publish-prediction
```

Esto crea un módulo en `ILSC_MRD_suite_extensions/` con:

- runner autogenerado
- `module_context.json` con jueces/candados aplicados
- contexto de investigación web opcional (arXiv/Crossref, mejor esfuerzo)
- borrador de predicción opcional

### Jueces (especificación de afirmación)

```bash
occ judge examples/claim_specs/minimal_pass.yaml
occ judge examples/claim_specs/trace_noeval.yaml --strict-trace --out out/judge.json
```
