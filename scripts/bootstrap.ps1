$ErrorActionPreference = "Stop"

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

Write-Host ""
Write-Host "✅ Environment ready. Try:" 
Write-Host "  occ --help"
Write-Host "  pytest -q"
Write-Host "  occ verify"
