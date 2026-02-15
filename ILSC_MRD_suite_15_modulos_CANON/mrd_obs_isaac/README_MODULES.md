# ILSC MRD — Modules (Scaffolding v1)

This repo currently implements MRD-1X-SK. We add a **module interface** so we can extend MRDs to:
- vacuum/DE
- G0 effective DM
- 4F operational dictionary (CUI/HUI)
- baryogenesis
- cosmology bridge (local ↔ cosmological)

## Module interface
Each module file exports:
- `compile(cfg) -> artifact` : finite auditable projection Π + error (if applicable)
- `check(artifact, cfg) -> (locks, diagnostic)` : module-specific locks

See `src/ilsc_mrd/modules/base.py`.

## MRD-PA dataset hardening
A deterministic audited dataset is included at:
- `/mnt/data/ILSC-MRD-1X-SK_exec_v4/data/mrd_pa_dataset_v1.csv`
- `/mnt/data/ILSC-MRD-1X-SK_exec_v4/data/mrd_pa_dataset_v1.meta.json`

The run audits dataset hashes into `_data_obj` automatically, so PA5/RFS5 become hard.
