# MRD — Gravedad efectiva IR / GW / PPN (Ejecutable) / Effective Gravity IR / GW / PPN (Executable)

Checks:
- PPN constraints (γ, β)
- GW propagation speed constraint (c_T/c)
- IR domain validity via v/c

Dataset:
- `data/mrd_grav_ir_bounds_v1.csv`
- `data/mrd_grav_ir_bounds_v1.meta.json`

Run:
```bash
python scripts/run_mrd_grav_ir.py inputs/mrd_grav_ir/pass.yaml
python scripts/run_mrd_grav_ir.py inputs/mrd_grav_ir/fail_GR3_cT.yaml
python scripts/run_mrd_grav_ir.py inputs/mrd_grav_ir/noeval_GR1_domain.yaml
```


**Dataset update (real bounds):** `data/mrd_grav_ir_bounds_v1.csv` now encodes published experimental constraints (Cassini PPN γ, solar-system β, and GW170817 speed-of-gravity bound). The MRD uses these as quantitative IR locks.
