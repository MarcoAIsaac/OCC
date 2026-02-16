# Glosario

Este glosario existe para que un lector (experimentalista, cosmólogo, o teórico de otra subárea)
pueda navegar el canon sin atascarse en siglas internas.

---

## Términos

### **OCC**
**Operational Consistency Compiler**. Marco + runtime (CLI) para evaluar afirmaciones físicas con un
enfoque operacional: evaluabilidad, consistencia inevitable y reporte auditable.

### **\(\Omega_I\) — Dominio operacional declarado**
Conjunto explícito de operaciones/mediciones/regímenes en los que una afirmación pretende ser evaluable.

### **MRD**
**Minimum Reproducible Demo**. “Módulo mínimo reproducible” que implementa una parte del criterio OCC
con entradas simples (paquetes YAML) y reportes deterministas.

### **ISAAC**
Sigla usada en el canon para referirse a *cierre operacional* (ej. anclajes operacionales provenientes de
luz + mecánica cuántica + relatividad general, según el marco).

> Si eres nuevo: trátalo como “el conjunto mínimo de restricciones operacionales” sobre lo que cuenta como medible.

### **PASS / FAIL / NO‑EVAL**
Taxonomía de salida de OCC:

- **PASS**: evaluable en \(\Omega_I\) y consistente con el módulo.
- **FAIL**: evaluable pero inconsistente (con motivo en el reporte).
- **NO‑EVAL**: no evaluable (falta especificación operacional, medición, o cierre).

### **Malleabilidad UV**
Situación donde los parámetros “UV” (alta energía / inaccesibles) permiten re‑ajustar un modelo para
evitar falsación sin cambiar el núcleo de la propuesta.

### **Reinyección UV**
Patrón donde, al enfrentar un fallo, se introduce libertad adicional en un régimen inobservable como
salida (por ejemplo, agregando sectores inaccesibles para rescatar compatibilidad).

### **EDM**
**Electric Dipole Moment** (momento dipolar eléctrico). Observable sensible a CP‑violation y nueva física.

### **GW**
**Gravitational Waves** (ondas gravitacionales). Incluye fondos estocásticos y señales cosmológicas.

### **Bariogénesis**
Mecanismos físicos propuestos para explicar el exceso bariónico del universo (asimetría materia/antimateria).

---

## Convenciones prácticas del repo

### Paquete YAML
Archivo YAML bajo `ILSC_MRD_suite_15_modulos_CANON/<módulo>/inputs/...` usado como entrada mínima.

### Reporte
Salida `.report.json` (o `out/report.json` si usas `--out`) que incluye veredicto y detalles.
