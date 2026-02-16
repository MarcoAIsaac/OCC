# Changelog

All notable changes to this project will be documented in this file.

The format is based on *Keep a Changelog* and this project adheres to *Semantic Versioning*.

## [1.3.0] - 2026-02-16

### Added

- Windows desktop frontend (`occ-desktop`) for claim judging, suite verification, module flow, and maintenance tools.
- Windows packaging script `scripts/build_windows_desktop.ps1` generating:
  - `OCCDesktop-windows-x64.exe`
  - `OCCDesktop-windows-x64.zip`
  - `OCCDesktop-Setup-windows-x64.exe` (Inno Setup installer)
  - `OCCDesktop-windows-x64.sha256`
- Release workflow `.github/workflows/windows_desktop_release.yml` to build/upload desktop assets on published releases.
- New desktop entry smoke test (`tests/test_desktop_entry.py`).

### Changed

- Version bump to `1.3.0` across runtime/citation metadata (`pyproject.toml`, `CITATION.cff`, `.zenodo.json`).
- README EN/ES now include direct download links to latest Windows desktop assets on GitHub Releases.
- Releasing docs EN/ES now document automatic Windows desktop asset publication.
- Desktop UI upgraded with Fluent-style workbench improvements, execution telemetry (last run + PASS/FAIL/NO-EVAL counters), and improved dark-theme consistency.
- Windows release pipeline now supports optional Authenticode signing when code-sign secrets are configured.
- Desktop app now persists run history in local SQLite (`~/.occ_desktop/occ_desktop.db`) with CSV export and history reset.
- Windows desktop release pipeline now auto-runs on pushed `v*` tags and auto-attaches artifacts to the release.

## [1.2.0] - 2026-02-16

### Added

- New domain-specific nuclear lock package: `nuclear_guard` (`NUC*` codes, C/E classes).
- New extension MRD module: `mrd_nuclear_guard` with PASS/NO-EVAL/FAIL(E) cases.
- New nuclear claim examples under `examples/claim_specs/`.
- New draft prediction `P-0004` for nuclear-domain falsification workflows.
- Canonical PDF addendum integrated into main compendium with formal NUC C/E equations.
- Stable judge-report metadata contract (`schema`, `schema_version`, `occ_version`, `generated_at`).
- `occ judge --json` output mode for machine-readable report consumption.
- `occ judge --profile nuclear` to evaluate claims with the NUC lock package.

### Changed

- `module auto` now validates claim minimum shape up-front and emits clearer validation errors.
- Auto-generated module context now includes explicit schema and OCC version metadata.
- Research query builder now incorporates nuclear-domain descriptors (`sector`, isotopes, reaction channel).
- NUC Class-E now requires observational provenance locator (`dataset_ref` + `source_url`/`dataset_doi`) to avoid untraceable evidence anchors.

## [1.1.0] - 2026-02-15

### Added

- Docs portal (MkDocs Material) + GitHub Pages workflow.
- Predictions registry (YAML) + `occ predict` commands.
- Claim judges & locks (operational filters) + `occ judge` command.
- Extension MRD suite (meta-MRDs for registry/claim/UV-guard validation).
- CLI UX upgrades: `occ list`, `occ explain`, `occ doctor`.

### Changed

- `occ verify` now supports selecting suites (canon/extensions/all).

## [1.0.0] - 2026-02-15

### Added

- OCC runtime (`occ` CLI) and MRD suite runner.
- Canonical MRD suite (15 modules).
- Canonical documentation bundle in `docs/`.
- GitHub Actions CI (smoke + ruff lint).
- Manual workflow for full-suite verification.
