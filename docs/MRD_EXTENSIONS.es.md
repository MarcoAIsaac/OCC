# Suite de extensiones

El repo incluye una suite adicional:

`ILSC_MRD_suite_extensions/`

Su propósito es **mejorar la usabilidad** sin tocar el canon (los 15 módulos).

Incluye meta‑MRDs de ejemplo para:

- Validar que una especificación de afirmación esté bien formada.
- Demostrar el candado UV (NO‑EVAL si parámetros inaccesibles afectan observables).
- Demostrar el candado nuclear numerado (L4C*/L4E*, juez J4) en claims de física nuclear.
- Validar el `predictions/registry.yaml`.

## Ejecutar

```bash
occ verify --suite extensions
```

## Diseño

La suite canónica no cambia.
Las extensiones viven aparte para que el canon permanezca estable.
