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

### `occ run <archivo.yaml> [--module ...] [--out out/]`

Ejecuta un archivo YAML asociado a un módulo MRD.

Ejemplo:

```bash
occ run ILSC_MRD_suite_15_modulos_CANON/mrd_obs_isaac/inputs/mrd_obs_isaac/pass.yaml --out out/
```

- Si `--module` no se especifica, el CLI intenta inferirlo de la ruta (busca una carpeta `mrd_*`).
- Si `--out` se especifica, se escribe `out/report.json`.

### `occ list`

Lista módulos MRD disponibles.

```bash
occ list
occ list --suite canon
occ list --suite extensions
```

### `occ doctor`

Diagnóstico rápido (versiones, rutas y suites detectadas).

```bash
occ doctor
```

### `occ predict`

Explora el registro YAML de predicciones.

```bash
occ predict list
occ predict show P-0003
```

### `occ judge <afirmacion.yaml>`

Ejecuta jueces básicos sobre una especificación de afirmación.

```bash
occ judge examples/claim_specs/minimal_pass.yaml
```

### `occ verify`

Ejecuta la verificación de una suite.

```bash
occ verify
occ verify --suite extensions
occ verify --suite all
```

En CI normalmente se ejecuta solo la prueba de humo, y `occ verify` se deja como flujo manual.
