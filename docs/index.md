# OCC: Auditable runtime for operational verdicts

<section class="occ-hero reveal-on-scroll">
  <p class="occ-eyebrow">Operational Consistency Compiler</p>
  <p class="occ-title">Run claims, validate MRD modules, and emit reproducible verdicts</p>
  <p class="occ-lead">
    OCC prioritizes falsifiable claims with a simple, auditable output:
    <strong>PASS</strong>, <strong>FAIL</strong>, or <strong>NO-EVAL</strong>.
  </p>
  <div class="occ-cta-row">
    <a class="md-button md-button--primary" href="START_HERE.md">Get started in 5 minutes</a>
    <a class="md-button" href="USAGE.md">See CLI commands</a>
  </div>
</section>

<section class="occ-metrics">
  <article class="occ-metric reveal-on-scroll">
    <span class="occ-metric-value" data-count-to="15">15</span>
    <span class="occ-metric-label">Canonical MRD modules</span>
  </article>
  <article class="occ-metric reveal-on-scroll">
    <span class="occ-metric-value" data-count-to="3">3</span>
    <span class="occ-metric-label">Operational verdicts</span>
  </article>
  <article class="occ-metric reveal-on-scroll">
    <span class="occ-metric-value" data-count-to="1">1</span>
    <span class="occ-metric-label">Stable CLI: <code>occ</code></span>
  </article>
</section>

## Quick project bootstrap

Run OCC locally with a short, reproducible flow:

```bash
make bootstrap
make smoke
make check
```

To launch docs with live reload:

```bash
make docs-serve
```

## Recommended flow

<section class="occ-card-grid">
  <article class="occ-card reveal-on-scroll">
    <h3>1) Diagnose your environment</h3>
    <p>Check versions, paths, and discovered suites.</p>
    <pre><code>occ doctor</code></pre>
  </article>
  <article class="occ-card reveal-on-scroll">
    <h3>2) Discover capabilities</h3>
    <p>Inspect MRD modules and predictions before diving into code.</p>
    <pre><code>occ list --suite all
occ predict list</code></pre>
  </article>
  <article class="occ-card reveal-on-scroll">
    <h3>3) Run a real evaluation</h3>
    <p>Execute a bundle and generate a JSON report.</p>
    <pre><code>occ run ILSC_MRD_suite_15_modulos_CANON/mrd_obs_isaac/inputs/mrd_obs_isaac/pass.yaml --out out/</code></pre>
  </article>
</section>

## Canon navigation

- [Start Here](START_HERE.md): guided entry point for first execution.
- [Executive Summary](EXECUTIVE_SUMMARY.md): compact scientific overview.
- [Glossary](GLOSSARY.md): key terms and context for non-specialists.
- [MRD Suite](MRD_SUITE.md): module layout and verdict logic.
- [Canonical Index](INDEX_CANONICAL.md): full map of docs and assets.
