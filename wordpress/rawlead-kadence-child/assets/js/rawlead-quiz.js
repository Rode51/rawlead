(function () {
  "use strict";

  var cfg = window.rawleadQuiz || {};
  var root = document.getElementById("rl-quiz");
  if (!root) {
    return;
  }

  var overlayEl = document.getElementById("rl-feed-quiz-overlay");
  var overlayBackdropEl = document.getElementById("rl-feed-quiz-overlay-backdrop");
  var overlayCloseBtn = document.getElementById("rl-feed-quiz-overlay-close");
  var overlayMode = !!cfg.overlayMode || !!overlayEl;
  var overlayOpen = false;
  var overlayDidPush = false;
  var overlayReturnFocus = null;

  var SESSION_KEY = "rawlead_quiz_session";
  var COMPLETED_KEY = "rawlead_quiz_completed_v1";
  var TOKEN_KEY = "rawlead_access_token";
  var TAGS_SYNC_KEY = "rawlead_user_tags_rev";
  var RESTORE_IMPORT_KEY = "rawlead_quiz_restore_import_v1";
  var IMPORT_WEIGHT = 4.0;
  var MIN_EARLY_CTA = 5;
  var TOTAL_EXPECTED = 12;
  var ANIM_MS = 220;
  var ENTER_MS = 280;
  var QUIZ_NICHES = ["dev", "design", "marketing", "text"];

  var CATEGORY_META = {
    dev: { emoji: "💻", label: "Разработка" },
    design: { emoji: "🎨", label: "Дизайн" },
    marketing: { emoji: "📣", label: "Маркетинг" },
    text: { emoji: "✍️", label: "Тексты" },
  };

  var NICHE_ICONS = {
    dev: "</>",
    design: "✦",
    marketing: "◎",
    text: "Aa",
  };

  var introEl = document.getElementById("rl-quiz-intro");
  var introStartBtn = document.getElementById("rl-quiz-intro-start");
  var loadingEl = document.getElementById("rl-quiz-loading");
  var errorEl = document.getElementById("rl-quiz-error");
  var errorTextEl = document.getElementById("rl-quiz-error-text");
  var errorRetryBtn = document.getElementById("rl-quiz-error-retry");
  var playEl = document.getElementById("rl-quiz-play");
  var resultEl = document.getElementById("rl-quiz-result");
  var progressEl = document.getElementById("rl-quiz-progress");
  var progressFillEl = document.getElementById("rl-quiz-progress-fill");
  var restartPlayBtn = document.getElementById("rl-quiz-restart");
  var cardEl = document.getElementById("rl-quiz-card");
  var sourceEl = document.getElementById("rl-quiz-card-source");
  var timeEl = document.getElementById("rl-quiz-card-time");
  var budgetEl = document.getElementById("rl-quiz-card-budget");
  var titleEl = document.getElementById("rl-quiz-card-title");
  var taskEl = document.getElementById("rl-quiz-card-task");
  var linkEl = document.getElementById("rl-quiz-card-link");
  var tagsEl = document.getElementById("rl-quiz-card-tags");
  var likeBtn = document.getElementById("rl-quiz-like");
  var nopeBtn = document.getElementById("rl-quiz-nope");
  var earlyCtaEl = document.getElementById("rl-quiz-early-cta");
  var earlyBtn = document.getElementById("rl-quiz-early-btn");
  var resultTitleEl = document.getElementById("rl-quiz-result-title");
  var categoryBarsEl = document.getElementById("rl-quiz-category-bars");
  var resultSubEl = document.getElementById("rl-quiz-result-sub");
  var loginBlockEl = document.getElementById("rl-quiz-login");
  var cabinetCtaEl = document.getElementById("rl-quiz-cabinet-cta");
  var trialPromoEl = cabinetCtaEl;
  var retryEl = document.getElementById("rl-quiz-retry");
  var skipResultEl = document.getElementById("rl-quiz-skip-result");
  var loginStateEl = document.getElementById("rl-quiz-login-state");
  var widgetBox = document.getElementById("rl-quiz-telegram-widget");
  var stageEl = document.getElementById("rl-quiz-stage");
  var retakeCompletedEl = document.getElementById("rl-quiz-retake-completed");

  var session = { history: [], started_at: null };
  var currentCard = null;
  var profile = null;
  var authCompleted = false;
  var animating = false;
  var prefetchPromise = null;
  var prefetchData = null;
  var retakeMode = false;
  var retakeBackup = null;
  var pendingImportPromise = null;
  var pendingFeedRefresh = false;
  var anonCtaHtml = cabinetCtaEl ? cabinetCtaEl.innerHTML : "";
  var loggedInCtaLabel = "Открыть ленту →";
  var importPendingLabel = "Сохраняем навыки…";
  var primaryCtaPending = false;

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function readSession() {
    try {
      var raw = localStorage.getItem(SESSION_KEY);
      if (!raw) {
        return { history: [], started_at: null };
      }
      var data = JSON.parse(raw);
      if (!data || typeof data !== "object") {
        return { history: [], started_at: null };
      }
      if (!Array.isArray(data.history)) {
        data.history = [];
      }
      return data;
    } catch (err) {
      return { history: [], started_at: null };
    }
  }

  function writeSession(data) {
    try {
      localStorage.setItem(SESSION_KEY, JSON.stringify(data));
    } catch (err) {
      /* ignore */
    }
  }

  function readCompleted() {
    try {
      var raw = localStorage.getItem(COMPLETED_KEY);
      if (!raw) {
        return null;
      }
      var data = JSON.parse(raw);
      if (!data || typeof data !== "object") {
        return null;
      }
      return data;
    } catch (err) {
      return null;
    }
  }

  function writeCompleted(snap) {
    try {
      localStorage.setItem(COMPLETED_KEY, JSON.stringify(snap));
    } catch (err) {
      /* ignore */
    }
  }

  function clearCompleted() {
    try {
      localStorage.removeItem(COMPLETED_KEY);
    } catch (err) {
      /* ignore */
    }
  }

  function clearQuizLocalKeys() {
    try {
      localStorage.removeItem(SESSION_KEY);
      localStorage.removeItem(COMPLETED_KEY);
      localStorage.removeItem(RESTORE_IMPORT_KEY);
      sessionStorage.removeItem(RESTORE_IMPORT_KEY);
      sessionStorage.removeItem("rawlead_quiz_retake");
    } catch (err) {
      /* ignore */
    }
    session = { history: [], started_at: null };
    profile = null;
    currentCard = null;
    animating = false;
    retakeMode = false;
    retakeBackup = null;
  }

  window.rawleadClearQuizLocalKeys = clearQuizLocalKeys;

  window.addEventListener("rawlead-auth-changed", function () {
    if (!isAnon()) {
      return;
    }
    if (overlayMode && overlayOpen) {
      closeOverlay(false);
    }
  });

  window.addEventListener("pagehide", function () {
    if (!overlayMode || !overlayOpen || retakeMode) {
      return;
    }
    try {
      localStorage.removeItem(SESSION_KEY);
    } catch (err) {
      /* ignore */
    }
  });

  function discardIncompleteQuizSession() {
    try {
      localStorage.removeItem(SESSION_KEY);
    } catch (err) {
      /* ignore */
    }
    session = { history: [], started_at: null };
    currentCard = null;
    animating = false;
  }

  function authHeaders() {
    var h = { Accept: "application/json" };
    if (cfg.nonce) {
      h["X-WP-Nonce"] = cfg.nonce;
    }
    try {
      var token = localStorage.getItem(TOKEN_KEY) || "";
      if (token) {
        h.Authorization = "Bearer " + token;
      }
    } catch (err) {
      /* ignore */
    }
    return h;
  }

  function isAnon() {
    try {
      return !localStorage.getItem(TOKEN_KEY);
    } catch (err) {
      return true;
    }
  }

  function setToken(token) {
    try {
      localStorage.setItem(TOKEN_KEY, token);
      document.cookie =
        "rl_access=" +
        encodeURIComponent(token) +
        "; path=/; max-age=2592000; SameSite=Lax";
    } catch (err) {
      /* ignore */
    }
  }

  function setStagePhase(phase) {
    if (!stageEl) {
      return;
    }
    stageEl.classList.remove(
      "rl-quiz-stage--intro",
      "rl-quiz-stage--loading",
      "rl-quiz-stage--cards",
      "rl-quiz-stage--error"
    );
    if (phase) {
      stageEl.classList.add("rl-quiz-stage--" + phase);
    }
  }

  function showStageScreen(name) {
    var screens = {
      intro: introEl,
      loading: loadingEl,
      error: errorEl,
      play: playEl,
    };
    Object.keys(screens).forEach(function (key) {
      if (screens[key]) {
        screens[key].hidden = !name || key !== name;
      }
    });
    if (resultEl) {
      resultEl.hidden = true;
    }
    if (!name) {
      setStagePhase(null);
      return;
    }
    if (name === "play") {
      setStagePhase("cards");
      setOverlayPhase(overlayMode ? "cards" : null);
      return;
    }
    if (name === "loading") {
      setStagePhase("loading");
      setOverlayPhase(overlayMode ? "loading" : null);
      return;
    }
    if (name === "error") {
      setStagePhase("error");
      setOverlayPhase(overlayMode ? "intro" : null);
      return;
    }
    if (name === "intro") {
      setStagePhase("intro");
      setOverlayPhase(overlayMode ? "intro" : null);
    }
  }

  function setOverlayPhase(phase) {
    if (!overlayEl) {
      return;
    }
    overlayEl.classList.remove(
      "rl-feed-quiz-overlay--intro",
      "rl-feed-quiz-overlay--loading",
      "rl-feed-quiz-overlay--cards",
      "rl-feed-quiz-overlay--result"
    );
    if (phase) {
      overlayEl.classList.add("rl-feed-quiz-overlay--" + phase);
    }
  }

  function revealIntroAnimation() {
    if (!introEl) {
      return;
    }
    introEl.classList.remove("is-visible");
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        introEl.classList.add("is-visible");
      });
    });
  }

  function hideAllScreens() {
    showStageScreen(null);
    [introEl, loadingEl, errorEl, playEl, resultEl].forEach(function (el) {
      if (el) {
        el.hidden = true;
      }
    });
    setStagePhase(null);
  }

  function showError(msg) {
    if (resultEl) {
      resultEl.hidden = true;
    }
    showStageScreen("error");
    if (errorEl) {
      errorEl.hidden = false;
    }
    if (errorTextEl) {
      errorTextEl.textContent = msg || "Не удалось загрузить — попробуй ещё раз";
    }
  }

  function computeNicheConfidence(history) {
    var conf = { dev: 0, design: 0, marketing: 0, text: 0 };
    history.forEach(function (item) {
      var cat = item.category;
      if (!cat || conf[cat] == null) {
        return;
      }
      if (item.liked) {
        conf[cat] += 2;
      } else {
        conf[cat] -= 1;
      }
    });
    return conf;
  }

  function buildTagsToImport(history) {
    var out = [];
    var seen = {};
    history.forEach(function (item) {
      if (!item.liked) {
        return;
      }
      (item.tags || []).forEach(function (tag) {
        var t = String(tag);
        if (t && !seen[t]) {
          seen[t] = true;
          out.push(t);
        }
      });
    });
    return out;
  }

  function buildLocalProfile(history) {
    var conf = computeNicheConfidence(history);
    if (QUIZ_NICHES.every(function (n) { return conf[n] <= 0; })) {
      return null;
    }
    var niches = QUIZ_NICHES.filter(function (n) { return conf[n] >= 2; })
      .map(function (n) { return { niche: n, confidence: conf[n] }; })
      .sort(function (a, b) {
        return b.confidence - a.confidence || a.niche.localeCompare(b.niche);
      });
    var likedCx = history
      .filter(function (item) { return item.liked && item.complexity != null; })
      .map(function (item) { return Number(item.complexity); });
    var cxPref = 2.0;
    if (likedCx.length) {
      cxPref = likedCx.reduce(function (a, b) { return a + b; }, 0) / likedCx.length;
      cxPref = Math.max(1, Math.min(2, Math.round(cxPref * 10) / 10));
    }
    return {
      niches: niches,
      tags_to_import: buildTagsToImport(history),
      leads_per_week: 0,
      cx_pref: cxPref,
    };
  }

  function nicheConfidenceMap(profile) {
    var conf = { dev: 0, design: 0, marketing: 0, text: 0 };
    if (profile && profile.niches && profile.niches.length) {
      profile.niches.forEach(function (row) {
        if (row && row.niche && conf[row.niche] != null) {
          conf[row.niche] = Math.max(0, Number(row.confidence) || 0);
        }
      });
      return conf;
    }
    return computeNicheConfidence(session.history);
  }

  function nicheIconHtml(niche) {
    if (!NICHE_ICONS[niche]) {
      return "";
    }
    return (
      '<span class="rl-niche-icon rl-niche-icon--' +
      escapeHtml(niche) +
      '" aria-hidden="true">' +
      escapeHtml(NICHE_ICONS[niche]) +
      "</span>"
    );
  }

  function renderCategoryBars(profile) {
    if (!categoryBarsEl) {
      return;
    }
    var conf = nicheConfidenceMap(profile);
    var maxConf = 1;
    QUIZ_NICHES.forEach(function (niche) {
      if (conf[niche] > maxConf) {
        maxConf = conf[niche];
      }
    });
    var rows = QUIZ_NICHES.map(function (niche) {
      var meta = CATEGORY_META[niche] || { label: niche };
      var raw = Math.max(0, conf[niche] || 0);
      var pct = raw <= 0 ? 0 : Math.round((raw / maxConf) * 100);
      return { niche: niche, meta: meta, raw: raw, pct: pct };
    })
      .filter(function (row) {
        return row.pct > 0;
      })
      .sort(function (a, b) {
        return b.raw - a.raw;
      })
      .slice(0, 3);
    categoryBarsEl.innerHTML = rows
      .map(function (row) {
        return (
          '<div class="rl-quiz__category-bar" data-pct="' +
          row.pct +
          '">' +
          '<span class="rl-quiz__category-bar-label">' +
          nicheIconHtml(row.niche) +
          ' <span class="rl-quiz__category-bar-name">' +
          escapeHtml(row.meta.label) +
          "</span></span>" +
          '<span class="rl-quiz__category-bar-track" aria-hidden="true">' +
          '<span class="rl-quiz__category-bar-fill" style="width:' +
          row.pct +
          '%"></span>' +
          "</span></div>"
        );
      })
      .join("");
  }

  function updateProgress() {
    var shown = session.history.length;
    if (progressEl) {
      progressEl.textContent = "Профиль формируется…";
    }
    if (progressFillEl) {
      var pct = shown <= 0 ? 10 : Math.min(100, 10 + (shown / TOTAL_EXPECTED) * 90);
      progressFillEl.style.width = String(pct) + "%";
    }
    if (earlyCtaEl) {
      earlyCtaEl.hidden = shown < MIN_EARLY_CTA;
    }
  }

  function setCardActionsDisabled(disabled) {
    if (likeBtn) {
      likeBtn.disabled = disabled;
    }
    if (nopeBtn) {
      nopeBtn.disabled = disabled;
    }
    if (cardEl) {
      cardEl.style.pointerEvents = disabled ? "none" : "";
    }
  }

  function categoryLabel(category) {
    var meta = CATEGORY_META[category];
    return meta ? meta.label : category || "";
  }

  function sourceLabel(source) {
    var s = (source || "").toLowerCase();
    if (s.indexOf("fl") === 0 || s === "fl.ru") {
      return { label: "FL.ru", cls: "fl" };
    }
    if (s.indexOf("kwork") >= 0) {
      return { label: "Kwork", cls: "kwork" };
    }
    if (s === "youdo") {
      return { label: "YouDo", cls: "youdo" };
    }
    if (s.indexOf("tg") === 0 || s.indexOf("telegram") === 0) {
      return { label: "TG", cls: "tg" };
    }
    return { label: source || categoryLabel(source) || "—", cls: "other" };
  }

  function formatBudgetDisplay(text) {
    var value = String(text || "").trim();
    return value || "по договоренности";
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
    if (diff < 0) {
      diff = 0;
    }
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

  function taskBodyText(card) {
    var summary = String(card.task_summary || "").trim();
    if (summary) {
      return summary;
    }
    var raw = String(card.body || card.title || "").trim();
    if (raw.length <= 280) {
      return raw;
    }
    return raw.slice(0, 280).replace(/\s+\S*$/, "") + "…";
  }

  function renderSourceBadge(card) {
    if (!card.source || String(card.source).toLowerCase() === "synthetic") {
      return "";
    }
    var src = sourceLabel(card.source);
    return (
      '<span class="rl-feed-card__source rl-feed-card__source--' +
      escapeHtml(src.cls) +
      '">' +
      escapeHtml(src.label) +
      "</span>"
    );
  }

  function renderCurrentCard() {
    if (!cardEl || !currentCard) {
      return;
    }
    var headEl = cardEl.querySelector(".rl-feed-card__head");
    if (sourceEl) {
      var badgeHtml = renderSourceBadge(currentCard);
      if (badgeHtml) {
        sourceEl.innerHTML = badgeHtml;
        sourceEl.hidden = false;
      } else {
        sourceEl.innerHTML = "";
        sourceEl.hidden = true;
      }
    }
    if (timeEl) {
      var timeText = formatTime(currentCard.created_at);
      timeEl.textContent = timeText;
      timeEl.hidden = !timeText;
    }
    if (headEl) {
      headEl.hidden = !!(sourceEl && sourceEl.hidden && timeEl && timeEl.hidden);
    }
    if (titleEl) {
      titleEl.textContent = currentCard.title || "Без названия";
    }
    if (budgetEl) {
      budgetEl.textContent = "Бюджет: " + formatBudgetDisplay(currentCard.budget_text || currentCard.budget);
    }
    if (taskEl) {
      var task = taskBodyText(currentCard);
      taskEl.textContent = task || "Краткое описание появится после следующего цикла радара.";
    }
    if (linkEl) {
      var url = String(currentCard.url || "").trim();
      if (url) {
        linkEl.href = url;
        linkEl.hidden = false;
      } else {
        linkEl.hidden = true;
      }
    }
    if (tagsEl) {
      var labels = currentCard.lead_tags || [];
      tagsEl.innerHTML = labels
        .map(function (label) {
          return '<span class="rl-chip">' + escapeHtml(label) + "</span>";
        })
        .join("");
    }
    cardEl.hidden = false;
    updateProgress();
  }

  function revealNextCard() {
    if (!cardEl) {
      return;
    }
    cardEl.classList.add("is-swap");
    cardEl.classList.remove("is-exit-right", "is-exit-left", "is-visible", "is-enter");
    renderCurrentCard();
    cardEl.hidden = false;
    cardEl.classList.remove("is-swap");
    cardEl.classList.add("is-enter");
    void cardEl.offsetWidth;
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        cardEl.classList.add("is-visible");
      });
    });
    window.setTimeout(function () {
      cardEl.classList.remove("is-enter");
      cardEl.classList.add("is-visible");
      animating = false;
      setCardActionsDisabled(false);
    }, ENTER_MS);
  }

  function apiJson(url, options) {
    return fetch(url, options).then(function (res) {
      return res
        .json()
        .catch(function () {
          return {};
        })
        .then(function (data) {
          if (!res.ok) {
            var msg =
              (data && (data.message || data.detail || data.code)) || "request failed";
            throw new Error(msg);
          }
          return data;
        });
    });
  }

  function fetchQuizStartApi() {
    return apiJson(cfg.restQuizStart, {
      credentials: "same-origin",
      headers: authHeaders(),
    });
  }

  function prefetchQuizStart() {
    if (!cfg.restQuizStart || prefetchData || prefetchPromise) {
      return prefetchPromise;
    }
    prefetchPromise = fetchQuizStartApi()
      .then(function (data) {
        prefetchData = data;
        return data;
      })
      .catch(function () {
        prefetchPromise = null;
        prefetchData = null;
        return null;
      });
    return prefetchPromise;
  }

  function applyPrimaryCta(nullProfile) {
    if (!cabinetCtaEl) {
      return;
    }
    if (nullProfile) {
      cabinetCtaEl.hidden = true;
      return;
    }
    cabinetCtaEl.hidden = false;
    if (isAnon()) {
      cabinetCtaEl.innerHTML = anonCtaHtml;
      cabinetCtaEl.classList.remove("is-disabled");
      cabinetCtaEl.removeAttribute("aria-disabled");
      cabinetCtaEl.removeAttribute("role");
      var loginUrl = cfg.loginUrl || cfg.cabinetUrl || cabinetCtaEl.getAttribute("href");
      if (loginUrl) {
        cabinetCtaEl.setAttribute("href", loginUrl);
      }
      return;
    }
    cabinetCtaEl.innerHTML = "<span>" + escapeHtml(loggedInCtaLabel) + "</span>";
    if (overlayMode) {
      cabinetCtaEl.setAttribute("href", "#");
      cabinetCtaEl.setAttribute("role", "button");
    } else {
      cabinetCtaEl.setAttribute("href", cfg.lentaUrl || "/lenta/");
      cabinetCtaEl.removeAttribute("role");
    }
    setImportUiPending(primaryCtaPending);
  }

  function resetPrefetch() {
    prefetchPromise = null;
    prefetchData = null;
  }

  function showResult(fromProfile, isRestore) {
    writeSession(session);
    profile = fromProfile != null ? fromProfile : profile;
    [introEl, loadingEl, errorEl, playEl].forEach(function (el) {
      if (el) {
        el.hidden = true;
      }
    });
    if (stageEl) {
      stageEl.hidden = true;
    }
    setStagePhase(null);
    setOverlayPhase(overlayMode ? "result" : null);
    if (resultEl) {
      resultEl.hidden = false;
      resultEl.classList.add("rl-quiz__result--compact");
    }

    var nullProfile = !profile || !profile.niches || !profile.niches.length;
    if (resultTitleEl) {
      resultTitleEl.textContent = nullProfile
        ? "Пока не нашли конкретного профиля — посмотри весь поток"
        : "Готово. Вот что мы узнали:";
    }
    if (resultSubEl) {
      resultSubEl.hidden = nullProfile;
    }
    renderCategoryBars(nullProfile ? null : profile);

    if (loginBlockEl) {
      loginBlockEl.hidden = true;
    }
    if (cabinetCtaEl) {
      applyPrimaryCta(nullProfile);
    }
    if (skipResultEl) {
      skipResultEl.hidden = nullProfile || !isAnon();
    }
    if (retryEl) {
      retryEl.hidden = !nullProfile;
    }

    if (retakeCompletedEl) {
      retakeCompletedEl.hidden = !!nullProfile;
    }

    if (progressFillEl) {
      progressFillEl.style.width = "100%";
    }

    if (!isRestore) {
      var completedSnap = {
        profile: profile,
        history: session.history.slice(),
        completed_at: new Date().toISOString(),
      };
      var wasRetake = retakeMode;
      var failBackup = wasRetake && retakeBackup ? retakeBackup : null;
      var prevCompleted = failBackup || readCompleted();
      retakeMode = false;
      retakeBackup = null;
      pendingFeedRefresh = false;

      function onImportSuccess() {
        writeCompleted(completedSnap);
        try {
          localStorage.removeItem(SESSION_KEY);
        } catch (err) {
          /* ignore */
        }
        pendingFeedRefresh = true;
        setImportUiPending(false);
        window.dispatchEvent(new CustomEvent("rawlead-quiz-complete"));
      }

      function onImportFail(err) {
        if (failBackup) {
          writeCompleted(failBackup);
          profile = failBackup.profile || null;
        } else if (prevCompleted) {
          writeCompleted(prevCompleted);
          profile = prevCompleted.profile || null;
        } else {
          clearCompleted();
          profile = null;
        }
        renderCategoryBars(profile && profile.niches && profile.niches.length ? profile : null);
        setImportUiPending(false);
        showImportError(
          "Не удалось сохранить навыки. " +
            (err && err.message ? err.message + ". " : "") +
            "В ленте остались прежние навыки."
        );
      }

      function finishImportPromise() {
        pendingImportPromise = null;
      }

      if (!nullProfile && !isAnon()) {
        setImportUiPending(true);
        pendingImportPromise = importQuizTags()
          .then(onImportSuccess)
          .catch(onImportFail)
          .finally(finishImportPromise);
      } else {
        writeCompleted(completedSnap);
        try {
          localStorage.removeItem(SESSION_KEY);
        } catch (err) {
          /* ignore */
        }
      }
    } else {
      maybeRestoreImport();
    }
  }

  function handleQuizResponse(data) {
    if (data && data.done) {
      profile = data.profile || null;
      animating = false;
      if (cardEl) {
        cardEl.classList.remove("is-exit-right", "is-exit-left", "is-enter", "is-swap");
        cardEl.classList.add("is-visible");
      }
      showResult();
      return;
    }
    currentCard = (data && data.card) || null;
    if (!currentCard) {
      showError("Нет карточек для теста. Попробуй позже.");
      return;
    }
    showStageScreen("play");
    revealNextCard();
  }

  function requestNext() {
    var url = cfg.restQuizNext;
    var opts = {
      method: "POST",
      credentials: "same-origin",
      headers: Object.assign({ "Content-Type": "application/json" }, authHeaders()),
      body: JSON.stringify({ history: session.history }),
    };
    return apiJson(url, opts).then(handleQuizResponse);
  }

  function clearSession() {
    try {
      localStorage.removeItem(SESSION_KEY);
    } catch (err) {
      /* ignore */
    }
    session = { history: [], started_at: new Date().toISOString() };
    profile = null;
    currentCard = null;
    authCompleted = false;
  }

  function tagsImportPayload() {
    var niches = [];
    if (profile && profile.niches && profile.niches.length) {
      profile.niches.forEach(function (row) {
        if (row && row.niche) {
          niches.push(row.niche);
        }
      });
    }
    if (!profile || !profile.tags_to_import || !profile.tags_to_import.length) {
      return { tags: {}, cx_pref: profile && profile.cx_pref != null ? profile.cx_pref : null, niches: niches };
    }
    var out = {};
    profile.tags_to_import.forEach(function (tag) {
      out[tag] = IMPORT_WEIGHT;
    });
    return {
      tags: out,
      cx_pref: profile.cx_pref != null ? profile.cx_pref : null,
      niches: niches,
    };
  }

  function maybeRestoreImport() {
    if (isAnon()) {
      return;
    }
    if (!profile || !profile.niches || !profile.niches.length) {
      return;
    }
    try {
      if (sessionStorage.getItem(RESTORE_IMPORT_KEY)) {
        return;
      }
    } catch (err) {
      return;
    }
    importQuizTags()
      .then(function () {
        try {
          sessionStorage.setItem(RESTORE_IMPORT_KEY, "1");
        } catch (err) {
          /* ignore */
        }
        window.dispatchEvent(new CustomEvent("rawlead-quiz-complete"));
      })
      .catch(function () {
        /* best-effort sync for stale local profile; retake path surfaces errors */
      });
  }

  function importQuizTags() {
    var payload = tagsImportPayload();
    var hasTags = Object.keys(payload.tags).length > 0;
    var hasNiches = payload.niches && payload.niches.length > 0;
    var hasCx = payload.cx_pref != null;
    if (!hasTags && !hasNiches && !hasCx) {
      return Promise.resolve();
    }
    if (!cfg.restTagsImport) {
      return Promise.resolve();
    }
    return fetch(cfg.restTagsImport, {
      method: "POST",
      credentials: "same-origin",
      headers: Object.assign({ "Content-Type": "application/json" }, authHeaders()),
      body: JSON.stringify(payload),
    })
      .then(function (res) {
        return res
          .json()
          .catch(function () {
            return {};
          })
          .then(function (data) {
            if (!res.ok) {
              throw new Error((data && data.message) || "import failed");
            }
            clearSession();
            bumpTagsSyncRev();
          });
      });
  }

  function bumpTagsSyncRev() {
    var rev = String(Date.now());
    try {
      localStorage.setItem(TAGS_SYNC_KEY, rev);
    } catch (err) {
      return;
    }
    window.dispatchEvent(new CustomEvent("rawlead-tags-imported", { detail: { rev: rev } }));
  }

  function setImportUiPending(pending) {
    primaryCtaPending = !!pending;
    if (!cabinetCtaEl || isAnon()) {
      return;
    }
    var labelEl = cabinetCtaEl.querySelector("span");
    if (pending) {
      cabinetCtaEl.classList.add("is-disabled");
      cabinetCtaEl.setAttribute("aria-disabled", "true");
      if (labelEl) {
        labelEl.textContent = importPendingLabel;
      }
      return;
    }
    cabinetCtaEl.classList.remove("is-disabled");
    cabinetCtaEl.removeAttribute("aria-disabled");
    if (labelEl) {
      labelEl.textContent = loggedInCtaLabel;
    }
  }

  function flushFeedRefreshAfterImport() {
    if (!pendingFeedRefresh) {
      return;
    }
    pendingFeedRefresh = false;
    window.dispatchEvent(new CustomEvent("rawlead-quiz-complete"));
  }

  function showImportError(msg) {
    if (loginBlockEl) {
      loginBlockEl.hidden = false;
    }
    setLoginState(
      "error",
      msg ||
        "Не удалось сохранить навыки. В ленте остались прежние навыки — попробуй ещё раз."
    );
  }

  function setLoginState(kind, msg) {
    if (!loginStateEl) {
      return;
    }
    loginStateEl.hidden = !msg;
    loginStateEl.textContent = msg || "";
    loginStateEl.className =
      "rl-quiz__login-state" + (kind === "error" ? " rl-quiz__login-state--err" : "");
  }

  function afterQuizAuthSuccess() {
    if (overlayMode) {
      closeOverlay(false);
      window.dispatchEvent(new CustomEvent("rawlead-auth-changed"));
      window.dispatchEvent(new CustomEvent("rawlead-quiz-complete"));
      return;
    }
    window.location.href = cfg.lentaUrl || "/lenta/";
  }

  function setOverlayVisible(open) {
    if (!overlayEl) {
      return;
    }
    overlayOpen = open;
    overlayEl.hidden = !open;
    overlayEl.setAttribute("aria-hidden", open ? "false" : "true");
    document.body.classList.toggle("rl-quiz-overlay-open", open);
    if (open) {
      overlayReturnFocus = document.activeElement;
      if (overlayCloseBtn) {
        overlayCloseBtn.focus();
      }
      return;
    }
    if (overlayReturnFocus && typeof overlayReturnFocus.focus === "function") {
      overlayReturnFocus.focus();
    }
    overlayReturnFocus = null;
  }

  function closeOverlay(fromHistory) {
    if (!overlayMode || !overlayOpen) {
      return;
    }
    if (retakeMode && retakeBackup && !pendingImportPromise) {
      retakeMode = false;
      writeCompleted(retakeBackup);
      retakeBackup = null;
    } else {
      retakeMode = false;
    }
    try {
      localStorage.removeItem(SESSION_KEY);
    } catch (err) {
      /* ignore */
    }
    session = { history: [], started_at: null };
    setOverlayVisible(false);
    setOverlayPhase(null);
    if (fromHistory) {
      overlayDidPush = false;
      return;
    }
    if (overlayDidPush) {
      overlayDidPush = false;
      history.back();
      return;
    }
    if (location.hash === "#quiz") {
      history.replaceState(null, "", location.pathname + location.search);
    }
    flushFeedRefreshAfterImport();
  }

  function startRetake() {
    var completed = readCompleted();
    retakeBackup = completed || null;
    retakeMode = true;
    try {
      localStorage.removeItem(SESSION_KEY);
    } catch (err) {
      /* ignore */
    }
    resetPrefetch();
    if (widgetBox) {
      widgetBox.innerHTML = "";
    }
    if (resultEl) {
      resultEl.hidden = true;
      resultEl.classList.remove("rl-quiz__result--compact");
    }
    if (stageEl) {
      stageEl.hidden = false;
    }
    if (retakeCompletedEl) {
      retakeCompletedEl.hidden = true;
    }
    showStageScreen("intro");
    revealIntroAnimation();
    prefetchQuizStart();
  }

  function openOverlay(options) {
    if (!overlayMode || !overlayEl) {
      window.location.href = cfg.lentaUrl || "/lenta/";
      return;
    }
    if (overlayOpen) {
      return;
    }
    options = options || {};

    if (!options.retake) {
      discardIncompleteQuizSession();
      var completed = readCompleted();
      if (completed) {
        setOverlayVisible(true);
        setOverlayPhase("result");
        if (location.hash !== "#quiz") {
          history.pushState({ rlQuizOverlay: true }, "", "#quiz");
          overlayDidPush = true;
        } else {
          overlayDidPush = false;
        }
        profile = completed.profile || null;
        session = { history: completed.history || [], started_at: null };
        showResult(profile, true);
        return;
      }
    }

    setOverlayVisible(true);
    setOverlayPhase("intro");
    if (location.hash !== "#quiz") {
      history.pushState({ rlQuizOverlay: true }, "", "#quiz");
      overlayDidPush = true;
    } else {
      overlayDidPush = false;
    }
    if (options.autoStart !== false && cfg.overlayAutoStart) {
      beginQuizPlay();
    } else {
      showStageScreen("intro");
      revealIntroAnimation();
      prefetchQuizStart();
    }
  }

  function bindOverlayClose(el) {
    if (!el) {
      return;
    }
    el.addEventListener("click", function (event) {
      if (el.classList.contains("js-quiz-overlay-close")) {
        event.preventDefault();
      }
      if (pendingImportPromise) {
        pendingImportPromise.finally(function () {
          closeOverlay(false);
        });
        return;
      }
      closeOverlay(false);
    });
  }

  function completeTelegramAuth(user) {
    if (authCompleted) {
      return;
    }
    setLoginState("info", "Проверяем Telegram…");
    fetch(cfg.restAuth, {
      method: "POST",
      credentials: "same-origin",
      headers: Object.assign({ "Content-Type": "application/json" }, authHeaders()),
      body: JSON.stringify(user),
    })
      .then(function (res) {
        return res
          .json()
          .catch(function () {
            return {};
          })
          .then(function (data) {
            if (!res.ok) {
              throw new Error((data && data.detail) || "auth failed");
            }
            return data;
          });
      })
      .then(function (data) {
        if (!data.access_token) {
          throw new Error("no token");
        }
        authCompleted = true;
        setToken(data.access_token);
        setLoginState("info", "Импортируем профиль…");
        return importQuizTags().then(function () {
          setLoginState("ok", overlayMode ? "Готово!" : "Готово! Открываем ленту…");
          afterQuizAuthSuccess();
        });
      })
      .catch(function (err) {
        setLoginState(
          "error",
          "Не удалось войти. " + (err && err.message ? err.message : "Попробуй снова.")
        );
      });
  }

  window.onTelegramAuth = function (user) {
    completeTelegramAuth(user);
  };

  function mountTelegramWidget() {
    if (!widgetBox || !cfg.tgBotUsername) {
      return;
    }
    if (widgetBox.querySelector("iframe, script")) {
      return;
    }
    var script = document.createElement("script");
    script.async = true;
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.setAttribute("data-telegram-login", cfg.tgBotUsername);
    script.setAttribute("data-size", "large");
    script.setAttribute("data-onauth", "onTelegramAuth(user)");
    script.setAttribute("data-request-access", "write");
    widgetBox.appendChild(script);
  }

  function onDecision(liked) {
    if (animating || !currentCard) {
      return;
    }
    animating = true;
    setCardActionsDisabled(true);
    cardEl.classList.remove("is-enter", "is-visible", "is-exit-right", "is-exit-left");
    void cardEl.offsetWidth;
    var exitClass = liked ? "is-exit-right" : "is-exit-left";
    cardEl.classList.add(exitClass);

    var histEntry = {
      card_id: String(currentCard.card_id),
      liked: liked,
      tags: currentCard.lead_tags || [],
      complexity: currentCard.complexity,
      category: currentCard.category || "",
    };

    var exitDone = false;
    function finishExit() {
      if (exitDone) {
        return;
      }
      exitDone = true;
      session.history.push(histEntry);
      writeSession(session);
      currentCard = null;
      requestNext().catch(function () {
        cardEl.classList.remove("is-exit-right", "is-exit-left");
        cardEl.classList.add("is-visible");
        animating = false;
        setCardActionsDisabled(false);
        showError("Не удалось загрузить следующую карточку. Обнови страницу.");
      });
    }

    function onExitEnd(event) {
      if (event.target !== cardEl) {
        return;
      }
      if (event.propertyName !== "transform" && event.propertyName !== "opacity") {
        return;
      }
      cardEl.removeEventListener("transitionend", onExitEnd);
      finishExit();
    }

    cardEl.addEventListener("transitionend", onExitEnd);
    window.setTimeout(function () {
      cardEl.removeEventListener("transitionend", onExitEnd);
      finishExit();
    }, ANIM_MS);
  }

  function finishEarly() {
    if (session.history.length < MIN_EARLY_CTA || animating) {
      return;
    }
    profile = buildLocalProfile(session.history);
    showResult(profile);
  }

  function beginQuizPlay() {
    if (!cfg.restQuizStart) {
      showError("Квиз не настроен на сайте.");
      return;
    }
    session = { history: [], started_at: new Date().toISOString() };
    try {
      localStorage.removeItem(SESSION_KEY);
    } catch (err) {
      /* ignore */
    }

    if (prefetchData) {
      showStageScreen("play");
      handleQuizResponse(prefetchData);
      resetPrefetch();
      return;
    }

    showStageScreen("loading");

    var waitForStart = prefetchPromise || fetchQuizStartApi();
    waitForStart
      .then(function (data) {
        if (!data) {
          throw new Error("empty quiz start");
        }
        showStageScreen("play");
        handleQuizResponse(data);
      })
      .catch(function () {
        showError("Не удалось загрузить карточки. Обнови страницу.");
      })
      .finally(function () {
        resetPrefetch();
      });
  }

  function restartQuizDuringPlay() {
    if (animating) {
      return;
    }
    clearSession();
    resetPrefetch();
    currentCard = null;
    animating = false;
    setCardActionsDisabled(false);
    if (progressFillEl) {
      progressFillEl.style.width = "10%";
    }
    if (earlyCtaEl) {
      earlyCtaEl.hidden = true;
    }
    beginQuizPlay();
  }

  function restartQuiz() {
    clearSession();
    resetPrefetch();
    if (widgetBox) {
      widgetBox.innerHTML = "";
    }
    if (resultEl) {
      resultEl.hidden = true;
      resultEl.classList.remove("rl-quiz__result--compact");
    }
    if (stageEl) {
      stageEl.hidden = false;
    }
    showStageScreen("intro");
    revealIntroAnimation();
    prefetchQuizStart();
  }

  if (introStartBtn) {
    introStartBtn.addEventListener("click", function () {
      beginQuizPlay();
    });
  }
  if (likeBtn) {
    likeBtn.addEventListener("click", function () {
      onDecision(true);
    });
  }
  if (nopeBtn) {
    nopeBtn.addEventListener("click", function () {
      onDecision(false);
    });
  }
  if (earlyBtn) {
    earlyBtn.addEventListener("click", function () {
      finishEarly();
    });
  }
  if (restartPlayBtn) {
    restartPlayBtn.addEventListener("click", function () {
      restartQuizDuringPlay();
    });
  }
  if (retryEl) {
    retryEl.addEventListener("click", function () {
      restartQuiz();
    });
  }
  if (retakeCompletedEl) {
    retakeCompletedEl.addEventListener("click", function () {
      if (overlayMode) {
        startRetake();
      } else {
        clearCompleted();
        restartQuiz();
      }
    });
  }
  if (errorRetryBtn) {
    errorRetryBtn.addEventListener("click", function () {
      resetPrefetch();
      beginQuizPlay();
    });
  }
  if (cabinetCtaEl) {
    cabinetCtaEl.addEventListener("click", function (event) {
      if (primaryCtaPending) {
        event.preventDefault();
        return;
      }
      if (isAnon()) {
        if (!overlayMode) {
          return;
        }
        var loginUrl = cfg.loginUrl || cfg.cabinetUrl || cabinetCtaEl.getAttribute("href");
        if (!loginUrl) {
          return;
        }
        event.preventDefault();
        overlayDidPush = false;
        setOverlayVisible(false);
        window.location.href = loginUrl;
        return;
      }
      if (!overlayMode) {
        return;
      }
      event.preventDefault();
      if (pendingImportPromise) {
        pendingImportPromise.finally(function () {
          closeOverlay(false);
        });
        return;
      }
      closeOverlay(false);
    });
  }

  if (overlayMode) {
    bindOverlayClose(overlayBackdropEl);
    bindOverlayClose(overlayCloseBtn);
    root.querySelectorAll(".js-quiz-overlay-close").forEach(bindOverlayClose);
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && overlayOpen) {
        event.preventDefault();
        closeOverlay(false);
      }
    });
    window.addEventListener("popstate", function () {
      if (overlayOpen) {
        closeOverlay(true);
      }
    });
    if (location.hash === "#quiz") {
      var pendingRetake = false;
      try {
        pendingRetake = sessionStorage.getItem("rawlead_quiz_retake") === "1";
        if (pendingRetake) {
          sessionStorage.removeItem("rawlead_quiz_retake");
        }
      } catch (err) {
        /* ignore */
      }
      if (pendingRetake) {
        setOverlayVisible(true);
        setOverlayPhase("intro");
        startRetake();
      } else {
        openOverlay({ autoStart: false });
      }
    }
  }

  function importCompletedQuizIfPresent() {
    if (isAnon()) {
      return Promise.resolve(false);
    }
    if (!profile) {
      var completed = readCompleted();
      if (completed && completed.profile) {
        profile = completed.profile;
      }
    }
    if (!profile) {
      return Promise.resolve(false);
    }
    try {
      if (sessionStorage.getItem(RESTORE_IMPORT_KEY)) {
        return Promise.resolve(true);
      }
    } catch (err) {
      /* ignore */
    }
    var payload = tagsImportPayload();
    var hasTags = Object.keys(payload.tags).length > 0;
    var hasNiches = payload.niches && payload.niches.length > 0;
    var hasCx = payload.cx_pref != null;
    if (!hasTags && !hasNiches && !hasCx) {
      return Promise.resolve(false);
    }
    return importQuizTags()
      .then(function () {
        try {
          sessionStorage.setItem(RESTORE_IMPORT_KEY, "1");
        } catch (err) {
          /* ignore */
        }
        return true;
      })
      .catch(function () {
        return false;
      });
  }

  window.rawleadImportCompletedQuiz = importCompletedQuizIfPresent;

  window.rawleadQuizApp = {
    open: openOverlay,
    close: closeOverlay,
    start: beginQuizPlay,
    retake: startRetake,
  };

  session = { history: [], started_at: null };

  if (overlayMode) {
    prefetchQuizStart();
  } else if (introEl && (!resultEl || resultEl.hidden)) {
    discardIncompleteQuizSession();
    var _initCompleted = readCompleted();
    if (_initCompleted) {
      profile = _initCompleted.profile || null;
      session = { history: _initCompleted.history || [], started_at: null };
      showResult(profile, true);
    } else {
      showStageScreen("intro");
      revealIntroAnimation();
      prefetchQuizStart();
    }
  }
})();
