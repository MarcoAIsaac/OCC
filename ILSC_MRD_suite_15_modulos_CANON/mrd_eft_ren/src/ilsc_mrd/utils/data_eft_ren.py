from __future__ import annotations
import csv, json
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class EFTDatum:
    dataset_id: str
    row: Dict[str, Any]
    meta: Dict[str, Any]

def load_eft_datum(csv_path: str, meta_path: str) -> EFTDatum:
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    with open(csv_path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        row = next(r)
    out = {
        "E_probe_GeV": float(row["E_probe_GeV"]),
        "O_obs": float(row["O_obs"]),
        "sigma": float(row["sigma"]),
        "source": row.get("source",""),
    }
    return EFTDatum(dataset_id=meta.get("dataset_id","unknown"), row=out, meta=meta)
