# Predictions registry

This folder contains a **versioned YAML registry** of falsifiable predictions.

Why it exists:

- Make the scientific value discoverable (no one reads 300+ pages first).
- Keep a single list of *what is testable* and *how*.
- Enable tooling (`occ predict`) for quick browsing.

## Files

- `registry.yaml` — source of truth.
- `TEMPLATE.yaml` — copy/paste template for new entries.

## CLI

```bash
occ predict list
occ predict show P-0003
```
