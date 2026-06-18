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

  /** Demo km on homepage: card1 50%, card2 100% ideal, card3 80% — real titles from feed. */
  var PREVIEW_KM = [50, 100, 80];
  var NICHE_ICONS = {
    dev: "</>",
    design: "✦",
    marketing: "◎",
    text: "Aa",
  };

  function nicheIconHtml(category) {
    var c = String(category || "").trim();
    if (!NICHE_ICONS[c]) {
      return "";
    }
    return (
      '<span class="rl-niche-icon rl-niche-icon--' +
      escapeHtml(c) +
      '" aria-hidden="true">' +
      escapeHtml(NICHE_ICONS[c]) +
      "</span>"
    );
  }

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

  function decodeHtmlEntities(str) {
    var s = String(str || "");
    if (!s) {
      return "";
    }
    if (typeof document !== "undefined") {
      var el = document.createElement("textarea");
      el.innerHTML = s;
      return el.value;
    }
    return s;
  }

  function prepForDisplay(str, singleLine) {
    var s = decodeHtmlEntities(str);
    if (singleLine) {
      return String(s).replace(/\r\n?/g, " ").replace(/\s+/g, " ").trim();
    }
    return s.replace(/\r\n?/g, "\n");
  }

  function formatBudgetDisplay(s) {
    var text = prepForDisplay(s, true);
    if (!text || text === "—") {
      return "—";
    }
    return text
      .replace(/(\d[\d\s.,]*)\s*Р\b/g, "$1 ₽")
      .replace(/(\d[\d\s.,]*)р\.?(?=\s|$|[,.])/gi, "$1 ₽")
      .replace(/(\d[\d\s.,]*)\s*(?:руб\.?|rub)\b/gi, "$1 ₽")
      .replace(/\s*₽\s*/g, " ₽")
      .trim();
  }

  function sourceMeta(source) {
    var s = (source || "fl").toLowerCase();
    if (s.indexOf("kwork") >= 0) {
      return { cls: "kwork", label: "Kwork" };
    }
    if (s.indexOf("tg") === 0 || s.indexOf("telegram") === 0) {
      return { cls: "tg", label: "TG" };
    }
    return { cls: "fl", label: "FL.ru" };
  }

  function renderTagChips(item) {
    var tags =
      (item && item.lead_tag_labels && item.lead_tag_labels.length
        ? item.lead_tag_labels
        : item && item.lead_tags) || [];
    var max = 3;
    var html = [];
    var i;
    for (i = 0; i < tags.length && i < max; i++) {
      html.push(
        '<span class="rl-chip">' + escapeHtml(prepForDisplay(tags[i], true)) + "</span>"
      );
    }
    if (tags.length > max) {
      html.push(
        '<span class="rl-chip rl-chip--more">+' + (tags.length - max) + "</span>"
      );
    }
    return html.join("");
  }

  function previewKm(idx) {
    return PREVIEW_KM[idx] != null ? PREVIEW_KM[idx] : 50;
  }

  function previewCardHtml(item, lentaUrl, idx) {
    var src = sourceMeta(item.source);
    var km = previewKm(idx);
    var perfect = idx === 1;
    var title = escapeHtml(prepForDisplay(item.title || "Без названия", true));
    var budget = escapeHtml(formatBudgetDisplay(item.budget_text || "—"));
    var perfectBadge = "";
    var heroCls = idx === 1 ? " rl-lead-card--demo-hero" : "";
    return (
      '<article class="rl-lead-card is-visible' +
      (perfect ? " rl-lead-card--perfect-match" : "") +
      heroCls +
      '">' +
      '<div class="rl-feed-card__head">' +
      '<div class="rl-feed-card__head-start">' +
      '<span class="rl-feed-card__source rl-feed-card__source--' +
      src.cls +
      '">' +
      escapeHtml(src.label) +
      "</span>" +
      perfectBadge +
      "</div></div>" +
      '<h3 class="rl-lead-card__title"><span title="' +
      title +
      '">' +
      title +
      "</span></h3>" +
      '<p class="rl-lead-card__budget">Бюджет: ' +
      budget +
      "</p>" +
      '<div class="rl-match rl-match-bar">' +
      '<div class="rl-match__bar" role="progressbar" aria-valuenow="' +
      km +
      '" aria-valuemin="0" aria-valuemax="100" aria-label="Совместимость ' +
      km +
      '%">' +
      '<span class="rl-match__fill" data-match-pct="' +
      km +
      '" style="--match-value:' +
      km +
      '%"></span></div></div>' +
      '<div class="rl-chips">' +
      renderTagChips(item) +
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
            return previewCardHtml(item, lentaUrl, idx);
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
