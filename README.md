# OCC

CLI package for OCC workflows.

## Quickstart (macOS/Linux)

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
occ --help
pytest -q tests/test_cli_smoke.py
```

## Quickstart (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
occ --help
pytest -q tests/test_cli_smoke.py
```

## Manual verification

```bash
occ verify
```
