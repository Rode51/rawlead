(function () {
  "use strict";

  var cfg = window.rawleadPricing || {};
  var subBtn = document.getElementById("rl-price-checkout-sub");
  var trialBtn = document.getElementById("rl-price-checkout-trial");
  var noteEl = document.getElementById("rl-price-checkout-note");

  var TOKEN_KEY = "rawlead_access_token";

  function getToken() {
    try {
      return localStorage.getItem(TOKEN_KEY) || "";
    } catch (e) {
      return "";
    }
  }

  function authHeaders() {
    var h = { "X-WP-Nonce": cfg.nonce || "" };
    var token = getToken();
    if (token) {
      h.Authorization = "Bearer " + token;
    }
    return h;
  }

  function setNote(text, isErr) {
    if (!noteEl) {
      return;
    }
    noteEl.hidden = !text;
    noteEl.textContent = text || "";
    noteEl.className =
      "rl-price-card__checkout-note" + (isErr ? " rl-price-card__checkout-note--err" : "");
  }

  function redirectToLogin(kind) {
    var cabinet = cfg.cabinetUrl || "/cabinet/";
    var sep = cabinet.indexOf("?") >= 0 ? "&" : "?";
    window.location.href = cabinet + sep + "checkout=" + encodeURIComponent(kind || "subscription");
  }

  function startCheckout(kind, triggerEl) {
    if (!cfg.restCheckout) {
      setNote("Оплата временно недоступна", true);
      return Promise.resolve(null);
    }
    if (!getToken()) {
      redirectToLogin(kind);
      return Promise.resolve(null);
    }
    if (triggerEl) {
      triggerEl.disabled = true;
      triggerEl.classList.add("is-disabled");
    }
    setNote("Открываем оплату…", false);
    var headers = authHeaders();
    headers["Content-Type"] = "application/json";
    return fetch(cfg.restCheckout, {
      method: "POST",
      credentials: "same-origin",
      headers: headers,
      body: JSON.stringify({ kind: kind || "subscription" }),
    })
      .then(function (res) {
        return res.json().then(function (data) {
          if (!res.ok) {
            var msg =
              (data && data.message) ||
              (data && data.detail) ||
              "Не удалось создать платёж";
            throw new Error(msg);
          }
          return data;
        });
      })
      .then(function (data) {
        if (data && data.confirmation_url) {
          window.location.href = data.confirmation_url;
        }
        return data;
      })
      .catch(function (err) {
        setNote((err && err.message) || "Оплата недоступна", true);
        if (triggerEl) {
          triggerEl.disabled = false;
          triggerEl.classList.remove("is-disabled");
        }
        return null;
      });
  }

  function loadSubscriptionHints() {
    if (!cfg.restSubscription || !getToken() || !trialBtn) {
      return;
    }
    fetch(cfg.restSubscription, {
      credentials: "same-origin",
      headers: authHeaders(),
    })
      .then(function (res) {
        if (!res.ok) {
          return null;
        }
        return res.json();
      })
      .then(function (data) {
        if (!data) {
          return;
        }
        var used = !!data.trial_used;
        var hasAccess = !!data.effective_access;
        if (used || hasAccess || data.status === "trial") {
          trialBtn.hidden = true;
        }
      })
      .catch(function () {});
  }

  if (subBtn) {
    subBtn.addEventListener("click", function () {
      startCheckout("subscription", subBtn);
    });
  }
  if (trialBtn) {
    trialBtn.addEventListener("click", function () {
      startCheckout("trial", trialBtn);
    });
  }

  loadSubscriptionHints();
})();
