# MRD — 4F Unificación operacional (Gating) (Ejecutable) / 4F Operational Unification (Gating) (Executable)

Este MRD implementa el **gating**: una propuesta “4F unificada” sólo es evaluable si todos sus observables
**mapean** a invariantes del diccionario 4F (aquí: observables tipo traza).

## Datos auditable
- Artefacto del diccionario: `data/dict_artifact_toy_v1.json`
- Meta: `data/dict_artifact_toy_v1.meta.json`

## Candados
- **4U1** diccionario presente
- **4U2** mapping completo para observables reclamados
- **4U3** mapping válido (targets existen)
- **4U4** consistencia numérica (si declara valores)
- **4U5** prohibición explícita de no-invariantes

## Inputs
- PASS: `inputs/mrd_4f_unif_op/pass.yaml`
- FAIL(4U4): `inputs/mrd_4f_unif_op/fail_4U4_mismatch.yaml`
- NO-EVAL(4U2): `inputs/mrd_4f_unif_op/noeval_4U2_incomplete.yaml`
- FAIL(4U5): `inputs/mrd_4f_unif_op/fail_4U5_noninvariant.yaml`

## Ejecutar
```bash
python scripts/run_mrd_4f_unif_op.py inputs/mrd_4f_unif_op/pass.yaml
python scripts/run_mrd_4f_unif_op.py inputs/mrd_4f_unif_op/fail_4U4_mismatch.yaml
python scripts/run_mrd_4f_unif_op.py inputs/mrd_4f_unif_op/noeval_4U2_incomplete.yaml
python scripts/run_mrd_4f_unif_op.py inputs/mrd_4f_unif_op/fail_4U5_noninvariant.yaml
```
