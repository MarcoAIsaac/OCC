# Resolución de problemas

## `occ` no se encuentra

Si instalaste en entorno virtual:

```bash
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

En Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## `occ verify` tarda demasiado

La verificación completa ejecuta muchos casos.

- Prefiere el flujo manual de suite completa en GitHub Actions.
- Reduce el tiempo máximo por caso:

```bash
occ verify --timeout 60
```

## `NO-EVAL(TR*)` en `occ judge`

Declara solo rutas existentes o ejecuta sin `--strict-trace`.

## `occ research` sin resultados

La búsqueda externa usa API públicas (arXiv/Crossref) y depende de conectividad.

- Verifica salida a Internet.
- Aumenta el tiempo máximo:

```bash
occ research examples/claim_specs/minimal_pass.yaml --timeout 30
```
