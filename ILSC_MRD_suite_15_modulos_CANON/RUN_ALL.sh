#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
python "$ROOT/RUN_ALL.py" --root "$ROOT" --summary "$ROOT/verification_summary.json" --strict
echo "Wrote verification_summary.json"
