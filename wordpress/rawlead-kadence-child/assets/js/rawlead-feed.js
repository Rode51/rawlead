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
  var skillsBadgeEl = document.getElementById("rl-feed-skills-badge");
  var skillsHintEl = document.getElementById("rl-feed-skills-hint");
  var skillsApplyBtn = document.getElementById("rl-feed-skills-apply");
  var skillsClearBtn = document.getElementById("rl-feed-skills-clear");
  var skillsPanelEl = document.getElementById("rl-feed-skills-panel");
  var sidebarScroll = document.getElementById("rl-feed-sidebar-scroll");

  var state = {
    offset: 0,
    limit: 20,
    source: "",
    draftCategories: [],
    appliedCategories: [],
    sort: "time",
    draftTags: [],
    appliedTags: [],
    catalog: [],
    catalogGroups: [],
    tagsLoading: false,
    loading: false,
    done: false,
    totalShown: 0,
    expandedId: null,
    loadGeneration: 0,
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

  function stripLeadingTaskLabel(text) {
    var s = String(text || "").trim();
    var lower = s.toLowerCase();
    var prefixes = ["задача:", "задача", "task:"];
    var i;
    for (i = 0; i < prefixes.length; i++) {
      if (lower.indexOf(prefixes[i]) === 0) {
        s = s.slice(prefixes[i].length).replace(/^[\s:]+/, "");
        break;
      }
    }
    return s;
  }

  function truncateTaskSnippet(text, maxLen) {
    maxLen = maxLen || 500;
    var minPart = 200;
    var s = String(text || "").trim();
    var chunk;
    var seps;
    var best;
    var i;
    var idx;
    var m;
    if (!s) {
      return "";
    }
    if (s.length <= maxLen) {
      return s;
    }
    chunk = s.slice(0, maxLen);
    seps = [". ", "! ", "? ", "… ", ".\n"];
    best = -1;
    for (i = 0; i < seps.length; i++) {
      idx = chunk.lastIndexOf(seps[i]);
      if (idx >= minPart / 2 && idx > best) {
        best = idx + seps[i].length - 1;
      }
    }
    if (best > 0) {
      return chunk.slice(0, best).trim();
    }
    m = chunk.match(/^[\s\S]*?[.!?…](?:\s|$)/);
    if (m && m[0].trim()) {
      return m[0].trim();
    }
    return chunk.replace(/\s+$/, "") + "…";
  }

  function taskBodyText(item) {
    var summary = (item.task_summary || "").trim();
    if (summary) {
      return summary;
    }
    var raw = (item.body || item.title || "").trim();
    return truncateTaskSnippet(stripLeadingTaskLabel(raw), 280);
  }

  function renderExpandedBody(item) {
    var task = taskBodyText(item);
    var html = "";
    if (item.title) {
      html +=
        '<div class="rl-feed-card__section">' +
        '<h4 class="rl-feed-card__section-title">Полное название</h4>' +
        '<p class="rl-feed-card__task">' +
        escapeHtml(item.title) +
        "</p></div>";
    }
    if (task) {
      html +=
        '<div class="rl-feed-card__section">' +
        '<h4 class="rl-feed-card__section-title">Суть задания</h4>' +
        '<p class="rl-feed-card__task">' +
        escapeHtml(task) +
        "</p></div>";
    } else {
      html +=
        '<p class="rl-feed-card__text rl-feed-card__muted">Краткое описание появится после следующего цикла радара.</p>';
    }
    if (item.url) {
      html +=
        '<a class="rl-btn rl-btn--ghost rl-feed-card__link" href="' +
        escapeHtml(item.url) +
        '" target="_blank" rel="noopener" onclick="event.stopPropagation()">Читать на бирже ↗</a>';
    }
    return html;
  }

  function renderTagChips(leadTags) {
    var tags = leadTags || [];
    var max = 4;
    var html = [];
    var i;
    for (i = 0; i < tags.length && i < max; i++) {
      html.push('<span class="rl-chip">' + escapeHtml(tags[i]) + "</span>");
    }
    if (tags.length > max) {
      html.push('<span class="rl-chip rl-chip--more">+' + (tags.length - max) + "</span>");
    }
    return html.join("");
  }

  function renderCard(item) {
    var src = sourceLabel(item.source);
    var rank = item.final_rank != null ? item.final_rank : 0;
    var budget = item.budget_text || "—";
    var expanded = state.expandedId === item.id;

    return (
      '<article class="rl-lead-card' +
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
      '<h3 class="rl-lead-card__title">' +
      '<span title="' +
      escapeHtml(item.title || "Без названия") +
      '">' +
      escapeHtml(item.title || "Без названия") +
      "</span>" +
      "</h3>" +
      '<p class="rl-lead-card__budget">Бюджет: ' +
      escapeHtml(budget) +
      "</p>" +
      '<div class="rl-match">' +
      '<div class="rl-match__label">' +
      "<span>Совместимость</span>" +
      "<span><strong>" +
      rank +
      "%</strong></span>" +
      "</div>" +
      '<div class="rl-match__bar" role="progressbar" aria-valuenow="' +
      rank +
      '" aria-valuemin="0" aria-valuemax="100">' +
      '<span class="rl-match__fill" style="--match-value:' +
      rank +
      '%"></span>' +
      "</div>" +
      "</div>" +
      '<div class="rl-chips">' +
      renderTagChips(item.lead_tags) +
      "</div>" +
      '<div class="rl-feed-card__body">' +
      '<div class="rl-feed-card__body-inner">' +
      renderExpandedBody(item) +
      "</div></div>" +
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

  function readCategoriesFrom(root) {
    var box = root || sidebar;
    if (!box) {
      return [];
    }
    var cats = [];
    box.querySelectorAll('input[name="category"]:checked').forEach(function (inp) {
      if (inp.value) {
        cats.push(inp.value);
      }
    });
    return cats;
  }

  function categoriesEqual(a, b) {
    return tagsEqual(a, b);
  }

  function cloneCategories(cats) {
    return (cats || []).slice();
  }

  function readFilters() {
    if (!sidebar) {
      return;
    }
    var src = sidebar.querySelector('input[name="source"]:checked');
    var sortInp = sidebar.querySelector('input[name="sort"]:checked');
    state.source = src ? src.value : "";
    state.sort = sortInp ? sortInp.value : "time";
    var dirty =
      state.source !== "" ||
      state.appliedCategories.length > 0 ||
      state.appliedTags.length > 0 ||
      state.sort !== "time" ||
      !categoriesEqual(state.draftCategories, state.appliedCategories);
    if (resetBtn) {
      resetBtn.hidden = !dirty;
    }
  }

  function tagsEqual(a, b) {
    var left = (a || []).slice().sort();
    var right = (b || []).slice().sort();
    if (left.length !== right.length) {
      return false;
    }
    for (var i = 0; i < left.length; i++) {
      if (left[i] !== right[i]) {
        return false;
      }
    }
    return true;
  }

  function cloneTags(tags) {
    return (tags || []).slice();
  }

  function updateSkillsBadge() {
    var badges = [skillsBadgeEl];
    var sheet = document.getElementById("rl-feed-sheet");
    var sheetBody = document.getElementById("rl-feed-sheet-body");
    if (sheet && !sheet.hidden && sheetBody) {
      var sheetBadge = sheetBody.querySelector("#rl-feed-skills-badge");
      if (sheetBadge) {
        badges.push(sheetBadge);
      }
    }
    badges.forEach(function (el) {
      if (!el) {
        return;
      }
      if (state.appliedTags.length) {
        el.hidden = false;
        el.textContent = String(state.appliedTags.length);
        el.title = "Применено навыков: " + state.appliedTags.length;
      } else {
        el.hidden = true;
        el.textContent = "";
        el.removeAttribute("title");
      }
    });
  }

  function updateSkillsDraftUi() {
    var dirty =
      !tagsEqual(state.draftTags, state.appliedTags) ||
      !categoriesEqual(state.draftCategories, state.appliedCategories);
    var hints = [skillsHintEl];
    var applyBtns = [skillsApplyBtn];
    var sheet = document.getElementById("rl-feed-sheet");
    var sheetBody = document.getElementById("rl-feed-sheet-body");
    if (sheet && !sheet.hidden && sheetBody) {
      var sheetHint = sheetBody.querySelector(".rl-feed-skills__hint");
      var sheetApply = sheetBody.querySelector(".rl-feed-skills-apply");
      if (sheetHint) {
        hints.push(sheetHint);
      }
      if (sheetApply) {
        applyBtns.push(sheetApply);
      }
    }
    hints.forEach(function (el) {
      if (!el) {
        return;
      }
      el.hidden = !dirty;
    });
    applyBtns.forEach(function (btn) {
      if (!btn) {
        return;
      }
      btn.disabled = state.tagsLoading || !dirty;
    });
  }

  function toggleDraftTag(tag) {
    if (!tag) {
      return;
    }
    var idx = state.draftTags.indexOf(tag);
    state.draftTags =
      idx >= 0
        ? state.draftTags.filter(function (t) {
            return t !== tag;
          })
        : state.draftTags.concat([tag]);
    renderSkillsCatalog();
    updateSkillsDraftUi();
  }

  function clearSkills() {
    state.draftTags = [];
    renderSkillsCatalog();
    updateSkillsDraftUi();
    if (!state.appliedTags.length) {
      return;
    }
    persistTags([], { reload: true });
  }

  function bindSkillButtons(container) {
    if (!container) {
      return;
    }
    container.querySelectorAll(".rl-feed-skill").forEach(function (btn) {
      btn.addEventListener("click", function () {
        toggleDraftTag(btn.getAttribute("data-tag"));
      });
    });
  }

  function skillChipHtml(row) {
    var tag = row.tag || "";
    var active = state.draftTags.indexOf(tag) >= 0;
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
  }

  function renderSkillsInto(container) {
    if (!container) {
      return;
    }
    var groups = state.catalogGroups.length ? state.catalogGroups : null;
    if (!groups && !state.catalog.length) {
      container.innerHTML =
        '<p class="rl-feed-skills__empty">Пока нет навыков в ленте — дождитесь заказов из бота</p>';
      return;
    }
    if (groups) {
      container.innerHTML = groups
        .map(function (group) {
          var skills = group.skills || [];
          if (!skills.length) {
            return "";
          }
          return (
            '<div class="rl-feed-skills-group">' +
            '<p class="rl-feed-skills-group__title">' +
            escapeHtml(group.title || group.category || "") +
            "</p>" +
            '<div class="rl-feed-skills-group__chips">' +
            skills.map(skillChipHtml).join("") +
            "</div></div>"
          );
        })
        .join("");
    } else {
      container.innerHTML =
        '<div class="rl-feed-skills-group__chips">' +
        state.catalog.map(skillChipHtml).join("") +
        "</div>";
    }
    bindSkillButtons(container);
  }

  function renderSkillsCatalog() {
    updateSkillsBadge();
    updateSkillsDraftUi();
    renderSkillsInto(skillsEl);
    var sheet = document.getElementById("rl-feed-sheet");
    var sheetBody = document.getElementById("rl-feed-sheet-body");
    if (sheet && !sheet.hidden && sheetBody) {
      var sheetSkills = sheetBody.querySelector(".rl-feed-skills");
      if (sheetSkills) {
        renderSkillsInto(sheetSkills);
      }
    }
  }

  function setSortMatch() {
    if (!sidebar || !state.appliedTags.length) {
      return;
    }
    var sortInp = sidebar.querySelector('input[name="sort"][value="match"]');
    if (sortInp) {
      sortInp.checked = true;
      state.sort = "match";
      syncChips();
    }
  }

  function persistTags(tags, options) {
    options = options || {};
    if (!cfg.restTags || state.tagsLoading) {
      return Promise.resolve();
    }
    state.tagsLoading = true;
    updateSkillsDraftUi();
    return fetch(cfg.restTags, {
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
        state.appliedTags = data.tags || tags;
        state.draftTags = cloneTags(state.appliedTags);
        if (options.setSortMatch) {
          setSortMatch();
        }
        renderSkillsCatalog();
        readFilters();
        if (options.reload !== false) {
          resetAndLoad();
        }
      })
      .catch(function () {
        showError("Не удалось сохранить навыки.");
      })
      .finally(function () {
        state.tagsLoading = false;
        updateSkillsDraftUi();
      });
  }

  function pruneDraftTagsForCategories() {
    if (!state.draftCategories.length || !state.catalogGroups.length) {
      return;
    }
    var allowed = {};
    state.catalogGroups.forEach(function (group) {
      if (state.draftCategories.indexOf(group.category) < 0) {
        return;
      }
      (group.skills || []).forEach(function (row) {
        if (row.tag) {
          allowed[row.tag] = true;
        }
      });
    });
    state.draftTags = state.draftTags.filter(function (tag) {
      return allowed[tag];
    });
  }

  function applyDraftTags() {
    var tagsDirty = !tagsEqual(state.draftTags, state.appliedTags);
    var catsDirty = !categoriesEqual(state.draftCategories, state.appliedCategories);
    if (!tagsDirty && !catsDirty) {
      return;
    }
    state.appliedCategories = cloneCategories(state.draftCategories);
    if (tagsDirty) {
      persistTags(cloneTags(state.draftTags), { setSortMatch: true, reload: true });
      return;
    }
    readFilters();
    resetAndLoad();
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
        state.appliedTags = data.tags || [];
        state.draftTags = cloneTags(state.appliedTags);
      })
      .catch(function () {
        state.appliedTags = [];
        state.draftTags = [];
      });
  }

  function loadCatalog() {
    if (!cfg.restSkills) {
      return Promise.resolve();
    }
    var url = cfg.restSkills;
    if (state.draftCategories.length) {
      var sep = url.indexOf("?") >= 0 ? "&" : "?";
      url =
        url +
        sep +
        "category=" +
        encodeURIComponent(state.draftCategories.join(","));
    }
    return fetch(url, { credentials: "same-origin" })
      .then(function (res) {
        return res.ok ? res.json() : { skills: [] };
      })
      .then(function (data) {
        state.catalogGroups = data.groups || [];
        state.catalog = data.skills || [];
        renderSkillsCatalog();
      })
      .catch(function () {
        state.catalogGroups = [];
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
    state.loadGeneration += 1;
    state.offset = 0;
    state.done = false;
    state.totalShown = 0;
    state.expandedId = null;
    state.loading = false;
    if (listEl) {
      listEl.innerHTML = skeletonHtml(2);
    }
    if (endEl) {
      endEl.hidden = true;
    }
    loadMore(true);
  }

  function loadMore(replace) {
    if (state.done) {
      return;
    }
    if (state.loading && !replace) {
      return;
    }
    var gen = state.loadGeneration;
    state.loading = true;
    var params = {
      limit: state.limit,
      offset: state.offset,
      min_score: 0,
      sort: state.sort,
    };
    if (state.appliedTags.length) {
      params.skills = state.appliedTags.join(",");
    }
    if (state.appliedCategories.length) {
      params.category = state.appliedCategories.join(",");
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
        if (gen !== state.loadGeneration) {
          return;
        }
        var items = (data.items || []).filter(function (item) {
          return matchSource(item, state.source);
        });
        if (listEl) {
          listEl.querySelectorAll(".rl-feed-skeleton").forEach(function (el) {
            el.remove();
          });
        }
        if (replace && listEl) {
          listEl.innerHTML = "";
        }
        if (items.length === 0 && state.offset === 0) {
          listEl.innerHTML =
            '<p class="rl-feed-empty">' +
            (state.source ||
            state.appliedCategories.length ||
            state.appliedTags.length
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
          document.querySelectorAll(".rl-feed-list .rl-lead-card .rl-match__fill").forEach(function (el) {
            var card = el.closest(".rl-lead-card");
            if (card) {
              card.classList.add("rl-match-ready");
            }
          });
        });
      })
      .catch(function () {
        if (gen !== state.loadGeneration) {
          return;
        }
        if (replace && listEl) {
          listEl.innerHTML = "";
        }
        showError("Не удалось загрузить ленту.");
      })
      .finally(function () {
        if (gen === state.loadGeneration) {
          state.loading = false;
        }
      });
  }

  function bindCards() {
    listEl.querySelectorAll(".rl-lead-card").forEach(function (card) {
      if (card.dataset.bound) {
        return;
      }
      card.dataset.bound = "1";
      card.addEventListener("click", function (e) {
        if (e.target.closest(".rl-feed-card__link")) {
          return;
        }
        var id = parseInt(card.getAttribute("data-id"), 10);
        if (state.expandedId === id) {
          state.expandedId = null;
          card.classList.remove("is-expanded");
        } else {
          listEl.querySelectorAll(".rl-lead-card.is-expanded").forEach(function (c) {
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

  function bindWheelScroll(el) {
    if (!el || el.dataset.wheelBound === "1") {
      return;
    }
    el.dataset.wheelBound = "1";
    el.addEventListener(
      "wheel",
      function (e) {
        if (el.scrollHeight <= el.clientHeight) {
          return;
        }
        e.preventDefault();
        el.scrollTop += e.deltaY;
      },
      { passive: false }
    );
  }

  function bindSkillsPanels(root) {
    if (!root) {
      return;
    }
    var panel = root.querySelector("#rl-feed-skills-panel");
    if (panel) {
      bindWheelScroll(panel);
    }
    root.querySelectorAll(".rl-feed-skills-dd__panel").forEach(bindWheelScroll);
  }

  bindWheelScroll(sidebarScroll || sidebar);
  bindSkillsPanels(sidebar || document);

  if (skillsApplyBtn) {
    skillsApplyBtn.addEventListener("click", applyDraftTags);
  }
  if (skillsClearBtn) {
    skillsClearBtn.addEventListener("click", clearSkills);
  }

  function syncCategoryInputs(fromRoot, toRoot) {
    if (!fromRoot || !toRoot) {
      return;
    }
    fromRoot.querySelectorAll('input[name="category"]').forEach(function (inp) {
      var val = inp.getAttribute("value");
      var peer = toRoot.querySelector('input[name="category"][value="' + val + '"]');
      if (peer) {
        peer.checked = inp.checked;
      }
    });
    toRoot.querySelectorAll(".rl-feed-chip").forEach(function (label) {
      var input = label.querySelector("input");
      label.classList.toggle("is-active", input && input.checked);
    });
  }

  function bindCategoryFilters(root) {
    if (!root) {
      return;
    }
    var peer = root === sidebar ? document.getElementById("rl-feed-sheet-body") : sidebar;
    var allInp = root.querySelector('input[name="category"][value=""]');
    root.querySelectorAll('input[name="category"]').forEach(function (inp) {
      inp.addEventListener("change", function () {
        if (inp.value === "" && inp.checked) {
          root.querySelectorAll('input[name="category"]').forEach(function (other) {
            if (other !== inp && other.value) {
              other.checked = false;
            }
          });
        } else if (inp.value && inp.checked && allInp) {
          allInp.checked = false;
        }
        if (peer) {
          syncCategoryInputs(root, peer);
        }
        state.draftCategories = readCategoriesFrom(root);
        state.appliedCategories = cloneCategories(state.draftCategories);
        pruneDraftTagsForCategories();
        renderSkillsCatalog();
        loadCatalog();
        readFilters();
        updateSkillsDraftUi();
        syncChips();
        resetAndLoad();
      });
    });
  }

  if (sidebar) {
    bindCategoryFilters(sidebar);
    sidebar.addEventListener("change", function (e) {
      var name = e.target && e.target.getAttribute("name");
      if (name === "category") {
        return;
      }
      syncChips();
      readFilters();
      resetAndLoad();
    });
    if (resetBtn) {
      resetBtn.addEventListener("click", function () {
        sidebar.querySelector('input[name="source"][value=""]').checked = true;
        sidebar.querySelectorAll('input[name="category"]').forEach(function (inp) {
          inp.checked = inp.value === "";
        });
        sidebar.querySelector('input[name="sort"][value="time"]').checked = true;
        state.draftCategories = [];
        state.appliedCategories = [];
        state.draftTags = [];
        syncChips();
        loadCatalog();
        persistTags([], { reload: true });
      });
    }
  }

  /* Mobile bottom sheet */
  var sheet = document.getElementById("rl-feed-sheet");
  var sheetBody = document.getElementById("rl-feed-sheet-body");
  var openBtn = document.getElementById("rl-feed-filters-open");
  if (sheet && sheetBody && sidebar && openBtn) {
    openBtn.addEventListener("click", function () {
      var scrollBox = sidebar.querySelector(".rl-feed-sidebar__scroll");
      sheetBody.innerHTML = scrollBox ? scrollBox.innerHTML : sidebar.innerHTML;
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
        if (!input || input.name === "category") {
          return;
        }
        label.addEventListener("click", function () {
          sheetBody.querySelectorAll('input[name="' + input.name + '"]').forEach(function (r) {
            r.checked = false;
            r.parentElement.classList.remove("is-active");
          });
          input.checked = true;
          label.classList.add("is-active");
        });
      });
      bindCategoryFilters(sheetBody);
      bindSkillButtons(sheetBody.querySelector(".rl-feed-skills"));
      sheetBody.querySelectorAll(".rl-feed-skills-apply").forEach(function (btn) {
        btn.addEventListener("click", applyDraftTags);
      });
      sheetBody.querySelectorAll(".rl-feed-skills-clear").forEach(function (btn) {
        btn.addEventListener("click", clearSkills);
      });
      bindSkillsPanels(sheetBody);
      updateSkillsBadge();
      updateSkillsDraftUi();
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
      state.draftCategories = readCategoriesFrom(sidebar);
      syncChips();
      readFilters();
      closeSheet();
      if (!tagsEqual(state.draftTags, state.appliedTags)) {
        applyDraftTags();
        return;
      }
      state.appliedCategories = cloneCategories(state.draftCategories);
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
    state.draftCategories = readCategoriesFrom();
    state.appliedCategories = cloneCategories(state.draftCategories);
    renderSkillsCatalog();
    syncChips();
    readFilters();
    resetAndLoad();
  });
})();
