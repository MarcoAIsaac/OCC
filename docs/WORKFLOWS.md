# Automation workflows

This page documents helper scripts for recurring maintenance tasks.

## 1) Release doctor

Validate release metadata consistency across:

- `pyproject.toml`
- `CHANGELOG.md`
- `CITATION.cff`
- `.zenodo.json`
- `README.md` and `README.es.md` DOI badges

Run:

```bash
python scripts/release_doctor.py --strict
```

With explicit DOI check:

```bash
python scripts/release_doctor.py --strict --expected-doi 10.5281/zenodo.18656426
```

## 2) EN/ES docs consistency

Audit bilingual doc pairs and local links:

```bash
python scripts/check_docs_i18n.py --strict
```

## 3) CI doctor

Summarize recent failing GitHub Actions runs (requires authenticated `gh`):

```bash
python scripts/ci_doctor.py --workflow CI --limit 12
```

Machine-readable output:

```bash
python scripts/ci_doctor.py --workflow CI --json
```

## 4) Release notes generator

Build release notes from `CHANGELOG.md` + recent commit highlights:

```bash
python scripts/generate_release_notes.py
```

Write to file:

```bash
python scripts/generate_release_notes.py --output /tmp/release-notes.md
```

## 5) Guided MRD flow

Claim -> judge evaluation -> optional module generation -> optional verification.

Safe default: this script does not run generated MRD modules unless you pass `--verify-generated`.

```bash
python scripts/mrd_flow.py examples/claim_specs/minimal_pass.yaml --generate-module
```

With prediction draft and verification:

```bash
python scripts/mrd_flow.py examples/claim_specs/minimal_pass.yaml \
  --generate-module \
  --create-prediction \
  --verify-generated
```

## Make targets

Equivalent shortcuts:

```bash
make release-doctor
make docs-i18n
make ci-doctor
make release-notes
```
