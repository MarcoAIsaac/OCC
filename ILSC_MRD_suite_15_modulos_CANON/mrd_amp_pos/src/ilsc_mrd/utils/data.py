from __future__ import annotations
import csv, json
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

@dataclass
class Dataset:
    dataset_id: str
    rows: List[Dict[str, Any]]
    meta: Dict[str, Any]

def load_csv_with_meta(csv_path: str, meta_path: str) -> Dataset:
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            # coerce numeric fields if possible
            rr = dict(r)
            for k in ["E_GeV","O_eff","sigma"]:
                if k in rr:
                    rr[k] = float(rr[k])
            rows.append(rr)
    return Dataset(dataset_id=meta.get("dataset_id","unknown"), rows=rows, meta=meta)
