/**
 * O81-w1 — flow section animation (chips → logo → cards).
 */
(function () {
  "use strict";

  var CHIP_FLY_MS = 920;
  var IMPACT_AT_MS = 690;
  var CARD_STAGGER_MS = 380;
  var CHARGE_AT_MS = 1640;
  var SHOOT_AT_MS = 2270;
  var BARS_AT_MS = 2620;

  var started = false;

  function $(sel, root) {
    return (root || document).querySelector(sel);
  }

  function $$(sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  }

  function prefersReducedMotion() {
    return (
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    );
  }

  function fillBars(section) {
    $$(".rl-flow-anim__card", section).forEach(function (card) {
      var match = card.getAttribute("data-match") || "0";
      var fill = $(".rl-match__fill", card);
      if (fill) {
        fill.style.setProperty("--match-value", match + "%");
      }
    });
  }

  function showFinalState(section) {
    section.classList.add("is-complete");
    $$(".rl-flow-chip", section).forEach(function (chip) {
      chip.style.opacity = "0";
      chip.style.visibility = "hidden";
    });
    $$(".rl-flow-anim__card", section).forEach(function (card) {
      card.classList.add("is-visible");
      card.style.transform = "none";
      card.style.opacity = "1";
    });
    var svg = $(".rl-flow-anim__logo .rl-logo__icon svg", section);
    if (svg) {
      svg.classList.remove("is-idle");
    }
    fillBars(section);
  }

  var REF_STAGE_W = 640;
  var REF_STAGE_H = 320;

  function layoutChips(section, logoWrap, chipsWrap) {
    if (!logoWrap || !chipsWrap) {
      return;
    }
    var stage = $(".rl-flow-anim__stage", section);
    if (!stage) {
      return;
    }
    var stageRect = stage.getBoundingClientRect();
    var logoRect = logoWrap.getBoundingClientRect();
    var cx = logoRect.left + logoRect.width / 2 - stageRect.left;
    var cy = logoRect.top + logoRect.height / 2 - stageRect.top;
    var scaleX = stageRect.width / REF_STAGE_W;
    var scaleY = stageRect.height / REF_STAGE_H;

    $$(".rl-flow-chip", section).forEach(function (chip) {
      var dx = parseFloat(chip.getAttribute("data-dx") || "0") * scaleX;
      var dy = parseFloat(chip.getAttribute("data-dy") || "0") * scaleY;
      var rot = chip.getAttribute("data-rot") || "0deg";
      var color = chip.getAttribute("data-color") || "#0A0A0A";
      var chipW = chip.offsetWidth || 130;
      var chipH = chip.offsetHeight || 38;
      chip.dataset.hitX = String(chipW / 2);
      chip.dataset.hitY = String(chipH / 2);
      chip.style.left = cx - chipW / 2 + "px";
      chip.style.top = cy - chipH / 2 + "px";
      chip.style.boxShadow = "3px 3px 0 " + color;
      chip.style.transform =
        "translate(" + dx + "px, " + dy + "px) rotate(" + rot + ")";
    });
  }

  function layoutCardFly(section, logoWrap) {
    if (!logoWrap) {
      return;
    }
    var logoRect = logoWrap.getBoundingClientRect();
    var lx = logoRect.left + logoRect.width / 2;
    var ly = logoRect.top + logoRect.height / 2;

    $$(".rl-flow-anim__card", section).forEach(function (card) {
      var cardRect = card.getBoundingClientRect();
      var tx = lx - (cardRect.left + cardRect.width / 2);
      var ty = ly - (cardRect.top + cardRect.height / 2);
      card.style.setProperty("--fly-dx", tx + "px");
      card.style.setProperty("--fly-dy", ty + "px");
    });
  }

  function createRipple(section, color) {
    var ripples = $(".rl-flow-anim__ripples", section);
    var logoWrap = $(".rl-flow-anim__logo-wrap", section);
    var stage = $(".rl-flow-anim__stage", section);
    if (!ripples || !logoWrap || !stage) {
      return;
    }
    var stageRect = stage.getBoundingClientRect();
    var logoRect = logoWrap.getBoundingClientRect();
    var cx = logoRect.left + logoRect.width / 2 - stageRect.left;
    var cy = logoRect.top + logoRect.height / 2 - stageRect.top;
    var ripple = document.createElement("span");
    ripple.className = "rl-flow-ripple";
    ripple.style.left = cx - 20 + "px";
    ripple.style.top = cy - 20 + "px";
    ripple.style.border = "2px solid " + color;
    ripples.appendChild(ripple);
    ripple.classList.add("is-running");
    ripple.addEventListener(
      "animationend",
      function () {
        ripple.remove();
      },
      { once: true }
    );
  }

  function startAnimation(section) {
    if (started) {
      return;
    }
    started = true;

    if (prefersReducedMotion()) {
      showFinalState(section);
      return;
    }

    var scaleEl = $(".rl-flow-logo__scale", section);
    var shakeEl = $(".rl-flow-logo__shake", section);
    var reactionEl = $(".rl-flow-logo__reaction", section);
    var logoWrap = $(".rl-flow-anim__logo-wrap", section);
    var chipsWrap = $(".rl-flow-anim__chips", section);
    var cards = $$(".rl-flow-anim__card", section);
    var svg = $(".rl-flow-anim__logo .rl-logo__icon svg", section);

    if (svg) {
      svg.classList.add("is-idle");
    }

    layoutChips(section, logoWrap, chipsWrap);
    window.requestAnimationFrame(function () {
      layoutCardFly(section, logoWrap);
    });

    var impactCount = 0;
    var recoilCount = 0;

    function setLogoScale() {
      if (!scaleEl) {
        return;
      }
      var scale =
        1 +
        Math.min(impactCount, 5) * 0.052 -
        Math.min(recoilCount, 3) * 0.088;
      scaleEl.style.transform = "scale(" + scale + ")";
    }

    function triggerImpact(color) {
      impactCount += 1;
      setLogoScale();
      if (!shakeEl) {
        return;
      }
      shakeEl.classList.remove("is-impact");
      void shakeEl.offsetWidth;
      shakeEl.classList.add("is-impact");
      createRipple(section, color);
      window.setTimeout(function () {
        shakeEl.classList.remove("is-impact");
      }, 300);
    }

    function triggerRecoil() {
      recoilCount += 1;
      setLogoScale();
      if (!reactionEl) {
        return;
      }
      reactionEl.classList.remove("is-charging", "is-recoil");
      void reactionEl.offsetWidth;
      reactionEl.classList.add("is-recoil");
      window.setTimeout(function () {
        reactionEl.classList.remove("is-recoil");
      }, 370);
    }

    $$(".rl-flow-chip", section).forEach(function (chip) {
      var ms = parseInt(chip.getAttribute("data-ms") || "0", 10);
      var color = chip.getAttribute("data-color") || "#0A0A0A";
      window.setTimeout(function () {
        var hitX = chip.dataset.hitX || "65";
        var hitY = chip.dataset.hitY || "19";
        chip.style.transition =
          "transform " + CHIP_FLY_MS + "ms cubic-bezier(0.22, 1, 0.36, 1), opacity 180ms ease";
        chip.style.transform =
          "translate(" + hitX + "px, " + hitY + "px) scale(0.15) rotate(0deg)";
        window.setTimeout(function () {
          chip.style.opacity = "0";
          triggerImpact(color);
        }, IMPACT_AT_MS);
      }, 100 + ms);
    });

    window.setTimeout(function () {
      if (reactionEl) {
        reactionEl.classList.add("is-charging");
      }
    }, CHARGE_AT_MS);

    cards.forEach(function (card, index) {
      window.setTimeout(
        function () {
          if (reactionEl) {
            reactionEl.classList.remove("is-charging");
          }
          triggerRecoil();
          card.classList.add("is-visible");
        },
        SHOOT_AT_MS + index * CARD_STAGGER_MS
      );
    });

    window.setTimeout(function () {
      if (svg) {
        svg.classList.remove("is-idle");
      }
      fillBars(section);
      section.classList.add("is-complete");
    }, BARS_AT_MS);

    var resizeTimer;
    window.addEventListener("resize", function () {
      window.clearTimeout(resizeTimer);
      resizeTimer = window.setTimeout(function () {
        layoutChips(section, logoWrap, chipsWrap);
        if (section.classList.contains("is-complete")) {
          return;
        }
        layoutCardFly(section, logoWrap);
      }, 120);
    });
  }

  function init() {
    var section = $(".rl-flow-anim");
    if (!section) {
      return;
    }

    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              io.unobserve(entry.target);
              startAnimation(entry.target);
            }
          });
        },
        { threshold: 0.35 }
      );
      io.observe(section);
    } else {
      startAnimation(section);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
