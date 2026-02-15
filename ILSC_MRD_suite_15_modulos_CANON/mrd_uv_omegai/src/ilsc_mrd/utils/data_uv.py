from __future__ import annotations
import csv, json
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class UVDataset:
    dataset_id: str
    rows: List[Dict[str, Any]]
    meta: Dict[str, Any]

def load_uv_dataset(csv_path: str, meta_path: str) -> UVDataset:
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    with open(csv_path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        rows = []
        for row in r:
            rr = dict(row)
            rr["E_GeV"] = float(rr["E_GeV"])
            rr["O_obs"] = float(rr["O_obs"])
            rr["sigma"] = float(rr["sigma"])
            rows.append(rr)
    return UVDataset(dataset_id=meta.get("dataset_id","unknown"), rows=rows, meta=meta)
