# Registro de predicciones

El archivo `predictions/registry.yaml` hace que las predicciones sean más fáciles de descubrir.

En la práctica, una predicción puede ser sólida pero difícil de encontrar si está enterrada en
documentos largos. El registro resuelve ese problema de visibilidad.

## Ver predicciones

```bash
occ predict list
occ predict show P-0003
```

## Añadir una predicción

1. Copia `predictions/TEMPLATE.yaml`.
2. Añade una entrada en `predictions/registry.yaml`.
3. Asegúrate de que tenga:
   - `id` único,
   - `summary` falsable,
   - al menos un canal de prueba en `tests`.

## Validación

La suite de extensiones incluye un meta-MRD que valida el registro:

```bash
occ verify --suite extensions
```
