from __future__ import annotations
import csv, json
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class CouplingsAtMu0:
    dataset_id: str
    row: Dict[str, Any]
    meta: Dict[str, Any]

def load_couplings(csv_path: str, meta_path: str) -> CouplingsAtMu0:
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    with open(csv_path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        row = next(r)
    out = {
        "mu0_GeV": float(row["mu0_GeV"]),
        "g1": float(row["g1"]),
        "g2": float(row["g2"]),
        "g3": float(row["g3"]),
        "sigma": float(row.get("sigma","0.0") or 0.0),
        "source": row.get("source",""),
    }
    return CouplingsAtMu0(dataset_id=meta.get("dataset_id","unknown"), row=out, meta=meta)
