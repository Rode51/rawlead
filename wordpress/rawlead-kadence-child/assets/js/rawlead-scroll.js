/**
 * RawLead front page — Lenis smooth scroll, progress, reveal, live preview feed.
 */
(function () {
  "use strict";

  var main = document.querySelector(".rl-landing");
  if (!main) {
    return;
  }

  var homeCfg = window.rawleadHome || {};
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

  /* Reveal on scroll */
  var motionTargets = main.querySelectorAll(".rl-reveal");
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
    motionTargets.forEach(function (el) {
      revealIo.observe(el);
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

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function sourceMeta(source) {
    var s = (source || "fl").toLowerCase();
    if (s === "kwork") {
      return { cls: "kwork", label: "Kwork" };
    }
    if (s === "tg" || s === "telegram") {
      return { cls: "tg", label: "TG" };
    }
    return { cls: "fl", label: "FL.ru" };
  }

  function previewCardHtml(item, lentaUrl, hero) {
    var src = sourceMeta(item.source);
    var km = item.keyword_match != null ? item.keyword_match : 0;
    var tags = item.lead_tag_labels || item.lead_tags || [];
    var perfect = km >= 100 && tags.length >= 2;
    var title = escapeHtml(item.title || "Без названия");
    var chips = "";
    var list = Array.isArray(tags) ? tags.slice(0, 4) : [];
    list.forEach(function (tag) {
      chips += '<span class="rl-chip">' + escapeHtml(String(tag)) + "</span>";
    });
    if (tags.length > 4) {
      chips +=
        '<span class="rl-chip rl-chip--more">+' + (tags.length - 4) + "</span>";
    }
    var perfectBadge = perfect
      ? '<span class="rl-badge rl-badge--perfect">ИДЕАЛЬНО ✦</span>'
      : "";
    var heroCls = hero ? " rl-lead-card--demo-hero" : "";
    return (
      '<article class="rl-lead-card is-visible' +
      (perfect ? " rl-lead-card--perfect-match" : "") +
      heroCls +
      '">' +
      '<div class="rl-lead-card__head">' +
      '<span class="rl-badge rl-badge--source rl-badge--' +
      src.cls +
      '">' +
      escapeHtml(src.label) +
      "</span>" +
      perfectBadge +
      "</div>" +
      "<h3 class=\"rl-lead-card__title\">" +
      title +
      "</h3>" +
      '<div class="rl-match">' +
      '<div class="rl-match__label"><span>Совместимость ' +
      km +
      "%</span></div>" +
      '<div class="rl-match__bar" role="progressbar" aria-valuenow="' +
      km +
      '" aria-valuemin="0" aria-valuemax="100">' +
      '<span class="rl-match__fill" style="--match-value:' +
      km +
      '%"></span></div></div>' +
      '<div class="rl-chips">' +
      chips +
      "</div>" +
      '<div class="rl-live-preview__cta">' +
      '<a class="rl-btn rl-btn--primary" href="' +
      escapeHtml(lentaUrl) +
      '">Написать отклик</a>' +
      "</div></article>"
    );
  }

  /* WAVE-4-ADDON — parallax hero geo */
  function initHeroParallax() {
    var geoEl = document.querySelector(".rl-hero__geo");
    if (!geoEl || prefersReduced) {
      return;
    }
    window.addEventListener(
      "scroll",
      function () {
        geoEl.style.transform = "translateY(" + window.scrollY * 0.15 + "px)";
      },
      { passive: true }
    );
  }

  function initLivePreview() {
    var box = document.getElementById("rl-live-preview-cards");
    if (!box) {
      return;
    }
    var lentaUrl = box.getAttribute("data-lenta-url") || homeCfg.lentaUrl || "/lenta/";
    var feedUrl = homeCfg.restFeed || "";
    if (!feedUrl) {
      box.querySelectorAll(".rl-lead-card").forEach(function (card) {
        card.classList.add("is-visible");
      });
      return;
    }
    var url =
      feedUrl +
      (feedUrl.indexOf("?") >= 0 ? "&" : "?") +
      "limit=3&sort=time&min_score=0";
    fetch(url, { credentials: "same-origin" })
      .then(function (res) {
        if (!res.ok) {
          throw new Error("feed " + res.status);
        }
        return res.json();
      })
      .then(function (data) {
        var items = data && data.items ? data.items : [];
        if (!items.length) {
          box.querySelectorAll(".rl-lead-card").forEach(function (card) {
            card.classList.add("is-visible");
          });
          return;
        }
        box.classList.remove("rl-live-preview__cards--demo");
        box.innerHTML = items
          .slice(0, 3)
          .map(function (item, idx) {
            return previewCardHtml(item, lentaUrl, idx === 1);
          })
          .join("");
      })
      .catch(function () {
        box.querySelectorAll(".rl-lead-card").forEach(function (card) {
          card.classList.add("is-visible");
        });
      });
  }

  initHeroParallax();
  initLivePreview();
})();
