/**
 * RawLead front page — Lenis smooth scroll, progress, reveal. Без snap.
 */
(function () {
  "use strict";

  var main = document.querySelector(".rl-landing");
  if (!main) {
    return;
  }

  var prefersReduced =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  document.documentElement.classList.add("rl-smooth-root");

  /* Progress bar */
  var progress = document.createElement("div");
  progress.className = "rl-scroll-progress";
  progress.setAttribute("aria-hidden", "true");
  document.body.appendChild(progress);

  function updateProgress(scrollY) {
    var y = scrollY;
    if (y === undefined) {
      y = window.scrollY || document.documentElement.scrollTop;
    }
    var max =
      document.documentElement.scrollHeight -
      document.documentElement.clientHeight;
    progress.style.width = (max > 0 ? (y / max) * 100 : 0) + "%";
  }

  /* Reveal on scroll + flow source cubes */
  var motionTargets = main.querySelectorAll(".rl-reveal, .rl-flow__sources");
  if (!prefersReduced && "IntersectionObserver" in window) {
    var revealIo = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            revealIo.unobserve(entry.target);
          }
        });
      },
      { root: null, rootMargin: "0px 0px -10% 0px", threshold: 0.1 }
    );
    var sourcesIo = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            sourcesIo.unobserve(entry.target);
          }
        });
      },
      { root: null, rootMargin: "0px 0px -8% 0px", threshold: 0.15 }
    );
    motionTargets.forEach(function (el) {
      if (el.classList.contains("rl-flow__sources")) {
        sourcesIo.observe(el);
      } else {
        revealIo.observe(el);
      }
    });
  } else {
    motionTargets.forEach(function (el) {
      el.classList.add("is-visible");
    });
  }

  /* Lenis — плавная инерция как на премиальных лендингах */
  var lenis = null;

  if (!prefersReduced && typeof window.Lenis === "function") {
    lenis = new window.Lenis({
      duration: 1.15,
      easing: function (t) {
        return Math.min(1, 1.001 - Math.pow(2, -10 * t));
      },
      orientation: "vertical",
      smoothWheel: true,
      wheelMultiplier: 0.9,
      touchMultiplier: 1.5,
    });

    document.documentElement.classList.add("lenis");

    lenis.on("scroll", function (e) {
      updateProgress(e.scroll);
    });

    function lenisRaf(time) {
      lenis.raf(time);
      requestAnimationFrame(lenisRaf);
    }
    requestAnimationFrame(lenisRaf);
  } else {
    window.addEventListener(
      "scroll",
      function () {
        updateProgress();
      },
      { passive: true }
    );
  }

  updateProgress();
})();
