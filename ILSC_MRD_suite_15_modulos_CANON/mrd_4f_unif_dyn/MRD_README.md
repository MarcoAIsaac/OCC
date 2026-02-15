# MRD — Unificación dinámica 4F (Ejecutable) / 4F Dynamic Unification (Executable)

Este MRD implementa un test mínimo de unificación dinámica (toy) usando corrida 1-loop de acoplos gauge.

## Candados
- **UD0**: prerequisito de gating (debe pasar 4F unificación operacional)
- **UD1**: se encuentra un punto válido en el scan
- **UD2**: unificación dentro de tolerancia (PASS/FAIL)
- **UD3**: el scale de unificación μ_U está dentro de ΩI (o NO-EVAL)
- **UD4**: estabilidad de PASS bajo perturbaciones pequeñas (PCN-like)

## Dataset auditable
- `data/mrd_4f_unif_dyn_couplings_v1.csv`
- `data/mrd_4f_unif_dyn_couplings_v1.meta.json`

## Inputs
- PASS: `inputs/mrd_4f_unif_dyn/pass.yaml`
- FAIL(UD2): `inputs/mrd_4f_unif_dyn/fail_UD2_no_unification.yaml`
- NO-EVAL(UD0): `inputs/mrd_4f_unif_dyn/noeval_UD0_no_gating.yaml`
- FAIL(UD4): `inputs/mrd_4f_unif_dyn/fail_UD4_unstable.yaml`

## Ejecutar / Run
```bash
python scripts/run_mrd_4f_unif_dyn.py inputs/mrd_4f_unif_dyn/pass.yaml
python scripts/run_mrd_4f_unif_dyn.py inputs/mrd_4f_unif_dyn/fail_UD2_no_unification.yaml
python scripts/run_mrd_4f_unif_dyn.py inputs/mrd_4f_unif_dyn/noeval_UD0_no_gating.yaml
python scripts/run_mrd_4f_unif_dyn.py inputs/mrd_4f_unif_dyn/fail_UD4_unstable.yaml
```
Outputs: `outputs/*.report.json`
