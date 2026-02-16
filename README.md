# OCC - Operational Consistency Compiler

English | [Español](README.es.md)

[![CI](https://github.com/MarcoAIsaac/OCC/actions/workflows/ci.yml/badge.svg)](https://github.com/MarcoAIsaac/OCC/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)
[![DOI](https://zenodo.org/badge/1158388233.svg)](https://doi.org/10.5281/zenodo.18656426)
[![arXiv: pending](https://img.shields.io/badge/arXiv-pending-b31b1b)](docs/RELEASING.md)

**OCC** is a reproducible runtime with a stable CLI (`occ`) to execute MRD modules (YAML/JSON inputs)
and emit **PASS/FAIL/NO-EVAL** verdicts with auditable reports.

## Why OCC exists

In UV/BSM-heavy modeling workflows, physically meaningful claims can remain difficult to falsify
because inaccessible assumptions can absorb failure signals. OCC provides an operational filter before
experimental deployment:

1. Is the claim evaluable in a declared operational domain \\(\Omega_I\\)?
2. Does it satisfy unavoidable consistency constraints?
3. Does it avoid UV reinjection as an escape route?

OCC does not replace experiment. It improves pre-experimental triage quality.

## Start here

- Quick entry: [`docs/START_HERE.md`](docs/START_HERE.md)
- Executive summary: [`docs/EXECUTIVE_SUMMARY.md`](docs/EXECUTIVE_SUMMARY.md)
- Glossary: [`docs/GLOSSARY.md`](docs/GLOSSARY.md)
- Canonical index: [`docs/INDEX_CANONICAL.md`](docs/INDEX_CANONICAL.md)
- Full compendium PDF: [`docs/OCC_Compendio_Canonico_Completo.pdf`](docs/OCC_Compendio_Canonico_Completo.pdf)

## Quickstart

### Fast path

```bash
make bootstrap
make smoke
make check
```

To run docs locally:

```bash
make docs-serve
```

### macOS / Linux

```bash
git clone https://github.com/MarcoAIsaac/OCC.git
cd OCC
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

occ --help
pytest -q
```

### Windows (PowerShell)

```powershell
git clone https://github.com/MarcoAIsaac/OCC.git
cd OCC
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

occ --help
pytest -q
```

## Discoverability commands

```bash
occ doctor
occ list
occ predict list
occ judge examples/claim_specs/minimal_pass.yaml
occ judge examples/claim_specs/nuclear_pass.yaml --profile nuclear
```

## Desktop app (Windows)

Run desktop frontend:

```bash
occ-desktop
```

From source without install entrypoint:

```bash
python -m occ.desktop
```

Build `.exe` on Windows (PowerShell):

```powershell
.\scripts\build_windows_desktop.ps1
```

## Maintenance helpers

```bash
python scripts/release_doctor.py --strict
python scripts/check_docs_i18n.py --strict
python scripts/ci_doctor.py --workflow CI --limit 12
python scripts/generate_release_notes.py
```

Guided claim-to-module pipeline:

```bash
python scripts/mrd_flow.py examples/claim_specs/minimal_pass.yaml --generate-module
```

## Automatic module generation

If a claim does not map to an existing module, OCC can generate an extension module:

```bash
occ module auto examples/claim_specs/minimal_pass.yaml --create-prediction
```

Useful options:

- `--publish-prediction`: append generated prediction to `predictions/registry.yaml`.
- `--no-research`: disable web research.
- `--module-name mrd_auto_my_module`: force module name.

Run standalone claim research:

```bash
occ research examples/claim_specs/minimal_pass.yaml --show 5
```

## Documentation portal (EN/ES)

MkDocs site includes two languages with **English default** and browser-aware switch to Spanish
when the reader's language is Spanish.

Local build:

```bash
python -m pip install -e ".[docs]"
mkdocs serve
```

## Run a module

```bash
occ run ILSC_MRD_suite_15_modulos_CANON/mrd_4f_dict/inputs/mrd_4f_dict/pass.yaml --out out/
cat out/report.json
```

Typical output:

```console
PASS
```

## Full suite verification

```bash
occ verify
```

For long runs, prefer the manual full-suite workflow in GitHub Actions.

## Domain expansions

`v1.2.0` adds a nuclear-domain operational lock set (`nuclear_guard`, codes `NUC*`)
and extension MRD coverage (`mrd_nuclear_guard`).

## Repository layout

- `occ/` - runtime and CLI
- `ILSC_MRD_suite_15_modulos_CANON/` - canonical MRD suite (15 modules)
- `ILSC_MRD_suite_extensions/` - extension suite (tooling/meta-MRDs)
- `docs/` - documentation and canonical PDFs
- `tests/` - smoke and regression tests

## License and citation

- License: [`LICENSE`](LICENSE) (Apache-2.0)
- Citation files: [`CITATION.cff`](CITATION.cff), [`CITATION.bib`](CITATION.bib)
- Zenodo metadata: [`.zenodo.json`](.zenodo.json)

## Publication notes

- Zenodo DOI workflow and badge template: [`docs/RELEASING.md`](docs/RELEASING.md)
- arXiv preprint is recommended for discoverability
