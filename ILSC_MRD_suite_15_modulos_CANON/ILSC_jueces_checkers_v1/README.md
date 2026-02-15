# ILSC — Judges Certificates (PA/IO/RFS) Schemas + Checkers (v1)

This folder contains:
- JSON Schemas for PA-CERT, IO-CERT, RFS-CERT
- Minimal Python checkers to validate presence + compute basic verdict downgrades:
  - Missing required fields -> NO-EVAL(<CODE>)
  - Projection dominance check (PA3): delta_proj vs sigma_data
  - PCN/PCD stability flags (RFS2/RFS3): verdict flips -> NO-EVAL

Install:
    pip install jsonschema pyyaml

Run:
    python -m checkers.validate examples/pa_cert_example.json
