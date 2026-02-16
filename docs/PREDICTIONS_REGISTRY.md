# Predictions registry

El archivo `predictions/registry.yaml` existe para que las predicciones sean **discoverable**.

En física, el problema típico es que un trabajo puede estar bien, pero si la predicción falsable está enterrada en 300 páginas, nadie la encuentra.

## Ver predicciones

```bash
occ predict list
occ predict show P-0003
```

## Añadir una predicción nueva

1. Copia `predictions/TEMPLATE.yaml`.
2. Añádelo como nueva entrada en `predictions/registry.yaml`.
3. Asegúrate de que:
   - el `id` sea único,
   - la `summary` sea falsable,
   - incluya al menos un canal de test (`tests`).

## Validación

La suite de extensiones incluye un meta‑MRD que valida el registry.

```bash
occ verify --suite extensions
```
