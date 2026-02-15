# PATCH_NOTES_v8 — Robustez de rutas (path hardening)

Motivo: algunos runners abrían `data/...` o `certs/...` asumiendo que el *working directory* era el directorio del módulo.
Eso podía fallar si el MRD se ejecutaba desde el root de la suite o desde otra ruta.

Cambio aplicado (v8):
- Se añadió un helper `_resolve()` (o se reutilizó) para resolver rutas relativas contra `REPO_ROOT` (root del módulo).
- Se actualizó la carga de datasets y certificados (`PA/IO/RFS`) para usar `_resolve()`.
- Se ancló `outputs/` al root del módulo (`REPO_ROOT / "outputs"`), evitando escritura accidental en un CWD externo.

Runners parcheados:
- `mrd_uv_omegai/scripts/run_mrd_uv_omegai.py`
- `mrd_sym_topo/scripts/run_mrd_sym_anom_topo.py`
- `mrd_4f_dict/scripts/run_mrd_4f_dict.py`
- `mrd_4f_unif_op/scripts/run_mrd_4f_unif_op.py`
- `mrd_4f_unif_dyn/scripts/run_mrd_4f_unif_dyn.py`

Test mínimo:
- PASS ejecutado desde (a) root del módulo y (b) root de la suite para los runners parcheados.

