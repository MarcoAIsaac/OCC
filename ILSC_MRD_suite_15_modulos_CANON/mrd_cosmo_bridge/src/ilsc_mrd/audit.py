import hashlib, json, os, platform, sys, subprocess, pathlib, fnmatch, time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple, Optional

def sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def sha256_json(obj: Any) -> str:
    data = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",",":")).encode("utf-8")
    return sha256_bytes(data)

def env_fingerprint() -> Dict[str, Any]:
    fp = {
        "python": sys.version.replace("\n"," "),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }
    try:
        fp["git_commit"] = subprocess.check_output(["git","rev-parse","HEAD"], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        fp["git_commit"] = None
    return fp

def versions() -> Dict[str, Any]:
    v = {"numpy": None, "scipy": None, "pyyaml": None}
    try:
        import numpy as np
        v["numpy"] = np.__version__
    except Exception:
        pass
    try:
        import scipy
        v["scipy"] = scipy.__version__
    except Exception:
        pass
    try:
        import yaml
        v["pyyaml"] = getattr(yaml, "__version__", None)
    except Exception:
        pass
    return v

def env_hash() -> str:
    return sha256_json({"fingerprint": env_fingerprint(), "versions": versions()})

def list_files(root: str, include_globs: List[str]) -> List[str]:
    rootp = pathlib.Path(root)
    out: List[str] = []
    for p in rootp.rglob("*"):
        if not p.is_file():
            continue
        rel = str(p.relative_to(rootp))
        if any(fnmatch.fnmatch(rel, g) for g in include_globs):
            out.append(str(p))
    out.sort()
    return out

def tree_hash(root: str, include_globs: Optional[List[str]] = None) -> Dict[str, Any]:
    """Return a stable hash of a file tree (paths + file hashes)."""
    if include_globs is None:
        include_globs = ["src/**/*.py", "pyproject.toml", "inputs/**/*.yaml", "README*.md"]
    files = list_files(root, include_globs)
    manifest: List[Tuple[str,str]] = []
    rootp = pathlib.Path(root)
    for f in files:
        rp = str(pathlib.Path(f).relative_to(rootp))
        manifest.append((rp, sha256_file(f)))
    h = sha256_json(manifest)
    return {"root": os.path.abspath(root), "include": include_globs, "manifest": manifest, "tree_sha256": h}

def now_utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
