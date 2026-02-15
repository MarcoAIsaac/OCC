from __future__ import annotations
import csv, json
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class AmpGrid:
    dataset_id: str
    energies: List[float]
    meta: Dict[str, Any]

def load_amp_grid(csv_path: str, meta_path: str) -> AmpGrid:
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    Es = []
    with open(csv_path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            Es.append(float(row["E_GeV"]))
    return AmpGrid(dataset_id=meta.get("dataset_id","unknown"), energies=Es, meta=meta)
