# Judges and locks

In OCC, a **judge** evaluates a claim or derived artifact and returns a verdict.

A **lock** is a concrete condition that must hold.

## Verdicts

- **PASS**: evaluable and consistent within \\(\Omega_I\\).
- **FAIL**: inconsistent with unavoidable rules or structural requirements.
- **NO-EVAL**: not yet operationally evaluable (missing definitions, projections, traceability,
  or dependence on inaccessible knobs).

## Built-in judges (tooling)

These judges exist in the runtime to support quick triage and onboarding.

### `domain` (DOM*)

Checks minimum declared operational domain in the claim:

- `domain.omega_I`
- `domain.observables[]`

Missing fields lead to **NO-EVAL(DOM*)**.

### `uv_guard` (UV*)

Checks that inaccessible (or unknown-accessibility) parameters do not materially affect observables.

If they do, verdict is **NO-EVAL(UV*)**.

### `nuclear_guard` (NUC*) — domain lock package

This is a domain lock package (Class C / Class E), not a foundational J-judge.
Foundational judges remain J0-J3 (ISAAC/PA/IO/RFS) in the canonical compendium.

Use it via:

```bash
occ judge examples/claim_specs/nuclear_pass.yaml --profile nuclear
```

It applies only to claims explicitly tagged as nuclear-domain and enforces:

- `domain.energy_range_mev.{min_mev,max_mev}`
- `domain.isotopes[]`
- `domain.reaction_channel`
- `domain.detectors[]`

Class-E anchor check:

- `z = |sigma_pred - sigma_obs| / sigma_obs_err <= z_max`
- evidence provenance metadata: `evidence.dataset_ref` and (`evidence.source_url` or `evidence.dataset_doi`)

Missing mandatory declarations produce **NO-EVAL(NUC*)**.
Inconsistent numerical anchors produce **FAIL(NUC12E)**.

### `trace` (TR*)

Generates a witness map `path -> sha256` for paths declared in `sources:`.

- Missing paths: **NO-EVAL(TR2)**.
- With `--strict-trace`: **NO-EVAL(TR1)**.

## Examples

```bash
occ judge examples/claim_specs/minimal_pass.yaml
occ judge examples/claim_specs/uv_noeval.yaml
occ judge examples/claim_specs/trace_noeval.yaml
```
