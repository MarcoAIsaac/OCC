from __future__ import annotations
import csv, json
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class VacBounds:
    dataset_id: str
    row: Dict[str, Any]
    meta: Dict[str, Any]

def load_vac_bounds(csv_path: str, meta_path: str) -> VacBounds:
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    with open(csv_path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        row = next(r)
    out = {k: float(row[k]) for k in ["w_center","w_halfwidth","coupling_max"]}
    out["source"] = row.get("source","")
    return VacBounds(dataset_id=meta.get("dataset_id","unknown"), row=out, meta=meta)
