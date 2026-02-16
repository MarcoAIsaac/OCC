# Empieza aquí (OCC)

Si es tu primera vez en este repositorio, esta página es tu punto de entrada.

> Si el PDF de 300+ páginas te intimida: perfecto. No está pensado para leerse linealmente.
> Úsalo como manual de referencia. Para vista rápida, empieza por el resumen ejecutivo.

- Resumen ejecutivo: [`EXECUTIVE_SUMMARY.es.md`](EXECUTIVE_SUMMARY.es.md)
- Glosario: [`GLOSSARY.es.md`](GLOSSARY.es.md)

## Qué es OCC

**OCC** (Operational Consistency Compiler) es un runtime reproducible con CLI (`occ`) para:

- Ejecutar módulos MRD individuales (`occ run`) con paquetes YAML.
- Verificar suites MRD completas (`occ verify`) de forma determinista.
- Descubrir contenido rápidamente (`occ list`, `occ predict`, `occ doctor`).
- Hacer triaje operacional sobre afirmaciones (`occ judge`).

El repositorio tiene dos objetivos prácticos:

1. Hacer accesibles los conceptos (documentación canónica + compendio).
2. Habilitar uso inmediato de herramientas (CLI + suites MRD ejecutables).

## Por qué existe

OCC filtra afirmaciones que pueden ser matemáticamente consistentes pero no operacionalmente
evaluables, o que siguen siendo UV-maleables por parámetros inaccesibles.

## Predicción destacada

El canon incluye una predicción falsable destacada:

- **Correlación EDM ↔ GW** en escenarios de bariogénesis.

Para perfiles experimentales, suele ser la entrada más directa a observables concretos.

## Ruta de 5 minutos

1. Instala en entorno virtual

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

2. Verifica que el CLI está disponible

```bash
occ --help
pytest -q tests/test_cli_smoke.py
```

3. Ejecuta un paquete de ejemplo

```bash
occ run ILSC_MRD_suite_15_modulos_CANON/mrd_obs_isaac/inputs/mrd_obs_isaac/pass.yaml --out out/
cat out/report.json
```

4. Verificación completa opcional

```bash
occ verify
occ verify --suite extensions
occ verify --suite all
```

## Cómo leer el compendio eficientemente

PDF principal:

- `docs/OCC_Compendio_Canonico_Completo.pdf`

Sugerencia:

- No lo leas linealmente.
- Úsalo como referencia y navega por secciones.
