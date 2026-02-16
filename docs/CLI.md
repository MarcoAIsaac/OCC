# CLI (`occ`)

The CLI is designed for two core workflows:

1. Execute MRDs (canonical suite and extensions).
2. Improve discoverability (list modules, predictions, diagnostics).

## Main commands

### List modules

```bash
occ list
occ list --suite canon
occ list --suite extensions
occ list --json
```

### Run one bundle

```bash
occ run ILSC_MRD_suite_15_modulos_CANON/mrd_4f_dict/inputs/mrd_4f_dict/pass.yaml
occ run ... --out out/
```

### Verify complete suites

```bash
occ verify
occ verify --suite extensions
occ verify --suite all
```

### Predictions

```bash
occ predict list
occ predict show P-0003
```

### Scientific web research

```bash
occ research examples/claim_specs/minimal_pass.yaml
occ research examples/claim_specs/minimal_pass.yaml --max-results 8 --show 5 --json
```

### Automatic module generation

```bash
occ module auto examples/claim_specs/minimal_pass.yaml
occ module auto examples/claim_specs/minimal_pass.yaml --create-prediction
occ module auto examples/claim_specs/minimal_pass.yaml --create-prediction --publish-prediction
```

This creates a module under `ILSC_MRD_suite_extensions/` with:

- auto-generated runner
- `module_context.json` with applied judges/locks
- optional web research context (arXiv/Crossref, best effort)
- optional prediction draft

### Judges (claim spec)

```bash
occ judge examples/claim_specs/minimal_pass.yaml
occ judge examples/claim_specs/nuclear_pass.yaml --profile nuclear
occ judge examples/claim_specs/trace_noeval.yaml --strict-trace --out out/judge.json
occ judge examples/claim_specs/minimal_pass.yaml --json
```
