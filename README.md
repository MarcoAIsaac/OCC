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
- Full compendium PDF (EN): [`docs/OCC_Canonical_Compendium_EN_v1.5.0.pdf`](docs/OCC_Canonical_Compendium_EN_v1.5.0.pdf)
- Full compendium PDF (ES): [`docs/OCC_Compendio_Canonico_ES_v1.5.0.pdf`](docs/OCC_Compendio_Canonico_ES_v1.5.0.pdf)

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

To integrate compendiums automatically (EN + ES + audits):

```bash
make integrate-all
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
occ quickstart
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

Desktop stores persistent local data in:

- `~/.occ_desktop/settings.json`
- `~/.occ_desktop/occ_desktop.db` (SQLite run history)

Built-in AI assistant (Assistant tab):

- Providers: `offline` (deterministic OCC copilot) and `OpenAI` (official API).
- API key source: `OPENAI_API_KEY` environment variable (recommended) or session-only key field.
- Model is configurable (default: `gpt-4.1-mini`).
- Optional runtime-context injection for OCC-aware troubleshooting.

Experiment Lab (new in 1.4.0):

- Run claim matrices across profiles (`core` / `nuclear`) and detect verdict divergence.
- Export auditable artifacts: `lab_report.json`, `lab_results.csv`,
  `lab_profile_summary.csv`, `lab_verdict_matrix.md`.
- CLI:
  `occ lab run --claims-dir examples/claim_specs --profiles core nuclear --out .occ_lab/latest`

Download prebuilt Windows package:

- Current stable desktop version: `1.5.0`
- Installer (recommended): [`OCCDesktop-Setup-windows-x64.exe`](https://github.com/MarcoAIsaac/OCC/releases/download/1.5.0/OCCDesktop-Setup-windows-x64.exe)
- Build info: [`OCCDesktop-build-info.json`](https://github.com/MarcoAIsaac/OCC/releases/download/1.5.0/OCCDesktop-build-info.json)
- Checksums: [`OCCDesktop-windows-x64.sha256`](https://github.com/MarcoAIsaac/OCC/releases/download/1.5.0/OCCDesktop-windows-x64.sha256)
- Rolling channel (optional, latest `main` build): [desktop-latest](https://github.com/MarcoAIsaac/OCC/releases/tag/desktop-latest)

If the direct installer link returns `404`, open release `1.5.0` and wait for workflow
`Windows desktop release` to finish uploading assets for that tag.
This pipeline runs automatically on every push to `main` (rolling `desktop-latest`)
and on version tags (for example `1.5.0` or `v1.5.0`).
If needed, trigger the workflow manually and set `release_tag`
(example `1.5.0` or `desktop-latest`) to refresh assets.

Windows checksum verification:

```powershell
certutil -hashfile .\OCCDesktop-Setup-windows-x64.exe SHA256
```

Compare with the `OCCDesktop-Setup-windows-x64.exe` row in `OCCDesktop-windows-x64.sha256`.

From source without install entrypoint:

```bash
python -m occ.desktop
```

Build `.exe` on Windows (PowerShell):

```powershell
.\scripts\build_windows_desktop.ps1
```

To reduce SmartScreen warnings in distributed binaries, configure repository secrets:

- `WINDOWS_CODESIGN_PFX_B64`: base64-encoded `.pfx` certificate.
- `WINDOWS_CODESIGN_PFX_PASSWORD`: password for the `.pfx`.

Without a trusted code-signing certificate (ideally EV), SmartScreen warnings cannot be fully
eliminated for fresh binaries.

## Mobile app (Android)

Android companion app (`android/`) includes:

- Workbench tab (claim YAML + `core`/`nuclear` judge profiles)
- Lab tab (profile matrix over sample claims with divergence summary)
- Assistant tab (offline OCC guidance)
- History tab (local Room database)

Required Android permissions:

- `INTERNET` (optional online endpoints / links)
- `ACCESS_NETWORK_STATE` (network availability checks)

Build locally:

```bash
cd android
./gradlew assembleRelease
```

Prerequisites: JDK 17 and Android SDK (`ANDROID_HOME` configured).

Generated APK:

- `android/app/build/outputs/apk/release/app-release.apk`

Download prebuilt APK:

- Current stable mobile version: `1.5.0`
- [`OCCMobile-android.apk`](https://github.com/MarcoAIsaac/OCC/releases/download/1.5.0/OCCMobile-android.apk)
- [`OCCMobile-android.sha256`](https://github.com/MarcoAIsaac/OCC/releases/download/1.5.0/OCCMobile-android.sha256)

Release automation:

- Workflow `.github/workflows/android_release.yml` publishes Android assets automatically on pushed version tags (`1.5.0` or `v1.5.0`).

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

`v1.5.0` keeps the nuclear-domain lock set (`j4_nuclear_guard`, `L4C*/L4E*`) and adds
Experiment Lab matrix workflows plus Windows desktop distribution via GitHub Releases
(`OCCDesktop-Setup-windows-x64.exe`).

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
