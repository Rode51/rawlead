/**
 * RawLead — FAB «Поддержка» + thread (O116-W4).
 */
(function () {
  "use strict";

  var fab = document.getElementById("rl-support-fab");
  var modal = document.getElementById("rl-support-modal");
  if (!fab || !modal) {
    return;
  }

  var cfg = window.rawleadSupport || {};
  var closeBtn = document.getElementById("rl-support-close");
  var overlay = document.getElementById("rl-support-overlay");
  var submit = document.getElementById("rl-support-submit");
  var success = document.getElementById("rl-support-success");
  var textarea = document.getElementById("rl-support-text");
  var threadEl = document.getElementById("rl-support-thread");
  var badgeEl = document.getElementById("rl-support-badge");

  var restTicket = cfg.restTicket || "/wp-json/rawlead/v1/support/ticket";
  var restThread = cfg.restThread || "/wp-json/rawlead/v1/support/thread";
  var restUnread = cfg.restUnread || "/wp-json/rawlead/v1/support/unread";
  var guestKey = "rawlead_support_guest";

  function authHeaders() {
    var headers = { "Content-Type": "application/json" };
    try {
      var token = localStorage.getItem("rawlead_access_token") || "";
      if (token) {
        headers.Authorization = "Bearer " + token;
      }
    } catch (e) {
      /* ignore */
    }
    var guest = ensureGuestToken();
    if (guest) {
      headers["X-RawLead-Guest-Token"] = guest;
    }
    return headers;
  }

  function ensureGuestToken() {
    try {
      var existing = localStorage.getItem(guestKey) || "";
      if (existing && existing.length >= 8) {
        return existing;
      }
      var token =
        "g" +
        Date.now().toString(36) +
        Math.random().toString(36).slice(2, 10);
      localStorage.setItem(guestKey, token);
      return token;
    } catch (e) {
      return "g" + Date.now().toString(36);
    }
  }

  function setBadge(count) {
    if (!badgeEl) {
      return;
    }
    var n = parseInt(String(count), 10) || 0;
    if (n > 0) {
      badgeEl.hidden = false;
      badgeEl.textContent = n > 9 ? "!" : "!";
    } else {
      badgeEl.hidden = true;
    }
  }

  function refreshUnread() {
    fetch(restUnread, { headers: authHeaders() })
      .then(function (r) {
        return r.ok ? r.json() : { unread: 0 };
      })
      .then(function (data) {
        setBadge(data && data.unread);
      })
      .catch(function () {
        setBadge(0);
      });
  }

  function renderThread(messages) {
    if (!threadEl) {
      return;
    }
    threadEl.innerHTML = "";
    if (!messages || !messages.length) {
      threadEl.hidden = true;
      return;
    }
    threadEl.hidden = false;
    messages.forEach(function (msg) {
      var row = document.createElement("div");
      row.className =
        "rl-support-msg rl-support-msg--" +
        (msg.from === "owner" ? "owner" : "user");
      row.textContent = msg.body || "";
      threadEl.appendChild(row);
    });
    threadEl.scrollTop = threadEl.scrollHeight;
  }

  function loadThread() {
    return fetch(restThread, { headers: authHeaders() })
      .then(function (r) {
        return r.ok ? r.json() : { messages: [] };
      })
      .then(function (data) {
        renderThread((data && data.messages) || []);
        setBadge(0);
      })
      .catch(function () {
        renderThread([]);
      });
  }

  function resetComposer() {
    if (textarea) {
      textarea.hidden = false;
      textarea.value = "";
    }
    if (submit) {
      submit.hidden = false;
      submit.disabled = false;
      submit.textContent = "Отправить →";
    }
    if (success) {
      success.hidden = true;
    }
  }

  function openModal() {
    modal.hidden = false;
    resetComposer();
    loadThread().then(function () {
      if (textarea) {
        textarea.focus();
      }
    });
  }

  function closeModal() {
    modal.hidden = true;
  }

  fab.addEventListener("click", openModal);
  if (closeBtn) {
    closeBtn.addEventListener("click", closeModal);
  }
  if (overlay) {
    overlay.addEventListener("click", closeModal);
  }

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !modal.hidden) {
      closeModal();
    }
  });

  if (submit) {
    submit.addEventListener("click", function () {
      var msg = textarea ? textarea.value.trim() : "";
      if (!msg) {
        return;
      }
      submit.disabled = true;
      submit.textContent = "Отправляем...";
      var source =
        document.body && document.body.classList.contains("page-contact")
          ? "contact"
          : "fab";
      fetch(restTicket, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          message: msg,
          url: location.href,
          source: source,
        }),
      })
        .then(function (r) {
          if (!r.ok) {
            throw new Error("send failed");
          }
          return r.json();
        })
        .then(function () {
          submit.hidden = true;
          if (textarea) {
            textarea.hidden = true;
          }
          if (success) {
            success.hidden = false;
          }
          return loadThread();
        })
        .catch(function () {
          submit.disabled = false;
          submit.textContent = "Отправить →";
          if (textarea) {
            textarea.focus();
          }
        })
        .finally(function () {
          window.setTimeout(function () {
            if (!modal.hidden && success && !success.hidden) {
              resetComposer();
              closeModal();
            }
          }, 2200);
        });
    });
  }

  refreshUnread();
  window.setInterval(refreshUnread, 60000);

  var contactForm = document.getElementById("rl-contact-form");
  if (contactForm) {
    contactForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var msgEl = document.getElementById("rl-contact-message");
      var nameEl = document.getElementById("rl-contact-name");
      var btn = document.getElementById("rl-contact-submit");
      var okEl = document.getElementById("rl-contact-success");
      var msg = msgEl ? msgEl.value.trim() : "";
      if (!msg) {
        return;
      }
      if (btn) {
        btn.disabled = true;
        btn.textContent = "Отправляем...";
      }
      fetch(restTicket, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          message: msg,
          contact_name: nameEl ? nameEl.value.trim() : "",
          url: location.href,
          source: "contact",
        }),
      })
        .then(function (r) {
          if (!r.ok) {
            throw new Error("send failed");
          }
          return r.json();
        })
        .then(function () {
          if (msgEl) {
            msgEl.value = "";
          }
          if (nameEl) {
            nameEl.value = "";
          }
          if (okEl) {
            okEl.hidden = false;
          }
          refreshUnread();
        })
        .catch(function () {
          if (btn) {
            btn.disabled = false;
            btn.textContent = "Отправить →";
          }
        });
    });
  }
})();
