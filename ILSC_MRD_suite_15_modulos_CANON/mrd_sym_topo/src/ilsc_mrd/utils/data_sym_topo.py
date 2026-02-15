from __future__ import annotations
import csv, json
from dataclasses import dataclass
from typing import Dict, Any, List

@dataclass
class SymTopoData:
    dataset_id: str
    fermions: List[Dict[str, Any]]
    chern_k: float
    meta: Dict[str, Any]

def load_sym_topo(csv_path: str, meta_path: str) -> SymTopoData:
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    fermions = []
    k = float("nan")
    with open(csv_path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            if row["type"] == "fermion":
                fermions.append({"name": row["name"], "charge_q": float(row["charge_q"])})
            elif row["type"] == "topo" and row["name"] == "chern_k":
                k = float(row["charge_q"])
    return SymTopoData(dataset_id=meta.get("dataset_id","unknown"), fermions=fermions, chern_k=k, meta=meta)
