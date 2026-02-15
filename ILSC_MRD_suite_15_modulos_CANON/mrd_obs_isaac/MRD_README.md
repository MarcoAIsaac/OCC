# MRD — Observabilidad & ISAAC (Ejecutable) / Observability & ISAAC (Executable)

Este MRD implementa el **módulo observability_isaac** como juez operacional de techo/floor de resolución,
incluyendo separación **concepto vs ecuación** (ISAAC0).

## Qué hace / What it does
- Calcula la instanciación numérica de LI = sqrt(hbar*G/c^3) (la ecuación puede actualizarse si cambian constantes).
- Exige que cualquier resolución solicitada respete un **piso operacional** safety_factor * LI.
- Exige declaración de ΩI (dominio operacional) y, si se declara L_min, que no viole el piso.

## Inputs
- PASS: `inputs/mrd_obs_isaac/pass.yaml`
- NO-EVAL: `inputs/mrd_obs_isaac/noeval_below_floor.yaml`

## Auditoría (hard)
Incluye dataset mínimo de especificaciones del instrumento:
- `data/mrd_obs_isaac_instrument_v1.csv`
- `data/mrd_obs_isaac_instrument_v1.meta.json`

El runner incorpora hashes del dataset en `_data_obj`, y el certificado RFS (AUTO) se rellena/valida.

## Run (example)
Use the project runner entrypoint from this repo (see README.md). Provide the YAML above.
