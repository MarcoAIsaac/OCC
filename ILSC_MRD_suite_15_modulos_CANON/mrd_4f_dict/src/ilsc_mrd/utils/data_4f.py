from __future__ import annotations
import csv, json
from dataclasses import dataclass
from typing import Dict, Any, List

@dataclass
class DictSpec:
    dataset_id: str
    paths: List[Dict[str, Any]]
    loops: List[Dict[str, Any]]
    observables: List[Dict[str, Any]]
    meta: Dict[str, Any]

def _parse_axis(s: str):
    parts = [p.strip() for p in s.split(",") if p.strip()]
    return [float(x) for x in parts] if parts else None

def load_4f_spec(csv_path: str, meta_path: str) -> DictSpec:
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    paths, loops, obs = [], [], []
    with open(csv_path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            kind = (row.get("kind") or "").strip()
            if kind == "path":
                paths.append({
                    "path_id": row["id"],
                    "axis": _parse_axis(row.get("axis","1,0,0")) or [1.0,0.0,0.0],
                    "angle": float(row.get("angle","0.0") or 0.0),
                })
            elif kind == "loop":
                pids = [x for x in (row.get("path_ids") or "").split(";") if x]
                loops.append({"loop_id": row["id"], "path_ids": pids})
            elif kind == "obs":
                obs.append({"name": row["id"], "type": row.get("obs_type","trace"), "loop_id": row.get("path_ids")})
    return DictSpec(dataset_id=meta.get("dataset_id","unknown"), paths=paths, loops=loops, observables=obs, meta=meta)
