# Glossary

This glossary helps readers from adjacent fields navigate OCC terminology quickly.

## Terms

### OCC

**Operational Consistency Compiler**. A framework + runtime CLI to evaluate claims through
operational evaluability, unavoidable consistency checks, and auditable outputs.

### \\(\Omega_I\\) — Declared operational domain

The explicit set of operations/measurements/regimes where a claim is intended to be evaluable.

### MRD

**Minimum Reproducible Demo**. A small, reproducible module implementing one part of the OCC criteria,
with simple inputs (YAML bundles) and deterministic reports.

### ISAAC

Canonical acronym related to operational closure constraints in the OCC framework.

### PASS / FAIL / NO-EVAL

Output taxonomy:

- **PASS**: evaluable in \\(\Omega_I\\) and consistent with the module.
- **FAIL**: evaluable but inconsistent.
- **NO-EVAL**: not evaluable due to missing operational definition/measurement/closure.

### UV malleability

Situation where inaccessible UV parameters let a model adapt repeatedly without clear falsification.

### UV reinjection

Pattern where additional inaccessible freedom is introduced after failure to rescue compatibility.

### EDM

**Electric Dipole Moment**. Observable sensitive to CP violation and beyond-standard-model effects.

### GW

**Gravitational Waves**. Includes stochastic backgrounds and cosmological signals.

### Baryogenesis

Physical mechanisms proposed to explain matter-antimatter asymmetry.

## Repository conventions

### YAML bundle

Input file under `ILSC_MRD_suite_15_modulos_CANON/<module>/inputs/...`.

### Report

Output `.report.json` (or `out/report.json` when using `--out`) containing verdict + details.
