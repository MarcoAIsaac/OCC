# OCC

OCC es una interfaz de línea de comandos para ejecutar y verificar flujos de trabajo modulares del runtime `occ`.
Incluye utilidades de smoke test y verificación manual para facilitar integración continua y uso local.

## Start here

- [Guía de arranque](docs/START_HERE.md)
- [Índice canónico](docs/INDEX_CANONICAL.md)
- [Compendio canónico (PDF, si existe)](docs/OCC_Compendio_Canonico_Completo.pdf)

## Quickstart (macOS/Linux)

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
occ --help
pytest -q tests/test_cli_smoke.py
# Manual / puede tardar:
occ verify
```

## Quickstart (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
occ --help
pytest -q tests/test_cli_smoke.py
# Manual / puede tardar:
occ verify
```

## Run a module

```bash
occ run module_a --out out/
```
