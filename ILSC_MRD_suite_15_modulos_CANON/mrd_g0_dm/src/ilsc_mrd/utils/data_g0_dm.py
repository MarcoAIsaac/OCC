from __future__ import annotations
import csv, json
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class GalaxyDataset:
    dataset_id: str
    rows: List[Dict[str, Any]]
    meta: Dict[str, Any]

def load_galaxy(csv_path: str, meta_path: str) -> GalaxyDataset:
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    rows=[]
    with open(csv_path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append({
                "r_kpc": float(row["r_kpc"]),
                "v_obs_kms": float(row["v_obs_kms"]),
                "sigma_v": float(row["sigma_v"]),
                "alpha_obs_arcsec": float(row["alpha_obs_arcsec"]),
                "sigma_alpha": float(row["sigma_alpha"]),
                "source": row.get("source",""),
            })
    return GalaxyDataset(dataset_id=meta.get("dataset_id","unknown"), rows=rows, meta=meta)
