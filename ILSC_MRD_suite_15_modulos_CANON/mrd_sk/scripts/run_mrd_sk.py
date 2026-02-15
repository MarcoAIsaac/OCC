#!/usr/bin/env python3
"""MRD-1X SK — runner wrapper."""
import sys, pathlib
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
from ilsc_mrd.runner import main
if __name__ == "__main__":
    main()
