# CLI Usage (`occ`)

The CLI is designed for a simple and reproducible flow.

## Installation (local/dev)

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Commands

### `occ --help`

Shows CLI help.

### `occ run <bundle.yaml> [--module ...] [--out out/]`

Runs one YAML bundle associated with an MRD module.

Example:

```bash
occ run ILSC_MRD_suite_15_modulos_CANON/mrd_obs_isaac/inputs/mrd_obs_isaac/pass.yaml --out out/
```

- If `--module` is omitted, the CLI tries to infer it from the path.
- If `--out` is set, the CLI writes `out/report.json`.

### `occ list`

Lists available MRD modules.

```bash
occ list
occ list --suite canon
occ list --suite extensions
```

### `occ doctor`

Quick diagnostics (versions, paths, discovered suites).

```bash
occ doctor
```

### `occ predict`

Browse the prediction registry.

```bash
occ predict list
occ predict show P-0003
```

### `occ judge <claim.yaml>`

Runs built-in judges on a claim spec.

```bash
occ judge examples/claim_specs/minimal_pass.yaml
occ judge examples/claim_specs/nuclear_pass.yaml --profile nuclear
occ judge examples/claim_specs/minimal_pass.yaml --json
```

### `occ verify`

Runs suite verification.

```bash
occ verify
occ verify --suite extensions
occ verify --suite all
```
