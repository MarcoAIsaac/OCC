# MRD — Simetrías, Anomalías y Topología operacional (Ejecutable) / Operational Symmetries, Anomalies & Topology (Executable)

Este MRD cierra un módulo mínimo para verificar consistencia estructural en un sector gauge.

## Candados / Locks
- **SYM1**: simetría declarada (group)
- **AN1**: cargas declaradas
- **AN2**: cancelación lineal (∑q = 0) — PASS/FAIL
- **AN3**: cancelación cúbica (∑q³ = 0) — PASS/FAIL
- **TOPO1**: k declarado
- **TOPO2**: cuantización topológica (k entero) — PASS/FAIL

## Dataset auditable
- `data/mrd_sym_anom_topo_v1.csv`
- `data/mrd_sym_anom_topo_v1.meta.json`

## Inputs
- PASS: `inputs/mrd_sym_topo/pass.yaml`
- FAIL(AN3): `inputs/mrd_sym_topo/fail_AN3_cubic.yaml`
- FAIL(TOPO2): `inputs/mrd_sym_topo/fail_TOPO2_noninteger.yaml`
- NO-EVAL(SYM1): `inputs/mrd_sym_topo/noeval_SYM1_missing.yaml`

## Ejecutar
```bash
python scripts/run_mrd_sym_anom_topo.py inputs/mrd_sym_topo/pass.yaml
python scripts/run_mrd_sym_anom_topo.py inputs/mrd_sym_topo/fail_AN3_cubic.yaml
python scripts/run_mrd_sym_anom_topo.py inputs/mrd_sym_topo/fail_TOPO2_noninteger.yaml
python scripts/run_mrd_sym_anom_topo.py inputs/mrd_sym_topo/noeval_SYM1_missing.yaml
```
Outputs: `outputs/*.report.json`
