# Releasing (DOI + arXiv)

This repository is technically ready. To maximize scientific reach, two publication steps are recommended:

1. **DOI** (Zenodo) to make software citable.
2. **Preprint** (arXiv) to make the framework discoverable.

## 1) DOI with Zenodo

### Steps

1. Connect GitHub with Zenodo and enable this repository.
2. Push a version tag (for example `v1.3.1`).
3. Windows desktop assets are built automatically by workflow
   `.github/workflows/windows_desktop_release.yml` and attached to the release:
   - `OCCDesktop-Setup-windows-x64.exe`
   - `OCCDesktop-windows-x64.zip`
   - `OCCDesktop-windows-x64.exe`
   - `OCCDesktop-windows-x64.sha256`
   - If needed, run workflow manually with input `release_tag` (example `v1.3.0`).
4. Wait for Zenodo to archive the release and assign a DOI.
5. Update README with DOI badge.

### Optional: Authenticode signing (recommended)

To reduce Windows SmartScreen warnings, configure repository secrets:

- `WINDOWS_CODESIGN_PFX_B64`: base64-encoded code-signing `.pfx`.
- `WINDOWS_CODESIGN_PFX_PASSWORD`: password for that certificate.

When those secrets are present, workflow `windows_desktop_release.yml` signs the EXE and installer,
timestamps them, and verifies signature status.

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
- Publish and verify SHA256 checksums from release assets.
- For direct download links, prefer `/releases/latest/download/...` only after assets are uploaded.
