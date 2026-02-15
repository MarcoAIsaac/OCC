# ILSC — MRD Suite (15 módulos cerrados)

Esta carpeta contiene 15 MRDs ejecutables, cada uno en su subcarpeta.

## Estructura
- `mrd_sk/` — MRD-1X Schwinger–Keldysh (base ejecutable)
- `mrd_obs_isaac/` — Observabilidad + ISAAC
- `mrd_uv_omegai/` — UV → ΩI (Proyección auditable)
- `mrd_sym_topo/` — Simetrías / Anomalías / Topología operacional
- `mrd_4f_dict/` — Diccionario 4F (CUI/HUI)
- `mrd_4f_unif_op/` — Unificación operacional (gating)
- `mrd_4f_unif_dyn/` — Unificación dinámica 4F
- `mrd_amp_pos/` — Amplitudes & positividad
- `mrd_eft_ren/` — EFT & renormalización operacional
- `mrd_grav_ir/` — Gravedad efectiva IR / GW / PPN
- `mrd_cosmo_bridge/` — Cosmología operacional: puente local↔cosmo
- `mrd_vac_de/` — Vacío / Energía oscura
- `mrd_g0_dm/` — G0: DM efectiva (rotación+lente)
- `mrd_rama_ef/` — Rama efectiva: decoherencia / objetividad
- `mrd_baryo/` — Bariogénesis (umbrella EWBG/LEP)

Cada MRD trae:
- `MRD_README.md` (bilingüe ES/EN)
- `scripts/run_*.py`
- `inputs/` con casos PASS / FAIL / NO-EVAL
- `data/` con datasets auditables y `*.meta.json`
- `certs/` con IO/RFS y PA cuando aplica

## Ejecución
Entra a cualquier carpeta y corre el script indicado en su README, por ejemplo:

```bash
cd mrd_baryo
python scripts/run_mrd_baryo.py inputs/mrd_baryo/pass_EWBG.yaml
```
