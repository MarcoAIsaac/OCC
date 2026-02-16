# Publicación (DOI + arXiv)

Este repositorio ya está técnicamente listo. Para maximizar alcance científico, se recomiendan dos pasos:

1. **DOI** (Zenodo) para volver el software citable.
2. **Preprint** (arXiv) para mejorar la visibilidad del marco.

## 1) DOI con Zenodo

### Pasos

1. Conecta GitHub con Zenodo y habilita este repositorio.
2. Crea una publicación de versión en GitHub (por ejemplo `v1.0.0`).
3. Los assets de escritorio para Windows se construyen automáticamente con
   `.github/workflows/windows_desktop_release.yml` y se adjuntan al release:
   - `OCCDesktop-Setup-windows-x64.exe`
   - `OCCDesktop-windows-x64.zip`
   - `OCCDesktop-windows-x64.exe`
   - `OCCDesktop-windows-x64.sha256`
   - Si falla la carga, ejecuta el workflow manualmente con `release_tag` (ejemplo `v1.3.0`).
4. Espera a que Zenodo archive la versión y asigne DOI.
5. Actualiza `README` con el distintivo del DOI.

### Opcional: firma Authenticode (recomendado)

Para reducir avisos de SmartScreen en Windows, configura estos secretos:

- `WINDOWS_CODESIGN_PFX_B64`: certificado de firma `.pfx` codificado en base64.
- `WINDOWS_CODESIGN_PFX_PASSWORD`: contraseña del certificado.

Cuando esos secretos existen, el workflow `windows_desktop_release.yml` firma el EXE y el
instalador, aplica timestamp y valida el estado de la firma.

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
- Publicar y verificar checksums SHA256 en los assets del release.
- Para enlaces directos `/releases/latest/download/...`, esperar a que los assets estén subidos.
