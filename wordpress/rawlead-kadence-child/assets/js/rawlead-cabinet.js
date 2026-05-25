/**

 * RawLead /cabinet — теги, персональная лента (final_rank), infinite scroll.

 */

(function () {

  "use strict";



  var root = document.querySelector('[data-rl-app="cabinet"]');

  if (!root || !window.rawleadCabinet) {

    return;

  }



  var cfg = window.rawleadCabinet;

  var tagsEl = document.getElementById("rl-cabinet-tags");

  var tagsHint = document.getElementById("rl-cabinet-tags-hint");

  var listEl = document.getElementById("rl-cabinet-list");

  var countEl = document.getElementById("rl-cabinet-count");

  var sentinelEl = document.getElementById("rl-cabinet-sentinel");

  var endEl = document.getElementById("rl-cabinet-end");

  var errorEl = document.getElementById("rl-cabinet-error");

  var noTagsEl = document.getElementById("rl-cabinet-no-tags");

  var noMatchEl = document.getElementById("rl-cabinet-no-match");

  var sidebar = document.getElementById("rl-cabinet-sidebar");

  var resetBtn = sidebar ? sidebar.querySelector(".rl-feed-reset") : null;



  var state = {

    tags: [],

    offset: 0,

    limit: 20,

    minScore: 0,

    source: "",

    loading: false,

    done: false,

    totalShown: 0,

    expandedId: null,

    tagsLoading: false,

  };



  function apiUrl(base, params) {

    var q = new URLSearchParams(params);

    return base + (base.indexOf("?") >= 0 ? "&" : "?") + q.toString();

  }



  function escapeHtml(str) {

    return String(str || "")

      .replace(/&/g, "&amp;")

      .replace(/</g, "&lt;")

      .replace(/>/g, "&gt;")

      .replace(/"/g, "&quot;");

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



  function skeletonHtml(n) {

    var html = "";

    for (var i = 0; i < n; i++) {

      html += '<div class="rl-feed-skeleton" aria-hidden="true"></div>';

    }

    return html;

  }



  function renderTags() {

    if (!tagsEl) {

      return;

    }

    var html = state.tags

      .map(function (tag) {

        return (

          '<span class="rl-cabinet-tag" role="listitem" data-tag="' +

          escapeHtml(tag) +

          '">#' +

          escapeHtml(tag) +

          '<button type="button" class="rl-cabinet-tag__remove" aria-label="Удалить тег">×</button></span>'

        );

      })

      .join("");

    html +=

      '<button type="button" class="rl-cabinet-tag rl-cabinet-tag--add" id="rl-cabinet-tag-add">+ Добавить тег</button>';

    tagsEl.innerHTML = html;



    if (tagsHint) {

      tagsHint.hidden = state.tags.length > 0;

    }

    if (noTagsEl) {

      noTagsEl.hidden = state.tags.length > 0;

    }



    tagsEl.querySelectorAll(".rl-cabinet-tag__remove").forEach(function (btn) {

      btn.addEventListener("click", function (e) {

        e.stopPropagation();

        var chip = btn.closest(".rl-cabinet-tag");

        var tag = chip && chip.getAttribute("data-tag");

        if (!tag) {

          return;

        }

        saveTags(state.tags.filter(function (t) {

          return t !== tag;

        }));

      });

    });



    var addBtn = document.getElementById("rl-cabinet-tag-add");

    if (addBtn) {

      addBtn.addEventListener("click", promptAddTag);

    }

  }



  function promptAddTag() {

    var raw = window.prompt("Введите тег (например wordpress):");

    if (!raw) {

      return;

    }

    var tag = raw.trim().toLowerCase().replace(/^#/, "");

    if (!tag || state.tags.indexOf(tag) >= 0) {

      return;

    }

    saveTags(state.tags.concat([tag]));

  }



  function saveTags(tags) {

    if (state.tagsLoading) {

      return;

    }

    state.tagsLoading = true;

    if (tagsEl) {

      tagsEl.classList.add("is-loading");

    }

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

        renderTags();

        resetAndLoad();

      })

      .catch(function () {

        showError("Не удалось сохранить теги.");

      })

      .finally(function () {

        state.tagsLoading = false;

        if (tagsEl) {

          tagsEl.classList.remove("is-loading");

        }

      });

  }



  function loadTags() {

    return fetch(cfg.restTags, { credentials: "same-origin" })

      .then(function (res) {

        if (!res.ok) {

          throw new Error("HTTP " + res.status);

        }

        return res.json();

      })

      .then(function (data) {

        state.tags = data.tags || [];

        renderTags();

      });

  }



  function renderCard(item) {

    var src = sourceLabel(item.source);

    var rank = item.final_rank != null ? item.final_rank : 0;

    var chip = verdictChip(item.ai_score, item.ai_verdict);

    var tags = (item.lead_tags || [])

      .map(function (t) {

        return '<span class="rl-feed-card__tag">#' + escapeHtml(t) + "</span>";

      })

      .join("");

    var reasons = (item.ai_reasons || []).join(". ");

    var budget = item.budget_text || "—";

    var expanded = state.expandedId === item.id;

    var km =

      item.keyword_match != null

        ? '<span class="rl-feed-card__km">Теги: ' + item.keyword_match + "%</span>"

        : "";



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

      '<span class="rl-feed-card__match-label">Совместимость</span>' +

      km +

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

      '<p class="rl-feed-card__agent">🤖 Рыночная цена: скоро</p>' +

      '<div class="rl-feed-card__actions">' +

      '<button type="button" class="rl-btn rl-btn--primary rl-btn--soon" disabled title="Скоро">Сгенерировать отклик</button>' +

      (item.url

        ? '<a class="rl-btn rl-btn--ghost rl-feed-card__link" href="' +

          escapeHtml(item.url) +

          '" target="_blank" rel="noopener" onclick="event.stopPropagation()">Открыть оригинал ↗</a>'

        : "") +

      "</div>" +

      "</div>" +

      "</article>"

    );

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

    state.source = src ? src.value : "";

    state.minScore = score ? parseInt(score.value, 10) || 0 : 0;

    var dirty = state.source !== "" || state.minScore !== 0;

    if (resetBtn) {

      resetBtn.hidden = !dirty;

    }

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

    if (state.tags.length === 0) {

      if (listEl) {

        listEl.innerHTML = "";

      }

      if (noMatchEl) {

        noMatchEl.hidden = true;

      }

      updateCount();

      return;

    }

    state.offset = 0;

    state.done = false;

    state.totalShown = 0;

    state.expandedId = null;

    if (noMatchEl) {

      noMatchEl.hidden = true;

    }

    if (listEl) {

      listEl.innerHTML = skeletonHtml(3);

      listEl.hidden = false;

    }

    if (endEl) {

      endEl.hidden = true;

    }

    loadMore(true);

  }



  function loadMore(replace) {

    if (state.loading || state.done || state.tags.length === 0) {

      return;

    }

    state.loading = true;

    var url = apiUrl(cfg.restFeed, {

      limit: state.limit,

      offset: state.offset,

      min_score: state.minScore,

    });



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

          listEl.innerHTML = "";

          listEl.hidden = true;

          if (noMatchEl) {

            noMatchEl.hidden = !(state.source === "" && state.minScore === 0);

          }

          if (!noMatchEl || noMatchEl.hidden) {

            listEl.hidden = false;

            listEl.innerHTML =

              '<p class="rl-feed-empty">По выбранным фильтрам ничего не найдено.</p>';

          }

        } else {

          listEl.hidden = false;

          if (noMatchEl) {

            noMatchEl.hidden = true;

          }

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

    if (!listEl) {

      return;

    }

    listEl.querySelectorAll(".rl-feed-card").forEach(function (card) {

      if (card.dataset.bound) {

        return;

      }

      card.dataset.bound = "1";

      card.addEventListener("click", function (e) {

        if (e.target.closest(".rl-btn--soon, .rl-feed-card__link")) {

          return;

        }

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

        syncChips();

        readFilters();

        resetAndLoad();

      });

    }

  }



  var addFirst = document.getElementById("rl-cabinet-add-first");

  if (addFirst) {

    addFirst.addEventListener("click", promptAddTag);

  }



  /* Mobile bottom sheet */

  var sheet = document.getElementById("rl-cabinet-sheet");

  var sheetBody = document.getElementById("rl-cabinet-sheet-body");

  var openBtn = document.getElementById("rl-cabinet-filters-open");

  if (sheet && sheetBody && sidebar && openBtn) {

    openBtn.addEventListener("click", function () {

      sheetBody.innerHTML = sidebar.innerHTML;

      sheet.hidden = false;

      openBtn.setAttribute("aria-expanded", "true");

    });

    document.getElementById("rl-cabinet-sheet-overlay").addEventListener("click", closeSheet);

    document.getElementById("rl-cabinet-sheet-apply").addEventListener("click", function () {

      sheetBody.querySelectorAll("input").forEach(function (inp) {

        var name = inp.getAttribute("name");

        var val = inp.getAttribute("value");

        var live = sidebar.querySelector('input[name="' + name + '"][value="' + val + '"]');

        if (live) {

          live.checked = inp.checked;

        }

      });

      syncChips();

      readFilters();

      closeSheet();

      resetAndLoad();

    });

    document.getElementById("rl-cabinet-sheet-reset").addEventListener("click", function () {

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



  syncChips();

  readFilters();

  loadTags()

    .then(function () {

      resetAndLoad();

    })

    .catch(function () {

      showError("Не удалось загрузить теги.");

    });

})();

