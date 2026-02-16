# Changelog

All notable changes to this project will be documented in this file.

The format is based on *Keep a Changelog* and this project adheres to *Semantic Versioning*.

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
