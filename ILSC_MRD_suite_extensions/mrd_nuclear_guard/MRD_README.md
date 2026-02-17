# mrd_nuclear_guard

Meta-MRD for the numbered nuclear-domain lock package (`J4`, `L4C*`, `L4E*`).

This module implements two lock classes aligned with the canonical framework:

- Class C (consistency/evaluability in declared Ω_I):
  - nuclear scope declaration,
  - `energy_range_mev` with `0 <= min < max`,
  - isotope list, reaction channel, detector list.
- Class E (evidence anchor):
  - declared observed cross section with uncertainty,
  - model prediction for the same observable,
  - provenance fields (`dataset_ref` and `source_url`/`dataset_doi`),
  - consistency test using
    `z = |sigma_pred - sigma_obs| / sigma_obs_err <= z_max`.

## Inputs

- `pass.yaml`: complete Class-C + Class-E declaration, expected `PASS`.
- `noeval_missing_reaction.yaml`: missing Class-C field, expected `NO-EVAL(L4C6)`.
- `fail_data_anchor.yaml`: inconsistent Class-E anchor, expected `FAIL(L4E5)`.

## Run manually

```bash
occ run ILSC_MRD_suite_extensions/mrd_nuclear_guard/inputs/pass.yaml --suite extensions --module mrd_nuclear_guard
occ run ILSC_MRD_suite_extensions/mrd_nuclear_guard/inputs/noeval_missing_reaction.yaml --suite extensions --module mrd_nuclear_guard
occ run ILSC_MRD_suite_extensions/mrd_nuclear_guard/inputs/fail_data_anchor.yaml --suite extensions --module mrd_nuclear_guard
```
