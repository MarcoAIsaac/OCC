# Start Here (OCC)

If this is your first time in the repository, this page is your entry point.

> If the 300+ page PDF feels overwhelming: perfect. You are not expected to read it linearly.
> Use it as a reference manual. For a fast overview, use the Executive Summary.

- Executive Summary: [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md)
- Glossary: [`GLOSSARY.md`](GLOSSARY.md)

## What OCC is

**OCC** (Operational Consistency Compiler) is a reproducible runtime with a CLI (`occ`) to:

- Run individual MRD modules (`occ run`) using YAML bundles.
- Verify complete MRD suites (`occ verify`) deterministically.
- Discover project content quickly (`occ list`, `occ predict`, `occ doctor`).
- Perform operational triage over claim specs (`occ judge`).

The repo has two practical goals:

1. Make core concepts accessible (canonical docs + compendium).
2. Enable immediate tool usage (CLI + runnable MRD suites).

## Why it exists (one line)

OCC filters physical claims that may be mathematically consistent but are not operationally evaluable,
or remain UV-malleable through inaccessible parameters.

## Highlight prediction

The canon includes a highlighted falsifiable prediction:

- **EDM ↔ GW** correlation in baryogenesis scenarios.

For experimental readers, this is usually the fastest way to connect the framework to observables.

## 5-minute path

1. Install in a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

2. Verify CLI availability

```bash
occ --help
pytest -q tests/test_cli_smoke.py
```

3. Run one example bundle

```bash
occ run ILSC_MRD_suite_15_modulos_CANON/mrd_obs_isaac/inputs/mrd_obs_isaac/pass.yaml --out out/
cat out/report.json
```

4. Optional judge examples

```bash
occ judge examples/claim_specs/nuclear_pass.yaml --profile nuclear
```

5. Optional desktop frontend (Windows)

```bash
occ-desktop
```

6. Optional full verification

```bash
occ verify
occ verify --suite extensions
occ verify --suite all
```

## How to read the compendium efficiently

Main PDF:

- `docs/OCC_Canonical_Compendium_EN_v1.5.0.pdf`

Suggestion:

- Do not read it linearly.
- Use it as a reference manual and jump by section/topic.
