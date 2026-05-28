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

  var TOKEN_KEY = "rawlead_access_token";

  var loginEl = document.getElementById("rl-cabinet-login");

  var appEl = document.getElementById("rl-cabinet-app");

  var loginHintEl = document.getElementById("rl-cabinet-login-hint");
  var loginStateEl = document.getElementById("rl-cabinet-login-state");
  var fallbackEl = document.getElementById("rl-cabinet-login-fallback");
  var fallbackLinkEl = document.getElementById("rl-cabinet-fallback-link");
  var widgetTimeoutMs = 3000;
  var hasWidgetAuthCompleted = false;

  function setLoginState(level, text) {
    if (!loginStateEl) {
      return;
    }
    loginStateEl.classList.remove(
      "rl-cabinet-login__state--info",
      "rl-cabinet-login__state--warn",
      "rl-cabinet-login__state--error",
      "rl-cabinet-login__state--ok"
    );
    loginStateEl.classList.add("rl-cabinet-login__state--" + (level || "info"));
    loginStateEl.textContent = text || "";
  }

  function showFallback(show, reasonText) {
    if (fallbackEl) {
      fallbackEl.hidden = !show;
    }
    if (!fallbackLinkEl) {
      return;
    }
    if (cfg.tgBotId || cfg.tgLoginFallbackUrl) {
      fallbackLinkEl.href = cfg.tgLoginFallbackUrl || "#";
      fallbackLinkEl.classList.remove("is-disabled");
      fallbackLinkEl.setAttribute("aria-disabled", "false");
      if (show && reasonText) {
        setLoginState("warn", reasonText);
      }
      return;
    }
    fallbackLinkEl.href = "#";
    fallbackLinkEl.classList.add("is-disabled");
    fallbackLinkEl.setAttribute("aria-disabled", "true");
    if (show) {
      setLoginState(
        "error",
        "Fallback URL не задан. Добавьте RAWLEAD_TG_LOGIN_FALLBACK_URL в wp-config.php."
      );
    }
  }

  function authPayloadFromAny(raw) {
    if (!raw) {
      return null;
    }
    if (typeof raw === "object" && raw.id && raw.auth_date && raw.hash) {
      return raw;
    }
    if (typeof raw !== "string") {
      return null;
    }
    var s = raw.trim();
    if (!s) {
      return null;
    }
    try {
      var obj = JSON.parse(s);
      if (obj && obj.id && obj.auth_date && obj.hash) {
        return obj;
      }
    } catch (e) {
      // keep trying other formats
    }
    var query = s;
    if (query.indexOf("?") >= 0) {
      query = query.split("?")[1];
    }
    if (query.indexOf("#") >= 0) {
      query = query.split("#")[1];
    }
    var p = parseAuthFromParams(new URLSearchParams(query));
    return p || null;
  }

  function normalizeTelegramAuthPayload(raw) {
    if (!raw || typeof raw !== "object") {
      return null;
    }
    var payload = {
      id: parseInt(raw.id, 10),
      first_name: raw.first_name || "",
      last_name: raw.last_name || "",
      username: raw.username || "",
      photo_url: raw.photo_url || "",
      auth_date: parseInt(raw.auth_date, 10),
      hash: raw.hash || "",
    };
    if (!payload.id || !payload.auth_date || !payload.hash) {
      return null;
    }
    return payload;
  }

  window.addEventListener("message", function (event) {
    var origin = String(event.origin || "");
    if (origin.indexOf("telegram.org") < 0 && origin.indexOf("oauth.telegram.org") < 0) {
      return;
    }
    var payload = authPayloadFromAny(event.data);
    if (!payload) {
      return;
    }
    payload = normalizeTelegramAuthPayload(payload);
    if (!payload) {
      return;
    }
    setLoginState("info", "Получили auth из Telegram popup. Проверяем...");
    completeTelegramAuth(payload);
  });

  if (fallbackLinkEl) {
    fallbackLinkEl.addEventListener("click", function (e) {
      if (!cfg.tgBotId && !cfg.tgLoginFallbackUrl) {
        return;
      }
      e.preventDefault();
      if (window.Telegram && window.Telegram.Login && cfg.tgBotId) {
        setLoginState("info", "Открываем Telegram Login popup...");
        window.Telegram.Login.auth(
          { bot_id: Number(cfg.tgBotId), request_access: "write" },
          function (data) {
            if (!data) {
              setLoginState("error", "Telegram popup закрыт без авторизации.");
              return;
            }
            var payload = data;
            if (data.user && data.auth_date && data.hash) {
              payload = Object.assign({}, data.user, {
                auth_date: data.auth_date,
                hash: data.hash,
              });
            }
            payload = normalizeTelegramAuthPayload(payload);
            if (!payload) {
              setLoginState("error", "Telegram вернул неполные auth-данные.");
              return;
            }
            setLoginState("info", "Получили auth из popup. Проверяем...");
            completeTelegramAuth(payload);
          }
        );
        return;
      }
      if (cfg.tgLoginFallbackUrl) {
        setLoginState("info", "Переходим в Telegram fallback и ждём возврат в /cabinet/...");
        window.location.href = cfg.tgLoginFallbackUrl;
        return;
      }
      setLoginState("error", "Telegram popup API недоступен.");
    });
  }

  function getToken() {

    return localStorage.getItem(TOKEN_KEY) || "";

  }

  function setToken(token) {

    if (token) {

      localStorage.setItem(TOKEN_KEY, token);

    } else {

      localStorage.removeItem(TOKEN_KEY);

    }

  }

  function authHeaders() {

    var h = { "X-WP-Nonce": cfg.nonce || "" };

    var t = getToken();

    if (t) {

      h.Authorization = "Bearer " + t;

    }

    return h;

  }

  function setGate(loggedIn) {

    if (root) {

      root.classList.toggle("rl-cabinet--logged-in", loggedIn);

      root.classList.toggle("rl-cabinet--gate", !loggedIn);

    }

  }

  function showLogin() {

    setGate(false);

    if (appEl) {

      appEl.hidden = true;

    }

    if (loginEl) {

      loginEl.hidden = false;

    }

  }

  function showApp() {

    setGate(true);

    if (loginEl) {

      loginEl.hidden = true;

    }

    if (appEl) {

      appEl.hidden = false;

    }

  }

  function mountTelegramWidget() {

    var box = document.getElementById("rl-telegram-login-widget");

    if (!box) {

      return;

    }

    box.innerHTML = "";
    showFallback(!!cfg.tgLoginFallbackUrl);
    setLoginState("info", "Загружаем Telegram Widget...");

    if (location.hostname !== "127.0.0.1") {

      if (loginHintEl) {

        loginHintEl.hidden = false;

        loginHintEl.textContent =

          "Кнопка Telegram только на http://127.0.0.1:" +

          (cfg.localPort || "10007") +

          "/cabinet/ — нажмите ссылку ниже.";

      }

      return;

    }

    if (!cfg.tgBotUsername) {

      if (loginHintEl) {

        loginHintEl.hidden = false;

        loginHintEl.textContent =

          "Добавьте в wp-config.php: define('RAWLEAD_TG_BOT_USERNAME', 'rawlead_bot');";

      }

      return;

    }

    var script = document.createElement("script");

    script.async = true;

    script.src = "https://telegram.org/js/telegram-widget.js?22";

    script.setAttribute("data-telegram-login", cfg.tgBotUsername);

    script.setAttribute("data-size", "large");

    script.setAttribute("data-onauth", "onTelegramAuth(user)");

    script.setAttribute("data-request-access", "write");

    box.appendChild(script);

    setTimeout(function () {
      if (hasWidgetAuthCompleted) {
        return;
      }

      var hasWidget = box.querySelector("iframe, .telegram-login-button");

      if (!hasWidget && loginHintEl) {

        loginHintEl.hidden = false;

        loginHintEl.textContent =

          "Виджет Telegram не загрузился. Обновите страницу (Ctrl+F5), отключите блокировщик/anti-tracker и откройте /cabinet/ только на 127.0.0.1.";
        showFallback(true, "Widget не загрузился. Используйте fallback-вход в новом окне.");
      } else {
        setLoginState("ok", "Widget загружен. Подтвердите вход в Telegram.");
        showFallback(true);

      }

    }, widgetTimeoutMs);

  }

  function completeTelegramAuth(user) {
    setLoginState("info", "Проверяем Telegram auth...");

    fetch(cfg.restAuth, {

      method: "POST",

      credentials: "same-origin",

      headers: Object.assign({ "Content-Type": "application/json" }, authHeaders()),

      body: JSON.stringify(user),

    })

      .then(function (res) {
        return res.json().catch(function () {
          return {};
        }).then(function (data) {
          if (!res.ok) {
            var msg = "";
            if (data && typeof data.message === "string" && data.message) {
              msg = data.message;
            } else if (data && typeof data.detail === "string" && data.detail) {
              msg = data.detail;
            }
            throw new Error(msg || ("HTTP " + res.status));
          }
          return data;
        });

      })

      .then(function (data) {
        hasWidgetAuthCompleted = true;

        if (!data.access_token) {

          throw new Error("no token");

        }

        setLoginState("info", "Сохраняем access_token...");
        try {
          setToken(data.access_token);
        } catch (err) {
          throw new Error("token save failed");
        }
        setLoginState("ok", "Вход выполнен. Загружаем кабинет...");

        showApp();

        bootCabinet();

      })

      .catch(function (err) {

        if (loginHintEl) {

          loginHintEl.hidden = false;
          var msg = err && err.message ? err.message : "Попробуйте снова.";
          if (msg === "token save failed") {
            loginHintEl.textContent = "Не удалось сохранить access_token. Проверьте режим приватности браузера.";
            setLoginState("error", "Ошибка сохранения токена.");
          } else {
            loginHintEl.textContent = "Не удалось войти: " + msg;
            setLoginState("error", "Ошибка проверки Telegram auth.");
          }

        }
        showFallback(true, "Fallback доступен: откройте вход в новом окне.");

      });

  }

  window.onTelegramAuth = function (user) {
    completeTelegramAuth(user);
  };

  function parseAuthFromParams(params) {
    if (!params || !params.get("id") || !params.get("auth_date") || !params.get("hash")) {
      return null;
    }
    return {
      id: parseInt(params.get("id"), 10),
      first_name: params.get("first_name") || "",
      last_name: params.get("last_name") || "",
      username: params.get("username") || "",
      photo_url: params.get("photo_url") || "",
      auth_date: parseInt(params.get("auth_date"), 10),
      hash: params.get("hash") || "",
    };
  }

  function consumeDeepLinkAuth() {
    var queryPayload = parseAuthFromParams(new URLSearchParams(window.location.search || ""));
    var hashPayload = null;
    if (!queryPayload && window.location.hash) {
      var rawHash = window.location.hash.replace(/^#/, "");
      if (rawHash.indexOf("?") >= 0) {
        rawHash = rawHash.split("?")[1];
      }
      hashPayload = parseAuthFromParams(new URLSearchParams(rawHash));
    }
    var payload = queryPayload || hashPayload;
    if (!payload || !payload.id || !payload.auth_date || !payload.hash) {
      return false;
    }
    if (window.history && window.history.replaceState) {
      window.history.replaceState({}, document.title, window.location.pathname);
    }
    setLoginState("info", "Получили fallback auth. Проверяем...");
    completeTelegramAuth(payload);
    return true;
  }

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

    draftCategories: [],

    appliedCategories: [],

    loading: false,

    done: false,

    totalShown: 0,

    expandedId: null,

    tagsLoading: false,

    loadGeneration: 0,

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

    var tools = item.tools_required || [];

    if (tools.length) {

      html +=

        '<div class="rl-feed-card__section">' +

        '<h4 class="rl-feed-card__section-title">Инструменты</h4>' +

        '<ul class="rl-feed-card__tools">' +

        tools

          .map(function (tool) {

            return "<li>" + escapeHtml(tool) + "</li>";

          })

          .join("") +

        "</ul></div>";

    } else {

      html +=

        '<div class="rl-feed-card__section">' +

        '<h4 class="rl-feed-card__section-title">Инструменты</h4>' +

        '<p class="rl-feed-card__text rl-feed-card__muted">Список инструментов появится после premium-разбора.</p>' +

        "</div>";

    }

    var reply = (item.reply_draft || "").trim();

    if (reply) {

      html +=

        '<div class="rl-feed-card__section">' +

        '<h4 class="rl-feed-card__section-title">Черновик отклика</h4>' +

        '<p class="rl-feed-card__reply">' +

        escapeHtml(reply) +

        "</p></div>";

    } else {

      html +=

        '<div class="rl-feed-card__section">' +

        '<h4 class="rl-feed-card__section-title">Черновик отклика</h4>' +

        '<p class="rl-feed-card__text rl-feed-card__muted">Черновик отклика появится после premium-разбора.</p>' +

        "</div>";

    }

    html += '<div class="rl-feed-card__actions">';

    if (item.url) {

      html +=

        '<a class="rl-btn rl-btn--ghost rl-feed-card__link" href="' +

        escapeHtml(item.url) +

        '" target="_blank" rel="noopener" onclick="event.stopPropagation()">Открыть оригинал ↗</a>';

    }

    html += "</div>";

    return html;

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

      headers: Object.assign(

        { "Content-Type": "application/json" },

        authHeaders()

      ),

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

    return fetch(cfg.restTags, { credentials: "same-origin", headers: authHeaders() })

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

      '<div class="rl-feed-card__head-start">' +

      '<span class="rl-feed-card__source rl-feed-card__source--' +

      src.cls +

      '">' +

      escapeHtml(src.label) +

      "</span>" +

      hotBadgeHtml(item) +

      "</div>" +

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

      "<span>Совместимость " +

      rank +

      "%</span>" +

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



  function readFilters() {

    if (!sidebar) {

      return;

    }

    var src = sidebar.querySelector('input[name="source"]:checked');

    var score = sidebar.querySelector('input[name="min_score"]:checked');

    state.source = src ? src.value : "";

    state.appliedCategories = readCategoriesFrom();

    state.minScore = score ? parseInt(score.value, 10) || 0 : 0;

    var dirty =

      state.source !== "" || state.appliedCategories.length > 0 || state.minScore !== 0;

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

    state.loadGeneration += 1;

    state.offset = 0;

    state.done = false;

    state.totalShown = 0;

    state.expandedId = null;

    state.loading = false;

    if (noMatchEl) {

      noMatchEl.hidden = true;

    }

    if (listEl) {

      listEl.innerHTML = skeletonHtml(2);

      listEl.hidden = false;

    }

    if (endEl) {

      endEl.hidden = true;

    }

    loadMore(true);

  }



  function loadMore(replace) {

    if (state.done || state.tags.length === 0) {

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

      min_score: state.minScore,

    };

    if (state.appliedCategories.length) {

      params.category = state.appliedCategories.join(",");

    }

    var url = apiUrl(cfg.restFeed, params);



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

        if (listEl) {

          listEl.querySelectorAll(".rl-feed-skeleton").forEach(function (el) {

            el.remove();

          });

        }

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

              '<p class="rl-feed-empty">В этой нише пока нет заказов — попробуйте «Все»</p>';

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

          document.querySelectorAll("#rl-cabinet-list .rl-lead-card .rl-match__fill").forEach(function (el) {

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

        showError("Не удалось загрузить");

      })

      .finally(function () {

        if (gen === state.loadGeneration) {

          state.loading = false;

        }

      });

  }



  function bindCards() {

    if (!listEl) {

      return;

    }

    listEl.querySelectorAll(".rl-lead-card").forEach(function (card) {

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



  function bindCategoryFilters(root) {

    if (!root) {

      return;

    }

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

        state.draftCategories = readCategoriesFrom(root);

        syncChips();

      });

    });

  }



  if (sidebar) {

    bindCategoryFilters(sidebar);

    sidebar.addEventListener("change", function (e) {

      var name = e.target && e.target.getAttribute("name");

      if (name === "category") {

        state.appliedCategories = readCategoriesFrom();

        syncChips();

        readFilters();

        resetAndLoad();

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

        sidebar.querySelector('input[name="min_score"][value="0"]').checked = true;

        state.draftCategories = [];

        state.appliedCategories = [];

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

  var changeSkills = document.getElementById("rl-cabinet-change-skills");

  if (changeSkills) {

    changeSkills.addEventListener("click", promptAddTag);

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



  function bootCabinet() {

    syncChips();

    state.draftCategories = readCategoriesFrom();

    state.appliedCategories = state.draftCategories.slice();

    readFilters();

    loadTags()

      .then(function () {

        resetAndLoad();

      })

      .catch(function () {

        showError("Не удалось загрузить теги.");

      });

  }

  function startLoggedOut() {

    setToken("");

    showLogin();

    if (consumeDeepLinkAuth()) {
      showFallback(true);
      return;
    }

    mountTelegramWidget();

  }

  function startLoggedIn() {

    showApp();

    bootCabinet();

  }

  if (!getToken()) {

    startLoggedOut();

    return;

  }

  fetch(cfg.restTags, { credentials: "same-origin", headers: authHeaders() })

    .then(function (res) {

      if (res.ok) {

        startLoggedIn();

        return;

      }

      startLoggedOut();

    })

    .catch(function () {

      startLoggedOut();

    });

})();

