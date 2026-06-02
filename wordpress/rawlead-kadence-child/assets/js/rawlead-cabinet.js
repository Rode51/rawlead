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
  var AUTH_COOKIE = "rl_access";
  var AUTH_COOKIE_MAX_AGE = 7 * 24 * 3600;

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
  var SORT_KEY = "rawlead_cabinet_sort";
  var USER_META_KEY = "rawlead_user_meta";
  var GUEST_SKILLS_KEYS = ["rawlead_lenta_skills", "rawlead_guest_skills"];
  var MAX_USER_TAGS = 12;
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

  var loginEl = document.getElementById("rl-cabinet-login");

  var appEl = document.getElementById("rl-cabinet-app");

  var loginBtn = document.getElementById("rl-cabinet-login-btn");

  var loginStateEl = document.getElementById("rl-cabinet-login-state");
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
    var msg = text || "";
    if (msg) {
      loginStateEl.classList.add("rl-cabinet-login__state--" + (level || "info"));
      loginStateEl.textContent = msg;
      loginStateEl.hidden = false;
      return;
    }
    loginStateEl.textContent = "";
    loginStateEl.hidden = true;
  }

  function showFallback(_show, reasonText) {
    if (reasonText) {
      setLoginState("warn", reasonText);
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

  function apiEndpoint(path) {
    var base = (cfg.apiBase || "").replace(/\/$/, "");
    if (!base) {
      return path;
    }
    return base + path;
  }

  function isWideScreen() {
    return window.innerWidth >= 768;
  }

  function qrImageUrl(deepLink) {
    var base = cfg.restQrImage || "";
    if (base) {
      return (
        base +
        (base.indexOf("?") >= 0 ? "&" : "?") +
        "data=" +
        encodeURIComponent(deepLink || "")
      );
    }
    return (
      "https://api.qrserver.com/v1/create-qr-code/?size=260x260&margin=12&data=" +
      encodeURIComponent(deepLink || "")
    );
  }

  var qrPollTimer = null;

  function stopQrPoll() {
    if (qrPollTimer) {
      clearTimeout(qrPollTimer);
      qrPollTimer = null;
    }
  }

  function hideQrPanel() {
    stopQrPoll();
    var qr = document.getElementById("rl-cabinet-login-qr");
    if (qr) {
      qr.classList.remove("rl-cabinet-login__qr--mobile");
      qr.setAttribute("hidden", "hidden");
    }
    var img = document.getElementById("rl-cabinet-login-qr-img");
    if (img) {
      img.hidden = false;
    }
    if (loginBtn) {
      loginBtn.hidden = false;
      loginBtn.disabled = false;
    }
  }

  function showQrPanel(deepLink, mobileMode) {
    var qr = document.getElementById("rl-cabinet-login-qr");
    var img = document.getElementById("rl-cabinet-login-qr-img");
    var link = document.getElementById("rl-cabinet-login-qr-link");
    if (!qr) {
      return false;
    }
    if (mobileMode) {
      qr.classList.add("rl-cabinet-login__qr--mobile");
      if (img) {
        img.removeAttribute("src");
        img.hidden = true;
      }
    } else {
      qr.classList.remove("rl-cabinet-login__qr--mobile");
      if (img) {
        img.hidden = false;
        img.src = qrImageUrl(deepLink);
      }
    }
    if (link) {
      link.href = deepLink || "#";
      link.textContent = mobileMode
        ? "Открыть Telegram"
        : "Открыть ссылку на телефоне";
    }
    qr.removeAttribute("hidden");
    if (loginBtn) {
      loginBtn.hidden = true;
      loginBtn.disabled = false;
    }
    return true;
  }

  function pollBotComplete(authToken, expiresAt) {
    stopQrPoll();
    var completeBase = cfg.restBotComplete || "";
    if (!completeBase || !authToken) {
      return;
    }
    var deadline = Date.parse(expiresAt || "") || Date.now() + 5 * 60 * 1000;
    var waitEl = document.getElementById("rl-cabinet-login-qr-wait");

    function tick() {
      if (Date.now() > deadline) {
        hideQrPanel();
        setLoginState("error", "Время вышло. Нажмите кнопку ещё раз.");
        return;
      }
      var pollUrl =
        completeBase +
        (completeBase.indexOf("?") >= 0 ? "&" : "?") +
        "auth=" +
        encodeURIComponent(authToken);
      fetch(pollUrl, {
        method: "GET",
        credentials: "same-origin",
        headers: { "X-WP-Nonce": cfg.nonce || "" },
      })
        .then(function (res) {
          return res
            .json()
            .catch(function () {
              return {};
            })
            .then(function (data) {
              return { res: res, data: data };
            });
        })
        .then(function (out) {
          if (out.res.ok && out.data && out.data.access_token) {
            hideQrPanel();
            setToken(out.data.access_token);
            saveUserMeta(out.data);
            setLoginState("ok", "Вход выполнен. Загружаем кабинет...");
            return mergeGuestSkillsAfterAuth().then(function () {
              showApp();
              bootCabinet();
            });
          }
          if (out.res.status === 401) {
            if (waitEl) {
              waitEl.textContent = "Ждём подтверждение в Telegram…";
            }
            qrPollTimer = setTimeout(tick, 2000);
            return;
          }
          var msg =
            (out.data && out.data.detail) ||
            (out.data && out.data.message) ||
            "HTTP " + out.res.status;
          throw new Error(String(msg));
        })
        .catch(function (err) {
          if (String(err && err.message).indexOf("HTTP 401") >= 0) {
            qrPollTimer = setTimeout(tick, 2000);
            return;
          }
          hideQrPanel();
          setLoginState(
            "error",
            (err && err.message) || "Не удалось завершить вход. Попробуйте ещё раз."
          );
        });
    }

    tick();
  }

  function startBotLogin() {
    var sessionUrl = cfg.restBotSession || "";
    if (!sessionUrl) {
      setLoginState("error", "Сервис временно недоступен. Попробуйте позже.");
      return;
    }
    if (loginBtn) {
      loginBtn.disabled = true;
    }
    setLoginState(
      "info",
      isWideScreen() ? "Готовим QR-код…" : "Откройте Telegram и нажмите Start."
    );
    fetch(sessionUrl, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-WP-Nonce": cfg.nonce || "",
      },
      body: "{}",
    })
      .then(function (res) {
        return res.json().catch(function () {
          return {};
        }).then(function (data) {
          if (!res.ok) {
            var msg =
              (data && data.detail) ||
              (data && data.message) ||
              "HTTP " + res.status;
            throw new Error(String(msg));
          }
          return data;
        });
      })
      .then(function (data) {
        if (!data.deep_link || !data.auth_token) {
          throw new Error("no deep_link");
        }
        var mobileMode = !isWideScreen();
        if (!showQrPanel(data.deep_link, mobileMode)) {
          throw new Error("qr panel missing");
        }
        if (mobileMode) {
          setLoginState("info", "Откройте Telegram и нажмите Start.");
        } else {
          setLoginState("info", "Отсканируйте QR телефоном и нажмите Start в боте.");
        }
        pollBotComplete(data.auth_token, data.expires_at);
      })
      .catch(function (err) {
        hideQrPanel();
        if (loginBtn) {
          loginBtn.disabled = false;
        }
        setLoginState(
          "error",
          "Не удалось открыть Telegram. Попробуйте через бота ниже."
        );
      });
  }

  var qrCancelBtn = document.getElementById("rl-cabinet-login-qr-cancel");
  if (qrCancelBtn) {
    qrCancelBtn.addEventListener("click", function () {
      hideQrPanel();
      setLoginState("info", "");
    });
  }

  if (loginBtn) {
    loginBtn.addEventListener("click", startBotLogin);
  }

  function completeBotAuth(authToken) {
    if (!authToken) {
      return Promise.reject(new Error("no auth token"));
    }
    setLoginState("info", "Завершаем вход...");
    var completeUrl = cfg.restBotComplete || "";
    if (!completeUrl) {
      return Promise.reject(new Error("auth endpoint missing"));
    }
    return fetch(completeUrl, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-WP-Nonce": cfg.nonce || "",
      },
      body: JSON.stringify({ auth_token: authToken }),
    })
      .then(function (res) {
        return res.json().catch(function () {
          return {};
        }).then(function (data) {
          if (!res.ok) {
            var msg =
              (data && data.detail) ||
              (data && data.message) ||
              "HTTP " + res.status;
            throw new Error(String(msg));
          }
          return data;
        });
      })
      .then(function (data) {
        if (!data.access_token) {
          throw new Error("no token");
        }
        setToken(data.access_token);
        saveUserMeta(data);
        setLoginState("ok", "Вход выполнен. Загружаем кабинет...");
        return mergeGuestSkillsAfterAuth().then(function () {
          showApp();
          bootCabinet();
        });
      });
  }

  function consumeBotAuthFromQuery() {
    var params = new URLSearchParams(window.location.search || "");
    var authToken = (params.get("auth") || "").trim();
    if (!authToken) {
      return false;
    }
    if (window.history && window.history.replaceState) {
      window.history.replaceState({}, document.title, window.location.pathname);
    }
    setLoginState("info", "Подтверждаем вход из Telegram...");
    completeBotAuth(authToken).catch(function () {
      setLoginState("error", "Не удалось завершить вход. Нажмите кнопку ещё раз.");
    });
    return true;
  }

  function redirectTgLoginFallback() {
    if (!cfg.tgLoginFallbackUrl) {
      setLoginState("error", "Не удалось открыть Telegram. Попробуйте ещё раз.");
      return;
    }
    setLoginState("info", "Открываем Telegram…");
    window.location.href = cfg.tgLoginFallbackUrl;
  }

  function getToken() {

    return localStorage.getItem(TOKEN_KEY) || "";

  }

  function setToken(token) {

    if (token) {

      localStorage.setItem(TOKEN_KEY, token);
      syncAuthCookie(token);

    } else {

      localStorage.removeItem(TOKEN_KEY);
      syncAuthCookie("");

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
  var notifHintEl = document.getElementById("rl-cabinet-notif-hint");

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
      active: "Подписка активна ✓",
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
    updateInboxEmptyStates();
    loadNotificationSettings(data);
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

  function hasPushAccess(sub) {
    if (!sub) {
      return false;
    }
    if (sub.effective_access) {
      return true;
    }
    var st = sub.status || "";
    return st === "active" || st === "beta";
  }

  function renderNotificationSettings(data, sub) {
    if (!notifEl) {
      return;
    }
    if (!getToken()) {
      notifEl.hidden = true;
      if (notifHintEl) {
        notifHintEl.hidden = true;
      }
      return;
    }
    var paid = hasPushAccess(sub || subscriptionState);
    if (!paid) {
      notifEl.hidden = true;
      if (notifHintEl) {
        notifHintEl.hidden = false;
      }
      return;
    }
    if (notifHintEl) {
      notifHintEl.hidden = true;
    }
    if (!data) {
      notifEl.hidden = false;
      return;
    }
    notifEl.hidden = false;
    if (notifThresholdEl) {
      var threshold = String(data.push_min_match || 60);
      notifThresholdEl.querySelectorAll(".rl-notif-threshold-chip").forEach(function (chip) {
        var active = chip.getAttribute("data-value") === threshold;
        chip.classList.toggle("is-active", active);
        chip.setAttribute("aria-pressed", active ? "true" : "false");
      });
    }
    if (notifEnabledEl) {
      var enabled = data.push_enabled !== false;
      notifEnabledEl.setAttribute("aria-checked", enabled ? "true" : "false");
      notifEnabledEl.classList.toggle("is-on", enabled);
    }
  }

  function loadNotificationSettings(sub) {
    var subState = sub || subscriptionState;
    if (!cfg.restNotificationSettings || !getToken()) {
      renderNotificationSettings(null, subState);
      return Promise.resolve(null);
    }
    if (!hasPushAccess(subState)) {
      renderNotificationSettings(null, subState);
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
        renderNotificationSettings(data, subState);
        return data;
      })
      .catch(function () {
        renderNotificationSettings(null, subState);
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
        renderNotificationSettings(data, subscriptionState);
        _notifSetStatus("Сохранено", false);
        setTimeout(function () { _notifSetStatus(""); }, 2000);
        return data;
      });
    }).catch(function (e) {
      _notifSetStatus(e.message || "Ошибка сохранения", true);
    });
  }

  if (notifThresholdEl) {
    notifThresholdEl.addEventListener("click", function (e) {
      var chip = e.target.closest(".rl-notif-threshold-chip");
      if (!chip) {
        return;
      }
      var val = parseInt(chip.getAttribute("data-value"), 10);
      if (isNaN(val)) {
        return;
      }
      notifThresholdEl.querySelectorAll(".rl-notif-threshold-chip").forEach(function (c) {
        var active = c === chip;
        c.classList.toggle("is-active", active);
        c.setAttribute("aria-pressed", active ? "true" : "false");
      });
      patchNotificationSettings({ push_min_match: val });
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

  }

  var PROD_LOGIN_HOSTS = ["rawlead.ru", "www.rawlead.ru"];

  function cfgTruthy(v) {
    return v === true || v === 1 || v === "1" || v === "true";
  }

  function cfgFalsy(v) {
    return v === false || v === 0 || v === "0" || v === "false" || v === "" || v == null;
  }

  function isProdLoginHost() {
    var host = (location.hostname || "").toLowerCase();
    return PROD_LOGIN_HOSTS.indexOf(host) >= 0;
  }

  function canMountTelegramWidget() {
    if (cfgTruthy(cfg.tgLoginDev)) {
      return location.hostname === "127.0.0.1";
    }
    if (cfgFalsy(cfg.tgLoginWidgetAllowed)) {
      return false;
    }
    if (cfgTruthy(cfg.tgLoginWidgetAllowed) || isProdLoginHost()) {
      return true;
    }
    return false;
  }

  function mountTelegramWidget() {

    var box = document.getElementById("rl-telegram-login-widget");

    if (!box) {

      return;

    }

    box.innerHTML = "";
    box.hidden = false;
    showFallback(true);
    setLoginState("info", "Загружаем Telegram Widget (fallback)...");

    if (!canMountTelegramWidget()) {
      if (cfgTruthy(cfg.tgLoginDev)) {
        setLoginState(
          "warn",
          "Локальный вход — только через http://127.0.0.1:" +
            (cfg.localPort || "10007") +
            "/cabinet/"
        );
      } else {
        setLoginState("warn", "Виджет недоступен. Используйте кнопку входа.");
      }
      return;
    }

    if (!cfg.tgBotUsername) {
      setLoginState("error", "Бот не настроен на сайте.");
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
        setLoginState("warn", "Не удалось загрузить виджет. Нажмите кнопку входа.");
      } else {
        setLoginState("ok", "Подтвердите вход в Telegram.");
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
        var msg = err && err.message ? err.message : "Попробуйте снова.";
        if (msg === "token save failed") {
          setLoginState(
            "error",
            "Не удалось сохранить сессию. Проверьте настройки браузера."
          );
          return;
        }
        setLoginState("error", "Не удалось войти. " + msg);
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

  var paginationEl = document.getElementById("rl-cabinet-pagination");

  var loadMoreBtn = document.getElementById("rl-cabinet-load-more");

  var paginationCountEl = document.getElementById("rl-cabinet-pagination-count");
  var paginationShownEl = document.getElementById("rl-cabinet-shown");
  var paginationTotalEl = document.getElementById("rl-cabinet-total");
  var paginationLoadingEl = document.getElementById("rl-cabinet-loading");

  var endEl = document.getElementById("rl-cabinet-end");

  var errorEl = document.getElementById("rl-cabinet-error");

  var noTagsEl = document.getElementById("rl-cabinet-no-tags");

  var noMatchEl = document.getElementById("rl-cabinet-no-match");
  var noMatchFreeEl = document.getElementById("rl-cabinet-no-match-free");

  var sidebar = document.getElementById("rl-cabinet-sidebar");

  var resetBtn = sidebar ? sidebar.querySelector(".rl-feed-reset") : null;

  var skillsModalEl = document.getElementById("rl-cabinet-skills-modal");
  var skillsOverlayEl = document.getElementById("rl-cabinet-skills-modal-overlay");
  var skillsPanelEl =
    skillsModalEl && skillsModalEl.querySelector(".rl-cabinet-skills-modal__panel");
  var skillTreeRootsEl = document.getElementById("rl-cabinet-skill-tree-roots");
  var skillTreeCounterEl = document.getElementById("rl-cabinet-skill-tree-counter");
  var skillTreeHintEl = document.getElementById("rl-cabinet-skill-tree-hint");
  var skillTreeLimitEl = document.getElementById("rl-cabinet-skill-tree-limit");
  var skillTreeCloseBtn = document.getElementById("rl-cabinet-skill-tree-close");
  var skillTreeResetBtn = document.getElementById("rl-cabinet-skill-tree-reset");
  var skillTreeSaveErrEl = document.getElementById("rl-cabinet-skill-tree-save-error");
  var skillsApplyBtn = document.getElementById("rl-cabinet-skills-apply");



  var state = {

    tags: [],

    catalog: [],

    catalogGroups: [],

    pickerDraft: [],

    expandedNiches: { dev: false, design: false, marketing: false, text: false },

    expandedL1: {},

    catalogByTag: {},

    catalogByNiche: { dev: [], design: [], marketing: [], text: [] },

    catalogLoading: false,

    tagsStripSkeleton: false,

    offset: 0,

    limit: 20,

    minMatch: 0,

    sort: "match",

    source: "",

    draftCategories: [],

    appliedCategories: [],

    loading: false,

    showLoadSpinner: false,

    done: false,

    totalShown: 0,

    total: 0,

    expandedId: null,

    tagsLoading: false,

    loadGeneration: 0,

    itemsById: {},

  };

  var prefersReduced =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var rlInboxIo = null;
  if (!prefersReduced && "IntersectionObserver" in window) {
    rlInboxIo = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            rlInboxIo.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.08, rootMargin: "0px 0px -5% 0px" }
    );
  }

  function observeInboxCards(root) {
    if (!root) {
      return;
    }
    var cards = root.querySelectorAll(".rl-lead-card:not(.is-visible)");
    if (prefersReduced || !rlInboxIo) {
      cards.forEach(function (el) {
        el.classList.add("is-visible");
      });
      return;
    }
    cards.forEach(function (el) {
      rlInboxIo.observe(el);
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
    if (paginationLoadingEl) {
      paginationLoadingEl.hidden = !state.showLoadSpinner;
    }
    if (paginationEl) {
      paginationEl.hidden = shown <= 0 && !state.showLoadSpinner;
    }
  }



  function apiUrl(base, params) {

    var q = new URLSearchParams(params);

    return base + (base.indexOf("?") >= 0 ? "&" : "?") + q.toString();

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

    var tools = item.tools_required || [];

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

    } else if (reply) {

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



  function titleForTag(tag) {

    var row = state.catalogByTag[tag];

    return (row && row.title_ru) || tag;

  }



  function nicheForTag(tag) {

    var row = state.catalogByTag[tag];

    if (row && row.category) {

      return row.category;

    }

    return catalogCategoryForTag(tag);

  }



  function orderedTagsForStrip(tags) {

    var buckets = { dev: [], design: [], marketing: [], text: [], other: [] };

    var i;

    var n;

    for (i = 0; i < tags.length; i++) {

      n = nicheForTag(tags[i]) || "other";

      if (!buckets[n]) {

        buckets.other.push(tags[i]);

      } else {

        buckets[n].push(tags[i]);

      }

    }

    return buckets.dev

      .concat(buckets.design, buckets.marketing, buckets.text, buckets.other);

  }



  function flashTagsStrip() {

    if (!tagsEl) {

      return;

    }

    tagsEl.classList.add("is-saved-flash");

    window.setTimeout(function () {

      tagsEl.classList.remove("is-saved-flash");

    }, 2000);

  }



  function tagsStripSkeletonHtml() {

    return (

      '<span class="rl-cabinet-tag rl-cabinet-tag--skel" aria-hidden="true"></span>' +

      '<span class="rl-cabinet-tag rl-cabinet-tag--skel" aria-hidden="true"></span>' +

      '<span class="rl-cabinet-tag rl-cabinet-tag--skel" aria-hidden="true"></span>'

    );

  }



  function renderTags() {

    if (!tagsEl) {

      return;

    }

    if (state.tagsStripSkeleton) {

      tagsEl.classList.add("is-skeleton");

      tagsEl.innerHTML = tagsStripSkeletonHtml();

      if (tagsHint) {

        tagsHint.hidden = true;

      }

      if (noTagsEl) {

        noTagsEl.hidden = true;

      }

      if (tagsClearBtn) {

        tagsClearBtn.hidden = true;

      }

      return;

    }

    tagsEl.classList.remove("is-skeleton");

    var html = "";

    var ordered = orderedTagsForStrip(state.tags);

    var mobile = !isWideScreen();

    if (!ordered.length) {

      html +=

        '<button type="button" class="rl-cabinet-tag--empty-link" id="rl-cabinet-tag-add">+ Добавь навыки для совместимости →</button>';

      if (tagsHint) {

        tagsHint.hidden = false;

        tagsHint.textContent = "Лента покажет совместимость";

        tagsHint.classList.add("rl-cabinet-head__hint--compat");

      }

    } else {

      html = ordered

        .map(function (tag) {

          var label = titleForTag(tag);

          return (

            '<span class="rl-cabinet-tag' +

            (mobile ? " rl-cabinet-tag--open-sheet" : "") +

            '" role="listitem" data-tag="' +

            escapeHtml(tag) +

            '">' +

            escapeHtml(label) +

            '<button type="button" class="rl-cabinet-tag__remove" aria-label="Убрать навык">×</button></span>'

          );

        })

        .join("");

      html +=

        '<button type="button" class="rl-cabinet-tag rl-cabinet-tag--add" id="rl-cabinet-tag-add">+ Добавить</button>';

      if (tagsHint) {

        tagsHint.hidden = true;

        tagsHint.classList.remove("rl-cabinet-head__hint--compat");

      }

    }

    tagsEl.innerHTML = html;

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

        saveTags(

          state.tags.filter(function (t) {

            return t !== tag;

          })

        );

      });

    });

    tagsEl.querySelectorAll(".rl-cabinet-tag--open-sheet").forEach(function (chip) {

      chip.addEventListener("click", function (e) {

        if (e.target.closest(".rl-cabinet-tag__remove")) {

          return;

        }

        openSkillsPicker();

      });

    });

    var addBtn = document.getElementById("rl-cabinet-tag-add");

    if (addBtn) {

      addBtn.addEventListener("click", openSkillsPicker);

    }

  }



  function trackSkillTelemetry(eventName, payload) {

    try {

      document.dispatchEvent(

        new CustomEvent("rawlead:telemetry", {

          detail: Object.assign({ event: eventName }, payload || {}),

        })

      );


    } catch (_err) {

      /* AC-9: never block UX */

    }

  }



  function skillTreeChipHtml(row, atLimit, opts) {
    opts = opts || {};
    var tag = row.tag || "";
    var label = (row.title_ru || tag).trim() || tag;
    var selected = state.pickerDraft.indexOf(tag) >= 0;
    var disabled = atLimit && !selected;
    var level = row.picker_level || opts.level || "L1";
    return (
      '<button type="button" class="rl-skill-chip' +
      (level === "L3" ? " rl-skill-chip--l3" : "") +
      (selected ? " is-selected" : "") +
      (disabled ? " is-disabled" : "") +
      '" data-tag="' +
      escapeHtml(tag) +
      '" data-niche="' +
      escapeHtml(row.category || opts.niche || "") +
      '"' +
      (disabled ? ' disabled aria-disabled="true"' : "") +
      ">" +
      (selected ? "✓ " : "") +
      escapeHtml(label) +
      "</button>"
    );
  }

  function renderL1ChipBlock(row, atLimit, niche) {
    var tag = row.tag || "";
    var selected = state.pickerDraft.indexOf(tag) >= 0;
    var children = row.children || [];
    var hasL3 = children.length > 0;
    var l3Open = selected && hasL3;
    var html =
      '<div class="rl-l1-chip-wrap">' +
      skillTreeChipHtml(row, atLimit, { niche: niche, level: "L1" }) +
      "</div>";
    if (hasL3) {
      html +=
        '<div class="rl-l3-row' +
        (l3Open ? " is-visible" : "") +
        '" data-l3-parent="' +
        escapeHtml(tag) +
        '">';
      for (var ci = 0; ci < children.length; ci++) {
        html += skillTreeChipHtml(
          {
            tag: children[ci].tag,
            title_ru: children[ci].title_ru,
            category: niche,
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

  function catalogGroupForNiche(niche) {
    var g;
    for (g = 0; g < state.catalogGroups.length; g++) {
      if (state.catalogGroups[g].category === niche) {
        return state.catalogGroups[g];
      }
    }
    return null;
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



  function rebuildCatalogIndex() {

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

        parent_id: row.parent_id || "",

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



    function tierRank(t) {

      return t === "A" ? 0 : 1;

    }



    NICHE_ORDER.forEach(function (niche) {

      byNiche[niche].sort(function (a, b) {

        var ta = tierRank(a.tier);

        var tb = tierRank(b.tier);

        if (ta !== tb) {

          return ta - tb;

        }

        return (a.title_ru || a.tag).localeCompare(b.title_ru || b.tag, "ru");

      });

    });



    state.catalogByTag = byTag;

    state.catalogByNiche = byNiche;

  }



  function renderDevNicheBody(skills, atLimit, niche) {
    var bodyHtml = "";
    var grp = catalogGroupForNiche(niche);
    var subheads = (grp && grp.picker_subheads) || DEV_PICKER_SUBHEADS;
    var si;
    var sh;
    var l1skills;
    for (si = 0; si < subheads.length; si++) {
      sh = subheads[si];
      l1skills = [];
      for (var i = 0; i < skills.length; i++) {
        if (
          skills[i].picker_group === sh.key &&
          (skills[i].picker_level || "L1") === "L1"
        ) {
          l1skills.push(skills[i]);
        }
      }
      if (!l1skills.length) {
        continue;
      }
      bodyHtml +=
        '<p class="rl-niche-subhead">' + escapeHtml(String(sh.label).toUpperCase()) + "</p>";
      bodyHtml += '<div class="rl-niche-root__chips">';
      for (var lj = 0; lj < l1skills.length; lj++) {
        bodyHtml += renderL1ChipBlock(l1skills[lj], atLimit, niche);
      }
      bodyHtml += "</div>";
    }
    return bodyHtml;
  }

  function renderFlatNicheBody(skills, atLimit, niche) {
    if (!skills.length) {
      return "";
    }
    return (
      '<div class="rl-niche-root__chips">' +
      skills
        .map(function (row) {
          return skillTreeChipHtml(row, atLimit, { niche: niche });
        })
        .join("") +
      "</div>"
    );
  }



  function nicheMixFromDraft() {

    var mix = [];

    var i;

    var n;

    for (i = 0; i < state.pickerDraft.length; i++) {

      n = nicheForTag(state.pickerDraft[i]);

      if (n && mix.indexOf(n) < 0) {

        mix.push(n);

      }

    }

    return mix;

  }



  function updateSkillTreeChrome() {

    var n = state.pickerDraft.length;

    var atLimit = n >= MAX_USER_TAGS;



    if (skillTreeCounterEl) {

      skillTreeCounterEl.textContent = "Выбрано " + n + " / " + MAX_USER_TAGS;

      skillTreeCounterEl.classList.toggle("is-active", n > 0);

    }

    if (skillTreeHintEl) {

      skillTreeHintEl.hidden = n < 7 || n >= MAX_USER_TAGS;

    }

    if (skillTreeLimitEl) {

      skillTreeLimitEl.hidden = !atLimit;

    }

    if (skillTreeSaveErrEl) {

      skillTreeSaveErrEl.hidden = true;

    }

    if (skillsApplyBtn && !skillsApplyBtn.classList.contains("is-loading")) {

      skillsApplyBtn.disabled = n === 0;

      skillsApplyBtn.classList.toggle("is-idle-disabled", n === 0);

    }

  }



  function setSkillTreeSaveState(mode) {

    if (!skillsApplyBtn) {

      return;

    }

    skillsApplyBtn.classList.remove("is-loading", "is-success", "is-idle-disabled");

    if (mode === "loading") {

      skillsApplyBtn.disabled = true;

      skillsApplyBtn.classList.add("is-loading");

      skillsApplyBtn.textContent = "Сохраняем…";

      return;

    }

    if (mode === "success") {

      skillsApplyBtn.disabled = true;

      skillsApplyBtn.classList.add("is-success");

      skillsApplyBtn.textContent = "Навыки сохранены ✓";

      return;

    }

    if (mode === "error") {

      skillsApplyBtn.disabled = state.pickerDraft.length === 0;

      skillsApplyBtn.textContent = "Сохранить навыки →";

      if (skillTreeSaveErrEl) {

        skillTreeSaveErrEl.hidden = false;

      }

      return;

    }

    skillsApplyBtn.textContent = "Сохранить навыки →";

    updateSkillTreeChrome();

  }



  function renderSkillTree() {

    if (!skillTreeRootsEl) {

      return;

    }

    updateSkillTreeChrome();

    var atLimit = state.pickerDraft.length >= MAX_USER_TAGS;

    var html = "";

    var ni;



    for (ni = 0; ni < NICHE_ORDER.length; ni++) {

      var niche = NICHE_ORDER[ni];

      var expanded = !!state.expandedNiches[niche];

      var skills = state.catalogByNiche[niche] || [];

      var bodyHtml = "";

      var grpNiche = catalogGroupForNiche(niche);
      if (grpNiche && grpNiche.picker_subheads) {
        bodyHtml = renderDevNicheBody(skills, atLimit, niche);
      } else {
        bodyHtml = renderFlatNicheBody(skills, atLimit, niche);
      }



      if (!bodyHtml && !state.catalogLoading) {

        bodyHtml = '<p class="rl-feed-skills__empty">Каталог загружается…</p>';

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

        "</span>" +

        "<span>" +

        escapeHtml(NICHE_ROOT_LABELS[niche] || niche) +

        "</span></button>" +

        '<div class="rl-niche-root__body">' +

        bodyHtml +

        "</div></section>";

    }



    skillTreeRootsEl.innerHTML = html;



    skillTreeRootsEl.querySelectorAll("[data-niche-toggle]").forEach(function (btn) {

      btn.addEventListener("click", function () {

        var nicheKey = btn.getAttribute("data-niche-toggle");

        if (!nicheKey) {

          return;

        }

        state.expandedNiches[nicheKey] = !state.expandedNiches[nicheKey];

        renderSkillTree();

      });

    });



    skillTreeRootsEl.querySelectorAll(".rl-skill-chip:not(.is-disabled)").forEach(function (btn) {

      btn.addEventListener("click", function () {

        toggleSkillTreeTag(btn.getAttribute("data-tag"), btn.getAttribute("data-niche"));

      });

    });

    skillTreeRootsEl.querySelectorAll("[data-l1-expand]").forEach(function (btn) {

      btn.addEventListener("click", function (e) {

        e.preventDefault();

        e.stopPropagation();

        var parentTag = btn.getAttribute("data-l1-expand");

        if (!parentTag) {

          return;

        }

        state.expandedL1[parentTag] = !state.expandedL1[parentTag];

        renderSkillTree();

      });

    });

  }



  function toggleSkillTreeTag(tag, nicheHint) {

    if (!tag) {

      return;

    }

    var idx = state.pickerDraft.indexOf(tag);

    var niche = nicheHint || nicheForTag(tag) || "";



    if (idx >= 0) {

      state.pickerDraft = state.pickerDraft.filter(function (t) {

        return t !== tag;

      });

      if (state.expandedL1[tag]) {

        delete state.expandedL1[tag];

      }

      trackSkillTelemetry("skill_unselect", { niche: niche, tag: tag });

    } else {

      if (state.pickerDraft.length >= MAX_USER_TAGS) {

        updateSkillTreeChrome();

        renderSkillTree();

        return;

      }

      state.pickerDraft = state.pickerDraft.concat([tag]);

      var catalogRow = state.catalogByTag[tag];

      if (catalogRow && (catalogRow.children || []).length > 0) {

        state.expandedL1[tag] = true;

      }

      trackSkillTelemetry("skill_select", { niche: niche, tag: tag });

    }

    renderSkillTree();

  }



  function closeSkillsPicker() {

    if (skillsModalEl) {

      skillsModalEl.hidden = true;

    }

    document.body.classList.remove("rl-skill-tree-open");

    state.pickerDraft = [];

    state.expandedL1 = {};

    NICHE_ORDER.forEach(function (n) {

      state.expandedNiches[n] = false;

    });

    setSkillTreeSaveState("idle");

  }



  function openSkillsPicker() {

    if (!skillsModalEl) {

      return;

    }

    state.pickerDraft = state.tags.slice();

    var ti;

    var ttag;

    for (ti = 0; ti < state.pickerDraft.length; ti++) {

      ttag = state.pickerDraft[ti];

      var trow = state.catalogByTag[ttag];

      if (trow && (trow.children || []).length > 0) {

        state.expandedL1[ttag] = true;

      }

    }

    NICHE_ORDER.forEach(function (n) {

      var has = false;

      var i;

      for (i = 0; i < state.pickerDraft.length; i++) {

        if (nicheForTag(state.pickerDraft[i]) === n) {

          has = true;

          break;

        }

      }

      state.expandedNiches[n] = has;

    });

    if (skillTreeHintEl) {

      skillTreeHintEl.hidden = true;

    }

    if (skillTreeLimitEl) {

      skillTreeLimitEl.hidden = state.pickerDraft.length < MAX_USER_TAGS;

    }

    if (skillTreeSaveErrEl) {

      skillTreeSaveErrEl.hidden = true;

    }

    setSkillTreeSaveState("idle");

    skillsModalEl.hidden = false;

    document.body.classList.add("rl-skill-tree-open");

    function afterCatalog() {

      rebuildCatalogIndex();

      renderSkillTree();

    }

    if (!state.catalog.length && !state.catalogGroups.length && !state.catalogLoading) {

      loadCatalog().finally(afterCatalog);

      return;

    }

    afterCatalog();

  }



  function applyPickerTags() {

    if (!state.pickerDraft.length || state.tagsLoading) {

      return;

    }

    setSkillTreeSaveState("loading");

    trackSkillTelemetry("skills_save", {

      selected_count: state.pickerDraft.length,

      niche_mix: nicheMixFromDraft(),

    });

    saveTags(state.pickerDraft.slice(), { fromSheet: true });

  }



  function loadCatalog() {

    if (!cfg.restSkills) {

      return Promise.resolve();

    }

    state.catalogLoading = true;

    var skillsUrl = cfg.restSkills + "?mode=full&limit=200";

    return fetch(skillsUrl, { credentials: "same-origin" })

      .then(function (res) {

        return res.ok ? res.json() : { skills: [] };

      })

      .then(function (data) {

        state.catalogGroups = data.groups || [];

        state.catalog = data.skills || [];

        rebuildCatalogIndex();

      })

      .catch(function () {

        state.catalogGroups = [];

        state.catalog = [];

        rebuildCatalogIndex();

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



  function saveTags(tags, opts) {

    opts = opts || {};

    if (state.tagsLoading) {

      return;

    }

    state.tagsLoading = true;

    if (tagsEl && !opts.fromSheet) {

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

        if (opts.fromSheet) {

          flashTagsStrip();

          setSkillTreeSaveState("success");

          window.setTimeout(closeSkillsPicker, 1500);

        }

        resetAndLoad();

      })

      .catch(function () {

        if (opts.fromSheet) {

          setSkillTreeSaveState("error");

        } else {

          showError("Не удалось сохранить навыки.");

        }

      })

      .finally(function () {

        state.tagsLoading = false;

        if (tagsEl) {

          tagsEl.classList.remove("is-loading");

        }

      });

  }



  function loadTags() {

    state.tagsStripSkeleton = true;

    renderTags();

    return fetch(cfg.restTags, { credentials: "same-origin", headers: authHeaders() })

      .then(function (res) {

        if (!res.ok) {

          throw new Error("HTTP " + res.status);

        }

        return res.json();

      })

      .then(function (data) {

        state.tags = data.tags || [];

        state.tagsStripSkeleton = false;

        renderTags();

      })

      .catch(function () {

        state.tagsStripSkeleton = false;

        renderTags();

        throw new Error("tags load failed");

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
    var userTags = (state.tags || []).map(function (t) {
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
    return state.tags && state.tags.length > 0;
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
    return (
      '<div class="rl-match-breakdown">' +
      escapeHtml("Укажи навыки в кабинете") +
      "</div>"
    );
  }

  function renderMatchBlock(item) {
    if (!hasUserSkills()) {
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

  function hasPaidAccess() {
    return !!(subscriptionState && subscriptionState.effective_access);
  }

  function formatRepliedDate(iso) {
    if (!iso) {
      return "";
    }
    var d = new Date(iso);
    if (isNaN(d.getTime())) {
      return "";
    }
    return d.toLocaleDateString("ru-RU", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  }

  function updateInboxEmptyStates() {
    if (noMatchEl) {
      noMatchEl.hidden = true;
    }
    if (noMatchFreeEl) {
      noMatchFreeEl.hidden = true;
    }
  }

  function repliedBadgeHtml() {
    return '<span class="rl-badge rl-badge--replied">Отклик ✓</span>';
  }

  function headBadgesHtml(item) {
    var src = sourceLabel(item.source);
    var reply = prepForDisplay(item.reply_draft || "", false).trim();
    var repliedBadge = reply ? repliedBadgeHtml() : "";
    return (
      '<span class="rl-feed-card__source rl-feed-card__source--' +
      src.cls +
      '">' +
      escapeHtml(src.label) +
      "</span>" +
      repliedBadge +
      hotBadgeHtml(item)
    );
  }

  function renderCard(item, isNew) {
    var perfect = isPerfectMatch(item);
    var budget = formatBudgetDisplay(item.budget_text || "—");
    var titleText = prepForDisplay(item.title || "Без названия", true);
    var titleHtml = escapeHtml(titleText);
    return (
      '<article class="rl-lead-card' +
      (isNew ? " is-new" : "") +
      (perfect ? " rl-lead-card--perfect-match" : "") +
      '" data-id="' +
      item.id +
      '" tabindex="0" role="button">' +
      '<div class="rl-feed-card__head">' +
      '<div class="rl-feed-card__head-start">' +
      headBadgesHtml(item) +
      "</div>" +
      '<div class="rl-feed-card__head-meta">' +
      '<span class="rl-feed-card__time">' +
      formatTime(item.created_at) +
      "</span>" +
      '<button type="button" class="rl-inbox-card__delete" aria-label="Удалить отклик" data-reply-id="' +
      item.id +
      '">✕</button>' +
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



  function updateCount() {

    if (!countEl) {

      return;

    }

    countEl.textContent =

      state.totalShown > 0

        ? state.totalShown + " откликов"

        : "";

    updatePagination();

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

    state.total = 0;

    state.expandedId = null;

    state.loading = false;

    state.showLoadSpinner = false;

    state.itemsById = {};

    if (noMatchEl) {
      noMatchEl.hidden = true;
    }
    if (noMatchFreeEl) {
      noMatchFreeEl.hidden = true;
    }

    if (listEl) {

      listEl.innerHTML = skeletonHtml(4);

      listEl.hidden = false;

    }

    if (endEl) {

      endEl.hidden = true;

    }

    if (paginationLoadingEl) {

      paginationLoadingEl.hidden = true;

    }

    if (loadMoreBtn) {

      loadMoreBtn.hidden = true;

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

    if (!replace) {
      state.showLoadSpinner = true;
      if (loadMoreBtn) {
        loadMoreBtn.hidden = true;
        loadMoreBtn.classList.add("is-loading");
      }
      if (paginationLoadingEl) {
        paginationLoadingEl.hidden = false;
      }
    }

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

          listEl.innerHTML = "";

          showInboxEmpty();

        } else {

          listEl.hidden = false;

          if (noMatchEl) {
            noMatchEl.hidden = true;
          }
          if (noMatchFreeEl) {
            noMatchFreeEl.hidden = true;
          }

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

        bindCards();

        observeInboxCards(listEl);

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



  function updateCardDraft(card, item) {

    var bodyInner = card.querySelector(".rl-feed-card__body-inner");

    if (!bodyInner) {

      return;

    }

    bodyInner.innerHTML = renderExpandedBody(item);

    var headStart = card.querySelector(".rl-feed-card__head-start");
    if (headStart) {
      headStart.innerHTML = headBadgesHtml(item, isPerfectMatch(item));
    }
    var id = parseInt(card.getAttribute("data-id"), 10) || item.id;
    state.expandedId = id;
    card.classList.add("is-expanded");

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



  var cabinetDelegationReady = false;

  function onCabinetListClick(e) {
    var card = e.target.closest(".rl-lead-card");
    if (!card || !listEl || !listEl.contains(card)) {
      return;
    }
    var deleteBtn = e.target.closest(".rl-inbox-card__delete");
    if (deleteBtn && card.contains(deleteBtn)) {
      e.stopPropagation();
      var id = parseInt(
        deleteBtn.getAttribute("data-reply-id") || card.getAttribute("data-id"),
        10
      );
      if (!id || !window.confirm("Удалить отклик из кабинета?")) {
        return;
      }
      deleteBtn.disabled = true;
      deleteReply(id)
        .then(function () {
          card.style.transition = "opacity 200ms ease-out";
          card.style.opacity = "0";
          window.setTimeout(function () {
            card.remove();
            delete state.itemsById[id];
            state.totalShown = Math.max(0, state.totalShown - 1);
            if (state.total > 0) {
              state.total = Math.max(0, state.total - 1);
            }
            updateCount();
            if (state.totalShown === 0) {
              showInboxEmpty();
            }
          }, 200);
        })
        .catch(function () {
          deleteBtn.disabled = false;
          showError("Не удалось удалить");
        });
      return;
    }
    var skillsLink = e.target.closest("[data-open-skills]");
    if (skillsLink && card.contains(skillsLink)) {
      e.stopPropagation();
      openSkillsPicker();
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
          window.setTimeout(function () {
            copyBtn.textContent = "Скопировать черновик";
          }, 2000);
        });
      }
      return;
    }
    if (
      e.target.closest(".rl-inbox-card__delete, .rl-feed-card__copy, .rl-feed-card__link, a, button")
    ) {
      return;
    }
    var wasExpanded = card.classList.contains("is-expanded");
    listEl.querySelectorAll(".rl-lead-card.is-expanded").forEach(function (c) {
      c.classList.remove("is-expanded");
    });
    if (!wasExpanded) {
      card.classList.add("is-expanded");
    }
  }

  function onCabinetListKeydown(e) {
    var card = e.target.closest(".rl-lead-card");
    if (!card || !listEl.contains(card)) {
      return;
    }
    if (e.key === "Enter" || e.key === " ") {
      if (e.target.closest("button, a, input, textarea")) {
        return;
      }
      e.preventDefault();
      var wasExpanded = card.classList.contains("is-expanded");
      listEl.querySelectorAll(".rl-lead-card.is-expanded").forEach(function (c) {
        c.classList.remove("is-expanded");
      });
      if (!wasExpanded) {
        card.classList.add("is-expanded");
      }
    }
  }

  function ensureCabinetDelegation() {
    if (!listEl || cabinetDelegationReady) {
      return;
    }
    cabinetDelegationReady = true;
    listEl.addEventListener("click", onCabinetListClick);
    listEl.addEventListener("keydown", onCabinetListKeydown);
  }

  function bindCards() {
    ensureCabinetDelegation();
  }

  function showInboxEmpty() {
    updateInboxEmptyStates();
    var paid = hasPaidAccess();
    var target = paid
      ? document.getElementById("rl-cabinet-no-match")
      : document.getElementById("rl-cabinet-no-match-free");
    if (target) {
      target.hidden = false;
    }
    if (listEl) {
      listEl.hidden = true;
    }
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

  function onSkillsModalBackdropClick(e) {

    if (e.target === skillsModalEl || e.target === skillsOverlayEl) {

      closeSkillsPicker();

    }

  }

  if (skillsModalEl) {

    skillsModalEl.addEventListener("click", onSkillsModalBackdropClick);

  }

  if (skillsPanelEl) {

    skillsPanelEl.addEventListener("click", function (e) {

      e.stopPropagation();

    });

  }

  if (skillsOverlayEl) {

    skillsOverlayEl.addEventListener("click", closeSkillsPicker);

  }

  if (skillTreeCloseBtn) {

    skillTreeCloseBtn.addEventListener("click", closeSkillsPicker);

  }

  if (skillsApplyBtn) {

    skillsApplyBtn.addEventListener("click", applyPickerTags);

  }

  if (skillTreeResetBtn) {

    skillTreeResetBtn.addEventListener("click", function () {

      state.pickerDraft = [];

      renderSkillTree();

    });

  }

  if (tagsClearBtn) {

    tagsClearBtn.addEventListener("click", clearAllTags);

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



  if (loadMoreBtn) {

    loadMoreBtn.addEventListener("click", function () {

      if (state.loading || state.done) {

        return;

      }

      loadMore(false);

    });

  }



  function bootCabinet() {

    state.tagsStripSkeleton = true;

    renderTags();

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

    if (consumeBotAuthFromQuery()) {
      return;
    }

    if (consumeDeepLinkAuth()) {
      return;
    }

    setLoginState("", "");
  }

  function startLoggedIn() {

    renderUserBar();

    showApp();

    bootCabinet();

  }

  ensureCabinetDelegation();

  if (getToken()) {
    syncAuthCookie(getToken());
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

