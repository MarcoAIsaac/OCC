# Resumen ejecutivo (científico)

Este documento responde, en 5-10 minutos, a la pregunta:

> ¿Para qué sirve OCC y cómo se usa sin leer 300+ páginas?

Si necesitas detalle formal completo, el compendio en espanol esta aqui:

- [`OCC_Compendio_Canonico_ES_v1.5.0.pdf`](OCC_Compendio_Canonico_ES_v1.5.0.pdf)

## 1) El problema que OCC busca resolver

En física teórica moderna, especialmente en contextos UV/BSM, muchas afirmaciones son
matemáticamente consistentes pero operacionalmente ambiguas:

- dependen de escalas o parámetros inaccesibles,
- recuperan ajuste reintroduciendo libertad UV oculta,
- o no declaran un dominio medible donde la afirmación pueda evaluarse.

Esto produce **malleabilidad UV** en la práctica: el modelo se vuelve difícil de falsar
al desplazar supuestos inaccesibles en lugar de asumir compromisos robustos y testeables.

## 2) Qué es OCC

OCC combina:

1. Un conjunto canónico de documentación (términos, reglas y criterios).
2. Un runtime con CLI (`occ`) que ejecuta una suite MRD de 15 módulos y emite veredictos auditables.

Puede leerse como disciplina de compilación para afirmaciones:

- entrada: afirmación + paquete operacional mínimo
- salida: veredicto + reporte trazable

## 3) Concepto central: dominio operacional `Omega_I`

Una afirmación útil debe declarar explícitamente `Omega_I`:

- qué es medible,
- con qué procedimientos,
- en qué régimen de escala/precisión,
- con qué supuestos mínimos.

Cuando esto no puede declararse consistentemente, el resultado típico es **NO-EVAL**.

## 4) Veredictos: PASS / FAIL / NO-EVAL

- **PASS**: evaluable en `Omega_I` y consistente con restricciones del módulo.
- **FAIL**: evaluable, pero falla consistencia/restricciones.
- **NO-EVAL**: no evaluable operacionalmente bajo los supuestos declarados.

Interpretación importante:

- PASS no demuestra verdad: indica viabilidad operacional.
- FAIL no descarta globalmente una idea: señala un conflicto específico.
- NO-EVAL no es rechazo: indica falta de cierre operacional.

## 5) Uso mínimo

```bash
occ doctor
occ list
occ run ILSC_MRD_suite_15_modulos_CANON/mrd_obs_isaac/inputs/mrd_obs_isaac/pass.yaml --out out/
occ verify --suite extensions
occ predict list
```

## 6) Predicción destacada

El canon destaca una predicción falsable:

- **Correlación EDM ↔ GW** en escenarios de bariogénesis.

Es un punto de entrada práctico para planificación experimental y estrategia de falsación.
