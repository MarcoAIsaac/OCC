# Agent notes

This repository is designed to be reproducible and audit-friendly.

If you are an automation/agent (Codex, CI, etc.):

- Prefer small, reviewable diffs.
- Do not rewrite the MRD suite outputs unless explicitly requested.
- Do not add large binaries. If a binary must be published, prefer GitHub Releases.
- Keep the CLI stable (`occ`).
