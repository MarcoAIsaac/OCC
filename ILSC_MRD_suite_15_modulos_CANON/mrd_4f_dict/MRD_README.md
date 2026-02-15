# MRD — 4F Diccionario operacional (CUI/HUI) (Ejecutable) / 4F Operational Dictionary (Executable)

Este MRD implementa un diccionario operacional mínimo tipo **CUI/HUI** en un sector gauge de juguete SU(2).

## Qué demuestra / What it demonstrates
- Un diccionario explícito **(paths → holonomías U(path))**.
- Composición a loops: **U(loop) = Π U(pathᵢ)**.
- Construcción de observables gauge-invariantes: **O = Tr(U(loop))/2**.
- Candados:
  - **4F1**: diccionario declarado (paths/loops/observables)
  - **4F2**: validez de grupo (unitaridad)
  - **4F3**: invariancia gauge (conjugación)
  - **4F4**: cierre (det(U)=1 en loops)

## Dataset auditable
- `data/mrd_4f_dict_spec_v1.csv`
- `data/mrd_4f_dict_spec_v1.meta.json`

## Entradas / Inputs
- PASS: `inputs/mrd_4f_dict/pass.yaml`
- FAIL(4F2): `inputs/mrd_4f_dict/fail_4F2_nonunitary.yaml`
- NO-EVAL(4F1): `inputs/mrd_4f_dict/noeval_4F1_missing.yaml`

## Ejecutar / Run
```bash
python scripts/run_mrd_4f_dict.py inputs/mrd_4f_dict/pass.yaml
python scripts/run_mrd_4f_dict.py inputs/mrd_4f_dict/fail_4F2_nonunitary.yaml
python scripts/run_mrd_4f_dict.py inputs/mrd_4f_dict/noeval_4F1_missing.yaml
```

Outputs: `outputs/*.report.json`
