# Contributing

Gracias por contribuir a OCC.

## Flujo

1. Abre un issue (bug/feature) describiendo el cambio.
2. Crea una rama desde `main`.
3. Mantén los cambios pequeños y auditables.
4. Asegúrate de que CI pase.

## Desarrollo local

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
ruff check .
pytest
```

## Estilo

- Código Python: **ruff** (lint/format).
- PRs deben incluir evidencia mínima (comandos/salida) si cambian el runtime.

## Documentación

Los cambios de UX/documentación deben tocar:

- `README.md`
- `docs/START_HERE.md`
- `docs/INDEX_CANONICAL.md`

cuando sea relevante.
