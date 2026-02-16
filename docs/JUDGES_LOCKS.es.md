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
