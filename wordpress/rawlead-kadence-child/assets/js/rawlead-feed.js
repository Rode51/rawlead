/**
 * RawLead /feed — карточки, фильтры, infinite scroll (REST proxy same-origin).
 */
(function () {
  "use strict";

  var root = document.querySelector('[data-rl-app="feed"]');
  if (!root || !window.rawleadFeed) {
    return;
  }

  var cfg = window.rawleadFeed;
  var listEl = document.getElementById("rl-feed-list");
  var countEl = document.getElementById("rl-feed-count");
  var sentinelEl = document.getElementById("rl-feed-sentinel");
  var endEl = document.getElementById("rl-feed-end");
  var errorEl = document.getElementById("rl-feed-error");
  var sidebar = document.getElementById("rl-feed-sidebar");
  var resetBtn = sidebar ? sidebar.querySelector(".rl-feed-reset") : null;

  var skillsEl = document.getElementById("rl-feed-skills");

  var state = {
    offset: 0,
    limit: 20,
    minScore: 0,
    source: "",
    sort: "time",
    tags: [],
    catalog: [],
    tagsLoading: false,
    loading: false,
    done: false,
    totalShown: 0,
    expandedId: null,
  };

  function apiUrl(params) {
    var q = new URLSearchParams(params);
    return cfg.restFeed + (cfg.restFeed.indexOf("?") >= 0 ? "&" : "?") + q.toString();
  }

  function sourceLabel(source) {
    var s = (source || "").toLowerCase();
    if (s.indexOf("fl") === 0 || s === "fl.ru") {
      return { key: "fl", label: "FL.ru", cls: "fl" };
    }
    if (s.indexOf("kwork") >= 0) {
      return { key: "kwork", label: "Kwork", cls: "kwork" };
    }
    if (s.indexOf("tg") === 0 || s.indexOf("telegram") >= 0) {
      return { key: "tg", label: "Telegram", cls: "tg" };
    }
    return { key: "other", label: source || "—", cls: "other" };
  }

  function matchSource(item, filter) {
    if (!filter) {
      return true;
    }
    return sourceLabel(item.source).key === filter;
  }

  function verdictChip(score, verdict) {
    if (verdict === "take" || (score !== null && score >= 85)) {
      return { text: "Брать ✓", cls: "take" };
    }
    if (score !== null && score >= 70) {
      return { text: "Брать", cls: "take" };
    }
    return { text: "Сомнительно", cls: "maybe" };
  }

  function formatTime(iso) {
    if (!iso) {
      return "";
    }
    var d = new Date(iso);
    if (isNaN(d.getTime())) {
      return "";
    }
    var diff = Date.now() - d.getTime();
    var mins = Math.floor(diff / 60000);
    if (mins < 60) {
      return mins <= 1 ? "только что" : mins + " мин назад";
    }
    var hrs = Math.floor(mins / 60);
    if (hrs < 48) {
      return hrs + " ч назад";
    }
    return d.toLocaleDateString("ru-RU");
  }

  function escapeHtml(str) {
    return String(str || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderCard(item) {
    var src = sourceLabel(item.source);
    var hasSkills = state.tags.length > 0;
    var rank = item.final_rank != null ? item.final_rank : item.ai_score || 0;
    var matchLabel = hasSkills ? "Совместимость" : "Оценка ИИ";
    var chip = verdictChip(item.ai_score, item.ai_verdict);
    var tags = (item.lead_tags || [])
      .map(function (t) {
        return '<span class="rl-feed-card__tag">#' + escapeHtml(t) + "</span>";
      })
      .join("");
    var reasons = (item.ai_reasons || []).join(". ");
    var budget = item.budget_text || "—";
    var expanded = state.expandedId === item.id;

    return (
      '<article class="rl-feed-card' +
      (expanded ? " is-expanded" : "") +
      '" data-id="' +
      item.id +
      '" tabindex="0" role="button">' +
      '<div class="rl-feed-card__head">' +
      '<span class="rl-feed-card__source rl-feed-card__source--' +
      src.cls +
      '">' +
      escapeHtml(src.label) +
      "</span>" +
      '<span class="rl-feed-card__time">' +
      formatTime(item.created_at) +
      "</span>" +
      "</div>" +
      '<h3 class="rl-feed-card__title">' +
      escapeHtml(item.title || "Без названия") +
      "</h3>" +
      '<p class="rl-feed-card__budget">Бюджет: ' +
      escapeHtml(budget) +
      "</p>" +
      '<div class="rl-feed-card__match">' +
      '<div class="rl-match__bar" role="progressbar" aria-valuenow="' +
      rank +
      '">' +
      '<span class="rl-match__fill" style="--match-value:' +
      rank +
      '%"></span>' +
      "</div>" +
      '<span class="rl-feed-card__pct">' +
      rank +
      "%</span>" +
      '<span class="rl-feed-card__match-label">' +
      escapeHtml(matchLabel) +
      "</span>" +
      '<span class="rl-feed-card__ai rl-feed-card__ai--' +
      chip.cls +
      '">' +
      escapeHtml(chip.text) +
      "</span>" +
      "</div>" +
      '<div class="rl-feed-card__tags">' +
      tags +
      "</div>" +
      '<div class="rl-feed-card__body">' +
      '<p class="rl-feed-card__text">' +
      escapeHtml(reasons || "Описание появится после обогащения лида.") +
      "</p>" +
      (item.url
        ? '<a class="rl-btn rl-btn--ghost rl-feed-card__link" href="' +
          escapeHtml(item.url) +
          '" target="_blank" rel="noopener" onclick="event.stopPropagation()">Открыть оригинал ↗</a>'
        : "") +
      "</div>" +
      "</article>"
    );
  }

  function skeletonHtml(n) {
    var html = "";
    for (var i = 0; i < n; i++) {
      html += '<div class="rl-feed-skeleton" aria-hidden="true"></div>';
    }
    return html;
  }

  function showError(msg) {
    if (!errorEl) {
      return;
    }
    errorEl.hidden = false;
    errorEl.innerHTML =
      escapeHtml(msg) +
      ' <button type="button" class="rl-feed-banner__retry">Попробовать снова</button>';
    var btn = errorEl.querySelector(".rl-feed-banner__retry");
    if (btn) {
      btn.addEventListener("click", function () {
        errorEl.hidden = true;
        resetAndLoad();
      });
    }
  }

  function updateCount() {
    if (!countEl) {
      return;
    }
    countEl.textContent =
      state.totalShown > 0
        ? state.totalShown + " заказов в ленте"
        : "";
  }

  function readFilters() {
    if (!sidebar) {
      return;
    }
    var src = sidebar.querySelector('input[name="source"]:checked');
    var score = sidebar.querySelector('input[name="min_score"]:checked');
    var sortInp = sidebar.querySelector('input[name="sort"]:checked');
    state.source = src ? src.value : "";
    state.minScore = score ? parseInt(score.value, 10) || 0 : 0;
    state.sort = sortInp ? sortInp.value : "time";
    var dirty =
      state.source !== "" || state.minScore !== 0 || state.tags.length > 0 || state.sort !== "time";
    if (resetBtn) {
      resetBtn.hidden = !dirty;
    }
  }

  function renderSkillsCatalog() {
    if (!skillsEl) {
      return;
    }
    if (!state.catalog.length) {
      skillsEl.innerHTML =
        '<p class="rl-feed-skills__empty">Пока нет навыков в ленте — дождитесь заказов из бота</p>';
      return;
    }
    skillsEl.innerHTML = state.catalog
      .map(function (row) {
        var tag = row.tag || "";
        var active = state.tags.indexOf(tag) >= 0;
        return (
          '<button type="button" class="rl-feed-chip rl-feed-skill' +
          (active ? " is-active" : "") +
          '" data-tag="' +
          escapeHtml(tag) +
          '">' +
          escapeHtml(tag) +
          (row.count ? ' <span class="rl-feed-skill__count">' + row.count + "</span>" : "") +
          "</button>"
        );
      })
      .join("");
    skillsEl.querySelectorAll(".rl-feed-skill").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var tag = btn.getAttribute("data-tag");
        if (!tag) {
          return;
        }
        var next = state.tags.indexOf(tag) >= 0
          ? state.tags.filter(function (t) {
              return t !== tag;
            })
          : state.tags.concat([tag]);
        saveTags(next);
      });
    });
  }

  function saveTags(tags) {
    if (!cfg.restTags || state.tagsLoading) {
      return;
    }
    state.tagsLoading = true;
    fetch(cfg.restTags, {
      method: "PUT",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-WP-Nonce": cfg.nonce || "",
      },
      body: JSON.stringify({ tags: tags }),
    })
      .then(function (res) {
        if (!res.ok) {
          throw new Error("HTTP " + res.status);
        }
        return res.json();
      })
      .then(function (data) {
        state.tags = data.tags || tags;
        renderSkillsCatalog();
        readFilters();
        resetAndLoad();
      })
      .catch(function () {
        showError("Не удалось сохранить навыки.");
      })
      .finally(function () {
        state.tagsLoading = false;
      });
  }

  function loadTags() {
    if (!cfg.restTags) {
      return Promise.resolve();
    }
    return fetch(cfg.restTags, { credentials: "same-origin" })
      .then(function (res) {
        return res.ok ? res.json() : { tags: [] };
      })
      .then(function (data) {
        state.tags = data.tags || [];
      })
      .catch(function () {
        state.tags = [];
      });
  }

  function loadCatalog() {
    if (!cfg.restSkills) {
      return Promise.resolve();
    }
    return fetch(cfg.restSkills, { credentials: "same-origin" })
      .then(function (res) {
        return res.ok ? res.json() : { skills: [] };
      })
      .then(function (data) {
        state.catalog = data.skills || [];
        renderSkillsCatalog();
      })
      .catch(function () {
        state.catalog = [];
        renderSkillsCatalog();
      });
  }

  function syncChips() {
    if (!sidebar) {
      return;
    }
    sidebar.querySelectorAll(".rl-feed-chip").forEach(function (label) {
      var input = label.querySelector("input");
      label.classList.toggle("is-active", input && input.checked);
    });
  }

  function resetAndLoad() {
    state.offset = 0;
    state.done = false;
    state.totalShown = 0;
    state.expandedId = null;
    if (listEl) {
      listEl.innerHTML = skeletonHtml(3);
    }
    if (endEl) {
      endEl.hidden = true;
    }
    loadMore(true);
  }

  function loadMore(replace) {
    if (state.loading || state.done) {
      return;
    }
    state.loading = true;
    var params = {
      limit: state.limit,
      offset: state.offset,
      min_score: state.minScore,
      sort: state.sort,
    };
    if (state.tags.length) {
      params.skills = state.tags.join(",");
    }
    var url = apiUrl(params);

    fetch(url, { credentials: "same-origin" })
      .then(function (res) {
        if (!res.ok) {
          throw new Error("HTTP " + res.status);
        }
        return res.json();
      })
      .then(function (data) {
        var items = (data.items || []).filter(function (item) {
          return matchSource(item, state.source);
        });
        if (replace && listEl) {
          listEl.innerHTML = "";
        }
        if (items.length === 0 && state.offset === 0) {
          listEl.innerHTML =
            '<p class="rl-feed-empty">' +
            (state.source || state.minScore
              ? "По выбранным фильтрам ничего не найдено."
              : "Заказов пока нет. Попробуйте позже.") +
            "</p>";
        } else {
          var frag = items.map(renderCard).join("");
          listEl.insertAdjacentHTML("beforeend", frag);
          state.totalShown += items.length;
        }
        state.offset += data.count != null ? data.count : items.length;
        if ((data.count || 0) < state.limit) {
          state.done = true;
          if (endEl && state.totalShown > 0) {
            endEl.hidden = false;
          }
        }
        updateCount();
        bindCards();
        requestAnimationFrame(function () {
          document.querySelectorAll(".rl-feed-card .rl-match__fill").forEach(function (el) {
            el.closest(".rl-match__bar");
            var card = el.closest(".rl-feed-card");
            if (card) {
              card.classList.add("rl-match-ready");
            }
          });
        });
      })
      .catch(function () {
        if (replace && listEl) {
          listEl.innerHTML = "";
        }
        showError("Не удалось загрузить ленту.");
      })
      .finally(function () {
        state.loading = false;
      });
  }

  function bindCards() {
    listEl.querySelectorAll(".rl-feed-card").forEach(function (card) {
      if (card.dataset.bound) {
        return;
      }
      card.dataset.bound = "1";
      card.addEventListener("click", function () {
        var id = parseInt(card.getAttribute("data-id"), 10);
        if (state.expandedId === id) {
          state.expandedId = null;
          card.classList.remove("is-expanded");
        } else {
          listEl.querySelectorAll(".rl-feed-card.is-expanded").forEach(function (c) {
            c.classList.remove("is-expanded");
          });
          state.expandedId = id;
          card.classList.add("is-expanded");
        }
      });
      card.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          card.click();
        }
      });
    });
  }

  if (sidebar) {
    sidebar.addEventListener("change", function () {
      syncChips();
      readFilters();
      resetAndLoad();
    });
    if (resetBtn) {
      resetBtn.addEventListener("click", function () {
        sidebar.querySelector('input[name="source"][value=""]').checked = true;
        sidebar.querySelector('input[name="min_score"][value="0"]').checked = true;
        sidebar.querySelector('input[name="sort"][value="time"]').checked = true;
        saveTags([]);
      });
    }
  }

  /* Mobile bottom sheet */
  var sheet = document.getElementById("rl-feed-sheet");
  var sheetBody = document.getElementById("rl-feed-sheet-body");
  var openBtn = document.getElementById("rl-feed-filters-open");
  if (sheet && sheetBody && sidebar && openBtn) {
    openBtn.addEventListener("click", function () {
      sheetBody.innerHTML = sidebar.innerHTML;
      sheet.hidden = false;
      openBtn.setAttribute("aria-expanded", "true");
      sheetBody.querySelectorAll("input").forEach(function (inp) {
        var name = inp.getAttribute("name");
        var val = inp.getAttribute("value");
        var live = sidebar.querySelector(
          'input[name="' + name + '"][value="' + val + '"]'
        );
        if (live) {
          inp.checked = live.checked;
        }
      });
      sheetBody.querySelectorAll(".rl-feed-chip").forEach(function (label) {
        var input = label.querySelector("input");
        label.classList.toggle("is-active", input && input.checked);
        label.addEventListener("click", function () {
          sheetBody.querySelectorAll('input[name="' + input.name + '"]').forEach(function (r) {
            r.checked = false;
            r.parentElement.classList.remove("is-active");
          });
          input.checked = true;
          label.classList.add("is-active");
        });
      });
    });
    document.getElementById("rl-feed-sheet-overlay").addEventListener("click", closeSheet);
    document.getElementById("rl-feed-sheet-apply").addEventListener("click", function () {
      sheetBody.querySelectorAll("input").forEach(function (inp) {
        var name = inp.getAttribute("name");
        var val = inp.getAttribute("value");
        var live = sidebar.querySelector(
          'input[name="' + name + '"][value="' + val + '"]'
        );
        if (live) {
          live.checked = inp.checked;
        }
      });
      syncChips();
      readFilters();
      closeSheet();
      resetAndLoad();
    });
    document.getElementById("rl-feed-sheet-reset").addEventListener("click", function () {
      if (resetBtn) {
        resetBtn.click();
      }
      closeSheet();
    });
    function closeSheet() {
      sheet.hidden = true;
      openBtn.setAttribute("aria-expanded", "false");
    }
  }

  if (sentinelEl && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting && !state.loading && !state.done) {
            loadMore(false);
          }
        });
      },
      { rootMargin: "200px" }
    );
    io.observe(sentinelEl);
  }

  Promise.all([loadTags(), loadCatalog()]).then(function () {
    renderSkillsCatalog();
    syncChips();
    readFilters();
    resetAndLoad();
  });
})();
