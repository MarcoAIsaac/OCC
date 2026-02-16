# Releasing (DOI + arXiv)

This repository is technically ready. To maximize scientific reach, two publication steps are recommended:

1. **DOI** (Zenodo) to make software citable.
2. **Preprint** (arXiv) to make the framework discoverable.

## 1) DOI with Zenodo

### Steps

1. Connect GitHub with Zenodo and enable this repository.
2. Create a GitHub Release (for example `v1.0.0`).
3. Windows desktop assets are built automatically by workflow
   `.github/workflows/windows_desktop_release.yml` and attached to the release:
   - `OCCDesktop-windows-x64.zip`
   - `OCCDesktop-windows-x64.exe`
4. Wait for Zenodo to archive the release and assign a DOI.
5. Update README with DOI badge.

### Badge template

When DOI is available (example `10.5281/zenodo.XXXXXXX`):

```md
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
```

## 2) Preprint on arXiv

A short paper (8 to 10 pages) materially improves discoverability.

Suggested structure:

1. Abstract
2. Motivation: operational evaluability problem
3. OCC framework: \\(\Omega_I\\), verdicts, non-reinjection
4. Implementation: MRD suite + CLI
5. Highlight prediction: EDM-GW link
6. Falsification path and experimental strategy
7. Scope and limitations

## 3) Operational recommendation

- Do not keep large ZIP artifacts on `main`.
- Use GitHub Releases for binaries/artifacts.
- Keep docs and source in the normal tree.
