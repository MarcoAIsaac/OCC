#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

echo ""
echo "✅ Environment ready. Try:" 
echo "  occ --help"
echo "  pytest -q"
echo "  occ verify" 
