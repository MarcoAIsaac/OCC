# Executive Summary (científico)

Este documento existe para responder, en 5–10 minutos, a la pregunta:

> **¿Para qué sirve OCC y cómo se usa sin leer 300+ páginas?**

Si luego quieres el detalle formal completo, el compendio está aquí:

- [`OCC_Compendio_Canonico_Completo.pdf`](OCC_Compendio_Canonico_Completo.pdf)

---

## 1) El problema que OCC intenta resolver

En física teórica moderna (especialmente en extensiones BSM/UV), es frecuente encontrarse con
afirmaciones que son matemáticamente consistentes pero **operacionalmente ambiguas**:

- dependen de escalas o parámetros en regímenes inaccesibles,
- reintroducen libertad “oculta” cuando el ajuste falla,
- o no especifican un dominio de medición donde la afirmación se pueda evaluar.

En la práctica, esto produce un patrón conocido como **malleabilidad UV**:

- si el dato no aparece, se “mueve” la escala,
- si un observable falla, se introduce otra pieza UV,
- si hay tensión con restricciones generales, se apela a un sector inaccesible.

Esto no es una crítica a la teoría en sí: es un **problema de despliegue** (*deployment*) y falsabilidad
cuando el contenido físico queda fuera del alcance operacional.

---

## 2) ¿Qué es OCC?

OCC (Operational Consistency Compiler) combina:

1. **Un canon** (documentación extensa) que define términos, reglas y criterios.
2. Un **runtime CLI** (`occ`) que ejecuta una suite MRD (15 módulos) y produce veredictos con reportes.

La intención es tratar afirmaciones físicas con una disciplina similar a “compilación”:

- input → afirmación + bundle/estructura mínima,
- output → veredicto + reporte auditable.

---

## 3) Concepto central: dominio operacional \(\Omega_I\)

Una afirmación física útil necesita declarar, explícitamente, su dominio operacional \(\Omega_I\):

- qué magnitudes son medibles,
- con qué procedimientos,
- en qué régimen de escalas/precisión,
- y con qué supuestos mínimos.

Cuando una afirmación no declara (o no puede declarar) un \(\Omega_I\) consistente, el resultado típico
no es “falso”: es **NO‑EVAL**.

---

## 4) Veredictos: PASS / FAIL / NO‑EVAL

OCC entrega veredictos con significado operativo:

- **PASS**: la afirmación es evaluable en \(\Omega_I\) y pasa restricciones inevitables dentro del alcance del módulo.
- **FAIL**: la afirmación es evaluable, pero falla restricciones/consistencia (con reporte del motivo).
- **NO‑EVAL**: no se puede evaluar de forma operacional bajo lo declarado (falta definición, medición o cierre).

**Interpretación importante:**

- PASS no “demuestra verdad”: indica *viabilidad operacional* para entrar a la siguiente etapa.
- FAIL no “mata” toda una idea: indica un conflicto concreto que debe resolverse sin reinyección UV.
- NO‑EVAL no es insulto: es una invitación a **declarar mejor** el dominio/medición.

---

## 5) ¿Cómo se usa (mínimo)?

### Ruta rápida

1) Instala y valida:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
occ --help
pytest -q
```

2) Ejecuta un bundle de ejemplo:

```bash
occ run ILSC_MRD_suite_15_modulos_CANON/mrd_4f_dict/inputs/mrd_4f_dict/pass.yaml --out out/
cat out/report.json
```

3) Suite completa (puede tardar):

```bash
occ verify
```

---

## 6) “Killer example” (lo que debes buscar en el canon)

El canon destaca una predicción falsable pensada para conectar marco ↔ observables:

- **Correlación EDM ↔ GW en bariogénesis**

Este tipo de ancla experimental es clave porque fuerza a que el marco no quede en un régimen UV
inaccesible: se compromete con una ruta de falsación.

> Nota: el compendio contiene el desarrollo completo, supuestos y condiciones. Este summary solo
> te dice “dónde mirar” y “por qué importa”.

---

## 7) Para no‑expertos (experimentalistas, cosmología, etc.)

Si llegas aquí sin el vocabulario interno:

- abre el glosario: [`GLOSSARY.md`](GLOSSARY.md)
- luego mira el índice: [`INDEX_CANONICAL.md`](INDEX_CANONICAL.md)
- y vuelve al CLI cuando tengas la ruta.

---

## 8) Siguiente paso recomendado (impacto/comunidad)

Para maximizar *discoverability*:

1) Preprint (ArXiv): 8–10 páginas (hep-ph o subárea relevante), centrado en la predicción destacada.
2) DOI (Zenodo): conectar repo → crear release → obtener DOI y badge.

Guía práctica: [`RELEASING.md`](RELEASING.md)
