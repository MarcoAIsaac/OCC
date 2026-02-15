# MRD — Cosmología operacional: Puente Local ↔ Cosmo (Ejecutable) / Operational Cosmology Bridge (Executable)

Candados/Locks:
- COS1: params declared (H0,Om,w0)
- COS2: local bound on gdot/G
- COS3: H(z) fit quality
- COS4: projection informativeness (ΔH from bounded Δw)

Dataset:
- `data/CC_data_unibo_v1.csv`
- `data/CC_data_unibo_v1.meta.json`

Run:
```bash
python scripts/run_mrd_cosmo_bridge.py inputs/mrd_cosmo_bridge/pass.yaml
python scripts/run_mrd_cosmo_bridge.py inputs/mrd_cosmo_bridge/fail_COS3_fit.yaml
python scripts/run_mrd_cosmo_bridge.py inputs/mrd_cosmo_bridge/noeval_COS4_missing_delta_w.yaml
```


**Dataset update (real-data anchor):** The default dataset for this MRD is now the public cosmic-chronometer H(z) compilation hosted at the University of Bologna (CC_data). It is packaged as `data/CC_data_unibo_v1.csv` with a hash-checked meta file.
