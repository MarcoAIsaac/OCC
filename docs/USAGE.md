# Uso del CLI (`occ`)

El CLI está diseñado para un flujo simple y reproducible.

## Instalación (desarrollo/local)

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

En Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Comandos

### `occ --help`

Muestra ayuda del CLI.

### `occ run <bundle.yaml> [--module ...] [--out out/]`

Ejecuta un bundle YAML asociado a un módulo MRD.

Ejemplo:

```bash
occ run ILSC_MRD_suite_15_modulos_CANON/mrd_obs_isaac/inputs/mrd_obs_isaac/pass.yaml --out out/
```

- Si `--module` no se especifica, el CLI intenta inferirlo del path (busca un folder `mrd_*`).
- Si `--out` se especifica, se escribe `out/report.json`.

### `occ verify`

Ejecuta la verificación completa del suite (llama `RUN_ALL.py`).

```bash
occ verify
```

En CI normalmente se ejecuta solo el smoke test, y `occ verify` se deja como workflow manual.
