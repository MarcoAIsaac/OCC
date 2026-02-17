# Executive Summary (scientific)

This document answers, in 5 to 10 minutes:

> What is OCC for, and how can I use it without reading 300+ pages first?

If you need formal detail, the full compendium is here:

- [`OCC_Canonical_Compendium_EN_v1.5.0.pdf`](OCC_Canonical_Compendium_EN_v1.5.0.pdf)

## 1) The problem OCC addresses

In modern theoretical physics, especially UV/BSM contexts, many claims are mathematically consistent
but operationally ambiguous:

- they depend on inaccessible scales or parameters,
- they recover fit quality by reintroducing hidden UV freedom,
- or they fail to declare a measurable domain where the claim can be evaluated.

This creates **UV malleability** in practice: the model remains difficult to falsify by shifting
inaccessible assumptions instead of producing robust, testable commitments.

## 2) What OCC is

OCC combines:

1. A canonical documentation set (terms, rules, criteria).
2. A runtime CLI (`occ`) that executes a 15-module MRD suite and emits auditable verdicts.

Think of it as a compilation discipline for claims:

- input: claim + minimal operational bundle
- output: verdict + traceable report

## 3) Core concept: operational domain \\(\Omega_I\\)

A useful claim should explicitly declare \\(\Omega_I\\):

- what is measurable,
- by which procedures,
- at what scale/precision regime,
- with which minimum assumptions.

When this cannot be declared consistently, the typical outcome is **NO-EVAL**.

## 4) Verdicts: PASS / FAIL / NO-EVAL

- **PASS**: evaluable in \\(\Omega_I\\) and consistent with module constraints.
- **FAIL**: evaluable, but fails consistency/constraints.
- **NO-EVAL**: not operationally evaluable under declared assumptions.

Important interpretation:

- PASS is not proof of truth; it indicates operational viability.
- FAIL is not global rejection of an idea; it points to a specific conflict.
- NO-EVAL is not a dismissal; it signals missing operational closure.

## 5) Minimal usage

```bash
occ doctor
occ list
occ run ILSC_MRD_suite_15_modulos_CANON/mrd_obs_isaac/inputs/mrd_obs_isaac/pass.yaml --out out/
occ verify --suite extensions
occ predict list
```

## 6) Highlight prediction

The canon highlights a falsifiable prediction:

- **EDM ↔ GW** correlation in baryogenesis scenarios.

This is a practical entry point for experimental planning and falsification strategy.
