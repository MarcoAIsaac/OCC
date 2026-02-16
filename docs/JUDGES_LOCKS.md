# Jueces y candados (locks)

En OCC, un **juez** evalúa una afirmación (*claim*) o un artefacto derivado y devuelve un veredicto.

Un **candado (lock)** es una condición concreta que debe cumplirse.

## Veredictos

- **PASS**: evaluable y consistente dentro de Ω_I.
- **FAIL**: inconsistente (contradicción con reglas inevitables / estructura inválida).
- **NO‑EVAL**: todavía no es evaluable operacionalmente (faltan definiciones, proyecciones, trazabilidad o el claim depende de knobs inaccesibles).

## Built-in judges (tooling)

Estos jueces existen en el runtime para facilitar revisiones rápidas y onboarding.

> Importante: no sustituyen el canon; son herramientas para triage.

### `domain` (DOM*)

Comprueba que el claim declare un dominio operacional mínimo:

- `domain.omega_I`
- `domain.observables[]`

Si falta alguno → **NO‑EVAL(DOM*)**.

### `uv_guard` (UV*)

Comprueba que parámetros **inaccesibles** (o con accesibilidad desconocida) no afecten materialmente a los observables.

Si ocurre → **NO‑EVAL(UV*)**.

### `trace` (TR*)

Genera un witness `path -> sha256` para fuentes declaradas en `sources:`.

- Si faltan paths → **NO‑EVAL(TR2)**.
- Con `--strict-trace` → **NO‑EVAL(TR1)**.

## Ejemplos

```bash
occ judge examples/claim_specs/minimal_pass.yaml
occ judge examples/claim_specs/uv_noeval.yaml
occ judge examples/claim_specs/trace_noeval.yaml
```
