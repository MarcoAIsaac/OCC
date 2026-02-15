# Start here (OCC)

Si estás viendo este repositorio por primera vez, esta página es el **punto de entrada**.

## Qué es OCC

**OCC** (Operational Consistency Compiler) es un runtime reproducible con CLI (`occ`) para:

- Ejecutar módulos MRD individuales (**`occ run`**) a partir de bundles YAML.
- Verificar la suite completa de 15 módulos MRD (**`occ verify`**) de forma determinista.

El objetivo práctico del repo es doble:

1. **Acceso a conceptos** (documentación canónica + compendio).
2. **Uso inmediato de herramientas** (CLI + suite MRD ejecutable).

## Ruta rápida (5 minutos)

1) Instala en un entorno virtual

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

2) Verifica que el CLI está disponible

```bash
occ --help
pytest -q tests/test_cli_smoke.py
```

3) Ejecuta un bundle de ejemplo

```bash
occ run ILSC_MRD_suite_15_modulos_CANON/mrd_obs_isaac/inputs/mrd_obs_isaac/pass.yaml --out out/
cat out/report.json
```

4) (Opcional) corre la verificación completa

```bash
occ verify
```

## Cómo leer el compendio sin morir en el intento

El PDF principal está aquí:

- **`docs/OCC_Compendio_Canonico_Completo.pdf`**

Sugerencia de lectura:

- No lo leas linealmente. Úsalo como **manual de referencia**.
- Empieza por la introducción y el índice.
- Luego salta a la sección que corresponda al tipo de afirmación/experimento que quieras evaluar.

## Mapa del repositorio

- `occ/` → runtime Python + CLI
- `ILSC_MRD_suite_15_modulos_CANON/` → suite MRD canónica (15 módulos)
- `docs/` → documentación y PDFs
- `tests/` → smoke tests (CI)
- `.github/workflows/` → CI (smoke) + verificación completa manual

## Siguiente paso

Ve a **`docs/INDEX_CANONICAL.md`** para navegar todos los documentos y assets.
