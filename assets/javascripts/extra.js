(() => {
  const langKey = "occ-docs-lang";
  const path = window.location.pathname;
  const lowerPath = path.toLowerCase();
  const isSpanishPath = lowerPath.includes("/es/");

  const knownPages = new Set([
    "index",
    "start_here",
    "cli",
    "usage",
    "troubleshooting",
    "executive_summary",
    "glossary",
    "faq",
    "judges_locks",
    "mrd_suite",
    "mrd_extensions",
    "predictions_registry",
    "index_canonical",
    "releasing",
    "search",
    "404",
  ]);

  const segments = path.split("/").filter(Boolean);
  const lastSegment = segments.length > 0 ? segments[segments.length - 1] : "";
  const pageSlug = lastSegment.replace(/\\.html$/i, "").toLowerCase();
  const isDefaultRoot = !isSpanishPath && (segments.length === 0 || !knownPages.has(pageSlug));

  if (isSpanishPath) {
    localStorage.setItem(langKey, "es");
    return;
  }
  if (!isDefaultRoot) {
    localStorage.setItem(langKey, "en");
    return;
  }

  const stored = localStorage.getItem(langKey);
  const browserLang = (navigator.languages && navigator.languages[0]) || navigator.language || "";
  const prefersSpanish = stored === "es" || (stored === null && browserLang.toLowerCase().startsWith("es"));
  if (!prefersSpanish) {
    return;
  }

  const query = window.location.search || "";
  const hash = window.location.hash || "";
  if (path.endsWith("/index.html")) {
    const target = path.replace(/index\\.html$/i, "es/index.html");
    window.location.replace(`${target}${query}${hash}`);
    return;
  }

  const base = path.endsWith("/") ? path : `${path}/`;
  window.location.replace(`${base}es/${query}${hash}`);
})();

(() => {
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const revealNodes = Array.from(document.querySelectorAll(".reveal-on-scroll"));
  const observedCounters = new WeakSet();

  const animateCounter = (node) => {
    if (reducedMotion || observedCounters.has(node)) {
      return;
    }
    observedCounters.add(node);

    const target = Number(node.dataset.countTo || node.textContent || "0");
    if (!Number.isFinite(target)) {
      return;
    }

    const duration = 750;
    const startedAt = performance.now();

    const tick = (now) => {
      const progress = Math.min((now - startedAt) / duration, 1);
      const eased = 1 - (1 - progress) * (1 - progress);
      node.textContent = String(Math.round(target * eased));

      if (progress < 1) {
        requestAnimationFrame(tick);
      }
    };

    requestAnimationFrame(tick);
  };

  const reveal = (node) => {
    node.classList.add("is-visible");
    node.querySelectorAll("[data-count-to]").forEach((counter) => animateCounter(counter));
  };

  if (reducedMotion || !("IntersectionObserver" in window)) {
    revealNodes.forEach(reveal);
    return;
  }

  const observer = new IntersectionObserver(
    (entries, currentObserver) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) {
          return;
        }
        reveal(entry.target);
        currentObserver.unobserve(entry.target);
      });
    },
    { threshold: 0.16, rootMargin: "0px 0px -4% 0px" }
  );

  revealNodes.forEach((node) => observer.observe(node));
})();
