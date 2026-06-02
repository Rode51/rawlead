/**
 * RawLead /feed — карточки, фильтры, infinite scroll (REST proxy same-origin).
 */
(function () {
  "use strict";

  console.log(
    "%c▲ RawLead Architecture by Rode51 ▲",
    "color:#00ff00;font-size:16px;font-weight:bold;"
  );

  var root = document.querySelector('[data-rl-app="feed"]');
  if (!root || !window.rawleadFeed) {
    return;
  }

  var cfg = window.rawleadFeed;
  var TOKEN_KEY = "rawlead_access_token";
  var GUEST_SKILLS_KEY = "rawlead_lenta_skills";
  var MAX_USER_TAGS = 12;
  var TIER_A_BY_NICHE = {
    dev: [
      "telegram_bot_dev",
      "wordpress_dev",
      "web_scraping",
      "api_integration",
      "llm_integration",
      "python",
      "javascript",
    ],
    design: ["ui_ux", "figma", "logo_design", "banner_design"],
    marketing: ["smm", "seo", "email_marketing", "target_ads", "yandex_direct", "google_ads"],
    text: [
      "copywriting",
      "seo_copywriting",
      "article_writing",
      "technical_writing",
      "editing_proofreading",
      "translation",
    ],
  };
  var NICHE_ORDER = ["dev", "design", "marketing", "text"];
  var NICHE_ROOT_LABELS = {
    dev: "Разработка",
    design: "Дизайн",
    marketing: "Маркетинг",
    text: "Тексты",
  };
  var DEV_PICKER_SUBHEADS = [
    { key: "use_case", label: "По задаче" },
    { key: "technology", label: "По технологии" },
  ];
  var listEl = document.getElementById("rl-feed-list");
  var countEl = document.getElementById("rl-feed-count");
  var paginationEl = document.getElementById("rl-feed-pagination");
  var loadMoreBtn = document.getElementById("rl-feed-load-more");
  var paginationCountEl = document.getElementById("rl-feed-pagination-count");
  var paginationShownEl = document.getElementById("rl-feed-shown");
  var paginationTotalEl = document.getElementById("rl-feed-total");
  var loadingEl = document.getElementById("rl-feed-loading");
  var endEl = document.getElementById("rl-feed-end");
  var errorEl = document.getElementById("rl-feed-error");
  var sidebar = document.getElementById("rl-feed-sidebar");
  var resetBtn = sidebar ? sidebar.querySelector(".rl-feed-reset") : null;

  var skillTreeRootsEl = document.getElementById("rl-feed-skill-tree-roots");
  var skillsBadgeEl = document.getElementById("rl-feed-skills-badge");
  var skillsHintEl = document.getElementById("rl-feed-skill-tree-hint");
  var skillsApplyBtn = document.getElementById("rl-feed-skills-apply");
  var skillsClearBtn = document.getElementById("rl-feed-skills-clear");
  var skillsMyBtn = document.getElementById("rl-feed-skills-my");
  var skillsRareBtn = document.getElementById("rl-feed-skills-rare");
  var skillsTriggerEl = document.getElementById("rl-feed-skills-trigger-label");
  var skillsTriggerBtn = document.getElementById("rl-feed-skills-trigger");
  var skillsModalEl = document.getElementById("rl-feed-skills-modal");
  var skillsOverlayEl = document.getElementById("rl-feed-skills-modal-overlay");
  var skillsCloseBtn = document.getElementById("rl-feed-skill-tree-close");
  var skillTreeCounterEl = document.getElementById("rl-feed-skill-tree-counter");
  var skillTreeLimitEl = document.getElementById("rl-feed-skill-tree-limit");
  var sortTriggerEl = document.getElementById("rl-feed-sort-trigger");
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
    catalogByTag: {},
    catalogByNiche: { dev: [], design: [], marketing: [], text: [] },
    expandedNiches: { dev: false, design: false, marketing: false, text: false },
    expandedL1: {},
    showRareSkills: false,
    tagsLimitFlash: false,
    tagsLoading: false,
    loading: false,
    showLoadSpinner: false,
    done: false,
    totalShown: 0,
    total: 0,
    expandedId: null,
    loadGeneration: 0,
    itemsById: {},
  };

  var subscriptionState = null;

  var prefersReduced =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var rlCardIo = null;
  if (!prefersReduced && "IntersectionObserver" in window) {
    rlCardIo = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            rlCardIo.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.08, rootMargin: "0px 0px -5% 0px" }
    );
  }

  function observeLeadCards(root) {
    if (!root) {
      return;
    }
    var cards = root.querySelectorAll(".rl-lead-card:not(.is-visible)");
    if (prefersReduced || !rlCardIo) {
      cards.forEach(function (el) {
        el.classList.add("is-visible");
      });
      return;
    }
    cards.forEach(function (el) {
      rlCardIo.observe(el);
    });
  }

  function updatePagination() {
    var shown = state.totalShown;
    var total = state.total > 0 ? state.total : (state.done ? shown : 0);
    var allLoaded = state.total > 0 ? shown >= state.total : state.done;

    if (paginationShownEl) {
      paginationShownEl.textContent = String(shown);
    }
    if (paginationTotalEl) {
      paginationTotalEl.textContent = String(total > 0 ? total : shown);
    }
    if (paginationCountEl) {
      paginationCountEl.hidden = shown <= 0 || allLoaded;
    }
    if (loadMoreBtn) {
      loadMoreBtn.hidden = shown <= 0 || allLoaded;
      loadMoreBtn.style.display = allLoaded ? "none" : "";
      if (!state.showLoadSpinner) {
        loadMoreBtn.classList.remove("is-loading");
      }
    }
    if (loadingEl) {
      loadingEl.hidden = !state.showLoadSpinner;
    }
    if (paginationEl) {
      paginationEl.hidden = shown <= 0 && !state.showLoadSpinner;
    }
  }

  function apiUrl(params) {
    var q = new URLSearchParams(params);
    return cfg.restFeed + (cfg.restFeed.indexOf("?") >= 0 ? "&" : "?") + q.toString();
  }

  function getToken() {
    try {
      return localStorage.getItem(TOKEN_KEY) || "";
    } catch (e) {
      return "";
    }
  }

  function isLoggedIn() {
    return !!getToken();
  }

  function authHeaders() {
    var h = { "X-WP-Nonce": cfg.nonce || "" };
    var t = getToken();
    if (t) {
      h.Authorization = "Bearer " + t;
    }
    return h;
  }

  function hasPaidAccess() {
    return !!(subscriptionState && subscriptionState.effective_access);
  }

  function loadSubscription() {
    if (!cfg.restSubscription || !getToken()) {
      subscriptionState = null;
      return Promise.resolve(null);
    }
    return fetch(cfg.restSubscription, {
      credentials: "same-origin",
      headers: authHeaders(),
    })
      .then(function (res) {
        if (!res.ok) {
          throw new Error("subscription " + res.status);
        }
        return res.json();
      })
      .then(function (data) {
        subscriptionState = data || null;
        return data;
      })
      .catch(function () {
        subscriptionState = null;
        return null;
      });
  }

  function draftUrl(leadId) {
    var base = (cfg.restDraft || "").replace(/\/$/, "");
    return base + "/" + leadId + "/draft";
  }

  var DRAFT_POLL_MS = 2000;
  var DRAFT_POLL_MAX_MS = 90000;
  var DRAFT_FAIL_RU = "ИИ временно недоступен — повторите";

  function draftReadyPayload(data) {
    if (!data || data.status === "failed") {
      var err = new Error((data && data.error) || DRAFT_FAIL_RU);
      err.status = 503;
      err.detail = (data && data.error) || DRAFT_FAIL_RU;
      throw err;
    }
    if (data.status === "ready" || (data.reply_draft && String(data.reply_draft).trim())) {
      return data;
    }
    return null;
  }

  function pollDraftStatus(leadId, startedMs) {
    if (Date.now() - startedMs > DRAFT_POLL_MAX_MS) {
      var timeoutErr = new Error(DRAFT_FAIL_RU);
      timeoutErr.status = 503;
      timeoutErr.detail = DRAFT_FAIL_RU;
      throw timeoutErr;
    }
    return new Promise(function (resolve) {
      window.setTimeout(resolve, DRAFT_POLL_MS);
    }).then(function () {
      return fetch(draftUrl(leadId), {
        method: "GET",
        credentials: "same-origin",
        headers: authHeaders(),
      }).then(function (res) {
        return res.json().catch(function () {
          return {};
        }).then(function (data) {
          if (res.status === 429 || res.status === 403 || res.status === 404) {
            throw parseDraftApiError(res, data);
          }
          var ready = draftReadyPayload(data);
          if (ready) {
            return ready;
          }
          if (res.status >= 500 && !data.status) {
            throw parseDraftApiError(res, data);
          }
          return pollDraftStatus(leadId, startedMs);
        });
      });
    });
  }

  function fetchDraft(leadId) {
    var startedMs = Date.now();
    return fetch(draftUrl(leadId), {
      method: "POST",
      credentials: "same-origin",
      headers: authHeaders(),
    })
      .then(function (res) {
        return res.json().catch(function () {
          return {};
        }).then(function (data) {
          if (res.status === 429 || res.status === 403 || res.status === 404) {
            throw parseDraftApiError(res, data);
          }
          var ready = draftReadyPayload(data);
          if (ready) {
            return ready;
          }
          if (res.status === 202 || data.status === "pending") {
            return pollDraftStatus(leadId, startedMs);
          }
          if (!res.ok) {
            throw parseDraftApiError(res, data);
          }
          return pollDraftStatus(leadId, startedMs);
        });
      });
  }

  function loadGuestTags() {
    try {
      var raw = localStorage.getItem(GUEST_SKILLS_KEY);
      if (!raw) {
        return [];
      }
      var parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      return [];
    }
  }

  function saveGuestTags(tags) {
    try {
      localStorage.setItem(GUEST_SKILLS_KEY, JSON.stringify(tags || []));
    } catch (e) {
      /* ignore quota / private mode */
    }
  }

  function applyPersistedTags(tags, options) {
    options = options || {};
    state.appliedTags = tags;
    state.draftTags = cloneTags(state.appliedTags);
    if (options.setSortMatch) {
      setSortMatch();
    }
    renderSkillsCatalog();
    readFilters();
    updateFilterBarUi();
    if (options.reload !== false) {
      resetAndLoad();
    }
  }

  function sourceLabel(source) {
    var s = (source || "").toLowerCase();
    if (s.indexOf("fl") === 0 || s === "fl.ru") {
      return { key: "fl", label: "FL.ru", cls: "fl" };
    }
    if (s.indexOf("kwork") >= 0) {
      return { key: "kwork", label: "Kwork", cls: "kwork" };
    }
    if (s === "youdo") {
      return { key: "youdo", label: "YouDo", cls: "youdo" };
    }
    if (s === "freelance_ru") {
      return { key: "freelance_ru", label: "Freelance.ru", cls: "freelance_ru" };
    }
    if (s === "freelancejob") {
      return { key: "freelancejob", label: "FreelanceJob", cls: "freelancejob" };
    }
    if (s === "pchyol") {
      return { key: "pchyol", label: "Пчёл.нет", cls: "pchyol" };
    }
    if (s.indexOf("tg") === 0 || s.indexOf("telegram") === 0) {
      return { key: "tg", label: "TG", cls: "tg" };
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

  var HOT_MAX_AGE_MS = 300000;

  function isHot(item) {
    if (!item) {
      return false;
    }
    if (item.is_hot === true) {
      return true;
    }
    if (item.is_hot === false) {
      return false;
    }
    if (!item.created_at) {
      return false;
    }
    var d = new Date(item.created_at);
    if (isNaN(d.getTime())) {
      return false;
    }
    var age = Date.now() - d.getTime();
    return age >= 0 && age < HOT_MAX_AGE_MS;
  }

  function hotBadgeHtml(item) {
    if (!isHot(item)) {
      return "";
    }
    return '<span class="rl-badge-hot" aria-label="Горячий заказ">Горячий</span>';
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
    return s
      .replace(/&amp;/g, "&")
      .replace(/&lt;/g, "<")
      .replace(/&gt;/g, ">")
      .replace(/&quot;/g, '"')
      .replace(/&mdash;/g, "—")
      .replace(/&ndash;/g, "–")
      .replace(/&nbsp;/g, " ");
  }

  function normalizeSingleLine(str) {
    return String(str || "")
      .replace(/\r\n?/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function prepForDisplay(str, singleLine) {
    var s = decodeHtmlEntities(str);
    if (singleLine) {
      return normalizeSingleLine(s);
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
    var summary = prepForDisplay(item.task_summary || "", false).trim();
    if (summary) {
      return summary;
    }
    var raw = prepForDisplay(item.body || item.title || "", false).trim();
    return truncateTaskSnippet(stripLeadingTaskLabel(raw), 280);
  }

  function renderExpandedBody(item) {
    var task = taskBodyText(item);
    var html = "";
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
    var reply = prepForDisplay(item.reply_draft || "", false).trim();
    var tools = isLoggedIn() && reply ? item.tools_required || [] : [];
    if (tools.length) {
      html +=
        '<div class="rl-feed-card__section">' +
        '<h4 class="rl-feed-card__section-title">Инструменты</h4>' +
        '<ul class="rl-feed-card__tools">' +
        tools
          .map(function (tool) {
            return "<li>" + escapeHtml(prepForDisplay(tool, true)) + "</li>";
          })
          .join("") +
        "</ul></div>";
    }
    if (reply) {
      html +=
        '<div class="rl-feed-card__section">' +
        '<h4 class="rl-feed-card__section-title">Черновик отклика</h4>' +
        '<p class="rl-feed-card__reply" data-reply-text>' +
        escapeHtml(reply) +
        "</p>" +
        '<button type="button" class="rl-btn rl-btn--ghost rl-feed-card__copy" data-copy-reply>Скопировать черновик</button>' +
        "</div>";
    }
    if (item.url) {
      html +=
        '<a class="rl-btn rl-btn--ghost rl-feed-card__link" href="' +
        escapeHtml(item.url) +
        '" target="_blank" rel="noopener" onclick="event.stopPropagation()">Читать на бирже ↗</a>';
    }
    return html;
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
      html.push('<span class="rl-chip rl-chip--more">+' + (tags.length - max) + "</span>");
    }
    return html.join("");
  }

  function leadTagKeys(item) {
    var raw =
      (item && item.lead_tags) ||
      (item && item.lead_tag_labels) ||
      [];
    if (!Array.isArray(raw)) {
      return [];
    }
    return raw
      .map(function (t) {
        return String(t).trim().toLowerCase().replace(/^#/, "");
      })
      .filter(Boolean);
  }

  function countMatchedSkills(item) {
    var leadTags = leadTagKeys(item);
    var userTags = (state.appliedTags || []).map(function (t) {
      return String(t).trim().toLowerCase().replace(/^#/, "");
    });
    var userSet = {};
    var i;
    for (i = 0; i < userTags.length; i++) {
      userSet[userTags[i]] = true;
    }
    var matched = 0;
    for (i = 0; i < leadTags.length; i++) {
      if (userSet[leadTags[i]]) {
        matched += 1;
      }
    }
    return { matched: matched, total: leadTags.length };
  }

  function hasUserSkills() {
    return state.appliedTags && state.appliedTags.length > 0;
  }

  function isPerfectMatch(item) {
    var km = item.keyword_match != null ? item.keyword_match : 0;
    return km >= 100 && hasUserSkills() && leadTagKeys(item).length >= 2;
  }

  function renderPerfectBadge(perfect) {
    if (perfect) {
      return '<span class="rl-badge rl-badge--perfect">ИДЕАЛЬНО ✦</span>';
    }
    return "";
  }

  function renderMatchBreakdown(item) {
    if (hasUserSkills()) {
      var counts = countMatchedSkills(item);
      var km = item.keyword_match != null ? item.keyword_match : 0;
      var text =
        counts.total > 0
          ? "Совпало " + counts.matched + " из " + counts.total + " навыков заказа"
          : "Совпадение навыков " + km + "%";
      return '<div class="rl-match-breakdown">' + escapeHtml(text) + "</div>";
    }
    if (!isLoggedIn()) {
      return (
        '<div class="rl-match-breakdown">' +
        '<button type="button" class="rl-match-breakdown__link" data-open-skills>' +
        "Добавь навыки, чтобы увидеть совместимость →" +
        "</button></div>"
      );
    }
    return (
      '<div class="rl-match-breakdown">' +
      escapeHtml("Укажи навыки в кабинете") +
      "</div>"
    );
  }

  function renderMatchBlock(item) {
    var skillsSelected = hasUserSkills();
    if (!skillsSelected) {
      return (
        '<div class="rl-match rl-match--no-skills">' +
        renderMatchBreakdown(item) +
        "</div>"
      );
    }
    var km = item.keyword_match != null ? item.keyword_match : 0;
    var perfect = isPerfectMatch(item);
    var compatTitle =
      ' title="Насколько ваш стек совпадает с заказом — не оценка качества заказа"';
    return (
      '<div class="rl-match">' +
      '<div class="rl-match-row">' +
      '<div class="rl-match__bar" role="progressbar" aria-valuenow="' +
      km +
      '" aria-valuemin="0" aria-valuemax="100">' +
      '<span class="rl-match__fill" style="--match-value:' +
      km +
      '%"></span>' +
      "</div>" +
      '<div class="rl-match__label">' +
      '<span class="rl-match__pct">' +
      km +
      "%</span> " +
      '<span class="rl-match__name"' +
      compatTitle +
      ">Совместимость</span>" +
      renderPerfectBadge(perfect) +
      "</div></div>" +
      renderMatchBreakdown(item) +
      "</div>"
    );
  }

  function syncExpandedL1FromDraft() {
    var i;
    var tag;
    for (i = 0; i < state.draftTags.length; i++) {
      tag = state.draftTags[i];
      var row = state.catalogByTag[tag];
      if (row && (row.children || []).length > 0) {
        state.expandedL1[tag] = true;
      }
    }
  }

  function closeFeedSkillsModal() {
    if (!skillsModalEl) {
      return;
    }
    skillsModalEl.hidden = true;
    document.body.classList.remove("rl-skill-tree-open");
    closeSkillsDropdown();
  }

  function openFeedSkillsModal() {
    if (!skillsModalEl) {
      openSheet();
      return;
    }
    var sortDd = document.querySelector(".rl-filter-sort-dd");
    if (sortDd && sortDd.open) {
      sortDd.open = false;
    }
    syncExpandedL1FromDraft();
    skillsModalEl.hidden = false;
    document.body.classList.add("rl-skill-tree-open");
    function afterCatalog() {
      rebuildFeedCatalogIndex();
      renderSkillsCatalog();
    }
    if (!state.catalog.length && !state.catalogGroups.length) {
      loadCatalog().finally(afterCatalog);
      return;
    }
    afterCatalog();
  }

  function openSkillsUi() {
    if (usesSkillTree() && skillsModalEl) {
      openFeedSkillsModal();
      return;
    }
    openSheet();
  }

  var VIEWS_EYE_SVG =
    '<svg class="rl-feed-card__views-icon" width="12" height="12" viewBox="0 0 24 24" aria-hidden="true" focusable="false">' +
    '<path fill="currentColor" d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zm0 12.5a5 5 0 110-10 5 5 0 010 10zm0-8a3 3 0 100 6 3 3 0 000-6z"/>' +
    "</svg>";

  function viewsHeadHtml(item) {
    var v = item.display_views;
    if (v == null || v <= 0) {
      return "";
    }
    var n = escapeHtml(String(v));
    return (
      '<span class="rl-feed-card__views" aria-label="' +
      n +
      ' просмотров">' +
      VIEWS_EYE_SVG +
      '<span class="rl-feed-card__views-count">' +
      n +
      "</span></span>"
    );
  }

  function repliedBadgeHtml() {
    return '<span class="rl-badge rl-badge--replied">Отклик ✓</span>';
  }

  function replyCtaHtml(item) {
    var reply = "";
    if (isLoggedIn()) {
      reply = prepForDisplay(item.reply_draft || "", false).trim();
    }
    if (reply) {
      return (
        '<div class="rl-feed-card__cta">' +
        repliedBadgeHtml() +
        "</div>"
      );
    }
    if (!hasPaidAccess()) {
      return "";
    }
    return (
      '<div class="rl-feed-card__cta">' +
      '<button type="button" class="rl-btn rl-btn--primary rl-feed-card__reply-btn">Написать отклик</button>' +
      "</div>"
    );
  }

  function headBadgesHtml(item) {
    var src = sourceLabel(item.source);
    return (
      '<span class="rl-feed-card__source rl-feed-card__source--' +
      src.cls +
      '">' +
      escapeHtml(src.label) +
      "</span>" +
      hotBadgeHtml(item)
    );
  }

  function renderCard(item, isNew) {
    var perfect = isPerfectMatch(item);
    var budget = formatBudgetDisplay(item.budget_text || "—");
    var titleText = prepForDisplay(item.title || "Без названия", true);
    var titleHtml = escapeHtml(titleText);
    var expanded = state.expandedId === item.id;

    return (
      '<article class="rl-lead-card' +
      (isNew ? " is-new" : "") +
      (expanded ? " is-expanded" : "") +
      (perfect ? " rl-lead-card--perfect-match" : "") +
      '" data-id="' +
      item.id +
      '" tabindex="0" role="button">' +
      '<div class="rl-feed-card__head">' +
      '<div class="rl-feed-card__head-start">' +
      headBadgesHtml(item) +
      "</div>" +
      '<div class="rl-feed-card__head-meta">' +
      viewsHeadHtml(item) +
      '<span class="rl-feed-card__time">' +
      formatTime(item.created_at) +
      "</span>" +
      "</div>" +
      "</div>" +
      '<h3 class="rl-lead-card__title">' +
      '<span title="' +
      titleHtml +
      '">' +
      titleHtml +
      "</span>" +
      "</h3>" +
      '<p class="rl-lead-card__budget">Бюджет: ' +
      escapeHtml(budget) +
      "</p>" +
      renderMatchBlock(item) +
      '<div class="rl-chips">' +
      renderTagChips(item) +
      "</div>" +
      replyCtaHtml(item) +
      '<div class="rl-feed-card__body">' +
      '<div class="rl-feed-card__body-inner">' +
      renderExpandedBody(item) +
      "</div></div>" +
      "</article>"
    );
  }

  function skeletonHtml(n) {
    var html = "";
    var i;
    for (i = 0; i < n; i++) {
      html +=
        '<div class="rl-lead-card rl-lead-card--skeleton" aria-hidden="true">' +
        '<div class="rl-skeleton rl-skeleton--badge"></div>' +
        '<div class="rl-skeleton rl-skeleton--title"></div>' +
        '<div class="rl-skeleton rl-skeleton--meta"></div>' +
        '<div class="rl-skeleton rl-skeleton--bar"></div>' +
        '<div class="rl-skeleton rl-skeleton--chips"></div>' +
        "</div>";
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

  function showDraftError(msg, retryFn) {
    if (!errorEl) {
      return;
    }
    errorEl.hidden = false;
    var html = escapeHtml(msg);
    if (retryFn) {
      html += ' <button type="button" class="rl-feed-banner__retry">Повторить</button>';
    }
    errorEl.innerHTML = html;
    var btn = errorEl.querySelector(".rl-feed-banner__retry");
    if (btn && retryFn) {
      btn.addEventListener("click", function () {
        errorEl.hidden = true;
        retryFn();
      });
    }
  }

  function parseDraftApiError(res, data) {
    var err = new Error("HTTP " + res.status);
    err.status = res.status;
    var detail = "";
    var retryAfter = null;
    if (data && typeof data === "object") {
      if (typeof data.detail === "string") {
        detail = data.detail;
      } else if (data.detail && typeof data.detail === "object") {
        detail = String(data.detail.error || data.detail.detail || "");
        retryAfter = data.detail.retry_after_sec;
      }
      if (!detail && data.error) {
        detail = String(data.error);
      }
      if (!detail && data.message) {
        detail = String(data.message);
      }
      if (data.data && data.data.retry_after_sec != null) {
        retryAfter = data.data.retry_after_sec;
      }
      if (data.retry_after_sec != null) {
        retryAfter = data.retry_after_sec;
      }
    }
    err.detail = detail;
    err.retryAfterSec = retryAfter;
    return err;
  }

  function updateDelayNotice() {
    var el = document.getElementById("rl-feed-delay-notice");
    if (!el) {
      return;
    }
    if (hasPaidAccess()) {
      el.hidden = true;
      return;
    }
    var pricing = (cfg.pricingUrl || "/pricing/").replace(/\/$/, "") + "/";
    el.innerHTML =
      "⏱ Лента обновляется раз в 15 мин · " +
      '<a href="' +
      escapeHtml(pricing) +
      '">Ускорить →</a>';
    el.hidden = false;
  }

  function feedCountSuffix() {
    return state.sort === "match" ? "по совместимости" : "по дате";
  }

  function updateCount() {
    if (!countEl) {
      return;
    }
    if (state.totalShown <= 0) {
      countEl.textContent = "";
      return;
    }
    countEl.textContent =
      state.totalShown + " заказов · " + feedCountSuffix();
    updatePagination();
  }

  function categoryEmptyMessage() {
    return (
      '<p class="rl-feed-empty">В этой нише пока нет заказов — попробуй «Все»</p>' +
      '<button type="button" class="rl-btn rl-btn--ghost rl-feed-empty__cta">Сбросить фильтры</button>'
    );
  }

  function bindEmptyCta() {
    if (!listEl) {
      return;
    }
    var btn = listEl.querySelector(".rl-feed-empty__cta");
    if (btn && resetBtn) {
      btn.addEventListener("click", function () {
        resetBtn.click();
      });
    }
  }

  function applySkillsSectionText(el, categories) {
    if (!el) {
      return;
    }
    var catLabels = {
      dev: "Разработка",
      design: "Дизайн",
      marketing: "Маркетинг",
      text: "Тексты",
    };
    if (categories.length === 1) {
      var key = categories[0];
      el.textContent = "По нише «" + (catLabels[key] || key) + "»:";
      el.hidden = false;
    } else if (categories.length === 0) {
      el.textContent = "Популярные навыки:";
      el.hidden = false;
    } else {
      el.textContent = "Популярные навыки:";
      el.hidden = false;
    }
  }

  function populatedSheetBody() {
    var body = document.getElementById("rl-feed-sheet-body");
    return body && body.querySelector(".rl-feed-skills") ? body : null;
  }

  function updateFilterBarUi() {
    if (skillsTriggerEl) {
      var skillsLabel =
        state.appliedTags.length > 0
          ? "Навыки · " + state.appliedTags.length
          : "Навыки";
      skillsTriggerEl.textContent = skillsLabel;
      var triggerWrap = document.getElementById("rl-feed-skills-trigger");
      if (triggerWrap) {
        triggerWrap.classList.toggle("has-selection", state.appliedTags.length > 0);
      }
    }
    if (sortTriggerEl) {
      var sortLabel = state.sort === "match" ? "По совместимости ▾" : "Дата ▾";
      sortTriggerEl.textContent = sortLabel;
      sortTriggerEl.classList.toggle("has-selection", state.sort === "match");
    }
    var sheetRoot = populatedSheetBody();
    if (sheetRoot) {
      applySkillsSectionText(
        sheetRoot.querySelector(".rl-feed-skills__section"),
        state.draftCategories
      );
    }
    var mobileFilterBtn = document.getElementById("rl-feed-filters-open");
    if (mobileFilterBtn) {
      var filterCount =
        state.appliedTags.length +
        (state.appliedCategories.length ? 1 : 0);
      mobileFilterBtn.textContent =
        filterCount > 0 ? "Фильтр · " + filterCount : "Фильтр";
      mobileFilterBtn.classList.toggle(
        "has-selection",
        filterCount > 0 ||
          state.source !== "" ||
          state.sort !== "time"
      );
    }
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
    var sheetRoot = populatedSheetBody();
    if (sheetRoot) {
      var sheetBadge = sheetRoot.querySelector(".rl-feed-skills-dd__badge");
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

  function updateFeedSkillTreeChrome() {
    var n = state.draftTags.length;
    var atLimit = n >= MAX_USER_TAGS;
    if (skillTreeCounterEl) {
      skillTreeCounterEl.textContent = "Выбрано " + n + " / " + MAX_USER_TAGS;
      skillTreeCounterEl.classList.toggle("is-active", n > 0);
    }
    if (skillTreeLimitEl) {
      skillTreeLimitEl.hidden = !atLimit;
    }
    if (skillsHintEl && !state.tagsLimitFlash) {
      skillsHintEl.hidden = !(
        !tagsEqual(state.draftTags, state.appliedTags) ||
        !categoriesEqual(state.draftCategories, state.appliedCategories)
      );
    }
  }

  function updateSkillsDraftUi() {
    var dirty =
      !tagsEqual(state.draftTags, state.appliedTags) ||
      !categoriesEqual(state.draftCategories, state.appliedCategories);
    var sortDirty = false;
    if (sidebar) {
      var sortInp = sidebar.querySelector('input[name="sort"]:checked');
      sortDirty = sortInp && sortInp.value !== state.sort;
    }
    dirty = dirty || sortDirty;
    updateFeedSkillTreeChrome();
    var hints = [skillsHintEl];
    var applyBtns = [skillsApplyBtn];
    var sheetRoot = populatedSheetBody();
    if (sheetRoot) {
      var sheetHint = sheetRoot.querySelector(".rl-feed-skills__hint");
      var sheetApply = sheetRoot.querySelector(".rl-feed-skills-apply");
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
      if (state.tagsLimitFlash) {
        el.hidden = false;
        el.textContent = "Максимум " + MAX_USER_TAGS + " навыков";
        return;
      }
      el.hidden = !dirty;
      if (!dirty && el.id === "rl-feed-skills-hint") {
        el.textContent = "Выберите навыки и нажмите Применить";
      }
    });
    applyBtns.forEach(function (btn) {
      if (!btn) {
        return;
      }
      btn.disabled = state.tagsLoading || !dirty;
    });
  }

  function pickerRowVisible(row) {
    if (!row || !row.tag) {
      return false;
    }
    var tier = row.tier || "A";
    var cats = state.draftCategories;
    var niche = cats.length === 1 ? cats[0] : null;

    if (niche) {
      var tierA = TIER_A_BY_NICHE[niche] || [];
      if (tierA.indexOf(row.tag) >= 0) {
        return true;
      }
      if (state.showRareSkills) {
        return row.category === niche;
      }
      return false;
    }

    if (cats.length > 1) {
      if (row.category && cats.indexOf(row.category) < 0) {
        return false;
      }
      if (state.showRareSkills) {
        return true;
      }
      var popular = TIER_A_BY_NICHE[row.category] || [];
      return popular.indexOf(row.tag) >= 0;
    }

    return state.showRareSkills || tier === "A";
  }

  function usesSkillTree() {
    var i;
    for (i = 0; i < state.catalogGroups.length; i++) {
      if (state.catalogGroups[i].picker_subheads) {
        return true;
      }
    }
    return false;
  }

  function catalogCategoryForTag(tag) {
    var i;
    for (i = 0; i < state.catalog.length; i++) {
      if (state.catalog[i].tag === tag) {
        return state.catalog[i].category;
      }
    }
    var g;
    for (g = 0; g < state.catalogGroups.length; g++) {
      var sk = state.catalogGroups[g].skills || [];
      var j;
      for (j = 0; j < sk.length; j++) {
        if (sk[j].tag === tag) {
          return state.catalogGroups[g].category;
        }
      }
    }
    return null;
  }

  function rebuildFeedCatalogIndex() {
    var byTag = {};
    var byNiche = { dev: [], design: [], marketing: [], text: [] };
    var seen = {};

    function ingest(row, category) {
      if (!row || !row.tag || seen[row.tag]) {
        return;
      }
      var cat = category || row.category || catalogCategoryForTag(row.tag);
      if (!cat || !byNiche[cat]) {
        return;
      }
      seen[row.tag] = true;
      var item = {
        tag: row.tag,
        title_ru: row.title_ru || row.tag,
        category: cat,
        tier: row.tier || "A",
        picker_level: row.picker_level || "L1",
        picker_group: row.picker_group || "",
        children: row.children || [],
      };
      byTag[row.tag] = item;
      if (item.picker_level === "L3") {
        return;
      }
      byNiche[cat].push(item);
      var ch;
      for (ch = 0; ch < (row.children || []).length; ch++) {
        ingest(row.children[ch], cat);
      }
    }

    var g;
    var s;
    for (g = 0; g < state.catalogGroups.length; g++) {
      var grp = state.catalogGroups[g];
      for (s = 0; s < (grp.skills || []).length; s++) {
        ingest(grp.skills[s], grp.category);
      }
    }
    for (g = 0; g < state.catalog.length; g++) {
      ingest(state.catalog[g]);
    }

    NICHE_ORDER.forEach(function (niche) {
      byNiche[niche].sort(function (a, b) {
        var ta = a.tier === "A" ? 0 : 1;
        var tb = b.tier === "A" ? 0 : 1;
        if (ta !== tb) {
          return ta - tb;
        }
        return (a.title_ru || a.tag).localeCompare(b.title_ru || b.tag, "ru");
      });
    });

    state.catalogByTag = byTag;
    state.catalogByNiche = byNiche;
  }

  function catalogGroupForNiche(niche) {
    var g;
    for (g = 0; g < state.catalogGroups.length; g++) {
      if (state.catalogGroups[g].category === niche) {
        return state.catalogGroups[g];
      }
    }
    return null;
  }

  function feedSkillChipHtml(row, atLimit, opts) {
    opts = opts || {};
    var tag = row.tag || "";
    var label = (row.title_ru || tag).trim() || tag;
    var selected = state.draftTags.indexOf(tag) >= 0;
    var disabled = atLimit && !selected;
    var level = row.picker_level || opts.level || "L1";
    return (
      '<button type="button" class="rl-skill-chip rl-feed-skill' +
      (level === "L3" ? " rl-skill-chip--l3" : "") +
      (selected ? " is-selected" : "") +
      (disabled ? " is-disabled" : "") +
      '" data-tag="' +
      escapeHtml(tag) +
      '"' +
      (disabled ? ' disabled aria-disabled="true"' : "") +
      ">" +
      (selected ? "✓ " : "") +
      escapeHtml(label) +
      "</button>"
    );
  }

  function renderFeedL1ChipBlock(row, atLimit, niche) {
    var tag = row.tag || "";
    var selected = state.draftTags.indexOf(tag) >= 0;
    var children = row.children || [];
    var hasL3 = children.length > 0;
    var l3Open = selected && hasL3;
    var html =
      '<div class="rl-l1-chip-wrap">' + feedSkillChipHtml(row, atLimit, { niche: niche, level: "L1" }) + "</div>";
    if (hasL3) {
      html +=
        '<div class="rl-l3-row' +
        (l3Open ? " is-visible" : "") +
        '" data-l3-parent="' +
        escapeHtml(tag) +
        '">';
      for (var ci = 0; ci < children.length; ci++) {
        html += feedSkillChipHtml(
          {
            tag: children[ci].tag,
            title_ru: children[ci].title_ru,
            picker_level: "L3",
          },
          atLimit,
          { niche: niche, level: "L3" }
        );
      }
      html += "</div>";
    }
    return html;
  }

  function renderFeedDevNicheBody(skills, atLimit, niche) {
    var bodyHtml = "";
    var grp = catalogGroupForNiche(niche);
    var subheads = (grp && grp.picker_subheads) || DEV_PICKER_SUBHEADS;
    var si;
    var sh;
    for (si = 0; si < subheads.length; si++) {
      sh = subheads[si];
      var l1skills = skills.filter(function (row) {
        return row.picker_group === sh.key && (row.picker_level || "L1") === "L1";
      });
      if (!l1skills.length) {
        continue;
      }
      bodyHtml +=
        '<p class="rl-niche-subhead">' + escapeHtml(String(sh.label).toUpperCase()) + "</p>";
      bodyHtml += '<div class="rl-niche-root__chips">';
      for (var lj = 0; lj < l1skills.length; lj++) {
        bodyHtml += renderFeedL1ChipBlock(l1skills[lj], atLimit, niche);
      }
      bodyHtml += "</div>";
    }
    return bodyHtml;
  }

  function visibleNichesForTree() {
    if (state.draftCategories.length === 1) {
      return [state.draftCategories[0]];
    }
    if (state.draftCategories.length > 1) {
      return state.draftCategories.slice();
    }
    return NICHE_ORDER.slice();
  }

  function renderFeedSkillTreeHtml() {
    var atLimit = state.draftTags.length >= MAX_USER_TAGS;
    var html = "";
    var niches = visibleNichesForTree();
    var ni;
    for (ni = 0; ni < niches.length; ni++) {
      var niche = niches[ni];
      if (NICHE_ORDER.indexOf(niche) < 0) {
        continue;
      }
      var expanded = !!state.expandedNiches[niche];
      var skills = state.catalogByNiche[niche] || [];
      var grpNiche = catalogGroupForNiche(niche);
      var bodyHtml = "";
      if (grpNiche && grpNiche.picker_subheads) {
        bodyHtml = renderFeedDevNicheBody(skills, atLimit, niche);
      } else if (skills.length) {
        bodyHtml =
          '<div class="rl-niche-root__chips">' +
          skills
            .map(function (row) {
              return feedSkillChipHtml(row, atLimit, { niche: niche });
            })
            .join("") +
          "</div>";
      }
      if (!bodyHtml) {
        continue;
      }
      html +=
        '<section class="rl-niche-root' +
        (expanded ? " rl-niche-root--expanded" : "") +
        '" data-niche="' +
        escapeHtml(niche) +
        '">' +
        '<button type="button" class="rl-niche-root__header" data-niche-toggle="' +
        escapeHtml(niche) +
        '">' +
        '<span class="rl-niche-root__chevron" aria-hidden="true">' +
        (expanded ? "▾" : "▸") +
        "</span><span>" +
        escapeHtml(NICHE_ROOT_LABELS[niche] || niche) +
        "</span></button>" +
        '<div class="rl-niche-root__body">' +
        bodyHtml +
        "</div></section>";
    }
    return html ? '<div class="rl-skill-tree__roots">' + html + "</div>" : "";
  }

  function renderRareSkillsSection() {
    if (!state.showRareSkills) {
      return "";
    }
    var rows = state.catalog.filter(function (row) {
      if (!row || !row.tag) {
        return false;
      }
      if ((row.picker_level || "") === "L3") {
        return false;
      }
      var niche = row.category;
      if (state.draftCategories.length && state.draftCategories.indexOf(niche) < 0) {
        return false;
      }
      var tierA = TIER_A_BY_NICHE[niche] || [];
      return tierA.indexOf(row.tag) < 0;
    });
    if (!rows.length) {
      return "";
    }
    return (
      '<div class="rl-feed-skills-rare">' +
      '<p class="rl-niche-subhead">ЕЩЁ НАВЫКИ</p>' +
      '<div class="rl-niche-root__chips">' +
      rows.map(skillChipHtml).join("") +
      "</div></div>"
    );
  }

  function bindFeedSkillTree(container) {
    if (!container) {
      return;
    }
    container.querySelectorAll("[data-niche-toggle]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var nicheKey = btn.getAttribute("data-niche-toggle");
        if (!nicheKey) {
          return;
        }
        state.expandedNiches[nicheKey] = !state.expandedNiches[nicheKey];
        renderSkillsCatalog();
      });
    });
    container.querySelectorAll(".rl-feed-skill:not(.is-disabled)").forEach(function (btn) {
      btn.addEventListener("click", function () {
        toggleDraftTag(btn.getAttribute("data-tag"));
      });
    });
    container.querySelectorAll("[data-l1-expand]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        var parentTag = btn.getAttribute("data-l1-expand");
        if (!parentTag) {
          return;
        }
        state.expandedL1[parentTag] = !state.expandedL1[parentTag];
        renderSkillsCatalog();
      });
    });
  }

  function setSheetActionLabel(btn, text) {
    if (!btn) {
      return;
    }
    var label = btn.querySelector(".rl-sheet-text-btn__label");
    if (label) {
      label.textContent = text;
    } else {
      btn.textContent = text;
    }
  }

  function updateRareSkillsUi() {
    var rareLabel = state.showRareSkills ? "Свернуть" : "Ещё навыки";
    var expanded = state.showRareSkills ? "true" : "false";
    var sheet = document.getElementById("rl-feed-sheet");
    var sheetRoot = populatedSheetBody();
    var sheetOpen = sheet && !sheet.hidden && sheetRoot;

    if (sheetOpen) {
      var rareBtn = sheetRoot.querySelector("#rl-sheet-skills-rare");
      if (rareBtn) {
        rareBtn.removeAttribute("hidden");
        rareBtn.hidden = false;
        setSheetActionLabel(rareBtn, rareLabel);
        rareBtn.setAttribute("aria-expanded", expanded);
      }
      return;
    }

    if (skillsRareBtn) {
      skillsRareBtn.hidden = false;
      skillsRareBtn.textContent = rareLabel;
      skillsRareBtn.setAttribute("aria-expanded", expanded);
    }
  }

  function catsLengthGt1(cats) {
    return (cats || []).length > 1;
  }

  function toggleDraftTag(tag) {
    if (!tag) {
      return;
    }
    var idx = state.draftTags.indexOf(tag);
    if (idx < 0 && state.draftTags.length >= MAX_USER_TAGS) {
      state.tagsLimitFlash = true;
      updateSkillsDraftUi();
      return;
    }
    state.tagsLimitFlash = false;
    if (idx >= 0) {
      state.draftTags = state.draftTags.filter(function (t) {
        return t !== tag;
      });
      if (state.expandedL1[tag]) {
        delete state.expandedL1[tag];
      }
    } else {
      state.draftTags = state.draftTags.concat([tag]);
      var row = state.catalogByTag[tag];
      if (row && (row.children || []).length > 0) {
        state.expandedL1[tag] = true;
      }
    }
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
    var label = (row.title_ru || tag).trim() || tag;
    var active = state.draftTags.indexOf(tag) >= 0;
    return (
      '<button type="button" class="rl-feed-chip rl-feed-skill' +
      (active ? " is-active" : "") +
      '" data-tag="' +
      escapeHtml(tag) +
      '">' +
      escapeHtml(label) +
      (row.count ? ' <span class="rl-feed-skill__count">' + row.count + "</span>" : "") +
      "</button>"
    );
  }

  function renderSkillsInto(container) {
    if (!container) {
      return;
    }
    if (!state.catalogGroups.length && !state.catalog.length) {
      container.innerHTML =
        '<p class="rl-feed-skills__empty">Пока нет навыков в ленте — дождитесь заказов из бота</p>';
      return;
    }
    if (usesSkillTree()) {
      rebuildFeedCatalogIndex();
      var treeHtml = renderFeedSkillTreeHtml();
      var rareHtml = renderRareSkillsSection();
      container.innerHTML =
        treeHtml + rareHtml ||
        '<p class="rl-feed-skills__empty">Нет навыков для выбранной ниши</p>';
      bindFeedSkillTree(container);
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
          var skills = (group.skills || []).filter(function (row) {
            return pickerRowVisible({
              tag: row.tag,
              tier: row.tier,
              category: row.category || group.category,
            });
          });
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
      var flat = state.catalog.filter(pickerRowVisible);
      container.innerHTML = flat.length
        ? '<div class="rl-feed-skills-group__chips">' + flat.map(skillChipHtml).join("") + "</div>"
        : '<p class="rl-feed-skills__empty">Нет навыков для выбранной ниши</p>';
    }
    bindSkillButtons(container);
  }

  function renderSkillsCatalog() {
    updateSkillsBadge();
    updateSkillsDraftUi();
    updateFilterBarUi();
    if (skillTreeRootsEl) {
      renderSkillsInto(skillTreeRootsEl);
    }
    var sheetRoot = populatedSheetBody();
    if (sheetRoot) {
      var sheetSkills = sheetRoot.querySelector(".rl-feed-skills");
      if (sheetSkills) {
        renderSkillsInto(sheetSkills);
      }
    }
    updateRareSkillsUi();
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
      updateFilterBarUi();
    }
  }

  function persistTags(tags, options) {
    options = options || {};
    if (state.tagsLoading) {
      return Promise.resolve();
    }
    state.tagsLoading = true;
    updateSkillsDraftUi();
    saveGuestTags(tags);
    applyPersistedTags(tags, options);
    state.tagsLoading = false;
    updateSkillsDraftUi();
    return Promise.resolve();
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
        (row.children || []).forEach(function (child) {
          if (child.tag) {
            allowed[child.tag] = true;
          }
        });
      });
    });
    state.catalog.forEach(function (row) {
      if (row.tag) {
        allowed[row.tag] = true;
      }
    });
    state.draftTags = state.draftTags.filter(function (tag) {
      return allowed[tag];
    });
  }

  function applyDraftTags() {
    var tagsDirty = !tagsEqual(state.draftTags, state.appliedTags);
    var catsDirty = !categoriesEqual(state.draftCategories, state.appliedCategories);
    if (!tagsDirty && !catsDirty) {
      closeFeedSkillsModal();
      return;
    }
    state.appliedCategories = cloneCategories(state.draftCategories);
    closeFeedSkillsModal();
    if (tagsDirty) {
      persistTags(cloneTags(state.draftTags), { setSortMatch: true, reload: true });
      return;
    }
    readFilters();
    resetAndLoad();
  }

  function loadTags() {
    state.appliedTags = loadGuestTags();
    state.draftTags = cloneTags(state.appliedTags);
    return Promise.resolve();
  }

  function loadMyProfileSkills() {
    if (!isLoggedIn()) {
      if (skillsHintEl) {
        skillsHintEl.hidden = false;
        skillsHintEl.textContent = "Войди в кабинет, чтобы подставить навыки профиля";
      }
      return;
    }
    if (!cfg.restTags) {
      return;
    }
    state.tagsLoading = true;
    updateSkillsDraftUi();
    fetch(cfg.restTags, { credentials: "same-origin", headers: authHeaders() })
      .then(function (res) {
        return res.ok ? res.json() : { tags: [] };
      })
      .then(function (data) {
        state.draftTags = cloneTags(data.tags || []);
        state.tagsLimitFlash = false;
        renderSkillsCatalog();
        if (skillsHintEl) {
          skillsHintEl.hidden = false;
          skillsHintEl.textContent = "Навыки профиля подставлены — нажми «Применить»";
        }
      })
      .catch(function () {
        showError("Не удалось загрузить навыки профиля.");
      })
      .finally(function () {
        state.tagsLoading = false;
        updateSkillsDraftUi();
      });
  }

  function loadCatalog() {
    if (!cfg.restSkills) {
      return Promise.resolve();
    }
    var url = cfg.restSkills;
    var sep = url.indexOf("?") >= 0 ? "&" : "?";
    url = url + sep + "mode=full&limit=200";
    if (state.draftCategories.length === 1) {
      url += "&category=" + encodeURIComponent(state.draftCategories[0]);
    } else if (state.draftCategories.length > 1) {
      url += "&category=" + encodeURIComponent(state.draftCategories.join(","));
    }
    return fetch(url, { credentials: "same-origin" })
      .then(function (res) {
        return res.ok ? res.json() : { skills: [] };
      })
      .then(function (data) {
        state.catalogGroups = data.groups || [];
        state.catalog = data.skills || [];
        rebuildFeedCatalogIndex();
        NICHE_ORDER.forEach(function (n) {
          if (state.expandedNiches[n] === undefined) {
            state.expandedNiches[n] = state.draftCategories.indexOf(n) >= 0;
          }
        });
        renderSkillsCatalog();
      })
      .catch(function () {
        state.catalogGroups = [];
        state.catalog = [];
        renderSkillsCatalog();
      });
  }

  function syncChipActiveStates(root) {
    if (!root) {
      return;
    }
    root.querySelectorAll(".rl-feed-chip, .rl-cat-chip, .rl-sort-option").forEach(function (label) {
      var input = label.querySelector("input");
      label.classList.toggle("is-active", !!(input && input.checked));
    });
  }

  function syncChips() {
    syncChipActiveStates(sidebar);
    var sheetRoot = populatedSheetBody();
    if (sheetRoot) {
      syncChipActiveStates(sheetRoot);
    }
  }

  function resetAndLoad() {
    state.loadGeneration += 1;
    state.offset = 0;
    state.done = false;
    state.totalShown = 0;
    state.total = 0;
    state.expandedId = null;
    state.loading = false;
    state.showLoadSpinner = false;
    if (listEl) {
      listEl.innerHTML = skeletonHtml(4);
    }
    if (endEl) {
      endEl.hidden = true;
    }
    if (loadingEl) {
      loadingEl.hidden = true;
    }
    if (loadMoreBtn) {
      loadMoreBtn.hidden = true;
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
    if (!replace) {
      state.showLoadSpinner = true;
      if (loadMoreBtn) {
        loadMoreBtn.hidden = true;
        loadMoreBtn.classList.add("is-loading");
      }
      if (loadingEl) {
        loadingEl.hidden = false;
      }
      if (endEl) {
        endEl.hidden = true;
      }
    }
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

    fetch(url, { credentials: "same-origin", headers: authHeaders() })
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
        if (data.total != null) {
          state.total = parseInt(data.total, 10) || 0;
        }
        if (listEl) {
          listEl.querySelectorAll(".rl-lead-card--skeleton, .rl-feed-skeleton").forEach(function (el) {
            el.remove();
          });
        }
        if (replace && listEl) {
          listEl.innerHTML = "";
        }
        if (items.length === 0 && state.offset === 0) {
          if (state.appliedCategories.length && !state.source && !state.appliedTags.length) {
            listEl.innerHTML = categoryEmptyMessage();
            bindEmptyCta();
          } else if (
            state.source ||
            state.appliedCategories.length ||
            state.appliedTags.length
          ) {
            listEl.innerHTML =
              '<p class="rl-feed-empty">В этой нише пока нет заказов — попробуй «Все»</p>';
          } else {
            listEl.innerHTML =
              '<p class="rl-feed-empty">Пока нет заказов. Биржи обновляются каждые 15 минут.</p>';
          }
        } else {
          var frag = items
            .map(function (item) {
              return renderCard(item, !replace);
            })
            .join("");
          listEl.insertAdjacentHTML("beforeend", frag);
          items.forEach(function (item) {
            state.itemsById[item.id] = item;
          });
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
        updateFilterBarUi();
        bindCards();
        observeLeadCards(listEl);
        updatePagination();
      })
      .catch(function () {
        if (gen !== state.loadGeneration) {
          return;
        }
        if (replace && listEl) {
          listEl.innerHTML = "";
        }
        showError("Не удалось загрузить");
      })
      .finally(function () {
        if (gen === state.loadGeneration) {
          state.loading = false;
          state.showLoadSpinner = false;
          updatePagination();
        }
      });
  }

  function updateCardDraft(card, item) {
    var bodyInner = card.querySelector(".rl-feed-card__body-inner");
    if (bodyInner) {
      bodyInner.innerHTML = renderExpandedBody(item);
    }
    var headStart = card.querySelector(".rl-feed-card__head-start");
    if (headStart) {
      headStart.innerHTML = headBadgesHtml(item, isPerfectMatch(item));
    }
    var ctaHtml = replyCtaHtml(item);
    var cta = card.querySelector(".rl-feed-card__cta");
    if (ctaHtml) {
      if (cta) {
        cta.outerHTML = ctaHtml;
      } else {
        var body = card.querySelector(".rl-feed-card__body");
        if (body) {
          body.insertAdjacentHTML("beforebegin", ctaHtml);
        }
      }
    } else if (cta) {
      cta.remove();
    }
    var id = parseInt(card.getAttribute("data-id"), 10) || item.id;
    state.expandedId = id;
    card.classList.add("is-expanded");
    var replyEl = card.querySelector("[data-reply-text]");
    if (replyEl) {
      replyEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }

  var cardDelegationReady = false;

  function toggleCardExpand(card) {
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
  }

  function runDraftFetchForCard(card, replyBtn) {
    if (!hasPaidAccess()) {
      return;
    }
    var id = parseInt(card.getAttribute("data-id"), 10);
    listEl.querySelectorAll(".rl-lead-card.is-expanded").forEach(function (c) {
      c.classList.remove("is-expanded");
    });
    state.expandedId = id;
    card.classList.add("is-expanded");
    var replyEl = card.querySelector("[data-reply-text]");
    if (replyEl && replyEl.textContent.trim()) {
      replyEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
      return;
    }
    var prevLabel = replyBtn.textContent;
    replyBtn.disabled = true;
    replyBtn.textContent = "Генерируем…";
    fetchDraft(id)
      .then(function (data) {
        var base = state.itemsById[id] || { id: id };
        var merged = Object.assign({}, base, {
          reply_draft: data.reply_draft,
          tools_required: data.tools_required || base.tools_required || [],
        });
        state.itemsById[id] = merged;
        updateCardDraft(card, merged);
      })
      .catch(function (err) {
        if (err && err.status === 403) {
          showError(err.detail || "Нет доступа");
          return;
        }
        if (err && err.status === 429) {
          var limMsg = err.detail || err.error || "";
          if (limMsg && limMsg.indexOf("rate limit") !== -1) {
            showError(limMsg);
          } else if (limMsg) {
            showError(limMsg);
          }
          return;
        }
        var msg = (err && err.detail) || DRAFT_FAIL_RU;
        if (msg === "draft generation failed" || msg === "ai unavailable") {
          msg = DRAFT_FAIL_RU;
        }
        showDraftError(msg, function () {
          runDraftFetchForCard(card, replyBtn);
        });
      })
      .finally(function () {
        if (replyBtn && replyBtn.isConnected) {
          replyBtn.disabled = false;
          replyBtn.textContent = prevLabel;
        }
      });
  }

  function onFeedListClick(e) {
    var card = e.target.closest(".rl-lead-card");
    if (!card || !listEl || !listEl.contains(card)) {
      return;
    }
    var skillsLink = e.target.closest("[data-open-skills]");
    if (skillsLink && card.contains(skillsLink)) {
      e.stopPropagation();
      openSkillsUi();
      return;
    }
    var replyBtn = e.target.closest(".rl-feed-card__reply-btn");
    if (replyBtn && card.contains(replyBtn)) {
      e.stopPropagation();
      runDraftFetchForCard(card, replyBtn);
      return;
    }
    var copyBtn = e.target.closest("[data-copy-reply], .rl-feed-card__copy");
    if (copyBtn && card.contains(copyBtn)) {
      e.stopPropagation();
      var replyEl = card.querySelector("[data-reply-text]");
      var text = replyEl ? replyEl.textContent : "";
      if (!text) {
        return;
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () {
          copyBtn.textContent = "Скопировано ✓";
          setTimeout(function () {
            copyBtn.textContent = "Скопировать черновик";
          }, 2000);
        });
      }
      return;
    }
    if (
      e.target.closest(".rl-feed-card__link, a, button, input, textarea, select")
    ) {
      return;
    }
    toggleCardExpand(card);
  }

  function onFeedListKeydown(e) {
    var card = e.target.closest(".rl-lead-card");
    if (!card || !listEl.contains(card)) {
      return;
    }
    if (e.key === "Enter" || e.key === " ") {
      if (e.target.closest("button, a, input, textarea")) {
        return;
      }
      e.preventDefault();
      toggleCardExpand(card);
    }
  }

  function ensureCardDelegation() {
    if (!listEl || cardDelegationReady) {
      return;
    }
    cardDelegationReady = true;
    listEl.addEventListener("click", onFeedListClick);
    listEl.addEventListener("keydown", onFeedListKeydown);
    document.addEventListener("click", function (e) {
      if (e.target.closest(".rl-lead-card")) {
        return;
      }
      if (!listEl) {
        return;
      }
      listEl.querySelectorAll(".rl-lead-card.is-expanded").forEach(function (c) {
        c.classList.remove("is-expanded");
      });
      state.expandedId = null;
    });
  }

  function bindCards() {
    ensureCardDelegation();
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
    root.querySelectorAll(".rl-skills-panel__body, .rl-skill-tree__body").forEach(bindWheelScroll);
    var modalBody = document.getElementById("rl-feed-skill-tree-body");
    if (modalBody) {
      bindWheelScroll(modalBody);
    }
  }

  function closeSkillsDropdown() {
    closeFeedSkillsModal();
  }

  document.addEventListener("mousedown", function (e) {
    var sortDd = document.querySelector(".rl-filter-sort-dd");
    if (!sortDd || !sortDd.open) {
      return;
    }
    if (e.target.closest(".rl-filter-sort-dd")) {
      return;
    }
    sortDd.open = false;
  });

  bindWheelScroll(sidebarScroll || sidebar);
  bindSkillsPanels(sidebar || document);

  if (skillsTriggerBtn) {
    skillsTriggerBtn.addEventListener("click", function (e) {
      e.preventDefault();
      openSkillsUi();
    });
  }
  if (skillsOverlayEl) {
    skillsOverlayEl.addEventListener("click", closeFeedSkillsModal);
  }
  if (skillsCloseBtn) {
    skillsCloseBtn.addEventListener("click", closeFeedSkillsModal);
  }
  if (skillsApplyBtn) {
    skillsApplyBtn.addEventListener("click", applyDraftTags);
  }
  if (skillsClearBtn) {
    skillsClearBtn.addEventListener("click", clearSkills);
  }
  if (skillsMyBtn) {
    skillsMyBtn.addEventListener("click", loadMyProfileSkills);
  }
  if (skillsRareBtn) {
    skillsRareBtn.addEventListener("click", function () {
      state.showRareSkills = !state.showRareSkills;
      renderSkillsCatalog();
    });
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
    toRoot.querySelectorAll(".rl-feed-chip, .rl-cat-chip, .rl-sort-option").forEach(function (label) {
      var input = label.querySelector("input");
      label.classList.toggle("is-active", !!(input && input.checked));
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
        state.showRareSkills = false;
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
      if (name === "sort") {
        updateFilterBarUi();
        if (state.totalShown > 0) {
          updateCount();
        }
      }
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
  var sheetCloseBtn = document.getElementById("rl-feed-sheet-close");
  var sheetOverlayEl = document.getElementById("rl-feed-sheet-overlay");

  function closeSheet() {
    if (!sheet) {
      return;
    }
    sheet.hidden = true;
    if (openBtn) {
      openBtn.setAttribute("aria-expanded", "false");
    }
    document.body.style.overflow = "";
  }

  function onSheetCategoryChange(changedInp) {
    var allInp = sheetBody.querySelector('input[name="category"][value=""]');
    if (changedInp && changedInp.value === "" && changedInp.checked) {
      sheetBody.querySelectorAll('input[name="category"]').forEach(function (other) {
        if (other !== changedInp && other.value) {
          other.checked = false;
        }
      });
    } else if (changedInp && changedInp.value && changedInp.checked && allInp) {
      allInp.checked = false;
    }
    syncCategoryInputs(sheetBody, sidebar);
    syncChipActiveStates(sheetBody);
    state.draftCategories = readCategoriesFrom(sheetBody);
    state.showRareSkills = false;
    pruneDraftTagsForCategories();
    renderSkillsCatalog();
    loadCatalog();
    updateSkillsDraftUi();
    updateFilterBarUi();
  }

  function ensureSheetDelegation() {
    if (!sheetBody || sheetBody.dataset.rlSheetBound === "1") {
      return;
    }
    sheetBody.dataset.rlSheetBound = "1";
    sheetBody.addEventListener("change", function (e) {
      if (!sheet || sheet.hidden) {
        return;
      }
      var inp = e.target;
      if (!inp || inp.name !== "category" || !sheetBody.contains(inp)) {
        return;
      }
      onSheetCategoryChange(inp);
    });
    sheetBody.addEventListener("click", function (e) {
      if (!sheet || sheet.hidden) {
        return;
      }
      var skill = e.target.closest(".rl-feed-skill, .rl-skill-chip");
      if (skill && sheetBody.contains(skill)) {
        toggleDraftTag(skill.getAttribute("data-tag"));
        return;
      }
      var l1Expand = e.target.closest("[data-l1-expand]");
      if (l1Expand && sheetBody.contains(l1Expand)) {
        e.preventDefault();
        e.stopPropagation();
        var parentTag = l1Expand.getAttribute("data-l1-expand");
        if (parentTag) {
          state.expandedL1[parentTag] = !state.expandedL1[parentTag];
          renderSkillsCatalog();
        }
        return;
      }
      var nicheToggle = e.target.closest("[data-niche-toggle]");
      if (nicheToggle && sheetBody.contains(nicheToggle)) {
        var nicheKey = nicheToggle.getAttribute("data-niche-toggle");
        if (nicheKey) {
          state.expandedNiches[nicheKey] = !state.expandedNiches[nicheKey];
          renderSkillsCatalog();
        }
        return;
      }
      var rare = e.target.closest("#rl-sheet-skills-rare, .rl-sheet-text-btn--expand");
      if (rare && sheetBody.contains(rare)) {
        e.preventDefault();
        state.showRareSkills = !state.showRareSkills;
        renderSkillsCatalog();
        return;
      }
      var applyInner = e.target.closest(".rl-feed-skills-apply");
      if (applyInner && sheetBody.contains(applyInner)) {
        applyDraftTags();
        return;
      }
      var clearInner = e.target.closest(".rl-feed-skills-clear");
      if (clearInner && sheetBody.contains(clearInner)) {
        clearSkills();
        return;
      }
      var sheetSkillsOpen = e.target.closest("#rl-sheet-skills-open, .rl-sheet-skills-open");
      if (sheetSkillsOpen && sheetBody.contains(sheetSkillsOpen)) {
        e.preventDefault();
        closeSheet();
        openFeedSkillsModal();
        return;
      }
      var myInner = e.target.closest(".rl-sheet-text-btn--my, .rl-feed-skills-my");
      if (myInner && sheetBody.contains(myInner)) {
        loadMyProfileSkills();
        return;
      }
      var chip = e.target.closest(".rl-feed-chip");
      if (chip && sheetBody.contains(chip)) {
        var input = chip.querySelector("input");
        if (!input || input.name === "category") {
          return;
        }
        sheetBody.querySelectorAll('input[name="' + input.name + '"]').forEach(function (r) {
          r.checked = false;
          if (r.parentElement) {
            r.parentElement.classList.remove("is-active");
          }
        });
        input.checked = true;
        chip.classList.add("is-active");
        return;
      }
      var sortOpt = e.target.closest(".rl-sort-option");
      if (sortOpt && sheetBody.contains(sortOpt)) {
        var sortInp = sortOpt.querySelector('input[name="sort"]');
        if (!sortInp) {
          return;
        }
        sheetBody.querySelectorAll('input[name="sort"]').forEach(function (r) {
          r.checked = false;
          if (r.parentElement) {
            r.parentElement.classList.remove("is-active");
          }
        });
        sortInp.checked = true;
        sortOpt.classList.add("is-active");
        state.sort = sortInp.value;
        updateSkillsDraftUi();
        updateFilterBarUi();
        if (state.totalShown > 0) {
          updateCount();
        }
      }
    });
  }

  function buildSheetContent() {
    sheetBody.innerHTML = "";
    var catField = sidebar.querySelector(".rl-feed-filter--category");
    if (catField) {
      var catBlock = document.createElement("section");
      catBlock.className = "rl-sheet-block rl-sheet-block--cats";
      catBlock.innerHTML = '<p class="rl-sheet-block__label">Специализация</p>';
      catBlock.appendChild(catField.cloneNode(true));
      sheetBody.appendChild(catBlock);
    }
    var skillsBlock = document.createElement("section");
    skillsBlock.className = "rl-sheet-block rl-sheet-block--skills";
    if (usesSkillTree()) {
      var skillsCount = state.appliedTags.length;
      var skillsOpenLabel =
        skillsCount > 0 ? "Навыки · " + skillsCount : "Навыки";
      skillsBlock.innerHTML =
        '<p class="rl-sheet-block__label">Навыки</p>' +
        '<button type="button" class="rl-btn rl-btn--ghost rl-sheet-skills-open" id="rl-sheet-skills-open">' +
        escapeHtml(skillsOpenLabel) +
        " ▾</button>";
    } else {
      skillsBlock.innerHTML =
        '<p class="rl-sheet-block__label">Навыки</p>' +
        '<p class="rl-feed-skills__section"></p>' +
        '<div class="rl-sheet-skills-actions">' +
        '<button type="button" id="rl-sheet-skills-rare" class="rl-sheet-text-btn rl-sheet-text-btn--expand" aria-expanded="false">' +
        '<span class="rl-sheet-text-btn__label">Ещё навыки</span></button>' +
        '<button type="button" class="rl-sheet-text-btn rl-sheet-text-btn--muted rl-sheet-text-btn--my">' +
        '<span class="rl-sheet-text-btn__label">Мои навыки</span></button>' +
        "</div>" +
        '<div class="rl-feed-skills" aria-live="polite"></div>' +
        '<p class="rl-feed-skills__hint" hidden>Выберите навыки и нажмите Применить</p>';
    }
    sheetBody.appendChild(skillsBlock);
    var sortPanel = sidebar.querySelector(".rl-sort-panel");
    if (sortPanel) {
      var sortBlock = document.createElement("section");
      sortBlock.className = "rl-sheet-block rl-sheet-block--sort";
      sortBlock.innerHTML = '<p class="rl-sheet-block__label">Сортировка</p>';
      sortBlock.appendChild(sortPanel.cloneNode(true));
      sheetBody.appendChild(sortBlock);
    }
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
    syncChipActiveStates(sheetBody);
    state.draftCategories = readCategoriesFrom(sheetBody);
    state.showRareSkills = false;
  }

  function openSheet() {
    if (!sheet || !sheetBody || !sidebar) {
      return;
    }
    buildSheetContent();
    ensureSheetDelegation();
    bindSkillsPanels(sheetBody);
    updateFilterBarUi();
    renderSkillsCatalog();
    if (!state.catalog.length && !state.catalogGroups.length) {
      loadCatalog().then(function () {
        renderSkillsCatalog();
      });
    }
    sheet.hidden = false;
    if (openBtn) {
      openBtn.setAttribute("aria-expanded", "true");
    }
    document.body.style.overflow = "hidden";
    updateSkillsBadge();
    updateSkillsDraftUi();
    updateRareSkillsUi();
  }

  if (sheet && sheetBody && sidebar && openBtn) {
    openBtn.addEventListener("click", openSheet);
    if (sheetOverlayEl) {
      sheetOverlayEl.addEventListener("click", function () {
        closeSkillsDropdown();
        closeSheet();
      });
    }
    if (sheetCloseBtn) {
      sheetCloseBtn.addEventListener("click", function () {
        closeSkillsDropdown();
        closeSheet();
      });
    }
    document.addEventListener("keydown", function (e) {
      if (e.key !== "Escape") {
        return;
      }
      if (skillsModalEl && !skillsModalEl.hidden) {
        closeFeedSkillsModal();
        return;
      }
      if (sheet && !sheet.hidden) {
        closeSheet();
      }
    });
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
      updateFilterBarUi();
      closeSheet();
      state.appliedCategories = cloneCategories(state.draftCategories);
      if (!tagsEqual(state.draftTags, state.appliedTags)) {
        persistTags(cloneTags(state.draftTags), { setSortMatch: true, reload: true });
        return;
      }
      resetAndLoad();
    });
    document.getElementById("rl-feed-sheet-reset").addEventListener("click", function () {
      if (resetBtn) {
        resetBtn.click();
      }
      closeSheet();
    });
  }

  if (loadMoreBtn) {
    loadMoreBtn.addEventListener("click", function () {
      if (state.loading || state.done) {
        return;
      }
      loadMore(false);
    });
  }

  ensureCardDelegation();

  loadSubscription().then(function () {
    updateDelayNotice();
    return Promise.all([loadTags(), loadCatalog()]);
  }).then(function () {
    state.draftCategories = readCategoriesFrom();
    state.appliedCategories = cloneCategories(state.draftCategories);
    renderSkillsCatalog();
    syncChips();
    readFilters();
    updateFilterBarUi();
    resetAndLoad();
  });

  var siteHeader = document.querySelector(".rl-header");
  if (siteHeader) {
    window.addEventListener(
      "scroll",
      function () {
        siteHeader.classList.toggle("rl-header--scrolled", window.scrollY > 0);
      },
      { passive: true }
    );
  }

  if (window.rawleadSyncHeader) {
    window.rawleadSyncHeader();
  }
})();
