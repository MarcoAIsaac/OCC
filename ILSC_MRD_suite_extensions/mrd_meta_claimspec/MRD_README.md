# MRD — Meta ClaimSpec

This MRD validates a minimal *claim spec* format and demonstrates operational verdicts.

It intentionally runs the same built‑in judge pipeline exposed by:

```bash
occ judge <claim.yaml>
```

Cases:

- `pass.yaml` → PASS
- `noeval_missing_domain.yaml` → NO‑EVAL(DOM1)
