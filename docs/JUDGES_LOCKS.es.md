# Jueces y candados

En OCC, un **juez** evalúa una afirmación o artefacto derivado y devuelve un veredicto.

Un **candado** es una condición concreta que debe cumplirse.

## Veredictos

- **PASS**: evaluable y consistente dentro de `Omega_I`.
- **FAIL**: inconsistente con reglas inevitables o requisitos estructurales.
- **NO-EVAL**: aún no evaluable operacionalmente (faltan definiciones, proyecciones,
  trazabilidad, o hay dependencia de parámetros inaccesibles).

## Jueces integrados (herramientas)

Estos jueces existen en el runtime para triaje rápido y adopción inicial.

### `domain` (DOM*)

Verifica dominio operacional mínimo declarado en la afirmación:

- `domain.omega_I`
- `domain.observables[]`

Si faltan campos, el resultado es **NO-EVAL(DOM*)**.

### `uv_guard` (UV*)

Verifica que parámetros inaccesibles (o de accesibilidad desconocida) no afecten
materialmente los observables.

Si los afectan, el resultado es **NO-EVAL(UV*)**.

### `j4_nuclear_guard` (J4 / L4C* / L4E*) — paquete de candados por dominio

Es el paquete de candados nucleares alineado con numeración canónica:
- id del juez: **J4**
- candados clase C: **L4C1..L4C7**
- candados clase E: **L4E1..L4E7**

Los jueces fundacionales siguen siendo J0–J3 (ISAAC/PA/IO/RFS) según el compendio.
J4 extiende el frontend operacional para claims nucleares.

Se usa con:

```bash
occ judge examples/claim_specs/nuclear_pass.yaml --profile nuclear
```

Se aplica solo a afirmaciones etiquetadas explícitamente en dominio nuclear y exige:

- `domain.energy_range_mev.{min_mev,max_mev}`
- `domain.isotopes[]`
- `domain.reaction_channel`
- `domain.detectors[]`

Chequeo de anclaje de evidencia (clase E):

- `z = |sigma_pred - sigma_obs| / sigma_obs_err <= z_max`
- metadatos de trazabilidad: `evidence.dataset_ref` y (`evidence.source_url` o `evidence.dataset_doi`)

Si faltan declaraciones obligatorias, el resultado es **NO-EVAL(L4C*/L4E*)**.
Si el anclaje numérico es inconsistente, el resultado es **FAIL(L4E5)**.

### `trace` (TR*)

Genera un mapa de evidencias `ruta -> sha256` para rutas declaradas en `sources:`.

- Rutas faltantes: **NO-EVAL(TR2)**.
- Con `--strict-trace`: **NO-EVAL(TR1)**.

## Ejemplos

```bash
occ judge examples/claim_specs/minimal_pass.yaml
occ judge examples/claim_specs/uv_noeval.yaml
occ judge examples/claim_specs/trace_noeval.yaml
```
