# OCC - Operational Consistency Compiler

Español | [English](README.md)

[![CI](https://github.com/MarcoAIsaac/OCC/actions/workflows/ci.yml/badge.svg)](https://github.com/MarcoAIsaac/OCC/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)
[![DOI](https://zenodo.org/badge/1158388233.svg)](https://doi.org/10.5281/zenodo.18656426)
[![arXiv: pending](https://img.shields.io/badge/arXiv-pending-b31b1b)](docs/RELEASING.es.md)

**OCC** es un runtime reproducible con CLI estable (`occ`) para ejecutar módulos MRD
(entradas YAML/JSON) y emitir veredictos **PASS/FAIL/NO-EVAL** con reportes auditables.

## Por qué existe OCC

En flujos de modelado con alta carga UV/BSM, afirmaciones físicamente relevantes pueden volverse
difíciles de falsar porque supuestos inaccesibles absorben señales de fallo.
OCC añade un filtro operacional antes del despliegue experimental:

1. ¿La afirmación es evaluable dentro de un dominio operacional declarado `Omega_I`?
2. ¿Satisface restricciones de consistencia inevitables?
3. ¿Evita la reinyección UV como vía de escape?

OCC no reemplaza al experimento. Mejora la calidad del triaje preexperimental.

## Empieza aquí

- Entrada rápida: [`docs/START_HERE.es.md`](docs/START_HERE.es.md)
- Resumen ejecutivo: [`docs/EXECUTIVE_SUMMARY.es.md`](docs/EXECUTIVE_SUMMARY.es.md)
- Glosario: [`docs/GLOSSARY.es.md`](docs/GLOSSARY.es.md)
- Índice canónico: [`docs/INDEX_CANONICAL.es.md`](docs/INDEX_CANONICAL.es.md)
- Compendio completo (PDF): [`docs/OCC_Compendio_Canonico_Completo.pdf`](docs/OCC_Compendio_Canonico_Completo.pdf)

## Inicio rápido

### Ruta rápida

```bash
make bootstrap
make smoke
make check
```

Para levantar documentación local:

```bash
make docs-serve
```

### macOS / Linux

```bash
git clone https://github.com/MarcoAIsaac/OCC.git
cd OCC
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

occ --help
pytest -q
```

### Windows (PowerShell)

```powershell
git clone https://github.com/MarcoAIsaac/OCC.git
cd OCC
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

occ --help
pytest -q
```

## Comandos de orientación

```bash
occ doctor
occ list
occ predict list
occ judge examples/claim_specs/minimal_pass.yaml
occ judge examples/claim_specs/nuclear_pass.yaml --profile nuclear
```

## App de escritorio (Windows)

Ejecutar frontend de escritorio:

```bash
occ-desktop
```

Descargar paquete preconstruido más reciente para Windows:

- Página de release (siempre disponible): [Último release](https://github.com/MarcoAIsaac/OCC/releases/latest)
- ZIP (recomendado): [`OCCDesktop-windows-x64.zip`](https://github.com/MarcoAIsaac/OCC/releases/latest/download/OCCDesktop-windows-x64.zip)
- EXE: [`OCCDesktop-windows-x64.exe`](https://github.com/MarcoAIsaac/OCC/releases/latest/download/OCCDesktop-windows-x64.exe)
- Checksums: [`OCCDesktop-windows-x64.sha256`](https://github.com/MarcoAIsaac/OCC/releases/latest/download/OCCDesktop-windows-x64.sha256)

Si los enlaces directos devuelven `404`, abre la página del release y espera a que el workflow
`Windows desktop release` termine de subir los assets.
Si hace falta, ejecuta ese workflow manualmente y usa `release_tag` con la versión
(ejemplo `v1.3.0`) para adjuntar assets a un release ya existente.

Verificación SHA256 en Windows:

```powershell
certutil -hashfile .\OCCDesktop-windows-x64.exe SHA256
```

Compara con `OCCDesktop-windows-x64.sha256`.

Desde código fuente sin entrypoint instalado:

```bash
python -m occ.desktop
```

Construir `.exe` en Windows (PowerShell):

```powershell
.\scripts\build_windows_desktop.ps1
```

Para reducir avisos de SmartScreen en binarios distribuidos, configura secretos del repositorio:

- `WINDOWS_CODESIGN_PFX_B64`: certificado `.pfx` codificado en base64.
- `WINDOWS_CODESIGN_PFX_PASSWORD`: contraseña del `.pfx`.

## Utilidades de mantenimiento

```bash
python scripts/release_doctor.py --strict
python scripts/check_docs_i18n.py --strict
python scripts/ci_doctor.py --workflow CI --limit 12
python scripts/generate_release_notes.py
```

Flujo guiado de claim a módulo:

```bash
python scripts/mrd_flow.py examples/claim_specs/minimal_pass.yaml --generate-module
```

## Generación automática de módulos

Si una afirmación no mapea a un módulo existente, OCC puede generar un módulo en extensiones:

```bash
occ module auto examples/claim_specs/minimal_pass.yaml --create-prediction
```

Opciones útiles:

- `--publish-prediction`: publica la predicción generada en `predictions/registry.yaml`.
- `--no-research`: desactiva la búsqueda web.
- `--module-name mrd_auto_mi_modulo`: fija el nombre del módulo.

Investigación científica web desde una afirmación:

```bash
occ research examples/claim_specs/minimal_pass.yaml --show 5
```

## Portal de documentación (EN/ES)

El sitio MkDocs incluye dos idiomas con **inglés por defecto** y cambio automático a español
cuando el idioma preferido del navegador es español.

Construcción local:

```bash
python -m pip install -e ".[docs]"
mkdocs serve
```

## Ejecutar un módulo

```bash
occ run ILSC_MRD_suite_15_modulos_CANON/mrd_4f_dict/inputs/mrd_4f_dict/pass.yaml --out out/
cat out/report.json
```

Salida típica:

```console
PASS
```

## Verificación completa de suite

```bash
occ verify
```

Para ejecuciones largas, conviene usar el flujo manual de verificación completa en GitHub Actions.

## Expansiones de dominio

`v1.3.0` mantiene el conjunto de candados nucleares (`nuclear_guard`, `NUC*`) y agrega
distribución de escritorio para Windows vía GitHub Releases
(`OCCDesktop-windows-x64.exe/.zip`).

## Estructura del repositorio

- `occ/`: runtime y CLI
- `ILSC_MRD_suite_15_modulos_CANON/`: suite MRD canónica (15 módulos)
- `ILSC_MRD_suite_extensions/`: suite de extensiones (herramientas/meta-MRDs)
- `docs/`: documentación y PDFs canónicos
- `tests/`: pruebas de humo y de regresión

## Licencia y cita

- Licencia: [`LICENSE`](LICENSE) (Apache-2.0)
- Archivos de citación: [`CITATION.cff`](CITATION.cff), [`CITATION.bib`](CITATION.bib)
- Metadatos Zenodo: [`.zenodo.json`](.zenodo.json)

## Publicación

- Guía DOI (Zenodo) y distintivo: [`docs/RELEASING.es.md`](docs/RELEASING.es.md)
- Preprint en arXiv recomendado para mejorar visibilidad
