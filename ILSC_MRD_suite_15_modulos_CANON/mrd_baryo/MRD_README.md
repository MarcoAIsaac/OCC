# MRD — Bariogénesis (Umbrella EWBG/Leptogénesis) (Ejecutable) / Baryogenesis (Executable)

Este MRD demuestra cómo ILSC fuerza **correlaciones**: si una explicación tipo EWBG produce Y_B,
debe también producir (en general) señales correlacionadas (EDM/GW) que se pueden contrastar.

Dataset (toy, update for real use):
- `data/mrd_baryo_obs_v1.csv`
- `data/mrd_baryo_obs_v1.meta.json`

Locks:
- B0: mode declared (EWBG/LEP)
- B1: Y_obs declared
- B2: match Y_B (PASS/FAIL)
- B3: Sakharov proxy (strong PT for EWBG; epsilon1 for LEP) (PASS/FAIL/NO-EVAL)
- B4: EDM constraint for EWBG (PASS/FAIL/NO-EVAL)

Run:
```bash
python scripts/run_mrd_baryo.py inputs/mrd_baryo/pass_EWBG.yaml
python scripts/run_mrd_baryo.py inputs/mrd_baryo/fail_B4_EDM.yaml
python scripts/run_mrd_baryo.py inputs/mrd_baryo/noeval_B3_missing_vcTc.yaml
```
