# Troubleshooting

## `occ` no se encuentra

Si instalaste en venv:

```bash
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

En Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## `occ verify` tarda mucho

La suite completa ejecuta muchos casos.

- Usa el workflow manual en GitHub.
- Reduce timeout por caso:

```bash
occ verify --timeout 60
```

## `NO‑EVAL(TR*)` en `occ judge`

Declara solo paths que existan o ejecuta sin `--strict-trace`.

## `occ research` sin resultados

La búsqueda externa usa APIs públicas (arXiv/Crossref) y depende de red.

- Verifica conectividad saliente.
- Aumenta timeout:

```bash
occ research examples/claim_specs/minimal_pass.yaml --timeout 30
```
