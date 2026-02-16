# Start here (OCC)

Si estás viendo este repositorio por primera vez, esta página es el **punto de entrada**.

> Si el PDF de 300+ páginas te intimida: perfecto. **No está pensado para leerse linealmente**.
> Está pensado como **manual de referencia**. Para una visión rápida, usa el *Executive Summary*.

📌 Executive Summary (científico): [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md)
📖 Glosario (no‑expertos): [`GLOSSARY.md`](GLOSSARY.md)

## Qué es OCC

**OCC** (Operational Consistency Compiler) es un runtime reproducible con CLI (`occ`) para:

- Ejecutar módulos MRD individuales (**`occ run`**) a partir de bundles YAML.
- Verificar suites MRD (**`occ verify`**) de forma determinista.
- Descubrir contenido rápidamente (**`occ list`**, **`occ predict`**, **`occ doctor`**).
- Hacer *triage* operacional sobre un claim spec (**`occ judge`**).

El objetivo práctico del repo es doble:

1. **Acceso a conceptos** (documentación canónica + compendio).
2. **Uso inmediato de herramientas** (CLI + suite MRD ejecutable).

## Por qué existe (en una frase)

OCC existe para filtrar afirmaciones físicas que, aun siendo matemáticamente consistentes, no son
**operacionalmente evaluables** (o quedan “malleables” por parámetros UV inaccesibles).

## Predicción destacada (para orientar lectura)

El canon incluye una predicción falsable destacada:

- Correlación **EDM ↔ GW** en escenarios de **bariogénesis**.

Si vienes del lado experimental: esta es una buena “entrada” porque aterriza el marco en un observable.

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
occ verify --suite extensions
occ verify --suite all
```

## Cómo leer el compendio sin morir en el intento

El PDF principal está aquí:

- **`docs/OCC_Compendio_Canonico_Completo.pdf`**

Sugerencia de lectura:

- No lo leas linealmente. Úsalo como **manual de referencia**.
- Empieza por la introducción y el índice.
- Luego salta a la sección que corresponda al tipo de afirmación/experimento que quieras evaluar.

Recomendación:

- Si eres *no‑experto* (o vienes de otra subárea), abre primero el glosario: [`GLOSSARY.md`](GLOSSARY.md).

## Mapa del repositorio

- `occ/` → runtime Python + CLI
- `ILSC_MRD_suite_15_modulos_CANON/` → suite MRD canónica (15 módulos)
- `ILSC_MRD_suite_extensions/` → suite extra (meta‑MRDs de UX/tooling)
- `docs/` → documentación y PDFs
- `predictions/` → registry YAML de predicciones (discoverability)
- `tests/` → smoke tests (CI)
- `.github/workflows/` → CI (smoke) + verificación completa manual
- `mkdocs.yml` → portal de documentación (MkDocs Material)

## Siguiente paso

Ve a **`docs/INDEX_CANONICAL.md`** para navegar todos los documentos y assets.
