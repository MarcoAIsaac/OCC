# MRD — Amplitudes & Positivity (Ejecutable) / Amplitudes & Positivity (Executable)

Este MRD implementa un conjunto mínimo de candados de consistencia tipo S-matrix:
**positividad**, **crossing** (toy) y un **proxy de unitaridad** sobre un grid en ΩI.

This MRD implements minimal S-matrix-style consistency locks:
**positivity**, (toy) **crossing**, and a **unitarity proxy** on an ΩI grid.

## Dataset (auditable grid) / Dataset (auditable grid)
- `data/mrd_amp_pos_grid_v1.csv`
- `data/mrd_amp_pos_grid_v1.meta.json`

## Locks / Candados
- AMP1: IR-safe dispersion scheme declared (NO-EVAL otherwise)
- AMP2: ΩI under cutoff fraction (NO UV reinjection)
- AMP3: positivity (c2>0)
- AMP4: crossing-evenness proxy (c3≈0 when required)
- AMP5: unitarity proxy |a0|≤1/2 on grid

## Run / Ejecutar
```bash
python scripts/run_mrd_amp_pos.py inputs/mrd_amp_pos/pass.yaml
python scripts/run_mrd_amp_pos.py inputs/mrd_amp_pos/fail_AMP3_positivity.yaml
python scripts/run_mrd_amp_pos.py inputs/mrd_amp_pos/noeval_AMP1_missing_ir.yaml
```
Outputs: `outputs/*.report.json`


## Real-data upgrade: aQGC sign-positivity + CMS 95% CL anchor (optional)

This MRD originally contains a *toy* forward-amplitude demo (grid + crossing proxy + partial-wave proxy).
To move toward a **realistic** amplitude-consistency workflow, the MRD now also supports an **aQGC (dimension-8)** mode:

- **AMP5_AQGC_POSITIVITY_TABLE4** (class = C): sign constraints representative of Table-4 positivity bounds for aQGC operators
  (FT0, FT1, FT2, FT8, FT9, ...). This is a strict inequality lock.

- **AMP6_AQGC_DATA_95CL_ANCHOR** (class = E): a minimal observational anchor using CMS-SMP-17-006 public 95% CL intervals
  (units: TeV^{-4}). This lock is **explicitly separated** as empirical (post-compile) and does not change the meaning of
  the consistency verdict.

### How to run (aQGC mode)

PASS example (positive coefficient inside the CMS 95% CL interval):

```bash
python scripts/run_mrd_amp_pos.py inputs/mrd_amp_pos/pass_aqgc_FT0.yaml
```

FAIL examples:

- Negative coefficient (violates AMP5 sign-positivity):

```bash
python scripts/run_mrd_amp_pos.py inputs/mrd_amp_pos/fail_aqgc_neg_FT0.yaml
```

- Outside the CMS 95% CL interval (fails AMP6 observational anchor, while still satisfying AMP5):

```bash
python scripts/run_mrd_amp_pos.py inputs/mrd_amp_pos/fail_aqgc_outside_FT0.yaml
```

