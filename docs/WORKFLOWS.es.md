# Flujos de automatización

Esta página documenta scripts auxiliares para tareas recurrentes del proyecto.

## 1) Release doctor

Valida consistencia de metadatos de publicación entre:

- `pyproject.toml`
- `CHANGELOG.md`
- `CITATION.cff`
- `.zenodo.json`
- badges DOI en `README.md` y `README.es.md`

Ejecutar:

```bash
python scripts/release_doctor.py --strict
```

Con DOI esperado explícito:

```bash
python scripts/release_doctor.py --strict --expected-doi 10.5281/zenodo.18656426
```

## 2) Consistencia de docs EN/ES

Audita pares bilingües y enlaces locales:

```bash
python scripts/check_docs_i18n.py --strict
```

## 3) CI doctor

Resume ejecuciones fallidas recientes en GitHub Actions (requiere `gh` autenticado):

```bash
python scripts/ci_doctor.py --workflow CI --limit 12
```

Salida JSON:

```bash
python scripts/ci_doctor.py --workflow CI --json
```

## 4) Generador de release notes

Construye notas de versión desde `CHANGELOG.md` + commits recientes:

```bash
python scripts/generate_release_notes.py
```

Guardar a archivo:

```bash
python scripts/generate_release_notes.py --output /tmp/release-notes.md
```

## 5) Flujo guiado MRD

Claim -> evaluación por jueces -> generación opcional de módulo -> verificación opcional.

Modo seguro por defecto: no ejecuta módulos MRD generados salvo que pases `--verify-generated`.

```bash
python scripts/mrd_flow.py examples/claim_specs/minimal_pass.yaml --generate-module
```

Con borrador de predicción y verificación:

```bash
python scripts/mrd_flow.py examples/claim_specs/minimal_pass.yaml \
  --generate-module \
  --create-prediction \
  --verify-generated
```

## Targets de Make

Atajos equivalentes:

```bash
make release-doctor
make docs-i18n
make ci-doctor
make release-notes
```
