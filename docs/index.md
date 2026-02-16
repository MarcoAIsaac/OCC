# OCC: Runtime auditable para veredictos operacionales

<section class="occ-hero reveal-on-scroll">
  <p class="occ-eyebrow">Operational Consistency Compiler</p>
  <p class="occ-title">Ejecuta claims, valida módulos MRD y genera veredictos reproducibles</p>
  <p class="occ-lead">
    OCC prioriza afirmaciones falsables con una salida simple y auditable:
    <strong>PASS</strong>, <strong>FAIL</strong> o <strong>NO-EVAL</strong>.
  </p>
  <div class="occ-cta-row">
    <a class="md-button md-button--primary" href="START_HERE.md">Arrancar en 5 minutos</a>
    <a class="md-button" href="USAGE.md">Ver comandos del CLI</a>
  </div>
</section>

<section class="occ-metrics">
  <article class="occ-metric reveal-on-scroll">
    <span class="occ-metric-value" data-count-to="15">15</span>
    <span class="occ-metric-label">Módulos MRD canónicos</span>
  </article>
  <article class="occ-metric reveal-on-scroll">
    <span class="occ-metric-value" data-count-to="3">3</span>
    <span class="occ-metric-label">Veredictos operacionales</span>
  </article>
  <article class="occ-metric reveal-on-scroll">
    <span class="occ-metric-value" data-count-to="1">1</span>
    <span class="occ-metric-label">CLI estable: <code>occ</code></span>
  </article>
</section>

## Inicio rápido del proyecto

Ejecuta OCC localmente con un flujo corto y repetible:

```bash
make bootstrap
make smoke
make check
```

Si quieres levantar la documentación con recarga en vivo:

```bash
make docs-serve
```

## Flujo recomendado

<section class="occ-card-grid">
  <article class="occ-card reveal-on-scroll">
    <h3>1) Diagnóstico del entorno</h3>
    <p>Verifica versión, rutas y suites detectadas.</p>
    <pre><code>occ doctor</code></pre>
  </article>
  <article class="occ-card reveal-on-scroll">
    <h3>2) Descubrir capacidades</h3>
    <p>Inspecciona módulos MRD y predicciones sin entrar al código.</p>
    <pre><code>occ list --suite all
occ predict list</code></pre>
  </article>
  <article class="occ-card reveal-on-scroll">
    <h3>3) Ejecutar una evaluación real</h3>
    <p>Lanza un bundle y genera reporte en JSON.</p>
    <pre><code>occ run ILSC_MRD_suite_15_modulos_CANON/mrd_obs_isaac/inputs/mrd_obs_isaac/pass.yaml --out out/</code></pre>
  </article>
</section>

## Navegación canónica

- [Start Here](START_HERE.md): entrada guiada para primera ejecución.
- [Executive Summary](EXECUTIVE_SUMMARY.md): visión científica compacta.
- [Glosario](GLOSSARY.md): términos clave y contexto para no expertos.
- [Suite MRD](MRD_SUITE.md): estructura de módulos y lógica de veredictos.
- [Índice Canónico](INDEX_CANONICAL.md): mapa completo de documentación y assets.
