# ILSC MRD Suite — Extensions

This suite exists to improve **usability and discoverability** without modifying the
canonical 15-module suite.

It contains *meta‑MRDs* that validate:

- Claim spec shape + minimal operational domain locks
- UV guard behavior (NO‑EVAL when inaccessible knobs affect observables)
- Predictions registry integrity

Run it via:

```bash
occ verify --suite extensions
```
