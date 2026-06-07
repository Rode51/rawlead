/**
 * FAQ group accordion — O116 Z4 (/faq/ only).
 */
(function () {
  "use strict";

  var root = document.querySelector(".rl-faq-groups");
  if (!root) {
    return;
  }

  root.querySelectorAll(".rl-faq-group__header").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var group = btn.closest(".rl-faq-group");
      if (!group) {
        return;
      }
      group.classList.toggle("is-open");
    });
  });
})();
