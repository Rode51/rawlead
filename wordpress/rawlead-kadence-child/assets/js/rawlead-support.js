/**
 * RawLead — FAB «Поддержка» (все shell-страницы).
 */
(function () {
  "use strict";

  var fab = document.getElementById("rl-support-fab");
  var modal = document.getElementById("rl-support-modal");
  if (!fab || !modal) {
    return;
  }

  var closeBtn = document.getElementById("rl-support-close");
  var overlay = document.getElementById("rl-support-overlay");
  var submit = document.getElementById("rl-support-submit");
  var success = document.getElementById("rl-support-success");
  var textarea = document.getElementById("rl-support-text");
  var restUrl =
    (window.rawleadSupport && window.rawleadSupport.restSupport) ||
    "/wp-json/rawlead/v1/support";

  function openModal() {
    modal.hidden = false;
    if (textarea) {
      textarea.hidden = false;
      textarea.value = "";
      textarea.focus();
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
      fetch(restUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, url: location.href }),
      }).catch(function () {
        /* stub — success anyway */
      }).finally(function () {
        submit.hidden = true;
        if (textarea) {
          textarea.hidden = true;
        }
        if (success) {
          success.hidden = false;
        }
        window.setTimeout(closeModal, 2500);
      });
    });
  }
})();
