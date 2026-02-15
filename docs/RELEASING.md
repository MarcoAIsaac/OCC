# Releasing (DOI + ArXiv)

Este repo ya está “técnicamente listo”. Para maximizar impacto en comunidad científica, faltan dos
cosas típicas:

1) **DOI** (Zenodo) → hace el software **citable**.
2) **Preprint** (ArXiv) → hace el marco **discoverable**.

---

## 1) DOI con Zenodo (recomendado)

### Pasos

1. Conecta tu GitHub con Zenodo y habilita el repositorio.
2. Crea un **GitHub Release** (por ejemplo `v1.0.0`).
3. Espera a que Zenodo procese el release y te asigne un DOI.
4. Actualiza el README con el badge del DOI.

### Badge (plantilla)

Cuando tengas el DOI (ej. `10.5281/zenodo.XXXXXXX`), reemplaza:

```md
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
```

---

## 2) Preprint (ArXiv)

Un paper corto (8–10 páginas) aumenta muchísimo la visibilidad. Recomendación:

- Enfatiza **motivación** (malleabilidad UV / evaluabilidad)
- Describe el pipeline OCC (PASS/FAIL/NO‑EVAL)
- Destaca 1 predicción falsable (EDM ↔ GW en bariogénesis)
- Incluye cómo ejecutar un MRD del repo

### Sugerencia de estructura

1. Abstract
2. Motivation: operational evaluability problem
3. OCC framework: \(\Omega_I\), verdicts, non‑reinj.
4. Implementation: MRD suite + CLI
5. Highlighted prediction: EDM–GW link
6. How to falsify + experimental path
7. Limitations + scope

---

## 3) Recomendación “empresa”

- No guardes ZIPs grandes en `main`.
- Usa **GitHub Releases** para binarios/artefactos.
- Mantén docs y código en árbol normal del repo.
