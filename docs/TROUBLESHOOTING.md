# Troubleshooting

## `occ` command not found

If installed in a virtual environment:

```bash
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## `occ verify` takes too long

Full verification runs many cases.

- Prefer the manual full-suite workflow in GitHub Actions.
- Reduce per-case timeout:

```bash
occ verify --timeout 60
```

## `NO-EVAL(TR*)` in `occ judge`

Declare only existing source paths or run without `--strict-trace`.

## `occ research` returns no results

External search uses public APIs (arXiv/Crossref) and depends on network access.

- Check outbound connectivity.
- Increase timeout:

```bash
occ research examples/claim_specs/minimal_pass.yaml --timeout 30
```
