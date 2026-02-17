# Extensions suite

The repo includes an additional suite:

`ILSC_MRD_suite_extensions/`

Its purpose is to improve usability without changing the canonical suite.

It includes example meta-MRDs to:

- validate claim spec structure,
- demonstrate UV guard behavior,
- demonstrate numbered nuclear guard behavior (J4, L4C*/L4E*),
- validate `predictions/registry.yaml`.

## Run

```bash
occ verify --suite extensions
```

## Design principle

Canonical suite remains unchanged.
Extensions stay separate to keep the canon stable.
