# ILSC MRD-1X (SK Hybrid Maximum) — Starter Package (ES/EN)

## ES — Qué es esto
Este paquete es el **starter** del **MRD-1X** para el módulo **Schwinger–Keldysh (SK)**, en versión **híbrida máxima**:
- Backend **Qubit + baño** (Spin-boson / dephasing) → CPTP/Choi y diagnósticos “tipo información”.
- Backend **Oscilador + baño** (Caldeira–Leggett) → kernels continuos, PSD, FDT, regímenes Markov/no-Markov.

Incluye:
- **Esquema YAML** canónico (inputs).
- **8 casos** listos como plantillas: 2 PASS fuerte, 4 FAIL con diagnóstico, 2 NO-EVAL honestos.
- Estructura de repo para runner/compilación/checks/reportes (a implementar).

> Nota: Este starter NO incluye todavía el código ejecutable. Es el paquete de **especificación y entradas**.

## EN — What this is
This package is the **starter** for **MRD-1X** (maximum hybrid) of the **Schwinger–Keldysh (SK)** module:
- **Qubit + bath** backend (Spin-boson / dephasing) → CPTP/Choi, information-style diagnostics.
- **Harmonic oscillator + bath** backend (Caldeira–Leggett) → continuous kernels, PSD, FDT, Markov/non-Markov.

It includes:
- Canonical **YAML schema** (inputs).
- **8 template cases**: 2 strong PASS, 4 FAIL with clear diagnostics, 2 honest NO-EVAL.
- Repo scaffolding for runner/compile/checks/reports (to be implemented).

> Note: this starter does NOT yet ship executable code; it is the **spec + inputs** package.


## Modules
See `README_MODULES.md` for the standardized module interface scaffolding.
