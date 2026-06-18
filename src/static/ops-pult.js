(function () {
  var meta = document.querySelector('meta[name="rl-ops-api-base"]');
  var API = (meta && meta.getAttribute("content")) || "/ops";
  function ctlFetchErr(r, body) {
    if (body && typeof body.detail === "string" && body.detail) return body.detail;
    if (body && typeof body.message === "string" && body.message) return body.message;
    return "HTTP " + r.status;
  }
  function showToast(msg, isErr) {
    var el = document.getElementById("rl-toast");
    if (!el) return;
    el.textContent = msg || "";
    el.style.borderColor = isErr ? "#7f1d1d" : "#334155";
    el.classList.add("is-visible");
    clearTimeout(showToast._t);
    showToast._t = setTimeout(function () { el.classList.remove("is-visible"); }, 3000);
  }
  function postControl(body, btn, statusEl) {
    if (statusEl) {
      statusEl.className = "ctl-status is-working";
      statusEl.innerHTML = '<span class="dot"></span><span>Выполняем…</span>';
    }
    if (btn) btn.disabled = true;
    var old = btn ? btn.textContent : "";
    if (btn) btn.textContent = "…";
    return fetch(API + "/control", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    }).then(function (r) {
      return r.json().catch(function () { return null; }).then(function (data) {
        if (!r.ok) throw new Error(ctlFetchErr(r, data));
        return data;
      });
    }).then(function (data) {
      var msg = (data && data.message) ? data.message : "Команда отправлена";
      if (statusEl) {
        statusEl.className = "ctl-status is-ok";
        statusEl.innerHTML = '<span class="dot"></span><span>' + msg + "</span>";
      }
      showToast(msg, false);
      return data;
    }).catch(function (e) {
      var msg = (e && e.message) || "Команда не выполнена";
      if (statusEl) {
        statusEl.className = "ctl-status is-bad";
        statusEl.innerHTML = '<span class="dot"></span><span>' + msg + "</span>";
      }
      showToast(msg, true);
      throw e;
    }).finally(function () {
      if (btn) {
        btn.disabled = false;
        btn.textContent = old;
      }
    });
  }
  document.querySelectorAll(".rl-ctl").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var action = btn.getAttribute("data-action") || "";
      var target = btn.getAttribute("data-target") || "";
      if (!action || !target) return;
      var ctl = document.getElementById("rl-ops-control-status");
      postControl({ action: action, target: target }, btn, ctl);
    });
  });
  function bindRestartSourceDelegation() {
    var exEl = document.getElementById("rl-ops-exchanges");
    if (!exEl || exEl._rlRestartBound) return;
    exEl._rlRestartBound = true;
    exEl.addEventListener("click", function (ev) {
      var btn = ev.target && ev.target.closest
        ? ev.target.closest(".rl-restart-source")
        : null;
      if (!btn || !exEl.contains(btn)) return;
      var target = btn.getAttribute("data-target") || "";
      if (!target) return;
      ev.preventDefault();
      postControl({ action: "restart_source", target: target }, btn, null);
    });
  }
  bindRestartSourceDelegation();
  document.querySelectorAll(".rl-hide").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var id = btn.getAttribute("data-id");
      btn.disabled = true;
      fetch(API + "/leads/" + id + "/hide", {
        method: "POST",
        credentials: "same-origin"
      }).then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        btn.textContent = "Скрыт";
      }).catch(function () {
        btn.disabled = false;
        alert("Не удалось скрыть lead #" + id);
      });
    });
  });
  var supportEl = document.getElementById("rl-ops-support");
  if (supportEl) {
    fetch(API + "/support/tickets", {
      credentials: "same-origin"
    }).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    }).then(function (data) {
      var tickets = (data && data.tickets) || [];
      if (!tickets.length) {
        supportEl.innerHTML = '<p class="sub">Тикетов пока нет.</p>';
        return;
      }
      supportEl.innerHTML = tickets.map(function (t) {
        var who = t.tg_username ? ("@" + t.tg_username) : (t.user_id || t.guest_token || "—");
        return '<div class="card" style="margin-bottom:.75rem">'
          + '<p><strong>#' + t.id + '</strong> · ' + who + ' · ' + (t.last_preview || "") + '</p>'
          + '<textarea class="rl-ops-reply" data-id="' + t.id + '" rows="2" style="width:100%;margin:.35rem 0"></textarea>'
          + '<button type="button" class="btn rl-ops-reply-btn" data-id="' + t.id + '">Ответить</button>'
          + '</div>';
      }).join("");
      supportEl.querySelectorAll(".rl-ops-reply-btn").forEach(function (btn) {
        btn.addEventListener("click", function () {
          var id = btn.getAttribute("data-id");
          var area = supportEl.querySelector('.rl-ops-reply[data-id="' + id + '"]');
          var text = area ? area.value.trim() : "";
          if (!text) return;
          btn.disabled = true;
          fetch(API + "/support/tickets/" + id + "/reply", {
            method: "POST",
            credentials: "same-origin",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
          }).then(function (r) {
            if (!r.ok) throw new Error("HTTP " + r.status);
            btn.textContent = "Отправлено";
            if (area) area.value = "";
          }).catch(function () {
            btn.disabled = false;
            alert("Не удалось ответить в тикет #" + id);
          });
        });
      });
    }).catch(function () {
      supportEl.innerHTML = '<p class="err">Поддержка: ошибка загрузки.</p>';
    });
  }
  function logClass(line) {
    var s = line || "";
    if (s.indexOf("── Цикл ──") >= 0) return "log-cycle";
    if (/fetch:(fl|kwork|youdo)/.test(s)) return "log-fetch";
    if (/listing:(fl|kwork|youdo).*parsed=/.test(s)) return "log-listing";
    if (/wall-clock|watchdog|timeout/i.test(s)) return "log-warn";
    if (/ошибка|error|err=|HTTP [45]/i.test(s)) return "log-err";
    if (/тг:|tg:/i.test(s)) return "log-tg";
    if (/neon_insert/.test(s)) return "log-neon";
    return "";
  }
  function appendLogLine(pre, line, stick) {
    if (!pre || !line) return;
    var span = document.createElement("span");
    var cls = logClass(line);
    if (cls) span.className = cls;
    span.style.display = "block";
    span.textContent = line;
    pre.appendChild(span);
    while (pre.childNodes.length > 800) pre.removeChild(pre.firstChild);
    if (stick !== false) pre.scrollTop = pre.scrollHeight;
  }
  function bindLogStream() {
    var pre = document.getElementById("rl-ops-log");
    var pauseBtn = document.getElementById("rl-ops-log-pause");
    var statusEl = document.getElementById("rl-ops-log-status");
    if (!pre) return;
    var paused = false;
    var userScrolled = false;
    pre.addEventListener("scroll", function () {
      userScrolled = pre.scrollTop + pre.clientHeight < pre.scrollHeight - 40;
    });
    if (pauseBtn) {
      pauseBtn.addEventListener("click", function () {
        paused = !paused;
        pauseBtn.textContent = paused ? "▶ Live" : "⏸ Пауза";
        if (statusEl) statusEl.textContent = paused ? "Пауза" : "Live";
        if (!paused) connect();
      });
    }
    var es = null;
    function connect() {
      if (paused || typeof EventSource === "undefined") return;
      if (es) { try { es.close(); } catch (e) {} es = null; }
      es = new EventSource("/ops/log/stream");
      es.onmessage = function (ev) {
        if (paused) return;
        var stick = !userScrolled;
        appendLogLine(pre, ev.data || "", stick);
      };
      es.onerror = function () {
        if (es) { try { es.close(); } catch (e) {} es = null; }
        if (!paused) setTimeout(connect, 2000);
      };
    }
    connect();
  }
  function refreshSummary() {
    fetch(API + "/dashboard", { credentials: "same-origin" })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(function (data) {
        var cards = document.getElementById("rl-ops-cards");
        if (!cards || !data) return;
        var t = data.today || {};
        var radar = data.radar || {};
        var feed = data.feed || {};
        var bot = data.bot || {};
        var prob = data.problems || {};
        function setCard(idx, val, hint) {
          var card = cards.children[idx];
          if (!card) return;
          var valEl = card.querySelector(".val");
          var hintEl = card.querySelector(".hint");
          if (valEl) valEl.textContent = val;
          if (hintEl && hint) hintEl.textContent = hint;
        }
        setCard(0, (t.visits || 0) + " просмотров",
          "Уникальных: " + (t.unique_visits || 0) + " · Новых: " + (t.new_users || 0));
        setCard(1, radar.status_label || "—", radar.hint || "");
        setCard(2, (feed.visible_count || 0) + " заказов", "Видимых на /lenta/");
        setCard(3, (bot.push_subscribers || 0) + " с push", "@rawlead_bot / @FLPARSINGBOT");
        setCard(4, (prob.auth_errors_24h || 0) + " вход · " + (prob.fetch_errors_24h || 0) + " парсер",
          "Детали — radar.log");
        var updated = document.getElementById("rl-ops-updated");
        if (updated) updated.textContent = "Обновлено " + new Date().toLocaleString("ru-RU");
      }).catch(function () {});
  }
  function scrollToSection(id, group) {
    var el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    if (group) {
      var proxy = document.querySelector('.ops-proxy-group[data-group="' + group + '"]');
      if (proxy) proxy.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }
  function bindFunnelAction(btn) {
    if (!btn || btn.getAttribute("data-bound")) return;
    btn.setAttribute("data-bound", "1");
    var target = btn.getAttribute("data-target") || "";
    var action = btn.getAttribute("data-action") || "";
    if (target && action) {
      btn.addEventListener("click", function () {
        postControl(
          { action: action, target: target },
          btn,
          document.getElementById("rl-ops-control-status")
        );
      });
      return;
    }
    btn.addEventListener("click", function () {
      scrollToSection(btn.getAttribute("data-scroll") || "", btn.getAttribute("data-group") || "");
    });
  }
  function lampClass(status) {
    return "ops-lamp ops-lamp--" + (status || "warn");
  }
  function renderFunnel(data) {
    if (!data) return;
    var bar = document.getElementById("rl-ops-lamp-bar");
    var diag = document.getElementById("rl-ops-diagnosis");
    var grid = document.getElementById("rl-ops-funnels");
    var hint = document.getElementById("rl-ops-funnel-hint");
    if (!bar || !grid) return;
    var lamps = data.lamps || {};
    var l1 = data.l1 || {};
    var order = ["radar", "fl", "kwork", "youdo", "tg"];
    bar.innerHTML = order.map(function (key) {
      var item = lamps[key] || {};
      var target = key === "radar" ? "ops-summary" : "ops-funnels-" + key;
      return '<button type="button" class="' + lampClass(item.status) + '" data-scroll="' + target + '">'
        + (item.status === "ok" ? "🟢" : item.status === "bad" ? "🔴" : "🟡") + " "
        + (item.label || key) + "</button>";
    }).join("")
      + '<span class="ops-lamp__l1">L1 '
      + (l1.status === "ok" ? "🟢" : l1.status === "bad" ? "🔴" : "🟡") + " "
      + (l1.label || "") + "</span>";
    bar.querySelectorAll("[data-scroll]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var id = btn.getAttribute("data-scroll") || "";
        if (id.indexOf("ops-funnels-") === 0) {
          var card = document.getElementById(id);
          if (card) card.scrollIntoView({ behavior: "smooth", block: "start" });
        } else {
          scrollToSection(id);
        }
      });
    });
    if (diag) {
      var d = data.diagnosis;
      if (d && d.text) {
        diag.hidden = false;
        diag.className = "ops-diagnosis" + (d.level === "warn" ? " ops-diagnosis--warn" : "");
        var act = d.action || {};
        var actBtn = "";
        if (act.label) {
          if (act.target && act.action) {
            actBtn = '<div class="ops-diagnosis__action"><button type="button" class="btn rl-funnel-action" data-target="'
              + act.target + '" data-action="' + act.action + '">' + act.label + "</button></div>";
          } else {
            actBtn = '<div class="ops-diagnosis__action"><button type="button" class="btn rl-funnel-action" data-scroll="'
              + (act.scroll_to || "") + '" data-group="' + (act.group || "") + '">' + act.label + "</button></div>";
          }
        }
        diag.innerHTML = "<div>" + (d.level === "bad" ? "🔴 " : "🟡 ") + d.text + "</div>" + actBtn;
        diag.querySelectorAll(".rl-funnel-action").forEach(bindFunnelAction);
      } else {
        diag.hidden = true;
        diag.innerHTML = "";
      }
    }
    grid.innerHTML = (data.sources || []).map(function (src) {
      var steps = (src.steps || []).map(function (st) {
        var dotCls = "ops-truth-step__dot ops-truth-step__dot--" + (st.status || "na");
        return '<div class="ops-truth-step' + (st.is_break ? " is-break" : "") + '" title="' + (st.tooltip || "") + '">'
          + '<span class="ops-truth-step__label">' + (st.label || st.id) + '</span>'
          + '<span class="' + dotCls + '"></span></div>';
      }).join("");
      var meta = src.meta || {};
      var metaLine = "сегодня " + (meta.new_today != null ? meta.new_today : "—")
        + " · за 24ч " + (meta.new_24h != null ? meta.new_24h : "—")
        + (meta.lag_min != null ? " · lag " + meta.lag_min + " мин" : "");
      var parsedTip = meta.parsed_title
        || ("разбор: " + (meta.parsed != null ? meta.parsed : "—") + " карточек за цикл");
      var muted = src.muted_note ? '<p class="ops-funnel-meta">' + src.muted_note + "</p>" : "";
      var tgLink = src.source_id === "tg"
        ? ' · <button type="button" class="btn btn-ghost rl-scroll-tg">Подробнее → TG</button>' : "";
      return '<div class="ops-funnel-card" id="ops-funnels-' + src.source_id + '">'
        + '<div class="ops-funnel-card__head"><span>' + (src.name || src.source_id) + '</span>'
        + '<span>' + (src.headline || "") + "</span></div>"
        + '<div class="ops-truth-ladder">' + steps + "</div>"
        + '<p class="ops-funnel-meta" title="' + parsedTip + '">' + metaLine + tgLink + "</p>" + muted + "</div>";
    }).join("");
    grid.querySelectorAll(".rl-scroll-tg").forEach(function (b) {
      b.addEventListener("click", function () { scrollToSection("ops-tg"); });
    });
    if (hint) {
      var age = data.cycle_age_min;
      hint.textContent = "Обновлено только что"
        + (age != null ? " · цикл радара " + age + " мин назад" : "");
    }
  }
  function renderTg(data) {
    if (!data) return;
    var bot = document.getElementById("rl-ops-tg-botapi");
    var tbody = document.getElementById("rl-ops-tg-tbody");
    var cards = document.getElementById("rl-ops-tg-cards");
    var queueHint = document.getElementById("rl-ops-tg-queue-hint");
    var b = data.botapi || {};
    var q = data.queue || {};
    if (bot) {
      bot.innerHTML = '<p><strong>Bot API:</strong> слот ' + (b.active_slot || "?") + " ● активен · "
        + "Авто: " + (b.auto_failover ? "вкл" : "выкл") + " · свободно " + (b.free || 0) + " из " + (b.total || 0)
        + "</p>"
        + (b.last_switch_at ? '<p class="sub">Последнее переключение: ' + b.last_switch_at + "</p>" : "")
        + '<button type="button" class="btn btn-ghost rl-scroll-proxy-tg">Открыть прокси TG →</button>';
      bot.querySelectorAll(".rl-scroll-proxy-tg").forEach(function (btn) {
        btn.addEventListener("click", function () { scrollToSection("ops-proxies", "tg-bot"); });
      });
    }
    function rowActions(acc) {
      var btns = [];
      if (acc.join_status === "pending" || acc.state === "join_pending") {
        btns.push('<button type="button" class="btn rl-tg-ctl" data-action="tg-join-tick" data-target="tg">Докрутить join</button>');
      } else {
        btns.push('<button type="button" class="btn rl-tg-ctl" data-action="tg-join-restart" data-target="tg">Перезапустить join</button>');
      }
      btns.push('<button type="button" class="btn" disabled title="Скоро">CRUD</button>');
      return btns.join(" ");
    }
    function tgListenLine(acc) {
      if (acc.listen_line) {
        return acc.listen_line;
      }
      var peers = acc.peers_count || acc.listen_count || 0;
      var file = acc.file_count || 0;
      var filt = acc.filter_count || 0;
      return "Слушают " + peers + " · вступили " + file + " · после фильтра " + filt;
    }
    function tgListenTitle(acc) {
      return acc.listen_title || "Сейчас в эфире / Вступили / После фильтра — три числа";
    }
    function tgMsgsLine(acc) {
      if (acc.msgs_line) {
        return acc.msgs_line;
      }
      return "—";
    }
    function tgMsgsTitle(acc) {
      return acc.msgs_title || "Сессия = с последнего рестарта радара · Всего = накопительно";
    }
    function tgLampReason(acc) {
      return acc.lamp_reason_ru || acc.state_label || "";
    }
    if (tbody) {
      tbody.innerHTML = (data.accounts || []).map(function (acc) {
        var icon = acc.lamp === "ok" ? "🟢" : acc.lamp === "bad" ? "🔴" : "🟡";
        return "<tr><td title=\"Номер TG на VPS: acc1/acc2/acc3\">" + acc.id + "</td><td title=\"" + tgLampReason(acc) + "\">" + icon + " " + (acc.state_label || "") + "</td>"
          + "<td title=\"" + tgListenTitle(acc) + "\">" + tgListenLine(acc) + "</td>"
          + "<td title=\"" + tgMsgsTitle(acc) + "\">" + tgMsgsLine(acc) + "</td>"
          + "<td title=\"Статус очереди join для этого acc\">" + (acc.join_label || "—") + "</td>"
          + "<td title=\"3 подряд fail → пауза вступлений\">" + (acc.strikes || "0/3") + "</td>"
          + "<td>" + rowActions(acc) + "</td></tr>";
      }).join("");
    }
    if (cards) {
      cards.innerHTML = (data.accounts || []).map(function (acc) {
        var icon = acc.lamp === "ok" ? "🟢" : acc.lamp === "bad" ? "🔴" : "🟡";
        return '<div class="ops-tg-card"><p class="ops-tg-card__title" title="' + tgLampReason(acc) + '">' + acc.id.toUpperCase()
          + " · " + icon + " " + (acc.state_label || "") + "</p>"
          + '<p class="ops-tg-card__row" title="' + tgListenTitle(acc) + '">' + tgListenLine(acc) + "</p>"
          + '<p class="ops-tg-card__row" title="' + tgMsgsTitle(acc) + '">' + tgMsgsLine(acc) + " · вступления "
          + (acc.join_label || "—") + "</p>"
          + '<p class="ops-tg-card__row">Ошибки join ' + (acc.strikes || "0/3") + "</p>"
          + rowActions(acc) + "</div>";
      }).join("");
    }
    if (queueHint) {
      queueHint.textContent = q.hint_ru || (
        "Очередь: " + (q.done || 0) + " готово · " + (q.pending || 0) + " ждут · "
        + (q.fail || 0) + " ошибка · лимит " + (q.max_per_hour || "?") + "/ч"
      );
      queueHint.title = "Статус CSV-очереди join по всем аккаунтам";
    }
    document.querySelectorAll(".rl-tg-ctl").forEach(function (btn) {
      if (btn.getAttribute("data-bound")) return;
      btn.setAttribute("data-bound", "1");
      btn.addEventListener("click", function () {
        var statusEl = document.getElementById("rl-ops-tg-status");
        postControl({
          action: btn.getAttribute("data-action") || "",
          target: btn.getAttribute("data-target") || "tg"
        }, btn, statusEl);
      });
    });
  }
  function refreshFunnelTg() {
    Promise.all([
      fetch(API + "/funnel", { credentials: "same-origin" }).then(function (r) {
        if (!r.ok) throw new Error("funnel HTTP " + r.status);
        return r.json();
      }),
      fetch(API + "/tg", { credentials: "same-origin" }).then(function (r) {
        if (!r.ok) throw new Error("tg HTTP " + r.status);
        return r.json();
      })
    ]).then(function (pair) {
      renderFunnel(pair[0]);
      renderTg(pair[1]);
    }).catch(function (e) {
      var msg = (e && e.message) || "Ошибка загрузки воронки/TG";
      var hint = document.getElementById("rl-ops-funnel-hint");
      if (hint) hint.textContent = msg;
      var grid = document.getElementById("rl-ops-funnels");
      if (grid && /Загрузка/i.test(grid.textContent || "")) {
        grid.innerHTML = '<p class="err">' + msg + "</p>";
      }
    });
  }
  function dotLevel(level) {
    var lv = (level === "ok" || level === "warn" || level === "bad") ? level : "warn";
    return '<span class="dot dot--' + lv + '"></span>';
  }
  function needsDashboardHydrate() {
    var bots = document.getElementById("rl-ops-bots");
    return !!(bots && !bots.innerHTML.trim());
  }
  function startDashboardLoadingTimer(botsEl, exEl) {
    var t0 = Date.now();
    var tid = setInterval(function () {
      var sec = ((Date.now() - t0) / 1000).toFixed(0);
      if (botsEl && /Загрузка/i.test(botsEl.textContent || "")) {
        botsEl.innerHTML = '<p class="sub">Загрузка… ' + sec + 'с</p>';
      }
      if (exEl && /Загрузка/i.test(exEl.textContent || "")) {
        exEl.innerHTML = '<p class="sub">Загрузка… ' + sec + 'с</p>';
      }
    }, 1000);
    return tid;
  }
  function renderBotsHtml(bots) {
    if (!bots || !bots.length) {
      return '<div class="card"><p class="hint">Нет данных о ботах</p></div>';
    }
    return bots.map(function (b) {
      var hint = "is-active: " + (b.is_active || "unknown");
      if (b.last_cmd) hint += " · " + b.last_cmd;
      return '<div class="card"><h2>' + dotLevel(b.level) + (b.username || "—") + "</h2>"
        + '<p class="val">' + (b.is_active || "unknown") + "</p>"
        + '<p class="hint">' + hint + '</p>'
        + '<button class="btn rl-ctl" data-target="' + (b.target || "") + '" data-action="restart">Перезапуск</button></div>';
    }).join("");
  }
  function renderExchangesHtml(rows) {
    if (!rows || !rows.length) {
      return '<div class="card"><p class="hint">Нет данных о биржах</p></div>';
    }
    var restartSources = { fl: 1, kwork: 1, youdo: 1, tg: 1 };
    return rows.map(function (row) {
      var sid = row.source_id || "";
      var err = row.error_human
        ? '<p class="exchange-meta err">' + row.error_human + "</p>" : "";
      var restart = restartSources[sid]
        ? '<button type="button" class="btn rl-restart-source" data-target="' + sid + '">Перезапустить источник</button>'
        : "";
      var cycleHint = row.cycle_hint
        ? '<p class="exchange-meta">' + row.cycle_hint + "</p>" : "";
      var tierHint = row.residential_hint
        ? '<p class="exchange-meta">' + row.residential_hint + "</p>" : "";
      return '<div class="card exchange-card"><h2>' + dotLevel(row.exchange_level || row.level) + "</h2>"
        + '<p class="exchange-title">' + (row.exchange_icon || "🟡") + " " + (row.name || "—")
        + " — " + (row.exchange_status_ru || "—") + "</p>"
        + '<p class="exchange-meta">Последний цикл: ' + (row.last_ok_ago || "нет данных") + "</p>"
        + '<p class="exchange-meta">Сегодня найдено новых заказов: ' + (row.today_new_ids || 0) + "</p>"
        + cycleHint
        + tierHint
        + '<p class="exchange-meta">Последнее: ' + (row.last_log_line || row.listing_line || "—") + "</p>"
        + err + '<div class="exchange-actions">' + restart + "</div></div>";
    }).join("");
  }
  function hydrateDashboardFallback() {
    if (!needsDashboardHydrate()) return;
    var botsEl = document.getElementById("rl-ops-bots");
    var exEl = document.getElementById("rl-ops-exchanges");
    var timerId = startDashboardLoadingTimer(botsEl, exEl);
    fetch(API + "/dashboard", { credentials: "same-origin" })
      .then(function (r) {
        if (!r.ok) throw new Error("dashboard HTTP " + r.status);
        return r.json();
      })
      .then(function (data) {
        clearInterval(timerId);
        var updated = document.getElementById("rl-ops-updated");
        if (updated) updated.textContent = "Обновлено " + new Date().toLocaleString("ru-RU");
        var botsEl = document.getElementById("rl-ops-bots");
        if (botsEl) botsEl.innerHTML = renderBotsHtml(data.bots || []);
        var botsCtl = document.getElementById("rl-ops-bots-ctl");
        if (botsCtl && !botsCtl.innerHTML.trim()) {
          botsCtl.innerHTML = '<button class="btn rl-ctl" data-target="bots-both" data-action="restart">Перезапуск обоих ботов</button>';
        }
        var exEl = document.getElementById("rl-ops-exchanges");
        if (exEl) exEl.innerHTML = renderExchangesHtml(data.exchanges || []);
        bindRestartSourceDelegation();
        var delistEl = document.getElementById("rl-ops-delist-stats");
        if (delistEl) {
          var delist = data.delist || {};
          if (delist.last_run_at) {
            delistEl.textContent = "Ссылки: последний прогон " + delist.last_run_at
              + " — проверено " + (delist.checked || 0) + ", снято " + (delist.delisted || 0);
          } else {
            delistEl.textContent = "Ссылки: автопроверка FL/Kwork ещё не запускалась";
          }
        }
        var lb = document.querySelector("#rl-ops-leads tbody");
        if (lb) {
          lb.innerHTML = (data.feed && data.feed.recent ? data.feed.recent : []).map(function (l) {
            var title = (l.title || "—").slice(0, 80);
            return "<tr><td>" + l.id + "</td><td>" + (l.source || "—") + "</td><td>"
              + title + '</td><td><button class="btn rl-hide" data-id="' + l.id + '">Скрыть</button></td></tr>';
          }).join("");
        }
        var vb = document.querySelector("#rl-ops-views tbody");
        if (vb) {
          vb.innerHTML = (data.pageviews || []).map(function (v) {
            return "<tr><td>" + v.day + "</td><td>" + v.path + "</td><td>" + v.views + "</td></tr>";
          }).join("");
        }
        if (data.proxies && window.rlOpsRenderProxies) window.rlOpsRenderProxies(data.proxies);
        if (data.funnel) renderFunnel(data.funnel);
        if (data.tg) renderTg(data.tg);
        refreshSummary();
      })
      .catch(function (e) {
        clearInterval(timerId);
        var msg = (e && e.message) || "Ошибка загрузки dashboard";
        if (botsEl && !botsEl.innerHTML.trim()) botsEl.innerHTML = '<p class="err">' + msg + "</p>";
        if (exEl && !exEl.innerHTML.trim()) exEl.innerHTML = '<p class="err">' + msg + "</p>";
        var pb = document.getElementById("rl-ops-proxies-body");
        if (pb && /Загрузка/i.test(pb.textContent || "")) pb.innerHTML = '<p class="err">' + msg + "</p>";
      });
  }
  bindLogStream();
  document.querySelectorAll(".rl-funnel-action, .rl-scroll-proxy-tg, .rl-scroll-tg").forEach(function (btn) {
    if (btn.classList.contains("rl-funnel-action")) {
      bindFunnelAction(btn);
      return;
    }
    btn.addEventListener("click", function () {
      scrollToSection(btn.getAttribute("data-scroll") || "ops-proxies", btn.getAttribute("data-group") || "tg-bot");
    });
  });
  document.querySelectorAll(".rl-tg-ctl").forEach(function (btn) {
    btn.addEventListener("click", function () {
      postControl({
        action: btn.getAttribute("data-action") || "",
        target: btn.getAttribute("data-target") || "tg"
      }, btn, document.getElementById("rl-ops-tg-status"));
    });
  });
  refreshFunnelTg();
  hydrateDashboardFallback();
  setInterval(refreshFunnelTg, 30000);
  function bindMiniNav() {
    var nav = document.getElementById("rl-ops-mini-nav");
    if (!nav) return;
    var chips = nav.querySelectorAll(".chip");
    var sections = ["ops-summary","ops-bots","ops-exchanges","ops-tg","ops-proxies","ops-controls","ops-logs","ops-leads"];
    function setActive(id) {
      chips.forEach(function (c) {
        c.classList.toggle("is-active", c.getAttribute("data-target") === id);
      });
    }
    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        var id = chip.getAttribute("data-target") || "";
        var el = document.getElementById(id);
        if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
        setActive(id);
      });
    });
    if (typeof IntersectionObserver !== "undefined") {
      var io = new IntersectionObserver(function (entries) {
        var best = null;
        entries.forEach(function (e) {
          if (e.isIntersecting) {
            if (!best || e.intersectionRatio > best.ratio) {
              best = { id: e.target.id, ratio: e.intersectionRatio };
            }
          }
        });
        if (best && best.id) setActive(best.id);
      }, { rootMargin: "-20% 0px -55% 0px", threshold: [0.1, 0.35, 0.6] });
      sections.forEach(function (sid) {
        var el = document.getElementById(sid);
        if (el) io.observe(el);
      });
    }
  }
  function setProxyStatus(kind, text) {
    var el = document.getElementById("rl-ops-proxy-status");
    if (!el) return;
    el.className = "ctl-status" + (kind ? " is-" + kind : "");
    el.innerHTML = '<span class="dot"></span><span>' + text + "</span>";
  }
  function showProbeResult(group, slot, probe) {
    var box = document.getElementById("ops-probe-" + group + "-" + slot);
    if (!box || !probe) return;
    var tcp = probe.tcp || {};
    var https = probe.https || {};
    box.className = "ops-proxy-probe is-open";
    box.innerHTML = "TCP: " + (tcp.ok ? "OK" : "FAIL") + " — " + (tcp.message || "")
      + "<br>HTTPS: " + (https.ok ? "OK" : "FAIL") + " — " + (https.message || "")
      + (https.target ? " → " + https.target : "");
  }
  function postProxyControl(body, btn) {
    setProxyStatus("working", "Выполняем…");
    if (btn) btn.disabled = true;
    return fetch(API + "/control", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    }).then(function (r) {
      return r.json().catch(function () { return null; }).then(function (data) {
        if (!r.ok) throw new Error(ctlFetchErr(r, data));
        return data;
      });
    }).then(function (data) {
      if (data && data.ok === false) {
        setProxyStatus("bad", (data && data.message) ? data.message : "Ошибка");
        return data;
      }
      setProxyStatus("ok", (data && data.message) ? data.message : "Готово");
      showToast((data && data.message) ? data.message : "Готово", false);
      if (data && data.probe && body.group && body.slot) {
        showProbeResult(body.group, body.slot, data.probe);
      }
      if (data && data.results) {
        data.results.forEach(function (item) {
          showProbeResult(item.group, item.slot, item.probe);
        });
      }
      if (data && data.proxies && window.rlOpsRenderProxies) {
        window.rlOpsRenderProxies(data.proxies);
      }
      return data;
    }).catch(function (e) {
      setProxyStatus("bad", (e && e.message) || "Ошибка");
      showToast((e && e.message) || "Ошибка", true);
      throw e;
    }).finally(function () {
      if (btn) btn.disabled = false;
    });
  }
  function bindProxyControls() {
    document.querySelectorAll(".rl-proxy-probe:not([data-bound])").forEach(function (btn) {
      btn.setAttribute("data-bound", "1");
      btn.addEventListener("click", function () {
        postProxyControl({
          target: "proxy",
          action: "probe",
          group: btn.getAttribute("data-group") || "",
          slot: parseInt(btn.getAttribute("data-slot") || "0", 10)
        }, btn);
      });
    });
    document.querySelectorAll(".rl-proxy-switch:not([data-bound])").forEach(function (btn) {
      btn.setAttribute("data-bound", "1");
      btn.addEventListener("click", function () {
        if (btn.disabled) return;
        postProxyControl({
          target: "proxy",
          action: "switch",
          group: btn.getAttribute("data-group") || "",
          slot: parseInt(btn.getAttribute("data-slot") || "0", 10)
        }, btn);
      });
    });
    document.querySelectorAll(".rl-proxy-probe-all:not([data-bound])").forEach(function (allBtn) {
      allBtn.setAttribute("data-bound", "1");
      allBtn.addEventListener("click", function () {
        postProxyControl({ target: "proxy", action: "probe-all" }, allBtn);
      });
    });
    document.querySelectorAll(".rl-proxy-clear-bans:not([data-bound])").forEach(function (clearBtn) {
      clearBtn.setAttribute("data-bound", "1");
      clearBtn.addEventListener("click", function () {
        postProxyControl({ target: "proxy", action: "clear-bans" }, clearBtn);
      });
    });
    document.querySelectorAll(".rl-proxy-clear-youdo-bans:not([data-bound])").forEach(function (clearBtn) {
      clearBtn.setAttribute("data-bound", "1");
      clearBtn.addEventListener("click", function () {
        postProxyControl({ target: "proxy", action: "clear-youdo-bans" }, clearBtn);
      });
    });
  }
  function proxyDot(status) {
    var lv = (status === "ok" || status === "warn" || status === "bad") ? status : "warn";
    return '<span class="ops-status-dot ops-status-dot--' + lv + '"></span>';
  }
  function proxySwitchable(gid) {
    return gid === "tg-bot" || gid === "exchange-fl" || gid === "exchange-kwork" || gid === "exchange-pool";
  }
  function proxySwitchBtn(gid, sn, active, banned) {
    if (!proxySwitchable(gid)) return "";
    if (banned) {
      return '<button type="button" class="btn rl-proxy-switch" data-group="' + gid
        + '" data-slot="' + sn + '" disabled>Забанен — сначала сброс</button>';
    }
    return '<button type="button" class="btn rl-proxy-switch" data-group="' + gid + '" data-slot="' + sn + '"'
      + (active ? " disabled" : "") + ">" + (active ? "Активен" : "→ Активировать") + "</button>";
  }
  function renderProxyGroup(group) {
    var gid = group.id || "";
    var title = group.title || gid;
    var slots = group.slots || [];
    if (!slots.length) {
      return '<div class="ops-proxy-group"><h4>' + title + '</h4><p class="sub">Слотов нет</p></div>';
    }
    var rows = "";
    var cards = "";
    slots.forEach(function (slot) {
      var sn = slot.slot || 0;
      var mask = slot.mask || "—";
      var status = slot.status || "warn";
      var active = !!slot.active;
      var banned = !!slot.banned_until;
      var label = slot.status_label || "—";
      var sw = proxySwitchBtn(gid, sn, active, banned);
      var actions = '<div class="ops-proxy-actions"><button type="button" class="btn rl-proxy-probe" data-group="'
        + gid + '" data-slot="' + sn + '">Проверить</button>' + sw + "</div>";
      var probe = '<div class="ops-proxy-probe" id="ops-probe-' + gid + "-" + sn + '"></div>';
      rows += '<tr class="ops-proxy-row' + (active ? " is-active" : "") + '"><td>' + sn + '</td><td>'
        + proxyDot(status) + mask + '</td><td>' + label + '</td><td>' + actions + '</td></tr>'
        + '<tr><td colspan="4">' + probe + '</td></tr>';
      cards += '<div class="ops-proxy-card card' + (active ? " is-active" : "") + '"><p><strong>'
        + proxyDot(status) + "Слот " + sn + '</strong></p><p>' + mask + '</p><p class="hint">' + label
        + '</p>' + actions + probe + '</div>';
    });
    return '<div class="ops-proxy-group" data-group="' + gid + '"><h4>' + title + '</h4>'
      + (group.residential_active
        ? '<p class="ops-proxy-group__help ops-proxy-residential">FL сейчас работает через residential ('
          + (group.res_alive || 0) + "/" + (group.res_total || 0) + " слотов)</p>"
        : "")
      + '<div class="ops-proxy-table-wrap"><table><thead><tr><th>#</th><th>Прокси</th><th>Что значит</th><th></th></tr></thead><tbody>'
      + rows + '</tbody></table></div><div class="ops-proxy-cards">' + cards + '</div></div>';
  }
  window.rlOpsRenderProxies = function (proxies) {
    var body = document.getElementById("rl-ops-proxies-body");
    if (!body || !proxies) return;
    var html = "";
    (proxies.groups || []).forEach(function (g) { html += renderProxyGroup(g); });
    body.innerHTML = html || '<p class="sub">Нет настроенных прокси в env</p>';
    bindProxyControls();
  };
  bindMiniNav();
  bindProxyControls();
})();
