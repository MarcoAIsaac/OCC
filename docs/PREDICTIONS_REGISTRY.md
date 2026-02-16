# Predictions registry

The file `predictions/registry.yaml` makes predictions discoverable.

In practice, a prediction can be strong but still hard to find if buried in long documents.
The registry addresses that discoverability gap.

## Inspect predictions

```bash
occ predict list
occ predict show P-0003
```

## Add a prediction

1. Copy `predictions/TEMPLATE.yaml`.
2. Add a new entry in `predictions/registry.yaml`.
3. Ensure:
   - unique `id`,
   - falsifiable `summary`,
   - at least one test channel under `tests`.

## Validation

The extensions suite includes a meta-MRD that validates the registry:

```bash
occ verify --suite extensions
```
