from __future__ import annotations
import csv, json
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class HzDataset:
    dataset_id: str
    rows: List[Dict[str, Any]]
    meta: Dict[str, Any]

def load_Hz(csv_path: str, meta_path: str) -> HzDataset:
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append({"z": float(row["z"]), "H_obs": float(row["H_obs"]), "sigma": float(row["sigma"]), "source": row.get("source","")})
    return HzDataset(dataset_id=meta.get("dataset_id","unknown"), rows=rows, meta=meta)
