(function () {
  "use strict";

  var cfg = window.rawleadMetrika || {};
  var id = parseInt(String(cfg.id || 0), 10);

  function goal(name) {
    if (!name || !id || typeof window.ym !== "function") {
      return;
    }
    window.ym(id, "reachGoal", name);
  }

  window.rawleadMetrikaGoal = goal;

  function trialLoginOnce(data) {
    if (!data) {
      return;
    }
    var plan = String(data.plan || "").toLowerCase();
    var status = String(data.status || "").toLowerCase();
    var isTrial = !!data.is_trial || plan === "trial" || status === "trial";
    if (!isTrial) {
      return;
    }
    var key = "rl_metrika_trial_login";
    try {
      if (sessionStorage.getItem(key)) {
        return;
      }
      sessionStorage.setItem(key, "1");
    } catch (e) {
      /* private mode */
    }
    goal("rl_trial_login");
  }

  window.rawleadMetrikaTrialLoginOnce = trialLoginOnce;

  window.addEventListener("rawlead-quiz-complete", function () {
    goal("rl_quiz_complete");
  });
})();
