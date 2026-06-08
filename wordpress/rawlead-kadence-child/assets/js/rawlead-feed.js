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
  root.classList.add("rl-feed-shell--pending");

  var cfg = window.rawleadFeed;
  var TOKEN_KEY = "rawlead_access_token";
  var PREFS_KEY = "rawlead_feed_prefs";
  var TAGS_SYNC_KEY = "rawlead_user_tags_rev";
  var MIN_MATCH_OPTIONS = [50, 60, 70, 80, 90];
  var SLOT_TOOLTIP =
    "На один заказ — до 10 персональных черновиков. Когда места заняты — кнопка отклика серая, заказ остаётся в ленте.";
  var HUMAN_VIEWS_KEY = "rawlead_card_human_views";
  var INFO_ICON_SVG =
    '<svg class="rl-feed-card__slot-info-icon" width="14" height="14" viewBox="0 0 24 24" aria-hidden="true" focusable="false">' +
    '<circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/>' +
    '<path fill="currentColor" d="M11 10h2v8h-2zm0-4h2v2h-2z"/></svg>';
  var AUTH_COOKIE = "rl_access";
  var AUTH_COOKIE_MAX_AGE = 7 * 24 * 3600;
  var MAX_USER_TAGS = 12;
  var cabinetLoginUrl = (cfg.cabinetUrl || "/cabinet/").replace(/\/?$/, "/");
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
    { key: "use_case", label: "ПО ЗАДАЧЕ" },
    { key: "technology", label: "ПО ТЕХНОЛОГИИ" },
  ];
  var NICHE_ICONS = {
    dev: "</>",
    design: "✦",
    marketing: "◎",
    text: "Aa",
  };
  var DIFFICULTY_BADGES = {
    1: {
      badge: "🟢 Один вечер",
      tip: "Скрипт, один файл, понятное ТЗ — вечер работы.",
    },
    2: {
      badge: "🟡 Проект",
      tip: "Типовая архитектура — FastAPI, лендинг, бот. Понятно с первого прочтения.",
    },
    3: {
      badge: "🟠 Система",
      tip: "Несколько компонентов или монолит с нормальным ТЗ. Потребует время на разбор.",
    },
    4: {
      badge: "🔴 Без норм ТЗ",
      tip: "Нет нормального ТЗ, «сделайте красиво» или каша в описании. Риск на тебе.",
    },
  };
  var listEl = document.getElementById("rl-feed-list");
  var toolbarEl = document.getElementById("rl-feed-toolbar");
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
  var skillsTriggerEl = document.getElementById("rl-feed-skills-trigger-label");
  var skillsTriggerBtn = document.getElementById("rl-feed-skills-trigger");
  var skillsModalEl = document.getElementById("rl-feed-skills-modal");
  var skillsOverlayEl = document.getElementById("rl-feed-skills-modal-overlay");
  var skillsCloseBtn = document.getElementById("rl-feed-skill-tree-close");
  var skillTreeCounterEl = document.getElementById("rl-feed-skill-tree-counter");
  var skillTreeLimitEl = document.getElementById("rl-feed-skill-tree-limit");
  var sidebarScroll = document.getElementById("rl-feed-sidebar-scroll");
  var filterHintEl = document.getElementById("rl-filter-hint");
  var sortPanelEl = document.getElementById("rl-feed-sort-panel");
  var sortTriggerLabelEl = document.getElementById("rl-feed-sort-trigger-label");
  var sortDdEl = document.getElementById("rl-feed-sort-dd");
  var filterHintTimer = null;

  var state = {
    offset: 0,
    limit: 20,
    source: "",
    draftCategories: [],
    appliedCategories: [],
    sort: "time",
    min_match: 80,
    draftTags: [],
    appliedTags: [],
    catalog: [],
    catalogGroups: [],
    catalogByTag: {},
    catalogByNiche: { dev: [], design: [], marketing: [], text: [] },
    expandedNiches: { dev: false, design: false, marketing: false, text: false },
    expandedL1: {},
    todayCount: 0,
    tagsLimitFlash: false,
    tagsSyncRev: "",
    tagsLoading: false,
    loading: false,
    showLoadSpinner: false,
    done: false,
    totalShown: 0,
    total: 0,
    expandedId: null,
    loadGeneration: 0,
    itemsById: {},
    focusLeadId: null,
    focusLeadHandled: false,
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

  function feedApiBase() {
    return cfg.restFeed;
  }

  function readLocalFeedPrefs() {
    try {
      var raw = localStorage.getItem(PREFS_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  function writeLocalFeedPrefs(prefs) {
    try {
      localStorage.setItem(PREFS_KEY, JSON.stringify(prefs || {}));
    } catch (e) {
      /* ignore */
    }
  }

  function prefsTimestamp(prefs) {
    if (!prefs || !prefs.updated_at) {
      return 0;
    }
    var t = Date.parse(prefs.updated_at);
    return isNaN(t) ? 0 : t;
  }

  function normalizeFeedPrefs(prefs) {
    var out = {
      sort: "time",
      min_match: 80,
      category: "",
      updated_at: prefs && prefs.updated_at ? prefs.updated_at : null,
    };
    if (!prefs) {
      return out;
    }
    if (prefs.sort === "match" || prefs.sort === "time") {
      out.sort = prefs.sort;
    }
    var mm = parseInt(String(prefs.min_match), 10);
    if (MIN_MATCH_OPTIONS.indexOf(mm) >= 0) {
      out.min_match = mm;
    }
    if (typeof prefs.category === "string") {
      out.category = prefs.category;
    }
    return out;
  }

  function applyFeedPrefsToState(prefs) {
    var p = normalizeFeedPrefs(prefs);
    state.sort = p.sort;
    state.min_match = p.min_match;
    if (p.category) {
      var cats = p.category.split(",").filter(Boolean);
      if (cats.length) {
        state.appliedCategories = cats;
        state.draftCategories = cats.slice();
      }
    }
  }

  function currentFeedPrefsPayload() {
    return {
      sort: state.sort,
      min_match: state.min_match,
      category: state.appliedCategories.join(","),
      updated_at: new Date().toISOString(),
    };
  }

  function persistFeedPrefs() {
    var payload = currentFeedPrefsPayload();
    writeLocalFeedPrefs(payload);
    if (!isLoggedIn() || !cfg.restFeedPrefs) {
      return Promise.resolve(payload);
    }
    return fetch(cfg.restFeedPrefs, {
      method: "PUT",
      credentials: "same-origin",
      headers: Object.assign({ "Content-Type": "application/json" }, authHeaders()),
      body: JSON.stringify({
        sort: payload.sort,
        min_match: payload.min_match,
        category: payload.category,
      }),
    })
      .then(function (res) {
        if (res.status === 401) {
          handleTagsAuthFailure();
          throw new Error("HTTP 401");
        }
        if (!res.ok) {
          throw new Error("HTTP " + res.status);
        }
        return res.json();
      })
      .then(function (data) {
        writeLocalFeedPrefs(data);
        return data;
      });
  }

  function mergeFeedPrefsOnLogin() {
    var local = normalizeFeedPrefs(readLocalFeedPrefs());
    if (!isLoggedIn() || !cfg.restFeedPrefs) {
      applyFeedPrefsToState(local);
      return Promise.resolve();
    }
    return fetch(cfg.restFeedPrefs, {
      credentials: "same-origin",
      headers: authHeaders(),
    })
      .then(function (res) {
        if (!res.ok) {
          throw new Error("HTTP " + res.status);
        }
        return res.json();
      })
      .then(function (server) {
        var remote = normalizeFeedPrefs(server);
        var winner =
          prefsTimestamp(remote) >= prefsTimestamp(local) ? remote : local;
        applyFeedPrefsToState(winner);
        writeLocalFeedPrefs(winner);
        if (prefsTimestamp(winner) > prefsTimestamp(remote)) {
          return persistFeedPrefs();
        }
      })
      .catch(function () {
        applyFeedPrefsToState(local);
      });
  }

  function apiUrl(params) {
    var q = new URLSearchParams(params);
    var base = feedApiBase();
    return base + (base.indexOf("?") >= 0 ? "&" : "?") + q.toString();
  }

  function syncAuthCookie(token) {
    if (!token) {
      document.cookie = AUTH_COOKIE + "=; path=/; max-age=0; secure; samesite=lax";
      return;
    }
    document.cookie =
      AUTH_COOKIE +
      "=" +
      encodeURIComponent(token) +
      "; path=/; max-age=" +
      AUTH_COOKIE_MAX_AGE +
      "; secure; samesite=lax";
  }

  function handleTagsAuthFailure() {
    try {
      localStorage.removeItem(TOKEN_KEY);
    } catch (e) {
      /* ignore */
    }
    syncAuthCookie("");
    applyFeedShellMode();
    state.appliedTags = [];
    state.draftTags = [];
    updateCount();
    updateSkillsBadge();
    showError("Сессия истекла — войдите снова в личном кабинете.");
    return true;
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

  function getFeedTier() {
    if (!isLoggedIn()) {
      return "anon";
    }
    if (hasPaidAccess()) {
      return "premium";
    }
    return "free";
  }

  function hideFilterHint() {
    if (filterHintEl) {
      filterHintEl.hidden = true;
    }
    if (filterHintTimer) {
      clearTimeout(filterHintTimer);
      filterHintTimer = null;
    }
  }

  function showFilterHint() {
    if (!filterHintEl || getFeedTier() !== "anon") {
      return;
    }
    filterHintEl.hidden = false;
    if (filterHintTimer) {
      clearTimeout(filterHintTimer);
    }
    filterHintTimer = window.setTimeout(hideFilterHint, 4000);
  }

  function updateSortTriggerLabel() {
    if (!sortTriggerLabelEl) {
      return;
    }
    sortTriggerLabelEl.textContent = "Сортировка";
    var sortTrigger = document.getElementById("rl-feed-sort-trigger");
    if (sortTrigger) {
      var tier = getFeedTier();
      var active =
        tier === "premium" &&
        (state.sort === "match" || state.min_match !== 80);
      sortTrigger.classList.toggle("rl-filter-btn--active", active);
    }
  }

  function renderSortPanel() {
    if (!sortPanelEl) {
      return;
    }
    var tier = getFeedTier();
    if (tier === "anon") {
      sortPanelEl.innerHTML = "";
      return;
    }
    sortPanelEl.innerHTML = buildSortOptionsHtml("rl-feed-sort", true);
    updateSortPanelPctVisibility();
  }

  function updateSortPanelPctVisibility() {
    if (!sortPanelEl) {
      return;
    }
    var wrap = sortPanelEl.querySelector(".rl-sort-panel__pct-wrap");
    if (!wrap) {
      return;
    }
    var picked = sortPanelEl.querySelector('input[name="rl-feed-sort"]:checked');
    wrap.hidden = !hasPaidAccess() || !picked || picked.value !== "match";
  }

  function enforceFeedSortTier() {
    if (!hasPaidAccess() && state.sort === "match") {
      state.sort = "time";
    }
  }

  function applyFeedTierUi() {
    var tier = getFeedTier();
    if (sidebar) {
      sidebar.setAttribute("data-tier", tier);
    }
    root.setAttribute("data-feed-tier", tier);
    var locked = tier === "anon";
    var sortTrigger = document.getElementById("rl-feed-sort-trigger");
    [skillsTriggerBtn, sortTrigger].forEach(function (btn) {
      if (!btn) {
        return;
      }
      btn.classList.toggle("rl-filter-btn--locked", locked);
      if (locked) {
        btn.setAttribute(
          "data-filter-locked",
          btn.id === "rl-feed-skills-trigger" ? "skills" : "sort"
        );
      } else {
        btn.removeAttribute("data-filter-locked");
      }
    });
    if (skillsTriggerBtn) {
      skillsTriggerBtn.classList.toggle(
        "rl-filter-btn--active",
        !locked && state.appliedTags.length > 0
      );
    }
    if (sortDdEl && locked) {
      sortDdEl.open = false;
    }
    enforceFeedSortTier();
    renderSortPanel();
    updateSortTriggerLabel();
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
  var DRAFT_POLL_MAX_MS = 120000;
  var DRAFT_FAIL_RU = "ИИ временно недоступен — повторите";
  var DRAFT_POLL_TIMEOUT_RU = "ИИ не успел — повторите";

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
      var timeoutErr = new Error(DRAFT_POLL_TIMEOUT_RU);
      timeoutErr.status = 503;
      timeoutErr.detail = DRAFT_POLL_TIMEOUT_RU;
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

  function updateFeedStrip() {
    var strip = document.getElementById("rl-feed-strip");
    if (!strip) {
      return;
    }
    if (isLoggedIn()) {
      strip.hidden = true;
      return;
    }
    strip.hidden = false;
    strip.classList.remove("rl-feed-strip--free");
  }

  function applyFeedShellMode() {
    try {
      localStorage.removeItem("rawlead_lenta_skills");
    } catch (e) {
      /* ignore */
    }
    var loggedIn = isLoggedIn();
    root.classList.remove("rl-feed-shell--pending");
    root.classList.toggle("rl-app--feed-logged-in", loggedIn);
    root.classList.toggle("rl-app--feed-anon", !loggedIn);
    updateFeedStrip();
    applyFeedTierUi();
    syncFeedCabinetLink();
    if (loggedIn) {
      state.appliedCategories = [];
      state.draftCategories = [];
      if (sidebar) {
        sidebar.querySelectorAll('input[name="category"]').forEach(function (inp) {
          inp.checked = inp.value === "";
        });
      }
    }
  }

  function readTagsSyncRev() {
    try {
      return localStorage.getItem(TAGS_SYNC_KEY) || "";
    } catch (e) {
      return "";
    }
  }

  function bumpTagsSyncRev() {
    var rev = String(Date.now());
    try {
      localStorage.setItem(TAGS_SYNC_KEY, rev);
    } catch (e) {
      return;
    }
    state.tagsSyncRev = rev;
  }

  function applyPersistedTags(tags, options) {
    options = options || {};
    state.appliedTags = cloneTags(tags);
    state.draftTags = cloneTags(state.appliedTags);
    if (!state.appliedTags.length && state.sort === "match") {
      state.sort = "time";
    }
    enforceFeedSortTier();
    if (options.setSortMatch) {
      setSortMatch();
    }
    renderSkillsCatalog();
    readFilters();
    updateFilterBarUi();
    updateCount();
    updateSkillsBadge();
    bumpTagsSyncRev();
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

  function renderExpandedMeta(item) {
    var html = "";
    if (isLoggedIn() && !hasUserSkills()) {
      html += renderMatchBreakdown(item);
    }
    var diff = renderDifficultyRow(item);
    if (diff) {
      html += diff;
    }
    if (hasPaidAccess() && !prepForDisplay(item.reply_draft || "", false).trim()) {
      html +=
        '<p class="rl-feed-card__cta-note rl-feed-card__cta-note--expanded">ИИ напишет формулировку под тебя — не как у остальных</p>';
    }
    return html;
  }

  function renderTzAttachmentWarn(item) {
    var tz = item && item.tz_attachment;
    if (!tz || !tz.status || tz.status.indexOf("skipped_") !== 0) {
      return "";
    }
    var label = "ТЗ не прочитано";
    if (tz.status === "skipped_size") {
      label += " · " + (tz.size_mb != null ? tz.size_mb : "?") + " MB";
    } else if (tz.status === "skipped_auth") {
      label += " · нужен вход на биржу";
    } else if (tz.status === "skipped_empty") {
      label += " · файл без текста";
    }
    return (
      '<p class="rl-feed-card__tz-warn" role="status">' +
      escapeHtml(label) +
      "</p>"
    );
  }

  function renderExpandedBody(item) {
    var task = taskBodyText(item);
    var html = renderExpandedMeta(item);
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
    html += renderTzAttachmentWarn(item);
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
    } else if (reply && isLoggedIn()) {
      html +=
        '<div class="rl-feed-card__section">' +
        '<h4 class="rl-feed-card__section-title">Инструменты</h4>' +
        '<p class="rl-feed-card__text rl-feed-card__muted">ИИ не выделил отдельный список инструментов для этого заказа.</p>' +
        "</div>";
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

  var SLOT_MAX = 10;

  function readHumanViewBumps() {
    try {
      var raw = sessionStorage.getItem(HUMAN_VIEWS_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch (e) {
      return {};
    }
  }

  function writeHumanViewBumps(map) {
    try {
      sessionStorage.setItem(HUMAN_VIEWS_KEY, JSON.stringify(map));
    } catch (e) {
      /* ignore */
    }
  }

  function bumpHumanView(leadId) {
    var id = parseInt(leadId, 10);
    if (!id) {
      return 0;
    }
    var map = readHumanViewBumps();
    if (map[id]) {
      return map[id];
    }
    map[id] = 1;
    writeHumanViewBumps(map);
    return 1;
  }

  function humanViewBump(leadId) {
    return readHumanViewBumps()[parseInt(leadId, 10)] || 0;
  }

  function effectiveDisplayViews(item) {
    var base = parseInt(item.display_views, 10) || 0;
    return base + humanViewBump(item.id);
  }

  function syntheticDisplayReplies(leadId, views) {
    var id = parseInt(leadId, 10) || 0;
    var v = parseInt(views, 10) || 0;
    if (v < 8 || v > 15) {
      return 0;
    }
    var threshold = id % 2 === 0 ? 8 : 10;
    if (v < threshold) {
      return 0;
    }
    return 1;
  }

  function effectiveDisplayReplies(item) {
    if (!item) {
      return 0;
    }
    var fakeViews = parseInt(item.display_views, 10) || 0;
    return syntheticDisplayReplies(item.id, fakeViews);
  }

  function replySlotsRemaining(item) {
    if (!item) {
      return SLOT_MAX;
    }
    var taken = effectiveDisplayReplies(item);
    if (isLoggedIn()) {
      var reply = prepForDisplay(item.reply_draft || "", false).trim();
      if (reply) {
        taken += 1;
      }
    }
    return Math.max(0, SLOT_MAX - taken);
  }

  function renderSlotLine(item) {
    if (getFeedTier() !== "premium") {
      return "";
    }
    var n = replySlotsRemaining(item);
    if (n <= 0) {
      return (
        '<div class="rl-row rl-row--paid-only rl-slot-row rl-slot-row--full" title="' +
        escapeHtml(SLOT_TOOLTIP) +
        '">' +
        escapeHtml("Все места заняты") +
        ' <span class="rl-feed-card__slot-info" title="' +
        escapeHtml(SLOT_TOOLTIP) +
        '">' +
        INFO_ICON_SVG +
        "</span></div>"
      );
    }
    var lastClass = n === 1 ? " rl-slot-row--last" : "";
    var text =
      n === 1
        ? "Последний черновик на этот заказ"
        : "Осталось " + n + " из " + SLOT_MAX;
    return (
      '<div class="rl-row rl-row--paid-only rl-slot-row' +
      lastClass +
      '" title="' +
      escapeHtml(SLOT_TOOLTIP) +
      '">' +
      escapeHtml(text) +
      ' <span class="rl-feed-card__slot-info" title="' +
      escapeHtml(SLOT_TOOLTIP) +
      '">' +
      INFO_ICON_SVG +
      "</span></div>"
    );
  }

  function renderTagChips(item, maxVisible) {
    var tags =
      (item && item.lead_tag_labels && item.lead_tag_labels.length
        ? item.lead_tag_labels
        : item && item.lead_tags) || [];
    var showAll = maxVisible == null;
    var max = showAll ? tags.length : maxVisible;
    var html = [];
    var i;
    for (i = 0; i < tags.length && i < max; i++) {
      html.push(
        '<span class="rl-chip ' +
        tagChipClass(tags[i], item) +
        '">' +
        escapeHtml(prepForDisplay(tags[i], true)) +
        "</span>"
      );
    }
    if (!showAll && tags.length > max) {
      html.push(
        '<span class="rl-chip rl-chip--more" title="Раскрой карточку — увидишь все навыки">+' +
          (tags.length - max) +
          "</span>"
      );
    }
    return html.join("");
  }

  function syncCardChips(card, item, expanded) {
    if (!card || !item) {
      return;
    }
    var chips = card.querySelector(".rl-feed-card__face--front > .rl-chips");
    if (!chips) {
      return;
    }
    chips.innerHTML = renderTagChips(item, expanded ? null : 2);
    chips.classList.toggle("rl-chips--expanded-visible", !!expanded);
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
    return !!(state.appliedTags && state.appliedTags.length);
  }

  function cardHasSkillMatch(item) {
    return !!(item && item.keyword_match != null && item.keyword_match > 0);
  }

  function showSkillMatchUi(item) {
    return hasUserSkills() || (isLoggedIn() && cardHasSkillMatch(item));
  }

  function isIdealMatch(item) {
    var km = item.keyword_match != null ? item.keyword_match : 0;
    return km >= 90 && hasUserSkills() && leadTagKeys(item).length >= 2;
  }

  function isPerfectMatch(item) {
    return isIdealMatch(item);
  }

  function tagChipClass(tag, item) {
    var userTags = (state.appliedTags || []).map(function (t) {
      return String(t).trim().toLowerCase().replace(/^#/, "");
    });
    var key = String(tag).trim().toLowerCase().replace(/^#/, "");
    if (userTags.indexOf(key) >= 0) {
      var km = item.keyword_match != null ? item.keyword_match : 0;
      return km >= 80 ? "rl-chip--match-high" : "rl-chip--match-mid";
    }
    return "rl-chip--missing";
  }

  function renderPerfectBadge(perfect) {
    if (perfect) {
      return '<span class="rl-badge rl-badge--perfect">ИДЕАЛЬНО ✦</span>';
    }
    return "";
  }

  function qualityScore(item) {
    var s = item.ai_score;
    if (s == null || s === "") {
      return null;
    }
    var n = Math.round(Number(s));
    return isNaN(n) ? null : n;
  }

  function matchPctForQuality(item) {
    var fr = item.final_rank;
    if (fr != null && fr !== "") {
      return Math.round(Number(fr)) || 0;
    }
    var q = qualityScore(item);
    return q != null ? q : 0;
  }

  function inferCategoryFromItem(item) {
    var c = String((item && item.category) || "").trim();
    if (NICHE_ICONS[c]) {
      return c;
    }
    var tags = leadTagKeys(item);
    var i;
    var niche;
    var j;
    var tag;
    for (i = 0; i < NICHE_ORDER.length; i++) {
      niche = NICHE_ORDER[i];
      var tier = TIER_A_BY_NICHE[niche] || [];
      for (j = 0; j < tags.length; j++) {
        tag = tags[j];
        if (tier.indexOf(tag) !== -1) {
          return niche;
        }
      }
    }
    return "";
  }

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

  function nicheIconHtmlForItem(item) {
    return nicheIconHtml(inferCategoryFromItem(item));
  }

  function renderDifficultyRow(item) {
    if (!hasPaidAccess()) {
      return "";
    }
    var d = item.difficulty;
    if (d == null || d === "") {
      return "";
    }
    var n = parseInt(String(d), 10);
    var meta = DIFFICULTY_BADGES[n];
    if (!meta) {
      return "";
    }
    return (
      '<div class="rl-difficulty-row">' +
      '<span class="rl-difficulty-row__label">Сложность:</span> ' +
      '<span class="rl-difficulty-badge" title="' +
      escapeHtml(meta.tip) +
      '">' +
      escapeHtml(meta.badge) +
      "</span></div>"
    );
  }

  function renderMatchBreakdown(item) {
    if (!isLoggedIn()) {
      return "";
    }
    if (!hasUserSkills()) {
      return (
        '<div class="rl-match-breakdown">' +
        '<button type="button" class="rl-match-breakdown__cta" data-open-skills>' +
        escapeHtml("Добавь навыки — увидишь совместимость →") +
        "</button></div>"
      );
    }
    return "";
  }

  function renderCompatMatchBar(item) {
    var km = item.keyword_match != null ? item.keyword_match : 0;
    var compatTitle =
      ' title="Насколько ваш стек совпадает с заказом — не оценка качества заказа"';
    return (
      '<div class="rl-match">' +
      '<div class="rl-match__label"><span' +
      compatTitle +
      ">" +
      km +
      "% Совместимость</span></div>" +
      '<div class="rl-match__bar" role="progressbar" aria-valuenow="' +
      km +
      '" aria-valuemin="0" aria-valuemax="100">' +
      '<span class="rl-match__fill" style="--match-value:' +
      km +
      "%;width:" +
      km +
      '%"></span>' +
      "</div>" +
      renderMatchBreakdown(item) +
      "</div>"
    );
  }

  function renderFreeLockedMatchBar() {
    return (
      '<div class="rl-match rl-match--free-locked">' +
      '<div class="rl-match__label"><span title="Точный % совместимости — в Premium">Совместимость</span></div>' +
      '<div class="rl-match__bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" aria-label="Совместимость — Premium">' +
      '<span class="rl-match__fill"></span>' +
      MATCH_LOCK_HTML +
      "</div>" +
      "</div>"
    );
  }

  function renderMatchBlock(item) {
    if (getFeedTier() === "anon") {
      return "";
    }
    if (getFeedTier() === "free") {
      return '<div class="rl-row rl-row--auth-only">' + renderFreeLockedMatchBar() + "</div>";
    }
    if (!hasUserSkills() && !cardHasSkillMatch(item)) {
      return "";
    }
    if (!showSkillMatchUi(item)) {
      return "";
    }
    var inner = renderCompatMatchBar(item);
    return '<div class="rl-row rl-row--auth-only">' + inner + "</div>";
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

  function isSkillsModalOpen() {
    return !!(skillsModalEl && !skillsModalEl.hidden);
  }

  function closeFeedSkillsModal() {
    if (!skillsModalEl) {
      return;
    }
    skillsModalEl.hidden = true;
    skillsModalEl.removeAttribute("data-stack-sheet");
    document.body.classList.remove("rl-skill-tree-open");
    if (sheet && !sheet.hidden) {
      document.body.classList.add("rl-feed-sheet-open");
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
  }

  function openFeedSkillsModal(options) {
    options = options || {};
    if (!skillsModalEl) {
      openSheet();
      return;
    }
    syncExpandedL1FromDraft();
    skillsModalEl.hidden = false;
    if (options.fromSheet || (sheet && !sheet.hidden)) {
      skillsModalEl.setAttribute("data-stack-sheet", "1");
    } else {
      skillsModalEl.removeAttribute("data-stack-sheet");
    }
    document.body.classList.add("rl-skill-tree-open");
    document.body.style.overflow = "hidden";
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

  var MATCH_LOCK_HTML =
    '<span class="rl-match__lock" aria-hidden="true">' +
    '<svg class="rl-match__lock-icon" width="10" height="10" viewBox="0 0 24 24" focusable="false">' +
    '<path fill="currentColor" d="M18 8h-1V6a5 5 0 00-10 0v2H6a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V10a2 2 0 00-2-2zm-7 8a2 2 0 112 0 2 2 0 01-2 0zm3.1-8H9.9V6a3.1 3.1 0 016.2 0v2z"/>' +
    "</svg></span>";

  function cardUpsellHtml() {
    var pricing = cfg.pricingUrl || "/pricing/";
    var cabinet = cfg.cabinetUrl || "/cabinet/";
    return (
      '<div class="rl-card-upsell" data-card-upsell>' +
      '<span class="rl-card-upsell__lead" aria-hidden="true">✍️</span> ' +
      "Черновик ИИ — только Premium<br>" +
      "→ <a href=\"" +
      escapeHtml(pricing) +
      '" onclick="event.stopPropagation()">Подключить Premium 790 ₽</a> ' +
      "или <a href=\"" +
      escapeHtml(cabinet) +
      '" onclick="event.stopPropagation()">Попробовать 3 дня</a>' +
      "</div>"
    );
  }

  function cardCtaHtml(item) {
    var tier = getFeedTier();
    var reply = "";
    if (isLoggedIn()) {
      reply = prepForDisplay(item.reply_draft || "", false).trim();
    }
    if (reply) {
      return (
        '<div class="rl-card-cta-zone">' +
        '<span class="rl-badge rl-badge--replied rl-card-cta--replied-slot">Отклик ✓</span>' +
        "</div>"
      );
    }
    if (tier === "anon") {
      return (
        '<a href="' +
        escapeHtml(cabinetLoginUrl) +
        '" class="rl-card-cta rl-card-cta--anon" onclick="event.stopPropagation()">Войди и проверь совместимость →</a>'
      );
    }
    if (tier === "free") {
      return (
        '<div class="rl-card-cta-zone">' +
        '<button type="button" class="rl-card-cta rl-card-cta--primary rl-feed-card__reply-btn" data-free-reply-lock>Написать отклик →</button>' +
        "</div>"
      );
    }
    if (replySlotsRemaining(item) <= 0) {
      return (
        '<div class="rl-card-cta-zone">' +
        '<button type="button" class="rl-card-cta rl-card-cta--primary rl-card-cta--exhausted rl-feed-card__reply-btn" disabled>Написать отклик →</button>' +
        "</div>"
      );
    }
    return (
      '<div class="rl-card-cta-zone">' +
      '<button type="button" class="rl-card-cta rl-card-cta--primary rl-feed-card__reply-btn">Написать отклик →</button>' +
      "</div>"
    );
  }

  function viewsHeadHtml(item) {
    var v = effectiveDisplayViews(item);
    var replies = effectiveDisplayReplies(item);
    if ((v == null || v <= 0) && (!replies || replies <= 0)) {
      return "";
    }
    var html = "";
    if (replies > 0) {
      html +=
        '<span class="rl-feed-card__replies" aria-label="' +
        replies +
        ' откликов">' +
        escapeHtml(String(replies)) +
        " откл.</span>";
    }
    if (v != null && v > 0) {
      var n = escapeHtml(String(v));
      html +=
        '<span class="rl-feed-card__views" aria-label="' +
        n +
        ' просмотров">' +
        VIEWS_EYE_SVG +
        '<span class="rl-feed-card__views-count">' +
        n +
        "</span></span>";
    }
    return html;
  }

  function repliedBadgeHtml() {
    return '<span class="rl-badge rl-badge--replied">Отклик ✓</span>';
  }

  function replyCtaHtml(item) {
    return cardCtaHtml(item);
  }

  function headBadgesHtml(item, perfect) {
    var src = sourceLabel(item.source);
    return (
      '<div class="rl-feed-card__badge-stack">' +
      nicheIconHtmlForItem(item) +
      '<span class="rl-feed-card__source rl-feed-card__source--' +
      src.cls +
      '">' +
      escapeHtml(src.label) +
      "</span>" +
      renderPerfectBadge(perfect) +
      hotBadgeHtml(item) +
      "</div>"
    );
  }

  function renderCard(item, isNew) {
    var perfect = isIdealMatch(item);
    var budget = formatBudgetDisplay(item.budget_text || "—");
    var titleText = prepForDisplay(item.title || "Без названия", true);
    var titleHtml = escapeHtml(titleText);
    var expanded = state.expandedId === item.id;
    var tier = getFeedTier();

    return (
      '<article class="rl-lead-card' +
      (isNew ? " is-new" : "") +
      (expanded ? " is-expanded" : "") +
      (perfect ? " rl-lead-card--ideal rl-lead-card--perfect-match" : "") +
      '" data-id="' +
      item.id +
      '" data-tier="' +
      tier +
      '" tabindex="0" role="button" aria-label="Карточка заказа">' +
      '<div class="rl-feed-card__flip">' +
      '<div class="rl-feed-card__flip-inner">' +
      '<div class="rl-feed-card__face rl-feed-card__face--front">' +
      '<div class="rl-feed-card__head">' +
      '<div class="rl-feed-card__head-start">' +
      headBadgesHtml(item, perfect) +
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
      renderSlotLine(item) +
      '<div class="rl-chips' +
      (expanded ? " rl-chips--expanded-visible" : "") +
      '">' +
      renderTagChips(item, expanded ? null : 2) +
      "</div>" +
      replyCtaHtml(item) +
      '<div class="rl-feed-card__body">' +
      '<div class="rl-feed-card__body-inner">' +
      renderExpandedBody(item) +
      "</div></div>" +
      "</div>" +
      '<div class="rl-feed-card__face rl-feed-card__face--back">' +
      '<div class="rl-feed-card__body-inner">' +
      renderExpandedBody(item) +
      "</div></div>" +
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
      ' · <button type="button" class="rl-feed-banner__retry">Попробовать снова</button>';
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
      html += ' · <button type="button" class="rl-feed-banner__retry">Повторить</button>';
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

  function renderFeedToolbar() {
    if (!toolbarEl) {
      updatePagination();
      return;
    }
    var html = "";
    if (state.totalShown > 0) {
      html +=
        '<p class="rl-feed-toolbar__meta">' +
        escapeHtml(state.totalShown + " заказов") +
        (state.todayCount != null
          ? " · " + state.todayCount + " новых сегодня"
          : "") +
        "</p>";
    }
    toolbarEl.innerHTML = html;
    updatePagination();
  }

  function setFeedSort(next) {
    if (next !== "time" && next !== "match") {
      return;
    }
    if (next === "match" && !hasPaidAccess()) {
      return;
    }
    if (state.sort === next) {
      return;
    }
    state.sort = next;
    persistFeedPrefs().finally(function () {
      updateFilterBarUi();
      renderFeedToolbar();
      renderSortPanel();
      resetAndLoad();
    });
  }

  function setFeedMinMatch(pct) {
    var n = parseInt(String(pct), 10);
    if (MIN_MATCH_OPTIONS.indexOf(n) < 0 || state.min_match === n) {
      return;
    }
    state.min_match = n;
    if (state.sort !== "match") {
      state.sort = "match";
    }
    persistFeedPrefs().finally(function () {
      updateFilterBarUi();
      renderFeedToolbar();
      renderSortPanel();
      resetAndLoad();
    });
  }

  function applySortPanelDraft() {
    if (!sortPanelEl) {
      return;
    }
    var picked = sortPanelEl.querySelector('input[name="rl-feed-sort"]:checked');
    var nextSort = picked ? picked.value : state.sort;
    if (nextSort === "match" && !hasPaidAccess()) {
      nextSort = "time";
    }
    state.sort = nextSort === "match" ? "match" : "time";
    var activePct = sortPanelEl.querySelector(".rl-sort-panel__pct-btn.is-active");
    if (activePct) {
      var pctVal = parseInt(activePct.getAttribute("data-feed-min-match"), 10);
      if (MIN_MATCH_OPTIONS.indexOf(pctVal) >= 0) {
        state.min_match = pctVal;
      }
    }
    if (sortDdEl) {
      sortDdEl.open = false;
    }
    persistFeedPrefs().finally(function () {
      updateFilterBarUi();
      renderFeedToolbar();
      renderSortPanel();
      resetAndLoad();
    });
  }

  function updateCount() {
    renderFeedToolbar();
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
    return body && body.querySelector(".rl-sheet-block") ? body : null;
  }

  function buildSortOptionsHtml(radioName, includeApply) {
    var html =
      '<label class="rl-sort-option' +
      (state.sort === "time" ? " is-active" : "") +
      '"><input type="radio" name="' +
      radioName +
      '" value="time"' +
      (state.sort === "time" ? " checked" : "") +
      "> По дате</label>";
    if (hasPaidAccess()) {
      html +=
        '<label class="rl-sort-option' +
        (state.sort === "match" ? " is-active" : "") +
        '"><input type="radio" name="' +
        radioName +
        '" value="match"' +
        (state.sort === "match" ? " checked" : "") +
        "> По совместимости</label>";
      html +=
        '<div class="rl-sort-panel__pct-wrap' +
        (state.sort === "match" ? "" : " hidden") +
        '"><p class="rl-sort-panel__divider">МИН. СОВМЕСТИМОСТЬ:</p><div class="rl-sort-panel__pct">';
      var mi;
      for (mi = 0; mi < MIN_MATCH_OPTIONS.length; mi++) {
        var pct = MIN_MATCH_OPTIONS[mi];
        html +=
          '<button type="button" class="rl-sort-panel__pct-btn' +
          (state.min_match === pct ? " is-active" : "") +
          '" data-feed-min-match="' +
          pct +
          '">' +
          pct +
          "%</button>";
      }
      html += "</div></div>";
    }
    if (includeApply) {
      html +=
        '<button type="button" class="rl-btn rl-btn--primary rl-sort-panel__apply" id="rl-feed-sort-apply">Применить \u2192</button>';
    }
    return html;
  }

  function renderSheetSortPanel() {
    var el = document.getElementById("rl-feed-sheet-sort");
    if (!el) {
      return;
    }
    if (!isLoggedIn()) {
      el.innerHTML = "";
      return;
    }
    el.innerHTML = buildSortOptionsHtml("rl-sheet-sort", false);
    updateSheetSortPctVisibility();
  }

  function updateSheetSortPctVisibility() {
    if (!sheetBody) {
      return;
    }
    var wrap = sheetBody.querySelector(".rl-sheet-block--sort .rl-sort-panel__pct-wrap");
    if (!wrap) {
      return;
    }
    var picked = sheetBody.querySelector('input[name="rl-sheet-sort"]:checked');
    wrap.hidden = !hasPaidAccess() || !picked || picked.value !== "match";
  }

  function applySheetSortDraft() {
    if (!sheetBody || !isLoggedIn()) {
      return;
    }
    var picked = sheetBody.querySelector('input[name="rl-sheet-sort"]:checked');
    var nextSort = picked ? picked.value : state.sort;
    if (nextSort === "match" && !hasPaidAccess()) {
      nextSort = "time";
    }
    state.sort = nextSort === "match" ? "match" : "time";
    var activePct = sheetBody.querySelector(
      ".rl-sheet-block--sort .rl-sort-panel__pct-btn.is-active"
    );
    if (activePct && state.sort === "match") {
      var pctVal = parseInt(activePct.getAttribute("data-feed-min-match"), 10);
      if (MIN_MATCH_OPTIONS.indexOf(pctVal) >= 0) {
        state.min_match = pctVal;
      }
    }
    enforceFeedSortTier();
    renderSortPanel();
    updateSortTriggerLabel();
  }

  function syncMobileFilterChrome() {
    var btn = document.getElementById("rl-feed-filters-open");
    if (!btn) {
      return;
    }
    var mobile =
      window.matchMedia && window.matchMedia("(max-width: 767px)").matches;
    var filterCount =
      state.appliedTags.length + (state.appliedCategories.length ? 1 : 0);
    var labelEl = btn.querySelector(".rl-filter-mobile-trigger__label");
    var labelText = filterCount > 0 ? "Фильтр · " + filterCount : "Фильтр";
    if (labelEl) {
      labelEl.textContent = labelText;
    } else {
      btn.textContent = labelText;
    }
    btn.classList.toggle(
      "has-selection",
      filterCount > 0 || state.source !== "" || state.sort !== "time"
    );
    btn.hidden = !mobile;
  }

  function updateFilterBarUi() {
    if (skillsTriggerEl) {
      var skillsLabel =
        state.appliedTags.length > 0
          ? "Навыки"
          : "Навыки";
      skillsTriggerEl.textContent = skillsLabel;
    }
    if (skillsTriggerBtn) {
      skillsTriggerBtn.classList.toggle(
        "rl-filter-btn--active",
        getFeedTier() !== "anon" && state.appliedTags.length > 0
      );
    }
    updateSkillsBadge();
    updateSortTriggerLabel();
    var sheetRoot = populatedSheetBody();
    if (sheetRoot) {
      applySkillsSectionText(
        sheetRoot.querySelector(".rl-feed-skills__section"),
        state.draftCategories
      );
    }
    syncMobileFilterChrome();
    renderSheetSortPanel();
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
    state.source = src ? src.value : "";
    var dirty =
      state.source !== "" ||
      state.appliedCategories.length > 0 ||
      state.appliedTags.length > 0 ||
      state.sort !== "time" ||
      state.min_match !== 80 ||
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
      skillTreeLimitEl.hidden = !state.tagsLimitFlash;
    }
    if (skillsHintEl && !state.tagsLimitFlash) {
      skillsHintEl.hidden = n < 7 || n >= MAX_USER_TAGS;
    }
  }

  function updateSkillsDraftUi() {
    var dirty =
      !tagsEqual(state.draftTags, state.appliedTags) ||
      !categoriesEqual(state.draftCategories, state.appliedCategories);
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
        el.textContent = "Максимум 12 — сними лишние.";
        return;
      }
      if (state.draftTags.length >= 7 && state.draftTags.length < MAX_USER_TAGS) {
        el.hidden = false;
        el.textContent = "Слишком широко — match упадёт. Оставь 6–8 ключевых.";
        return;
      }
      el.hidden = true;
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
    var cats = state.draftCategories;
    if (cats.length && row.category && cats.indexOf(row.category) < 0) {
      return false;
    }
    return true;
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

  function renderFeedL1ChipOnly(row, atLimit, niche) {
    return (
      '<div class="rl-l1-chip-wrap">' +
      feedSkillChipHtml(row, atLimit, { niche: niche, level: "L1" }) +
      "</div>"
    );
  }

  function renderFeedL3TrayHtml(l1skills, atLimit, niche) {
    var activeParents = [];
    var seen = {};
    var merged = [];
    var i;
    for (i = 0; i < l1skills.length; i++) {
      var row = l1skills[i];
      if (!row || !(row.children || []).length) {
        continue;
      }
      if (state.draftTags.indexOf(row.tag) >= 0) {
        activeParents.push(row);
      }
    }
    if (!activeParents.length) {
      return '<div class="rl-l3-tray" data-subhead-tray aria-hidden="true"></div>';
    }
    for (i = 0; i < activeParents.length; i++) {
      var parent = activeParents[i];
      var ch;
      for (ch = 0; ch < parent.children.length; ch++) {
        var child = parent.children[ch];
        if (!child || !child.tag || seen[child.tag]) {
          continue;
        }
        seen[child.tag] = true;
        merged.push(child);
      }
    }
    if (!merged.length) {
      return '<div class="rl-l3-tray" data-subhead-tray aria-hidden="true"></div>';
    }
    var html = '<div class="rl-l3-tray is-visible" data-subhead-tray>';
    html += '<p class="rl-l3-tray__label">Уточнение (необязательно)</p>';
    html += '<div class="rl-l3-tray__group" data-l3-deduped>';
    for (i = 0; i < merged.length; i++) {
      html += feedSkillChipHtml(
        {
          tag: merged[i].tag,
          title_ru: merged[i].title_ru,
          picker_level: "L3",
        },
        atLimit,
        { niche: niche, level: "L3" }
      );
    }
    html += "</div></div>";
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
      bodyHtml += '<div class="rl-niche-subhead-block">';
      bodyHtml +=
        '<p class="rl-niche-subhead">' + escapeHtml(String(sh.label).toUpperCase()) + "</p>";
      bodyHtml += '<div class="rl-niche-root__chips">';
      for (var lj = 0; lj < l1skills.length; lj++) {
        bodyHtml += renderFeedL1ChipOnly(l1skills[lj], atLimit, niche);
      }
      bodyHtml += "</div>";
      bodyHtml += renderFeedL3TrayHtml(l1skills, atLimit, niche);
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
      state.tagsLimitFlash = false;
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
    state.tagsLimitFlash = false;
    renderSkillsCatalog();
    updateSkillsDraftUi();
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
      container.innerHTML =
        treeHtml ||
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
  }

  function setSortMatch() {
    if (!state.appliedTags.length) {
      return;
    }
    state.sort = "match";
    updateFilterBarUi();
  }

  var tagsPersistQueue = Promise.resolve();

  function persistTagsRequest(tags, options) {
    options = options || {};
    state.tagsLoading = true;
    updateSkillsDraftUi();
    syncAuthCookie(getToken());
    return fetch(cfg.restTags, {
      method: "PUT",
      credentials: "same-origin",
      headers: Object.assign({ "Content-Type": "application/json" }, authHeaders()),
      body: JSON.stringify({ tags: tags || [] }),
    })
      .then(function (res) {
        if (res.status === 401) {
          handleTagsAuthFailure();
          throw new Error("HTTP 401");
        }
        if (!res.ok) {
          throw new Error("HTTP " + res.status);
        }
        return res.json();
      })
      .then(function () {
        return loadTags().then(function () {
          if (options.setSortMatch && state.appliedTags.length) {
            setSortMatch();
          }
          renderSkillsCatalog();
          readFilters();
          updateFilterBarUi();
          updateCount();
          updateSkillsBadge();
          bumpTagsSyncRev();
          if (options.reload !== false) {
            resetAndLoad();
          }
        });
      })
      .catch(function (err) {
        if (String(err && err.message).indexOf("401") >= 0) {
          throw err;
        }
        showError("Ошибка — попробуй снова");
        throw err;
      })
      .finally(function () {
        state.tagsLoading = false;
        updateSkillsDraftUi();
      });
  }

  function persistTags(tags, options) {
    options = options || {};
    if (!isLoggedIn()) {
      return Promise.resolve();
    }
    if (!cfg.restTags) {
      applyPersistedTags(tags, options);
      return Promise.resolve();
    }
    var job = function () {
      return persistTagsRequest(tags, options);
    };
    var chained = tagsPersistQueue.then(job, job);
    tagsPersistQueue = chained.catch(function () {});
    return chained;
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
    if (tagsDirty) {
      persistTags(cloneTags(state.draftTags), { setSortMatch: true, reload: true })
        .then(function () {
          closeFeedSkillsModal();
        })
        .catch(function () {
          /* ошибка уже в persistTags; модал остаётся открытым */
        });
      return;
    }
    closeFeedSkillsModal();
    readFilters();
    resetAndLoad();
  }

  function loadTags() {
    if (!isLoggedIn()) {
      state.appliedTags = [];
      state.draftTags = [];
      return Promise.resolve();
    }
    if (!cfg.restTags) {
      return Promise.resolve();
    }
    return fetch(cfg.restTags, { credentials: "same-origin", headers: authHeaders() })
      .then(function (res) {
        if (res.status === 401) {
          handleTagsAuthFailure();
          throw new Error("HTTP 401");
        }
        if (!res.ok) {
          throw new Error("HTTP " + res.status);
        }
        return res.json();
      })
      .then(function (data) {
        var tags = data.tags || [];
        var preserveDraft =
          isSkillsModalOpen() && !tagsEqual(state.draftTags, state.appliedTags);
        state.appliedTags = cloneTags(tags);
        if (!preserveDraft) {
          state.draftTags = cloneTags(tags);
        }
        state.tagsSyncRev = readTagsSyncRev();
        if (!tags.length && state.sort === "match" && !hasUserSkills()) {
          state.sort = "time";
        }
      })
      .catch(function (err) {
        if (String(err && err.message).indexOf("401") >= 0) {
          return;
        }
        showError("Не удалось загрузить навыки.");
        throw err;
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
    enforceFeedSortTier();
    var params = {
      limit: state.limit,
      offset: state.offset,
      min_score: 0,
      sort: state.sort,
      min_match: hasPaidAccess() && state.sort === "match" ? state.min_match : 0,
    };
    if (state.appliedTags.length && !isLoggedIn()) {
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
        if (data.today_count != null) {
          state.todayCount = parseInt(data.today_count, 10) || 0;
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
              '<p class="rl-feed-empty">Пока нет заказов. Биржи опрашиваются каждые 15 минут.</p>';
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
        if (replace && state.focusLeadId && !state.focusLeadHandled) {
          state.focusLeadHandled = true;
          focusLeadCard(state.focusLeadId);
        }
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

  function syncFlipHeight(card) {
    if (!card || !listEl || !listEl.contains(card)) {
      return;
    }
    if (!card.classList.contains("rl-lead-card--draft-flip")) {
      var innerReset = card.querySelector(".rl-feed-card__flip-inner");
      if (innerReset) {
        innerReset.style.minHeight = "";
      }
      return;
    }
    var inner = card.querySelector(".rl-feed-card__flip-inner");
    var front = card.querySelector(".rl-feed-card__face--front");
    var back = card.querySelector(".rl-feed-card__face--back");
    if (!inner || !front || !back) {
      return;
    }
    if (!card.classList.contains("is-expanded")) {
      inner.style.minHeight = "";
      return;
    }
    if (
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ) {
      inner.style.minHeight = "";
      return;
    }
    window.requestAnimationFrame(function () {
      var h = Math.max(front.offsetHeight, back.scrollHeight);
      inner.style.minHeight = h > 0 ? h + "px" : "";
    });
  }

  function refreshCardSocialMeta(card, item) {
    if (!card || !item) {
      return;
    }
    var meta = card.querySelector(".rl-feed-card__head-meta");
    if (meta) {
      var timeEl = meta.querySelector(".rl-feed-card__time");
      var timeHtml = timeEl
        ? timeEl.outerHTML
        : '<span class="rl-feed-card__time">' + formatTime(item.created_at) + "</span>";
      meta.innerHTML = viewsHeadHtml(item) + timeHtml;
    }
    var front = card.querySelector(".rl-feed-card__face--front");
    if (!front) {
      return;
    }
    var slotRow = front.querySelector(".rl-slot-row");
    var slotHtml = renderSlotLine(item);
    if (slotRow) {
      if (slotHtml) {
        slotRow.outerHTML = slotHtml;
      } else {
        slotRow.remove();
      }
    } else if (slotHtml) {
      var chips = front.querySelector(".rl-chips");
      if (chips) {
        chips.insertAdjacentHTML("beforebegin", slotHtml);
      }
    }
    var ctaZone = front.querySelector(".rl-card-cta-zone, .rl-card-cta");
    var ctaHtml = cardCtaHtml(item);
    if (ctaZone) {
      ctaZone.outerHTML = ctaHtml;
    } else {
      var bodyEl = front.querySelector(".rl-feed-card__body");
      if (bodyEl) {
        bodyEl.insertAdjacentHTML("beforebegin", ctaHtml);
      }
    }
  }

  function expandCard(card) {
    if (!card) {
      return;
    }
    var id = parseInt(card.getAttribute("data-id"), 10);
    if (!id) {
      return;
    }
    listEl.querySelectorAll(".rl-lead-card.is-expanded").forEach(function (c) {
      if (c !== card) {
        c.classList.remove("is-expanded", "rl-lead-card--draft-flip");
        var otherId = parseInt(c.getAttribute("data-id"), 10);
        if (otherId && state.itemsById[otherId]) {
          syncCardChips(c, state.itemsById[otherId], false);
        }
        syncFlipHeight(c);
      }
    });
    state.expandedId = id;
    card.classList.add("is-expanded");
    if (state.itemsById[id]) {
      syncCardChips(card, state.itemsById[id], true);
    }
    syncFlipHeight(card);
  }

  function setCardBodyHtml(card, html) {
    card.querySelectorAll(".rl-feed-card__body-inner").forEach(function (el) {
      el.innerHTML = html;
    });
  }

  function finishDraftFlip(card) {
    card.classList.remove("rl-lead-card--draft-flip");
    syncFlipHeight(card);
    var replyEl = card.querySelector("[data-reply-text]");
    if (replyEl) {
      replyEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }

  function flipCardOnce(card) {
    if (!card) {
      return;
    }
    var inner = card.querySelector(".rl-feed-card__flip-inner");
    var reduceMotion =
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    expandCard(card);
    card.classList.add("rl-lead-card--draft-flip");
    syncFlipHeight(card);
    if (!inner || reduceMotion) {
      window.setTimeout(function () {
        finishDraftFlip(card);
      }, 32);
      return;
    }
    function onFlipEnd(e) {
      if (e.propertyName !== "transform") {
        return;
      }
      inner.removeEventListener("transitionend", onFlipEnd);
      finishDraftFlip(card);
    }
    inner.addEventListener("transitionend", onFlipEnd);
    window.setTimeout(function () {
      if (card.classList.contains("rl-lead-card--draft-flip")) {
        inner.removeEventListener("transitionend", onFlipEnd);
        finishDraftFlip(card);
      }
    }, 700);
  }

  function updateCardDraft(card, item) {
    var bodyHtml = renderExpandedBody(item);
    setCardBodyHtml(card, bodyHtml);
    var headStart = card.querySelector(".rl-feed-card__head-start");
    if (headStart) {
      headStart.innerHTML = headBadgesHtml(item, isIdealMatch(item));
    }
    refreshCardSocialMeta(card, item);
    card.classList.add("rl-lead-card--draft-ready");
    flipCardOnce(card);
  }

  function parseFocusLeadId() {
    try {
      var params = new URLSearchParams(window.location.search || "");
      var raw = params.get("lead") || params.get("id") || "";
      var id = parseInt(raw, 10);
      return id > 0 ? id : null;
    } catch (e) {
      return null;
    }
  }

  function leadDetailApiUrl(leadId) {
    var base = cfg.restFeed || "";
    if (base.indexOf("/feed") >= 0) {
      return base.replace(/\/feed\/?$/, "/leads/" + leadId);
    }
    return base.replace(/\/?$/, "/leads/" + leadId);
  }

  function pulseFocusCard(card) {
    card.classList.add("rl-lead-card--push-focus");
    window.setTimeout(function () {
      card.classList.remove("rl-lead-card--push-focus");
    }, 2800);
  }

  function revealFocusCard(card) {
    if (!card) {
      return;
    }
    card.classList.add("is-visible");
    expandCard(card);
    card.scrollIntoView({ behavior: "smooth", block: "center" });
    pulseFocusCard(card);
  }

  function focusLeadCard(leadId) {
    if (!leadId || !listEl) {
      return Promise.resolve();
    }
    var card = listEl.querySelector('.rl-lead-card[data-id="' + leadId + '"]');
    if (card) {
      revealFocusCard(card);
      return Promise.resolve();
    }
    return fetch(leadDetailApiUrl(leadId), {
      credentials: "same-origin",
      headers: authHeaders(),
    })
      .then(function (res) {
        if (!res.ok) {
          throw new Error("HTTP " + res.status);
        }
        return res.json();
      })
      .then(function (item) {
        if (!item || !item.id) {
          return;
        }
        state.itemsById[item.id] = item;
        listEl.insertAdjacentHTML("afterbegin", renderCard(item, true));
        state.totalShown += 1;
        var newCard = listEl.querySelector('.rl-lead-card[data-id="' + leadId + '"]');
        if (!newCard) {
          return;
        }
        bindCards();
        revealFocusCard(newCard);
      })
      .catch(function () {
        /* карточка недоступна — остаёмся на ленте */
      });
  }

  var cardDelegationReady = false;

  function toggleCardExpand(card) {
    var id = parseInt(card.getAttribute("data-id"), 10);
    if (state.expandedId === id) {
      state.expandedId = null;
      card.classList.remove("is-expanded", "rl-lead-card--draft-flip");
      if (state.itemsById[id]) {
        syncCardChips(card, state.itemsById[id], false);
      }
      syncFlipHeight(card);
    } else {
      if (state.itemsById[id]) {
        bumpHumanView(id);
        refreshCardSocialMeta(card, state.itemsById[id]);
      }
      expandCard(card);
    }
  }

  function toggleCardUpsell(card) {
    var upsell = card.querySelector("[data-card-upsell]");
    if (!upsell) {
      return;
    }
    var show = !upsell.classList.contains("is-visible");
    if (listEl) {
      listEl.querySelectorAll(".rl-card-upsell.is-visible").forEach(function (el) {
        el.classList.remove("is-visible");
      });
    }
    if (show) {
      upsell.classList.add("is-visible");
    }
  }

  function runDraftFetchForCard(card, replyBtn) {
    if (!hasPaidAccess()) {
      return;
    }
    var id = parseInt(card.getAttribute("data-id"), 10);
    var baseItem = state.itemsById[id];
    if (baseItem && replySlotsRemaining(baseItem) <= 0) {
      return;
    }
    listEl.querySelectorAll(".rl-lead-card.is-expanded").forEach(function (c) {
      c.classList.remove("is-expanded", "rl-lead-card--draft-flip");
      var collapsedId = parseInt(c.getAttribute("data-id"), 10);
      if (collapsedId && state.itemsById[collapsedId]) {
        syncCardChips(c, state.itemsById[collapsedId], false);
      }
      syncFlipHeight(c);
    });
    state.expandedId = null;
    card.classList.remove("is-expanded", "rl-lead-card--draft-ready", "rl-lead-card--draft-flip");
    if (state.itemsById[id]) {
      syncCardChips(card, state.itemsById[id], false);
    }
    syncFlipHeight(card);
    var replyEl = card.querySelector("[data-reply-text]");
    if (replyEl && replyEl.textContent.trim()) {
      expandCard(card);
      replyEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
      return;
    }
    var prevLabel = replyBtn.textContent;
    replyBtn.disabled = true;
    replyBtn.textContent = "Генерируем…";
    card.classList.add("rl-lead-card--draft-pending");
    fetchDraft(id)
      .then(function (data) {
        var base = state.itemsById[id] || { id: id };
        var merged = Object.assign({}, base, {
          reply_draft: data.reply_draft,
          tools_required: data.tools_required || base.tools_required || [],
        });
        state.itemsById[id] = merged;
        card.classList.remove("rl-lead-card--draft-pending");
        card.classList.add("rl-lead-card--draft-ready");
        updateCardDraft(card, merged);
      })
      .catch(function (err) {
        card.classList.remove("rl-lead-card--draft-pending");
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

  function triggerFreeReplyShake(card, btn) {
    var pricing = cfg.pricingUrl || "/pricing/";
    if (btn.getAttribute("data-free-premium-step") === "1") {
      window.location.href = pricing;
      return;
    }
    btn.blur();
    card.classList.add("rl-lead-card--shake-cta");
    window.setTimeout(function () {
      card.classList.remove("rl-lead-card--shake-cta");
    }, 500);
    btn.textContent = "Купить Premium →";
    btn.classList.add("rl-card-cta--buy-premium");
    btn.setAttribute("data-free-premium-step", "1");
  }

  function onFeedListClick(e) {
    var card = e.target.closest(".rl-lead-card");
    if (!card || !listEl || !listEl.contains(card)) {
      return;
    }
    var replyBtn = e.target.closest(
      ".rl-feed-card__reply-btn, .rl-card-cta[data-free-reply-lock], .rl-card-cta--primary"
    );
    if (replyBtn && card.contains(replyBtn)) {
      e.stopPropagation();
      if (
        replyBtn.hasAttribute("data-free-reply-lock") ||
        replyBtn.getAttribute("data-free-premium-step") === "1"
      ) {
        triggerFreeReplyShake(card, replyBtn);
        return;
      }
      runDraftFetchForCard(card, replyBtn);
      return;
    }
    var skillsCta = e.target.closest("[data-open-skills]");
    if (skillsCta && card.contains(skillsCta)) {
      e.stopPropagation();
      openSkillsUi();
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
      e.target.closest(
        ".rl-feed-card__link, .rl-card-upsell a, a.rl-card-cta--anon, a, button, input, textarea, select"
      )
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
      if (listEl) {
        listEl.querySelectorAll(".rl-card-upsell.is-visible").forEach(function (el) {
          el.classList.remove("is-visible");
        });
        listEl.querySelectorAll(".rl-lead-card.is-expanded").forEach(function (c) {
          c.classList.remove("is-expanded", "rl-lead-card--draft-flip");
          syncFlipHeight(c);
        });
        state.expandedId = null;
      }
      if (!e.target.closest("#rl-feed-sidebar, .rl-filter-hint")) {
        hideFilterHint();
      }
    });
    listEl.addEventListener("transitionend", function (e) {
      if (!e.target.classList.contains("rl-feed-card__flip-inner")) {
        return;
      }
      var card = e.target.closest(".rl-lead-card");
      if (card && card.classList.contains("rl-lead-card--draft-flip")) {
        syncFlipHeight(card);
      }
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

  bindWheelScroll(sidebarScroll || sidebar);
  bindSkillsPanels(sidebar || document);

  if (skillsTriggerBtn) {
    skillsTriggerBtn.addEventListener("click", function (e) {
      e.preventDefault();
      if (getFeedTier() === "anon") {
        showFilterHint();
        return;
      }
      openSkillsUi();
    });
  }
  if (sortDdEl) {
    sortDdEl.addEventListener("toggle", function () {
      if (getFeedTier() === "anon" && sortDdEl.open) {
        sortDdEl.open = false;
        showFilterHint();
        return;
      }
      if (!sortDdEl.open) {
        renderSortPanel();
      }
    });
    sortDdEl.addEventListener("change", function (e) {
      if (
        e.target &&
        e.target.name === "rl-feed-sort" &&
        sortPanelEl &&
        sortPanelEl.contains(e.target)
      ) {
        sortPanelEl.querySelectorAll(".rl-sort-option").forEach(function (opt) {
          var inp = opt.querySelector("input");
          opt.classList.toggle("is-active", inp && inp.checked);
        });
        updateSortPanelPctVisibility();
      }
    });
    sortDdEl.addEventListener("click", function (e) {
      var sortOpt = e.target.closest(".rl-sort-option");
      if (sortOpt && sortPanelEl && sortPanelEl.contains(sortOpt)) {
        var sortInp = sortOpt.querySelector('input[name="rl-feed-sort"]');
        if (sortInp) {
          sortInp.checked = true;
          sortPanelEl.querySelectorAll(".rl-sort-option").forEach(function (opt) {
            var inp = opt.querySelector("input");
            opt.classList.toggle("is-active", inp && inp.checked);
          });
          updateSortPanelPctVisibility();
        }
      }
      var pctBtn = e.target.closest("[data-feed-min-match]");
      if (pctBtn && sortPanelEl && sortPanelEl.contains(pctBtn)) {
        e.preventDefault();
        var pct = parseInt(pctBtn.getAttribute("data-feed-min-match"), 10);
        sortPanelEl.querySelectorAll(".rl-sort-panel__pct-btn").forEach(function (btn) {
          btn.classList.toggle(
            "is-active",
            parseInt(btn.getAttribute("data-feed-min-match"), 10) === pct
          );
        });
        state.min_match = pct;
        var matchRadio = sortPanelEl.querySelector('input[value="match"]');
        if (matchRadio) {
          matchRadio.checked = true;
        }
        state.sort = "match";
        sortPanelEl.querySelectorAll(".rl-sort-option").forEach(function (opt) {
          var inp = opt.querySelector("input");
          opt.classList.toggle("is-active", inp && inp.value === "match");
        });
        updateSortPanelPctVisibility();
        return;
      }
      var applyBtn = e.target.closest("#rl-feed-sort-apply");
      if (applyBtn && sortPanelEl && sortPanelEl.contains(applyBtn)) {
        e.preventDefault();
        applySortPanelDraft();
        return;
      }
      if (
        getFeedTier() === "anon" &&
        e.target.closest("#rl-feed-sort-trigger, summary")
      ) {
        e.preventDefault();
        showFilterHint();
      }
    });
    document.addEventListener("click", function (e) {
      if (!sortDdEl || !sortDdEl.open) {
        return;
      }
      if (e.target.closest("#rl-feed-sort-panel, #rl-feed-sort-trigger")) {
        return;
      }
      sortDdEl.open = false;
    });
  }
  function onSkillsModalDismiss(e) {
    e.preventDefault();
    e.stopPropagation();
    closeFeedSkillsModal();
  }
  if (skillsOverlayEl) {
    skillsOverlayEl.addEventListener("click", onSkillsModalDismiss);
  }
  if (skillsCloseBtn) {
    skillsCloseBtn.addEventListener("click", onSkillsModalDismiss);
  }
  if (skillsApplyBtn) {
    skillsApplyBtn.addEventListener("click", applyDraftTags);
  }
  if (skillsClearBtn) {
    skillsClearBtn.addEventListener("click", clearSkills);
  }
  if (toolbarEl) {
    toolbarEl.addEventListener("click", function (e) {
      var sortBtn = e.target.closest("[data-feed-sort]");
      if (sortBtn && toolbarEl.contains(sortBtn)) {
        setFeedSort(sortBtn.getAttribute("data-feed-sort"));
        return;
      }
      var matchBtn = e.target.closest("[data-feed-min-match]");
      if (matchBtn && toolbarEl.contains(matchBtn)) {
        setFeedMinMatch(matchBtn.getAttribute("data-feed-min-match"));
      }
    });
  }

  function reloadTagsFromSync() {
    if (!isLoggedIn() || !cfg.restTags) {
      return;
    }
    var rev = readTagsSyncRev();
    if (rev === state.tagsSyncRev) {
      return;
    }
    loadTags().then(function () {
      renderSkillsCatalog();
      updateSkillsDraftUi();
      updateFilterBarUi();
      updateCount();
      updateSkillsBadge();
      resetAndLoad();
    });
  }

  window.addEventListener("storage", function (e) {
    if (e.key === TAGS_SYNC_KEY) {
      reloadTagsFromSync();
    }
  });
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "visible") {
      reloadTagsFromSync();
    }
  });

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
        state.sort = "time";
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
  var sheetSuppressOpenUntil = 0;

  function closeSheet() {
    if (!sheet || sheet.hidden) {
      return;
    }
    if (isSkillsModalOpen()) {
      skillsModalEl.hidden = true;
      skillsModalEl.removeAttribute("data-stack-sheet");
      document.body.classList.remove("rl-skill-tree-open");
    }
    sheet.hidden = true;
    sheet.setAttribute("aria-hidden", "true");
    if (openBtn) {
      openBtn.setAttribute("aria-expanded", "false");
    }
    document.body.style.overflow = "";
    document.body.classList.remove("rl-feed-sheet-open");
    sheetSuppressOpenUntil = Date.now() + 450;
  }

  function onSheetDismiss(e) {
    if (!sheet || sheet.hidden) {
      return;
    }
    e.preventDefault();
    e.stopPropagation();
    closeSheet();
  }

  if (sheet) {
    if (sheetOverlayEl) {
      sheetOverlayEl.addEventListener("click", onSheetDismiss);
    }
    if (sheetCloseBtn) {
      sheetCloseBtn.addEventListener("click", onSheetDismiss);
    }
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
      if (!inp || !sheetBody.contains(inp)) {
        return;
      }
      if (inp.name === "category") {
        onSheetCategoryChange(inp);
        return;
      }
      if (inp.name === "rl-sheet-sort") {
        sheetBody.querySelectorAll(".rl-sheet-block--sort .rl-sort-option").forEach(function (opt) {
          var radio = opt.querySelector("input");
          opt.classList.toggle("is-active", radio && radio.checked);
        });
        updateSheetSortPctVisibility();
      }
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
      var sortOpt = e.target.closest(".rl-sheet-block--sort .rl-sort-option");
      if (sortOpt && sheetBody.contains(sortOpt)) {
        var sortInp = sortOpt.querySelector('input[name="rl-sheet-sort"]');
        if (sortInp) {
          sortInp.checked = true;
          sheetBody.querySelectorAll(".rl-sheet-block--sort .rl-sort-option").forEach(function (opt) {
            var radio = opt.querySelector("input");
            opt.classList.toggle("is-active", radio && radio.checked);
          });
          updateSheetSortPctVisibility();
        }
      }
      var pctBtn = e.target.closest(".rl-sheet-block--sort [data-feed-min-match]");
      if (pctBtn && sheetBody.contains(pctBtn)) {
        e.preventDefault();
        var pct = parseInt(pctBtn.getAttribute("data-feed-min-match"), 10);
        sheetBody.querySelectorAll(".rl-sheet-block--sort .rl-sort-panel__pct-btn").forEach(function (btn) {
          btn.classList.toggle(
            "is-active",
            parseInt(btn.getAttribute("data-feed-min-match"), 10) === pct
          );
        });
        var matchRadio = sheetBody.querySelector('input[name="rl-sheet-sort"][value="match"]');
        if (matchRadio) {
          matchRadio.checked = true;
        }
        sheetBody.querySelectorAll(".rl-sheet-block--sort .rl-sort-option").forEach(function (opt) {
          var radio = opt.querySelector("input");
          opt.classList.toggle("is-active", radio && radio.value === "match");
        });
        updateSheetSortPctVisibility();
        return;
      }
      var sheetSkillsOpen = e.target.closest("#rl-sheet-skills-open, .rl-sheet-skills-open");
      if (sheetSkillsOpen && sheetBody.contains(sheetSkillsOpen)) {
        e.preventDefault();
        openFeedSkillsModal({ fromSheet: true });
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
    });
  }

  function buildSheetContent() {
    sheetBody.innerHTML = "";
    var catField = sidebar.querySelector(".rl-feed-filter--category");
    if (catField) {
      var catBlock = document.createElement("section");
      catBlock.className = "rl-sheet-block rl-sheet-block--cats";
      catBlock.innerHTML =
        '<p class="rl-sheet-block__label">Специализация</p>';
      catBlock.appendChild(catField.cloneNode(true));
      sheetBody.appendChild(catBlock);
    }
    if (isLoggedIn()) {
      var skillsBlock = document.createElement("section");
      skillsBlock.className = "rl-sheet-block rl-sheet-block--skills";
      var skillN = state.appliedTags.length;
      skillsBlock.innerHTML =
        '<p class="rl-sheet-block__label">Навыки</p>' +
        '<button type="button" class="rl-sheet-text-btn rl-sheet-skills-open" id="rl-sheet-skills-open">' +
        '<span class="rl-sheet-text-btn__label">' +
        (skillN > 0
          ? "Выбрано " + skillN + " · изменить →"
          : "Настроить навыки →") +
        "</span></button>";
      sheetBody.appendChild(skillsBlock);
      var sortBlock = document.createElement("section");
      sortBlock.className = "rl-sheet-block rl-sheet-block--sort";
      sortBlock.innerHTML =
        '<p class="rl-sheet-block__label">Сортировка</p>' +
        '<div class="rl-sheet-sort-panel" id="rl-feed-sheet-sort"></div>';
      sheetBody.appendChild(sortBlock);
      renderSheetSortPanel();
    } else {
      var loginBlock = document.createElement("section");
      loginBlock.className = "rl-sheet-block rl-sheet-block--login";
      loginBlock.innerHTML =
        '<p class="rl-sheet-block__label">Навыки и сортировка</p>' +
        '<p class="rl-sheet-block__hint">Войди через Telegram — настрой подбор по навыкам и сортировку.</p>' +
        '<a class="rl-btn rl-btn--secondary rl-sheet-login-btn" href="' +
        escapeHtml(cabinetLoginUrl) +
        '">Войти в кабинет →</a>';
      sheetBody.appendChild(loginBlock);
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
    sheet.setAttribute("aria-hidden", "false");
    if (openBtn) {
      openBtn.setAttribute("aria-expanded", "true");
    }
    document.body.style.overflow = "hidden";
    document.body.classList.add("rl-feed-sheet-open");
    updateSkillsBadge();
    updateSkillsDraftUi();
  }

  if (sheet && sheetBody && sidebar && openBtn) {
    openBtn.addEventListener("click", function (e) {
      if (Date.now() < sheetSuppressOpenUntil) {
        e.preventDefault();
        e.stopPropagation();
        return;
      }
      e.preventDefault();
      e.stopPropagation();
      openSheet();
    });
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
      sheetBody.querySelectorAll('input[name="category"]').forEach(function (inp) {
        var val = inp.getAttribute("value");
        var live = sidebar.querySelector(
          'input[name="category"][value="' + val + '"]'
        );
        if (live) {
          live.checked = inp.checked;
        }
      });
      applySheetSortDraft();
      state.draftCategories = readCategoriesFrom(sidebar);
      state.appliedCategories = cloneCategories(state.draftCategories);
      syncChips();
      readFilters();
      updateFilterBarUi();
      closeSheet();
      persistFeedPrefs().finally(function () {
        if (!tagsEqual(state.draftTags, state.appliedTags)) {
          persistTags(cloneTags(state.draftTags), { setSortMatch: true, reload: true });
          return;
        }
        resetAndLoad();
      });
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
  syncMobileFilterChrome();
  if (window.matchMedia) {
    window.matchMedia("(max-width: 767px)").addEventListener("change", syncMobileFilterChrome);
  }

  state.focusLeadId = parseFocusLeadId();

  if (getToken()) {
    syncAuthCookie(getToken());
  } else {
    applyFeedPrefsToState(readLocalFeedPrefs());
  }

  Promise.all([
    loadSubscription(),
    isLoggedIn() ? mergeFeedPrefsOnLogin() : Promise.resolve(),
    loadTags().catch(function () {}),
    loadCatalog().catch(function () {}),
  ])
    .then(function () {
    applyFeedShellMode();
    if (!isLoggedIn()) {
      state.draftCategories = readCategoriesFrom();
      state.appliedCategories = cloneCategories(state.draftCategories);
      state.sort = "time";
    }
    applyFeedTierUi();
    renderSkillsCatalog();
    syncChips();
    readFilters();
    updateFilterBarUi();
    updateCount();
    resetAndLoad();
  })
    .catch(function () {
      applyFeedShellMode();
      applyFeedTierUi();
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

  function syncFeedCabinetLink() {
    var link = document.getElementById("rl-feed-cabinet-link");
    if (!link) {
      return;
    }
    link.textContent = isLoggedIn() ? "Кабинет →" : "Войти в кабинет →";
    link.setAttribute(
      "href",
      isLoggedIn() ? cfg.cabinetUrl || "/cabinet/" : cabinetLoginUrl
    );
  }

  syncFeedCabinetLink();
  window.addEventListener("rawlead-auth-changed", syncFeedCabinetLink);

  if (window.rawleadSyncHeader) {
    window.rawleadSyncHeader();
  }
})();
