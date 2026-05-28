/**

 * RawLead /cabinet — навыки, персональная лента (final_rank), infinite scroll.

 */

(function () {

  "use strict";

  console.log(
    "%c▲ RawLead Architecture by Rode51 ▲",
    "color:#00ff00;font-size:16px;font-weight:bold;"
  );



  var root = document.querySelector('[data-rl-app="cabinet"]');

  if (!root || !window.rawleadCabinet) {

    return;

  }



  var cfg = window.rawleadCabinet;

  var TOKEN_KEY = "rawlead_access_token";
  var SORT_KEY = "rawlead_cabinet_sort";
  var USER_META_KEY = "rawlead_user_meta";
  var GUEST_SKILLS_KEYS = ["rawlead_lenta_skills", "rawlead_guest_skills"];
  var MAX_USER_TAGS = 6;
  var TIER_A_BY_NICHE = {
    dev: [
      "python",
      "javascript",
      "php",
      "wordpress_dev",
      "telegram_bot_dev",
      "api_integration",
    ],
    design: [
      "figma",
      "ui_ux",
      "web_design",
      "logo_design",
      "brand_identity",
      "banner_design",
    ],
    marketing: [
      "smm",
      "target_ads",
      "yandex_direct",
      "google_ads",
      "seo",
      "email_marketing",
    ],
    text: [
      "copywriting",
      "seo_copywriting",
      "article_writing",
      "translation",
      "technical_writing",
      "editing_proofreading",
    ],
  };

  var loginEl = document.getElementById("rl-cabinet-login");

  var appEl = document.getElementById("rl-cabinet-app");

  var loginHintEl = document.getElementById("rl-cabinet-login-hint");
  var loginStateEl = document.getElementById("rl-cabinet-login-state");
  var fallbackEl = document.getElementById("rl-cabinet-login-fallback");
  var fallbackLinkEl = document.getElementById("rl-cabinet-fallback-link");
  var widgetTimeoutMs = 3000;
  var popupTimeoutMs = 8000;
  var widgetLoadFailed = false;
  var popupTimedOut = false;
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

  function redirectTgLoginFallback() {
    if (!cfg.tgLoginFallbackUrl) {
      setLoginState(
        "error",
        "Fallback URL не задан. Добавьте RAWLEAD_TG_BOT_ID в wp-config.php."
      );
      return;
    }
    setLoginState("info", "Переходим в Telegram для входа...");
    window.location.href = cfg.tgLoginFallbackUrl;
  }

  if (fallbackLinkEl) {
    fallbackLinkEl.addEventListener("click", function (e) {
      if (!cfg.tgBotId && !cfg.tgLoginFallbackUrl) {
        return;
      }
      e.preventDefault();
      if (widgetLoadFailed || popupTimedOut || !cfg.tgBotId) {
        redirectTgLoginFallback();
        return;
      }
      if (window.Telegram && window.Telegram.Login) {
        setLoginState("info", "Открываем Telegram Login popup...");
        var popupDone = false;
        var popupTimer = setTimeout(function () {
          if (popupDone) {
            return;
          }
          popupTimedOut = true;
          setLoginState(
            "warn",
            "Не удалось открыть Telegram. Из РФ включите VPN или нажмите кнопку снова для redirect."
          );
        }, popupTimeoutMs);
        window.Telegram.Login.auth(
          { bot_id: Number(cfg.tgBotId), request_access: "write" },
          function (data) {
            popupDone = true;
            clearTimeout(popupTimer);
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
      redirectTgLoginFallback();
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

    try {
      window.dispatchEvent(new Event("rawlead-auth-changed"));
    } catch (e) {
      /* IE11 */
    }

  }

  function readUserMeta() {

    try {

      var raw = localStorage.getItem(USER_META_KEY);

      if (!raw) {

        return null;

      }

      return JSON.parse(raw);

    } catch (e) {

      return null;

    }

  }

  function saveUserMeta(data) {

    if (!data) {

      return;

    }

    var username = (data.username || "").trim();

    var firstName = (data.first_name || "").trim();

    var photoUrl = (data.photo_url || "").trim();

    var display = username ? "@" + username : firstName || "Telegram";

    try {

      localStorage.setItem(
        USER_META_KEY,
        JSON.stringify({
          username: username,
          first_name: firstName,
          photo_url: photoUrl,
          display: display,
        })
      );

    } catch (e) {

      /* private mode */

    }

    if (window.rawleadSyncHeader) {

      window.rawleadSyncHeader();

    }

  }

  function clearUserMeta() {

    try {

      localStorage.removeItem(USER_META_KEY);

    } catch (e) {

      /* private mode */

    }

    if (window.rawleadSyncHeader) {

      window.rawleadSyncHeader();

    }

  }

  function readGuestSkillTags() {

    var tags = [];

    var i;

    var key;

    var raw;

    var parsed;

    var j;

    for (i = 0; i < GUEST_SKILLS_KEYS.length; i++) {

      key = GUEST_SKILLS_KEYS[i];

      try {

        raw = localStorage.getItem(key);

        if (!raw) {

          continue;

        }

        parsed = JSON.parse(raw);

        if (!Array.isArray(parsed)) {

          continue;

        }

        for (j = 0; j < parsed.length; j++) {

          if (typeof parsed[j] === "string" && parsed[j] && tags.indexOf(parsed[j]) < 0) {

            tags.push(parsed[j]);

          }

        }

      } catch (e) {

        /* skip bad key */

      }

    }

    return tags;

  }

  function clearGuestSkillKeys() {

    var i;

    for (i = 0; i < GUEST_SKILLS_KEYS.length; i++) {

      try {

        localStorage.removeItem(GUEST_SKILLS_KEYS[i]);

      } catch (e) {

        /* private mode */

      }

    }

  }

  function mergeGuestSkillsAfterAuth() {

    var guest = readGuestSkillTags();

    if (!guest.length) {

      return Promise.resolve();

    }

    return fetch(cfg.restTags, { credentials: "same-origin", headers: authHeaders() })

      .then(function (res) {

        if (!res.ok) {

          throw new Error("HTTP " + res.status);

        }

        return res.json();

      })

      .then(function (data) {

        var server = data.tags || [];

        var merged = server.slice();

        var i;

        for (i = 0; i < guest.length; i++) {

          if (merged.indexOf(guest[i]) < 0) {

            merged.push(guest[i]);

          }

        }

        if (merged.length === server.length) {

          clearGuestSkillKeys();

          return merged;

        }

        return fetch(cfg.restTags, {

          method: "PUT",

          credentials: "same-origin",

          headers: Object.assign(

            { "Content-Type": "application/json" },

            authHeaders()

          ),

          body: JSON.stringify({ tags: merged }),

        }).then(function (res) {

          if (!res.ok) {

            throw new Error("HTTP " + res.status);

          }

          clearGuestSkillKeys();

          return res.json().then(function (putData) {

            return putData.tags || merged;

          });

        });

      })

      .catch(function () {

        /* keep guest keys if merge failed */

        return null;

      });

  }

  var userBarEl = document.getElementById("rl-cabinet-user");
  var userNameEl = document.getElementById("rl-cabinet-user-name");
  var userAvatarEl = document.getElementById("rl-cabinet-user-avatar");
  var logoutBtn = document.getElementById("rl-cabinet-logout");
  var subEl = document.getElementById("rl-cabinet-sub");
  var subBadgeEl = document.getElementById("rl-cabinet-sub-badge");
  var subPlanEl = document.getElementById("rl-cabinet-sub-plan");
  var subDetailEl = document.getElementById("rl-cabinet-sub-detail");
  var subPayEl = document.getElementById("rl-cabinet-sub-pay");
  var subPauseEl = document.getElementById("rl-cabinet-sub-pause");
  var subResumeEl = document.getElementById("rl-cabinet-sub-resume");
  var subNoteEl = document.getElementById("rl-cabinet-sub-note");
  var subscriptionState = null;

  var notifEl = document.getElementById("rl-cabinet-notif");
  var notifThresholdEl = document.getElementById("rl-cabinet-notif-threshold");
  var notifEnabledEl = document.getElementById("rl-cabinet-notif-enabled");
  var notifStatusEl = document.getElementById("rl-cabinet-notif-status");

  function renderUserBar() {

    if (!userBarEl) {

      return;

    }

    var meta = readUserMeta();

    if (!meta) {

      userBarEl.hidden = true;

      return;

    }

    userBarEl.hidden = false;

    if (userNameEl) {

      userNameEl.textContent = meta.display || meta.username || "Telegram";

    }

    if (userAvatarEl) {

      if (meta.photo_url) {

        userAvatarEl.src = meta.photo_url;

        userAvatarEl.hidden = false;

      } else {

        userAvatarEl.hidden = true;

        userAvatarEl.removeAttribute("src");

      }

    }

  }

  function formatSubDate(iso) {
    if (!iso) {
      return "";
    }
    try {
      return new Date(iso).toLocaleDateString("ru-RU", {
        day: "numeric",
        month: "long",
        year: "numeric",
      });
    } catch (e) {
      return iso;
    }
  }

  function subscriptionStatusLabel(status) {
    var map = {
      beta: "Beta",
      free: "Бесплатно",
      active: "Активна",
      paused: "Пауза",
      expired: "Истекла",
    };
    return map[status] || status || "—";
  }

  function renderSubscription(data) {
    if (!subEl) {
      return;
    }
    subscriptionState = data || null;
    if (!data) {
      subEl.hidden = true;
      return;
    }
    subEl.hidden = false;
    var status = data.status || "free";
    if (subBadgeEl) {
      subBadgeEl.textContent = subscriptionStatusLabel(status);
      subBadgeEl.className =
        "rl-cabinet-sub__badge rl-cabinet-sub__badge--" + status;
    }
    if (subPlanEl) {
      subPlanEl.textContent = data.plan_label || "ИИ-агент";
    }
    if (subDetailEl) {
      var detail = "";
      if (status === "paused" && data.paused_until) {
        detail = "На паузе до " + formatSubDate(data.paused_until);
      } else if (status === "active" && data.active_until) {
        detail = "Активна до " + formatSubDate(data.active_until);
      } else if (status === "beta") {
        detail = "Полный доступ в режиме beta — оплата пока не требуется";
      } else if (status === "free") {
        detail = "Лента с задержкой 15 мин. Stars — мгновенный доступ и «Написать отклик» на ленте.";
      } else if (status === "expired") {
        detail = "Подписка истекла — продлите через Telegram Stars";
      }
      subDetailEl.textContent = detail;
    }
    if (subPayEl) {
      if (data.stars_available) {
        subPayEl.href = cfg.botPayUrl || "https://t.me/rawlead_bot?start=pay";
        subPayEl.setAttribute("target", "_blank");
        subPayEl.setAttribute("rel", "noopener");
        subPayEl.removeAttribute("aria-disabled");
        subPayEl.classList.remove("is-disabled");
        subPayEl.textContent = "Оплатить Stars";
      } else {
        subPayEl.href = cfg.pricingUrl || subPayEl.getAttribute("href") || "#";
        subPayEl.removeAttribute("target");
        subPayEl.setAttribute("aria-disabled", "true");
        subPayEl.classList.add("is-disabled");
        subPayEl.textContent = "Оплатить Stars — скоро";
      }
    }
    if (subPauseEl) {
      subPauseEl.hidden = !data.can_pause;
      subPauseEl.disabled = !data.can_pause;
    }
    if (subResumeEl) {
      subResumeEl.hidden = status !== "paused";
    }
    if (subNoteEl) {
      if (status === "active" || status === "paused") {
        subNoteEl.textContent =
          "Пауза без штрафов — доступ к платным функциям приостановится до даты возобновления.";
      } else if (data.stars_available) {
        subNoteEl.textContent =
          "Оплата через Telegram Stars — мгновенная лента, «Написать отклик» и push match в боте.";
      } else {
        subNoteEl.textContent =
          "Сейчас лента и кабинет бесплатны в режиме beta. Оплата через Telegram Stars подключится в следующем релизе.";
      }
    }
  }

  function loadSubscription() {
    if (!cfg.restSubscription || !getToken()) {
      renderSubscription(null);
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
        renderSubscription(data);
        return data;
      })
      .catch(function () {
        renderSubscription(null);
        return null;
      });
  }

  function postSubscriptionPause(body) {
    if (!cfg.restSubscription) {
      return Promise.reject(new Error("no endpoint"));
    }
    return fetch(cfg.restSubscription, {
      method: "POST",
      credentials: "same-origin",
      headers: Object.assign({ "Content-Type": "application/json" }, authHeaders()),
      body: JSON.stringify(body || {}),
    }).then(function (res) {
      return res.json().then(function (data) {
        if (!res.ok) {
          throw new Error((data && data.message) || "pause failed");
        }
        renderSubscription(data);
        return data;
      });
    });
  }

  function renderNotificationSettings(data) {
    if (!notifEl) {
      return;
    }
    if (!data) {
      notifEl.hidden = true;
      return;
    }
    notifEl.hidden = false;
    if (notifThresholdEl) {
      notifThresholdEl.value = String(data.push_min_match || 60);
    }
    if (notifEnabledEl) {
      var enabled = data.push_enabled !== false;
      notifEnabledEl.setAttribute("aria-checked", enabled ? "true" : "false");
      notifEnabledEl.classList.toggle("is-on", enabled);
    }
  }

  function loadNotificationSettings() {
    if (!cfg.restNotificationSettings || !getToken()) {
      renderNotificationSettings(null);
      return Promise.resolve(null);
    }
    return fetch(cfg.restNotificationSettings, {
      credentials: "same-origin",
      headers: authHeaders(),
    })
      .then(function (res) {
        if (!res.ok) {
          throw new Error("notif-settings " + res.status);
        }
        return res.json();
      })
      .then(function (data) {
        renderNotificationSettings(data);
        return data;
      })
      .catch(function () {
        renderNotificationSettings(null);
        return null;
      });
  }

  function _notifSetStatus(msg, isErr) {
    if (!notifStatusEl) {
      return;
    }
    notifStatusEl.textContent = msg || "";
    notifStatusEl.className = "rl-cabinet-notif__status" + (isErr ? " rl-cabinet-notif__status--err" : "");
  }

  function patchNotificationSettings(payload) {
    if (!cfg.restNotificationSettings || !getToken()) {
      return Promise.reject(new Error("no endpoint"));
    }
    return fetch(cfg.restNotificationSettings, {
      method: "PATCH",
      credentials: "same-origin",
      headers: Object.assign({ "Content-Type": "application/json" }, authHeaders()),
      body: JSON.stringify(payload),
    }).then(function (res) {
      return res.json().then(function (data) {
        if (!res.ok) {
          throw new Error((data && data.detail) || "patch failed");
        }
        renderNotificationSettings(data);
        _notifSetStatus("Сохранено", false);
        setTimeout(function () { _notifSetStatus(""); }, 2000);
        return data;
      });
    }).catch(function (e) {
      _notifSetStatus(e.message || "Ошибка сохранения", true);
    });
  }

  if (notifThresholdEl) {
    notifThresholdEl.addEventListener("change", function () {
      var val = parseInt(notifThresholdEl.value, 10);
      if (!isNaN(val)) {
        patchNotificationSettings({ push_min_match: val });
      }
    });
  }

  if (notifEnabledEl) {
    notifEnabledEl.addEventListener("click", function () {
      var current = notifEnabledEl.getAttribute("aria-checked") === "true";
      patchNotificationSettings({ push_enabled: !current });
    });
  }

  if (subPauseEl) {
    subPauseEl.addEventListener("click", function () {
      subPauseEl.disabled = true;
      postSubscriptionPause({ days: 14 })
        .catch(function () {
          if (subPauseEl) {
            subPauseEl.disabled = false;
          }
        });
    });
  }

  if (subResumeEl) {
    subResumeEl.addEventListener("click", function () {
      subResumeEl.disabled = true;
      postSubscriptionPause({ resume: true })
        .catch(function () {
          if (subResumeEl) {
            subResumeEl.disabled = false;
          }
        })
        .finally(function () {
          if (subResumeEl) {
            subResumeEl.disabled = false;
          }
        });
    });
  }

  function logout() {

    setToken("");

    clearUserMeta();

    showLogin();

  }

  if (logoutBtn) {

    logoutBtn.addEventListener("click", logout);

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

    renderUserBar();

    loadSubscription();

    loadNotificationSettings();

  }

  function canMountTelegramWidget() {
    if (cfg.tgLoginDev) {
      return location.hostname === "127.0.0.1";
    }
    if (cfg.tgLoginWidgetAllowed === false) {
      return false;
    }
    return true;
  }

  function mountTelegramWidget() {

    var box = document.getElementById("rl-telegram-login-widget");

    if (!box) {

      return;

    }

    box.innerHTML = "";
    showFallback(!!cfg.tgLoginFallbackUrl);
    setLoginState("info", "Загружаем Telegram Widget...");

    if (!canMountTelegramWidget()) {

      if (loginHintEl) {

        loginHintEl.hidden = false;

        if (cfg.tgLoginDev) {
          loginHintEl.textContent =
            "Кнопка Telegram только на http://127.0.0.1:" +
            (cfg.localPort || "10007") +
            "/cabinet/ — нажмите ссылку ниже.";
        } else {
          loginHintEl.textContent =
            "Виджет Telegram доступен на rawlead.ru. Используйте fallback-вход ниже.";
        }

      }

      showFallback(true, "Widget недоступен на этом адресе. Используйте fallback-вход.");
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

      if (!hasWidget) {
        widgetLoadFailed = true;
      }

      if (!hasWidget && loginHintEl) {

        loginHintEl.hidden = false;

        loginHintEl.textContent =

          "Виджет Telegram не загрузился. Из РФ нужен VPN (Telegram заблокирован). Обновите страницу (Ctrl+F5) или используйте кнопку входа ниже.";
        showFallback(true, "Widget не загрузился. Нажмите «Войти через Telegram» — откроется redirect.");
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
        saveUserMeta(Object.assign({}, user, data));
        setLoginState("ok", "Вход выполнен. Загружаем кабинет...");

        return mergeGuestSkillsAfterAuth().then(function () {
          showApp();
          bootCabinet();
        });

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

  function parseTgAuthResultHash() {
    var rawHash = (window.location.hash || "").replace(/^#/, "");
    if (!rawHash || rawHash.indexOf("tgAuthResult=") !== 0) {
      return null;
    }
    try {
      var json = JSON.parse(decodeURIComponent(rawHash.slice("tgAuthResult=".length)));
      if (json && json.user) {
        return normalizeTelegramAuthPayload(
          Object.assign({}, json.user, {
            auth_date: json.auth_date,
            hash: json.hash,
          })
        );
      }
    } catch (e) {
      // fall through to query/hash parsers
    }
    return null;
  }

  function consumeDeepLinkAuth() {
    var payload = parseTgAuthResultHash();
    if (!payload) {
      payload = parseAuthFromParams(new URLSearchParams(window.location.search || ""));
    }
    var hashPayload = null;
    if (!payload && window.location.hash) {
      var rawHash = window.location.hash.replace(/^#/, "");
      if (rawHash.indexOf("?") >= 0) {
        rawHash = rawHash.split("?")[1];
      }
      hashPayload = parseAuthFromParams(new URLSearchParams(rawHash));
    }
    payload = payload || hashPayload;
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

  var tagsClearBtn = document.getElementById("rl-cabinet-tags-clear");

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

  var skillsModalEl = document.getElementById("rl-cabinet-skills-modal");
  var skillsOverlayEl = document.getElementById("rl-cabinet-skills-modal-overlay");
  var skillsCatalogEl = document.getElementById("rl-cabinet-skills-catalog");
  var skillsSearchEl = document.getElementById("rl-cabinet-skills-search");
  var skillsApplyBtn = document.getElementById("rl-cabinet-skills-apply");
  var skillsCancelBtn = document.getElementById("rl-cabinet-skills-cancel");
  var skillsRareBtn = document.getElementById("rl-cabinet-skills-rare");
  var skillsLimitEl = document.getElementById("rl-cabinet-skills-limit");



  var state = {

    tags: [],

    catalog: [],

    catalogGroups: [],

    pickerDraft: [],

    pickerQuery: "",

    pickerNiche: null,

    showRareSkills: false,

    catalogLoading: false,

    offset: 0,

    limit: 20,

    minMatch: 0,

    sort: "match",

    source: "",

    draftCategories: [],

    appliedCategories: [],

    loading: false,

    done: false,

    totalShown: 0,

    expandedId: null,

    tagsLoading: false,

    loadGeneration: 0,

    itemsById: {},

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

        '<p class="rl-feed-card__reply" data-reply-text>' +

        escapeHtml(reply) +

        "</p>" +

        '<button type="button" class="rl-btn rl-btn--ghost rl-feed-card__copy" data-copy-reply>Скопировать черновик</button>' +

        "</div>";

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

          '<button type="button" class="rl-cabinet-tag__remove" aria-label="Убрать навык">×</button></span>'

        );

      })

      .join("");

    html +=

      '<button type="button" class="rl-cabinet-tag rl-cabinet-tag--add" id="rl-cabinet-tag-add">+ Добавить навык</button>';

    tagsEl.innerHTML = html;



    if (tagsHint) {

      tagsHint.hidden = state.tags.length > 0;

    }

    if (noTagsEl) {

      noTagsEl.hidden = state.tags.length > 0;

    }

    if (tagsClearBtn) {

      tagsClearBtn.hidden = state.tags.length === 0;

      tagsClearBtn.disabled = state.tagsLoading;

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

      addBtn.addEventListener("click", openSkillsPicker);

    }

  }



  function skillChipHtml(row) {

    var tag = row.tag || "";

    var label = (row.title_ru || tag).trim() || tag;

    var active = state.pickerDraft.indexOf(tag) >= 0;

    var owned = state.tags.indexOf(tag) >= 0;

    return (

      '<button type="button" class="rl-feed-chip rl-feed-skill' +

      (active ? " is-active" : "") +

      (owned ? " is-disabled" : "") +

      '" data-tag="' +

      escapeHtml(tag) +

      '"' +

      (owned ? ' disabled aria-disabled="true"' : "") +

      ">" +

      escapeHtml(label) +

      (row.count ? ' <span class="rl-feed-skill__count">' + row.count + "</span>" : "") +

      "</button>"

    );

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



  function pickerRowVisible(row) {

    if (!row || !row.tag) {

      return false;

    }

    var tier = row.tier || "A";

    var niche = state.pickerNiche;

    if (niche) {

      var tierA = TIER_A_BY_NICHE[niche] || [];

      if (tierA.indexOf(row.tag) >= 0) {

        return true;

      }

      return !!(state.showRareSkills && tier === "B" && row.category === niche);

    }

    return state.showRareSkills || tier === "A";

  }



  function updateRareSkillsUi() {

    if (!skillsRareBtn) {

      return;

    }

    skillsRareBtn.hidden = false;

    skillsRareBtn.textContent = state.showRareSkills ? "Свернуть" : "Ещё навыки";

    skillsRareBtn.setAttribute("aria-expanded", state.showRareSkills ? "true" : "false");

  }



  function renderPickerCatalog() {

    if (!skillsCatalogEl) {

      return;

    }

    updateRareSkillsUi();

    var q = (state.pickerQuery || "").trim().toLowerCase();

    var groups = state.catalogGroups.length ? state.catalogGroups : null;

    if (!groups && !state.catalog.length) {

      skillsCatalogEl.innerHTML =

        '<p class="rl-feed-skills__empty">Пока нет навыков в ленте — дождитесь заказов из радара</p>';

      return;

    }

    function rowMatches(row) {

      if (!q) {

        return true;

      }

      var tag = (row.tag || "").toLowerCase();

      var label = (row.title_ru || row.tag || "").toLowerCase();

      return tag.indexOf(q) >= 0 || label.indexOf(q) >= 0;

    }

    if (groups) {

      skillsCatalogEl.innerHTML = groups

        .map(function (group) {

          var skills = (group.skills || []).filter(rowMatches).filter(pickerRowVisible);

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

      var flat = state.catalog.filter(rowMatches).filter(pickerRowVisible);

      skillsCatalogEl.innerHTML = flat.length

        ? '<div class="rl-feed-skills-group__chips">' + flat.map(skillChipHtml).join("") + "</div>"

        : '<p class="rl-feed-skills__empty">Ничего не найдено</p>';

    }

    skillsCatalogEl.querySelectorAll(".rl-feed-skill:not(.is-disabled)").forEach(function (btn) {

      btn.addEventListener("click", function () {

        togglePickerTag(btn.getAttribute("data-tag"));

      });

    });

    if (skillsApplyBtn) {

      skillsApplyBtn.disabled = state.pickerDraft.length === 0;

    }

  }



  function togglePickerTag(tag) {

    if (!tag || state.tags.indexOf(tag) >= 0) {

      return;

    }

    var idx = state.pickerDraft.indexOf(tag);

    if (idx < 0 && state.tags.length + state.pickerDraft.length >= MAX_USER_TAGS) {

      if (skillsLimitEl) {

        skillsLimitEl.hidden = false;

      }

      return;

    }

    if (skillsLimitEl) {

      skillsLimitEl.hidden = true;

    }

    state.pickerDraft =

      idx >= 0

        ? state.pickerDraft.filter(function (t) {

            return t !== tag;

          })

        : state.pickerDraft.concat([tag]);

    renderPickerCatalog();

  }



  function closeSkillsPicker() {

    if (skillsModalEl) {

      skillsModalEl.hidden = true;

    }

    state.pickerDraft = [];

    state.pickerQuery = "";

    state.showRareSkills = false;

    if (skillsLimitEl) {

      skillsLimitEl.hidden = true;

    }

    if (skillsSearchEl) {

      skillsSearchEl.value = "";

    }

  }



  function openSkillsPicker() {

    if (!skillsModalEl) {

      return;

    }

    state.pickerDraft = [];

    state.pickerQuery = "";

    state.showRareSkills = false;

    state.pickerNiche = null;

    if (skillsLimitEl) {

      skillsLimitEl.hidden = true;

    }

    if (skillsSearchEl) {

      skillsSearchEl.value = "";

    }

    skillsModalEl.hidden = false;

    if (!state.catalog.length && !state.catalogGroups.length && !state.catalogLoading) {

      loadCatalog().finally(renderPickerCatalog);

      return;

    }

    renderPickerCatalog();

  }



  function applyPickerTags() {

    if (!state.pickerDraft.length) {

      return;

    }

    var merged = state.tags.slice();

    state.pickerDraft.forEach(function (tag) {

      if (merged.indexOf(tag) < 0 && merged.length < MAX_USER_TAGS) {

        merged.push(tag);

      }

    });

    closeSkillsPicker();

    saveTags(merged);

  }



  function loadCatalog() {

    if (!cfg.restSkills) {

      return Promise.resolve();

    }

    state.catalogLoading = true;

    var skillsUrl = cfg.restSkills + "?mode=full&limit=200";

    if (state.pickerNiche) {

      skillsUrl += "&category=" + encodeURIComponent(state.pickerNiche);

    }

    return fetch(skillsUrl, { credentials: "same-origin" })

      .then(function (res) {

        return res.ok ? res.json() : { skills: [] };

      })

      .then(function (data) {

        state.catalogGroups = data.groups || [];

        state.catalog = data.skills || [];

      })

      .catch(function () {

        state.catalogGroups = [];

        state.catalog = [];

      })

      .finally(function () {

        state.catalogLoading = false;

      });

  }



  function clearAllTags() {

    if (state.tagsLoading || !state.tags.length) {

      return;

    }

    saveTags([]);

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

        if (!state.tags.length) {

          clearGuestSkillKeys();

        }

        renderTags();

        resetAndLoad();

      })

      .catch(function () {

        showError("Не удалось сохранить навыки.");

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



  function renderTagChips(item) {

    var tags =

      (item && item.lead_tag_labels && item.lead_tag_labels.length

        ? item.lead_tag_labels

        : item && item.lead_tags) || [];

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



  function hasUserSkills() {
    return state.tags && state.tags.length > 0;
  }

  function isPerfectMatch(item) {
    var km = item.keyword_match != null ? item.keyword_match : 0;
    return km >= 100 && hasUserSkills();
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

  function renderCard(item) {

    var src = sourceLabel(item.source);

    var km = item.keyword_match != null ? item.keyword_match : 0;

    var rank = item.keyword_match != null ? item.keyword_match : 0;

    var perfect = isPerfectMatch(item);

    var barPct = perfect ? km : rank;

    var budget = item.budget_text || "—";

    var expanded = state.expandedId === item.id;

    var matchBadge = perfect
      ? '<span class="rl-feed-card__match-badge">Точное совпадение</span>'
      : "";



    return (

      '<article class="rl-lead-card' +

      (expanded ? " is-expanded" : "") +

      (perfect ? " rl-lead-card--perfect-match" : "") +

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

      '<div class="rl-feed-card__head-meta">' +

      viewsHeadHtml(item) +

      '<span class="rl-feed-card__time">' +

      formatTime(item.created_at) +

      "</span>" +

      "</div>" +

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

      barPct +

      "%</span>" +

      matchBadge +

      "</div>" +

      '<div class="rl-match__bar" role="progressbar" aria-valuenow="' +

      barPct +

      '" aria-valuemin="0" aria-valuemax="100">' +

      '<span class="rl-match__fill" style="--match-value:' +

      barPct +

      '%"></span>' +

      "</div>" +

      "</div>" +

      '<div class="rl-chips">' +

      renderTagChips(item) +

      "</div>" +

      '<div class="rl-feed-card__cta">' +

      '<button type="button" class="rl-btn rl-btn--ghost rl-feed-card__delete-btn">Удалить из ЛК</button>' +

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

        ? state.totalShown + " откликов"

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

    var matchInp = sidebar.querySelector('input[name="min_match"]:checked');

    var sortInp = sidebar.querySelector('input[name="sort"]:checked');

    state.source = src ? src.value : "";

    state.appliedCategories = readCategoriesFrom();

    state.minMatch = matchInp ? parseInt(matchInp.value, 10) || 0 : 0;

    state.sort = sortInp ? sortInp.value : "match";

    var dirty =

      state.source !== "" ||

      state.appliedCategories.length > 0 ||

      state.minMatch !== 0 ||

      state.sort !== "match";

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

    state.loadGeneration += 1;

    state.offset = 0;

    state.done = false;

    state.totalShown = 0;

    state.expandedId = null;

    state.loading = false;

    state.itemsById = {};

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

    if (state.done || !cfg.restReplies) {

      return;

    }

    if (state.loading && !replace) {

      return;

    }

    var gen = state.loadGeneration;

    state.loading = true;

    var url = apiUrl(cfg.restReplies, {

      limit: state.limit,

      offset: state.offset,

    });

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

        var items = data.items || [];

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

            noMatchEl.hidden = false;

          }

        } else {

          listEl.hidden = false;

          if (noMatchEl) {

            noMatchEl.hidden = true;

          }

          var frag = items.map(renderCard).join("");

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



  function draftUrl(leadId) {

    var base = (cfg.restDraft || "").replace(/\/$/, "");

    return base + "/" + leadId + "/draft";

  }



  function fetchDraft(leadId) {

    return fetch(draftUrl(leadId), {

      method: "POST",

      credentials: "same-origin",

      headers: authHeaders(),

    }).then(function (res) {

      if (!res.ok) {

        throw new Error("HTTP " + res.status);

      }

      return res.json();

    });

  }



  function updateCardDraft(card, item) {

    var bodyInner = card.querySelector(".rl-feed-card__body-inner");

    if (!bodyInner) {

      return;

    }

    bodyInner.innerHTML = renderExpandedBody(item);

    delete card.dataset.bound;

    bindCards();

  }



  function deleteReplyUrl(leadId) {

    var base = (cfg.restReplies || "").replace(/\/$/, "");

    return base + "/" + leadId;

  }



  function deleteReply(leadId) {

    return fetch(deleteReplyUrl(leadId), {

      method: "DELETE",

      credentials: "same-origin",

      headers: authHeaders(),

    }).then(function (res) {

      if (!res.ok) {

        throw new Error("HTTP " + res.status);

      }

      return res.json();

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

        if (e.target.closest(".rl-btn--soon, .rl-feed-card__link, .rl-feed-card__delete-btn, .rl-feed-card__copy")) {

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

      var deleteBtn = card.querySelector(".rl-feed-card__delete-btn");

      if (deleteBtn) {

        deleteBtn.addEventListener("click", function (e) {

          e.stopPropagation();

          var id = parseInt(card.getAttribute("data-id"), 10);

          if (!id || !window.confirm("Удалить отклик из кабинета?")) {

            return;

          }

          deleteBtn.disabled = true;

          deleteReply(id)

            .then(function () {

              card.remove();

              delete state.itemsById[id];

              state.totalShown = Math.max(0, state.totalShown - 1);

              updateCount();

              if (state.totalShown === 0 && noMatchEl) {

                noMatchEl.hidden = false;

                if (listEl) {

                  listEl.hidden = true;

                }

              }

            })

            .catch(function () {

              deleteBtn.disabled = false;

              showError("Не удалось удалить");

            });

        });

      }

      var copyBtn = card.querySelector("[data-copy-reply]");

      if (copyBtn) {

        copyBtn.addEventListener("click", function (e) {

          e.stopPropagation();

          var replyEl = card.querySelector("[data-reply-text]");

          var text = replyEl ? replyEl.textContent : "";

          if (!text) {

            return;

          }

          function done(ok) {

            copyBtn.textContent = ok ? "Скопировано ✓" : "Скопировать черновик";

            setTimeout(function () {

              copyBtn.textContent = "Скопировать черновик";

            }, 2000);

          }

          if (navigator.clipboard && navigator.clipboard.writeText) {

            navigator.clipboard.writeText(text).then(function () {

              done(true);

            }).catch(function () {

              done(false);

            });

            return;

          }

          done(false);

        });

      }

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

      if (name === "sort") {

        syncChips();

        readFilters();

        try {

          sessionStorage.setItem(SORT_KEY, state.sort);

        } catch (err) {

          // ignore

        }

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

        sidebar.querySelector('input[name="min_match"][value="0"]').checked = true;

        var sortMatch = sidebar.querySelector('input[name="sort"][value="match"]');

        if (sortMatch) {

          sortMatch.checked = true;

        }

        try {

          sessionStorage.removeItem(SORT_KEY);

        } catch (e) {

          // ignore

        }

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

    addFirst.addEventListener("click", openSkillsPicker);

  }

  var changeSkills = document.getElementById("rl-cabinet-change-skills");

  if (changeSkills) {

    changeSkills.addEventListener("click", openSkillsPicker);

  }

  if (skillsOverlayEl) {

    skillsOverlayEl.addEventListener("click", closeSkillsPicker);

  }

  if (skillsCancelBtn) {

    skillsCancelBtn.addEventListener("click", closeSkillsPicker);

  }

  if (skillsApplyBtn) {

    skillsApplyBtn.addEventListener("click", applyPickerTags);

  }

  if (skillsRareBtn) {

    skillsRareBtn.addEventListener("click", function () {

      state.showRareSkills = !state.showRareSkills;

      renderPickerCatalog();

    });

  }

  if (tagsClearBtn) {

    tagsClearBtn.addEventListener("click", clearAllTags);

  }

  if (skillsSearchEl) {

    skillsSearchEl.addEventListener("input", function () {

      state.pickerQuery = skillsSearchEl.value || "";

      renderPickerCatalog();

    });

  }

  document.addEventListener("keydown", function (e) {

    if (e.key === "Escape" && skillsModalEl && !skillsModalEl.hidden) {

      closeSkillsPicker();

    }

  });



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

    loadSubscription();

    loadCatalog()

      .then(function () {

        return loadTags();

      })

      .then(function () {

        resetAndLoad();

      })

      .catch(function () {

        showError("Не удалось загрузить навыки.");

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

    renderUserBar();

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

