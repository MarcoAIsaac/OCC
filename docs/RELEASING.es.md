# Publicación (DOI + arXiv)

Este repositorio ya está técnicamente listo. Para maximizar alcance científico, se recomiendan dos pasos:

1. **DOI** (Zenodo) para volver el software citable.
2. **Preprint** (arXiv) para mejorar la visibilidad del marco.

## 1) DOI con Zenodo

### Pasos

1. Conecta GitHub con Zenodo y habilita este repositorio.
2. Crea una publicación de versión en GitHub (por ejemplo `v1.0.0`).
3. Espera a que Zenodo archive la versión y asigne DOI.
4. Actualiza `README` con el distintivo del DOI.

### Plantilla de distintivo

Cuando tengas DOI (ejemplo `10.5281/zenodo.XXXXXXX`):

```md
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
```

## 2) Preprint en arXiv

Un artículo corto (8-10 páginas) mejora mucho la visibilidad.

Estructura sugerida:

1. Resumen
2. Motivación: problema de evaluabilidad operacional
3. Marco OCC: `Omega_I`, veredictos y no-reinyección
4. Implementación: suite MRD + CLI
5. Predicción destacada: vínculo EDM-GW
6. Ruta de falsación y estrategia experimental
7. Alcance y limitaciones

## 3) Recomendación operativa

- No guardar ZIPs grandes en `main`.
- Usar GitHub Releases para binarios/artefactos.
- Mantener docs y código en el árbol normal del repositorio.
