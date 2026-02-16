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
