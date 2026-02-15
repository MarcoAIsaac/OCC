# OCC — Operational Consistency Compiler

[![CI](https://github.com/MarcoAIsaac/OCC/actions/workflows/ci.yml/badge.svg)](https://github.com/MarcoAIsaac/OCC/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

**OCC** es un runtime reproducible con CLI (`occ`) para ejecutar módulos MRD (inputs YAML/JSON) y emitir veredictos **PASS/FAIL/NO‑EVAL** con reportes auditables.

## Start here

- 📌 Guía rápida: [`docs/START_HERE.md`](docs/START_HERE.md)
- 📚 Índice canónico: [`docs/INDEX_CANONICAL.md`](docs/INDEX_CANONICAL.md)
- 📄 Compendio (PDF): [`docs/OCC_Compendio_Canonico_Completo.pdf`](docs/OCC_Compendio_Canonico_Completo.pdf)

## Quickstart

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

> Nota (PowerShell): usar comillas en `".[dev]"` evita problemas con los brackets.

## Ejecutar un módulo

Ejemplo mínimo (escribe `out/report.json`):

```bash
occ run ILSC_MRD_suite_15_modulos_CANON/mrd_obs_isaac/inputs/mrd_obs_isaac/pass.yaml --out out/
cat out/report.json
```

## Verificar la suite completa

```bash
occ verify
```

> En GitHub Actions esto se deja como workflow manual para evitar runtimes largos.

## Estructura del repo

- `occ/` → runtime + CLI
- `ILSC_MRD_suite_15_modulos_CANON/` → suite MRD canónica (15 módulos)
- `docs/` → documentación y PDFs canónicos
- `tests/` → smoke tests
- `.github/workflows/` → CI y verificación completa manual

## Licencia y cita

- Licencia: **Apache-2.0** (ver [`LICENSE`](LICENSE))
- Cita: [`CITATION.cff`](CITATION.cff) / [`CITATION.bib`](CITATION.bib)
