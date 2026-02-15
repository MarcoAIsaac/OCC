from __future__ import annotations
import csv, json
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class GravIRBounds:
    dataset_id: str
    row: Dict[str, Any]
    meta: Dict[str, Any]

def load_bounds(csv_path: str, meta_path: str) -> GravIRBounds:
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    with open(csv_path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        row = next(r)
    out = {k: float(row[k]) for k in ["dgamma_max","dbeta_max","dcT_max","v_over_c_dataset"]}
    out["source"] = row.get("source","")
    return GravIRBounds(dataset_id=meta.get("dataset_id","unknown"), row=out, meta=meta)
