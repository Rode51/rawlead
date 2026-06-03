"""O45/O78: /ops/ owner dashboard — plain-language health + visits."""

from __future__ import annotations

import html
import os
import re
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import psycopg
from src.storage import ProjectStorage

_LOG_TS = re.compile(
    r"^(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?)"
)
_AUTH_ERR = re.compile(r"bot_(?:auth|login):(?:fail|err)\b")
_FETCH_ERR = re.compile(r"fetch_error|fetch:(?:fl|kwork).*?(?:err|HTTP\s+[45])", re.I)

_OPS_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>RawLead — пульт</title>
<style>
:root{--ok:#22c55e;--warn:#eab308;--bad:#ef4444;--bg:#0f1419;--card:#1a2332;--line:#2a3544;--txt:#e8eaed;--muted:#94a3b8}
*{box-sizing:border-box} body{font-family:system-ui,sans-serif;margin:0;padding:1.25rem;background:var(--bg);color:var(--txt);line-height:1.45}
h1{font-size:1.35rem;margin:0 0 .25rem} .sub{color:var(--muted);font-size:.875rem;margin-bottom:1rem}
.grid{display:grid;gap:.75rem;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));margin:1rem 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:.9rem 1rem}
.card h2{font-size:.8rem;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin:0 0 .5rem;font-weight:600}
.card .val{font-size:1.5rem;font-weight:700;margin:0}
.card .hint{font-size:.8rem;color:var(--muted);margin:.35rem 0 0}
.dot{display:inline-block;width:.55rem;height:.55rem;border-radius:50%;margin-right:.35rem;vertical-align:middle}
.dot--ok{background:var(--ok)} .dot--warn{background:var(--warn)} .dot--bad{background:var(--bad)}
section{margin:1.25rem 0} section>h3{font-size:1rem;margin:0 0 .5rem}
table{border-collapse:collapse;width:100%;font-size:.85rem}
th,td{border:1px solid var(--line);padding:.35rem .5rem;text-align:left}
th{background:#121820} .err{color:var(--bad)} .btn{font-size:.75rem;padding:.2rem .45rem;border-radius:6px;border:1px solid var(--line);background:#243044;color:var(--txt);cursor:pointer}
.ctl{display:flex;flex-wrap:wrap;gap:.5rem}
.ctl .btn{padding:.45rem .7rem}
.btn:disabled{opacity:.5;cursor:default}
.ctl-status{display:flex;align-items:center;gap:.45rem;font-size:.82rem;color:var(--muted);margin-top:.55rem;min-height:1.2rem}
.ctl-status .dot{margin-right:0}
.ctl-status.is-working .dot{background:var(--warn);animation:rlPulse 1s ease-in-out infinite}
.ctl-status.is-ok .dot{background:var(--ok)}
.ctl-status.is-bad .dot{background:var(--bad)}
@keyframes rlPulse{0%{opacity:.45}50%{opacity:1}100%{opacity:.45}}
.login-box{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:1rem;margin:1rem 0}
.login-box ol{margin:.5rem 0 0 1.1rem;padding:0}
.login-box a{color:#7dd3fc}
</style>
</head>
<body>
<h1>Пульт RawLead</h1>
__LOGIN_BLOCK__
<p class="sub" id="rl-ops-status">__STATUS__</p>
<div class="grid" id="rl-ops-cards">__CARDS__</div>
<section><h3>Биржи и скорость</h3>
<div class="grid" id="rl-ops-exchanges">__EXCHANGES__</div>
</section>
<section><h3>Управление</h3><div class="ctl" id="rl-ops-controls">__CONTROLS__</div><div id="rl-ops-control-status" class="ctl-status"><span class="dot"></span><span>Ожидание команд</span></div></section>
<section><h3>Последние заказы в ленте</h3>
<table id="rl-ops-leads"><thead><tr><th>#</th><th>Источник</th><th>Заголовок</th><th></th></tr></thead><tbody>__LEADS__</tbody></table>
</section>
<section><h3>Посещения (7 дней)</h3>
<p class="sub" style="margin-top:0">По страницам — где открывали сайт. /lenta = лента, /cabinet = кабинет, / = главная.</p>
<table id="rl-ops-views"><thead><tr><th>День</th><th>Страница</th><th>Просмотры</th></tr></thead><tbody>__VIEWS__</tbody></table>
</section>
__SCRIPT__
</body>
</html>"""


_OPS_LOGIN_BLOCK = """<div class="login-box">
<p><strong>Сначала войди в кабинет</strong> — в <em>этом же браузере</em> (Chrome или Safari на телефоне, не панель Cursor):</p>
<ol>
<li><a href="/cabinet/">Открыть /cabinet/</a></li>
<li>Нажать «Войти через Telegram»</li>
<li>Вернуться сюда и обновить страницу (F5)</li>
</ol>
</div>"""

_OPS_SCRIPT_SSR = """<script>
(function () {
  var API = "__API_BASE__";
  document.querySelectorAll(".rl-ctl").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var action = btn.getAttribute("data-action") || "";
      var target = btn.getAttribute("data-target") || "";
      if (!action || !target) return;
      var ctl = document.getElementById("rl-ops-control-status");
      if (ctl) {
        ctl.className = "ctl-status is-working";
        ctl.innerHTML = '<span class="dot"></span><span>Выполняем: ' + target + " / " + action + "</span>";
      }
      btn.disabled = true;
      var old = btn.textContent;
      btn.textContent = "…";
      fetch(API + "/ops/control", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer " + (localStorage.getItem("rawlead_access_token") || "")
        },
        body: JSON.stringify({ action: action, target: target })
      }).then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      }).then(function (data) {
        if (ctl) {
          ctl.className = "ctl-status is-ok";
          ctl.innerHTML = '<span class="dot"></span><span>' + ((data && data.message) ? data.message : "Команда отправлена") + "</span>";
        }
        var st = document.getElementById("rl-ops-status");
        if (st) {
          st.textContent = (data && data.message) ? data.message : "Команда отправлена";
          st.className = "sub";
        }
      }).catch(function (e) {
        if (ctl) {
          ctl.className = "ctl-status is-bad";
          ctl.innerHTML = '<span class="dot"></span><span>' + (((e && e.message) || "Команда не выполнена")) + "</span>";
        }
        var st = document.getElementById("rl-ops-status");
        if (st) {
          st.textContent = (e && e.message) || "Команда не выполнена";
          st.className = "err";
        }
      }).finally(function () {
        btn.disabled = false;
        btn.textContent = old;
      });
    });
  });
  document.querySelectorAll(".rl-hide").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var id = btn.getAttribute("data-id");
      btn.disabled = true;
      fetch(API + "/ops/leads/" + id + "/hide", {
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
})();
</script>"""

_OPS_SCRIPT_CLIENT = """<script>
(function () {
  var API = "__API_BASE__";
  var SSR = __SSR__;
  if (SSR) return;
  var token = "";
  try {
    token = localStorage.getItem("rawlead_access_token") || "";
  } catch (e) {
    token = "";
  }
  var statusEl = document.getElementById("rl-ops-status");
  var cardsEl = document.getElementById("rl-ops-cards");
  var controlsEl = document.getElementById("rl-ops-controls");
  var controlStatusEl = document.getElementById("rl-ops-control-status");
  function dot(level) {
    return '<span class="dot dot--' + level + '"></span>';
  }
  function card(title, value, hint, level) {
    return '<div class="card"><h2>' + dot(level || "ok") + title + '</h2>'
      + '<p class="val">' + value + '</p>'
      + (hint ? '<p class="hint">' + hint + '</p>' : '') + '</div>';
  }
  function fail(msg) {
    statusEl.textContent = msg;
    statusEl.className = "err";
  }
  function bindControls(token) {
    document.querySelectorAll(".rl-ctl").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var action = btn.getAttribute("data-action") || "";
        var target = btn.getAttribute("data-target") || "";
        if (!action || !target) return;
        if (controlStatusEl) {
          controlStatusEl.className = "ctl-status is-working";
          controlStatusEl.innerHTML = '<span class="dot"></span><span>Выполняем: ' + target + " / " + action + "</span>";
        }
        btn.disabled = true;
        var old = btn.textContent;
        btn.textContent = "…";
        fetch(API + "/ops/control", {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ action: action, target: target })
        }).then(function (r) {
          if (!r.ok) throw new Error("HTTP " + r.status);
          return r.json();
        }).then(function (res) {
          if (controlStatusEl) {
            controlStatusEl.className = "ctl-status is-ok";
            controlStatusEl.innerHTML = '<span class="dot"></span><span>' + ((res && res.message) ? res.message : "Команда отправлена") + "</span>";
          }
          statusEl.textContent = (res && res.message) ? res.message : "Команда отправлена";
          statusEl.className = "sub";
        }).catch(function (e) {
          if (controlStatusEl) {
            controlStatusEl.className = "ctl-status is-bad";
            controlStatusEl.innerHTML = '<span class="dot"></span><span>' + (((e && e.message) || "Команда не выполнена")) + "</span>";
          }
          fail((e && e.message) || "Команда не выполнена");
        }).finally(function () {
          btn.disabled = false;
          btn.textContent = old;
        });
      });
    });
  }
  if (!token) {
    fail("Нет входа. Следуй шагам выше, затем обнови страницу.");
    return;
  }
  if (document.cookie.indexOf("rl_access=") === -1) {
    document.cookie = "rl_access=" + encodeURIComponent(token) + "; path=/; max-age=" + (7*24*3600) + "; secure; samesite=lax";
    location.reload();
    return;
  }
  statusEl.textContent = "Загружаем данные…";
  var ctrl = typeof AbortController !== "undefined" ? new AbortController() : null;
  var timer = ctrl ? setTimeout(function () { ctrl.abort(); }, 25000) : null;
  fetch(API + "/ops/dashboard", {
    signal: ctrl ? ctrl.signal : undefined,
    credentials: "same-origin",
    headers: { "Authorization": "Bearer " + token, "Accept": "application/json" }
  }).then(function (r) {
    if (r.status === 401) throw new Error("Сессия истекла — войди заново через /cabinet/");
    if (r.status === 403) throw new Error("Доступ только владельцу. Войди в /cabinet/ своим Telegram.");
    if (!r.ok) throw new Error("HTTP " + r.status);
    return r.json();
  }).then(function (data) {
    if (timer) clearTimeout(timer);
    statusEl.textContent = "Обновлено " + new Date().toLocaleString("ru-RU");
    statusEl.className = "sub";
    var t = data.today || {};
    var radar = data.radar || {};
    var feed = data.feed || {};
    var bot = data.bot || {};
    var prob = data.problems || {};
    var rLevel = radar.level || "warn";
    var pLevel = (prob.auth_errors_24h || 0) + (prob.fetch_errors_24h || 0) > 5 ? "bad"
      : (prob.auth_errors_24h || 0) + (prob.fetch_errors_24h || 0) > 0 ? "warn" : "ok";
    cardsEl.innerHTML =
      card("Сегодня на сайте", (t.visits || 0) + " просмотров",
        "Уникальных: " + (t.unique_visits || 0) + " · Новых: " + (t.new_users || 0), "ok")
      + card("Радар", radar.status_label || "—",
        radar.hint || "", rLevel)
      + card("Лента", (feed.visible_count || 0) + " заказов",
        "Видимых на /lenta/", "ok")
      + card("Бот", (bot.push_subscribers || 0) + " с push",
        bot.match_push_enabled === false ? "Push выключен глобально" : "Match-уведомления", "ok")
      + card("Проблемы за 24 ч",
        (prob.auth_errors_24h || 0) + " вход · " + (prob.fetch_errors_24h || 0) + " парсер",
        "Детали — radar.log", pLevel);
    var lb = document.querySelector("#rl-ops-leads tbody");
    lb.innerHTML = "";
    (feed.recent || []).forEach(function (l) {
      var tr = document.createElement("tr");
      var title = (l.title || "—").slice(0, 80);
      tr.innerHTML = "<td>" + l.id + "</td><td>" + (l.source || "—") + "</td><td>"
        + title + "</td><td><button class=\"btn rl-hide\" data-id=\"" + l.id + "\">Скрыть</button></td>";
      lb.appendChild(tr);
    });
    document.querySelectorAll(".rl-hide").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var id = btn.getAttribute("data-id");
        btn.disabled = true;
        fetch(API + "/ops/leads/" + id + "/hide", {
          method: "POST",
          credentials: "same-origin",
          headers: { "Authorization": "Bearer " + token }
        }).then(function (r) {
          if (!r.ok) throw new Error("HTTP " + r.status);
          btn.textContent = "Скрыт";
        }).catch(function () {
          btn.disabled = false;
          alert("Не удалось скрыть lead #" + id);
        });
      });
    });
    var vb = document.querySelector("#rl-ops-views tbody");
    vb.innerHTML = "";
    (data.pageviews || []).forEach(function (v) {
      var tr = document.createElement("tr");
      tr.innerHTML = "<td>" + v.day + "</td><td>" + v.path + "</td><td>" + v.views + "</td>";
      vb.appendChild(tr);
    });
    if (controlsEl && !controlsEl.innerHTML.trim()) {
      controlsEl.innerHTML =
        '<button class="btn rl-ctl" data-target="radar" data-action="pause">Radar: пауза</button>' +
        '<button class="btn rl-ctl" data-target="radar" data-action="resume">Radar: продолжить</button>' +
        '<button class="btn rl-ctl" data-target="radar" data-action="restart">Radar: перезапуск</button>' +
        '<button class="btn rl-ctl" data-target="site" data-action="restart">Site: перезапуск</button>';
    }
    bindControls(token);
  }).catch(function (e) {
    if (timer) clearTimeout(timer);
    if (e && e.name === "AbortError") {
      fail("Таймаут. Отключи блокировщик рекламы для rawlead.ru или войди через Chrome/Safari.");
      return;
    }
    fail((e && e.message) || String(e));
  });
})();
</script>"""


def owner_telegram_id() -> int | None:
    raw = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if raw.isdigit():
        return int(raw)
    return None


def is_owner_db_user(cur: Any, user_id: str) -> bool:
    owner_tid = owner_telegram_id()
    if owner_tid is not None:
        cur.execute(
            "SELECT tg_user_id FROM users WHERE id = %s::uuid",
            (user_id,),
        )
        row = cur.fetchone()
        if row and row[0] is not None and int(row[0]) == owner_tid:
            return True
    cur.execute(
        """
        SELECT s.plan FROM subscriptions s
        WHERE s.user_id = %s::uuid
        """,
        (user_id,),
    )
    sub = cur.fetchone()
    return bool(sub and str(sub[0]) == "owner")


def ensure_admin_tables(conn: Any) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_pageviews (
                path TEXT NOT NULL,
                day  DATE NOT NULL DEFAULT CURRENT_DATE,
                views INT NOT NULL DEFAULT 0,
                PRIMARY KEY (path, day)
            )
            """
        )
        cur.execute(
            """
            ALTER TABLE admin_pageviews
            ADD COLUMN IF NOT EXISTS unique_visitors INT NOT NULL DEFAULT 0
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_pageview_visitors (
                path TEXT NOT NULL,
                day  DATE NOT NULL DEFAULT CURRENT_DATE,
                visitor_id TEXT NOT NULL,
                PRIMARY KEY (path, day, visitor_id)
            )
            """
        )
    conn.commit()


def record_pageview(
    database_url: str,
    *,
    path: str,
    day: date | None = None,
    visitor_id: str = "",
) -> None:
    p = (path or "/").strip()[:200] or "/"
    if not p.startswith("/"):
        p = "/" + p
    d = day or datetime.now(timezone.utc).date()
    url = database_url.strip()
    if not url:
        return
    with psycopg.connect(url) as conn:
        ensure_admin_tables(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO admin_pageviews (path, day, views)
                VALUES (%s, %s, 1)
                ON CONFLICT (path, day) DO UPDATE
                SET views = admin_pageviews.views + 1
                """,
                (p, d),
            )
            vid = (visitor_id or "").strip()[:64]
            if vid:
                cur.execute(
                    """
                    INSERT INTO admin_pageview_visitors (path, day, visitor_id)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (p, d, vid),
                )
                if cur.rowcount > 0:
                    cur.execute(
                        """
                        UPDATE admin_pageviews
                        SET unique_visitors = unique_visitors + 1
                        WHERE path = %s AND day = %s
                        """,
                        (p, d),
                    )
        conn.commit()


def _resolve_log_path() -> Path | None:
    raw = os.environ.get("RADAR_LOG_PATH", "").strip()
    if raw:
        p = Path(raw)
        if not p.is_absolute():
            root = Path(__file__).resolve().parent.parent
            p = root / p
        return p if p.is_file() else None
    for candidate in ("data/radar_site.log", "data/radar.log"):
        p = Path(__file__).resolve().parent.parent / candidate
        if p.is_file():
            return p
    return None


def _resolve_sqlite_path() -> Path | None:
    raw = os.environ.get("SQLITE_PATH", "").strip()
    if raw:
        p = Path(raw)
        if not p.is_absolute():
            p = Path(__file__).resolve().parent.parent / p
        return p if p.is_file() else None
    p = Path(__file__).resolve().parent.parent / "data" / "projects.db"
    return p if p.is_file() else None


def _parse_log_ts(line: str) -> datetime | None:
    m = _LOG_TS.match(line.strip())
    if not m:
        return None
    raw = m.group(1).replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def count_log_errors(*, hours: int = 24, max_lines: int = 4000) -> dict[str, int]:
    """Счётчики auth/parser ошибок из хвоста radar.log."""
    path = _resolve_log_path()
    if path is None:
        return {"auth_errors_24h": 0, "fetch_errors_24h": 0}
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {"auth_errors_24h": 0, "fetch_errors_24h": 0}
    lines = text.splitlines()[-max_lines:]
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    auth = fetch = 0
    for line in lines:
        ts = _parse_log_ts(line)
        if ts is not None and ts < cutoff:
            continue
        if _AUTH_ERR.search(line):
            auth += 1
        elif _FETCH_ERR.search(line):
            fetch += 1
    return {"auth_errors_24h": auth, "fetch_errors_24h": fetch}


def _radar_snapshot() -> dict[str, Any]:
    sqlite = _resolve_sqlite_path()
    if sqlite is None:
        return {
            "level": "warn",
            "status": "unknown",
            "status_label": "Нет данных радара",
            "hint": "SQLite projects.db не найден на VPS",
            "last_cycle_at": None,
            "fl_downloaded": 0,
            "kwork_downloaded": 0,
        }
    try:
        from radar_cycle_log import load_cycle_summary
        from storage import ProjectStorage

        storage = ProjectStorage(sqlite)
        paused = storage.is_radar_paused()
        summary = load_cycle_summary(storage)
    except Exception:
        return {
            "level": "warn",
            "status": "unknown",
            "status_label": "Не удалось прочитать радар",
            "hint": "",
            "last_cycle_at": None,
            "fl_downloaded": 0,
            "kwork_downloaded": 0,
        }

    fl_dl = kw_dl = 0
    last_at = None
    if summary is not None:
        last_at = summary.ts or None
        fl = summary.ensure("fl")
        kw = summary.ensure("kwork")
        fl_dl = fl.downloaded
        kw_dl = kw.downloaded

    ingest_metrics = _ingest_metrics_snapshot()
    extra_hint = _format_ingest_hint(ingest_metrics)
    base_hint = _cycle_hint(last_at, fl_dl, kw_dl)
    full_hint = " · ".join(p for p in (base_hint, extra_hint) if p)

    if paused:
        return {
            "level": "warn",
            "status": "paused",
            "status_label": "На паузе",
            "hint": full_hint,
            "last_cycle_at": last_at,
            "fl_downloaded": fl_dl,
            "kwork_downloaded": kw_dl,
            "ingest": ingest_metrics,
        }
    return {
        "level": "ok",
        "status": "active",
        "status_label": "Сканирует заказы",
        "hint": full_hint,
        "last_cycle_at": last_at,
        "fl_downloaded": fl_dl,
        "kwork_downloaded": kw_dl,
        "ingest": ingest_metrics,
    }


def _cycle_hint(last_at: str | None, fl_dl: int, kw_dl: int) -> str:
    parts: list[str] = []
    if last_at:
        parts.append(f"Последний цикл: {last_at}")
    if fl_dl or kw_dl:
        parts.append(f"FL {fl_dl} · Kwork {kw_dl}")
    return " · ".join(parts) if parts else "Цикл ещё не завершался"


def _ingest_metrics_snapshot() -> dict[str, dict[str, int | float | str]]:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        return {}
    out: dict[str, dict[str, int | float | str]] = {}
    try:
        with psycopg.connect(url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    WITH base AS (
                      SELECT
                        CASE
                          WHEN source LIKE 'tg:%%' THEN 'tg'
                          ELSE split_part(source, ':', 1)
                        END AS source_bucket,
                        created_at,
                        l1_completed_at,
                        source_published_at
                      FROM leads
                    )
                    SELECT
                      source_bucket,
                      EXTRACT(EPOCH FROM (NOW() - MAX(created_at)))::int AS last_insert_gap_sec,
                      TO_CHAR(MAX(created_at) AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS "UTC"') AS last_insert_at,
                      COUNT(*) FILTER (
                        WHERE l1_completed_at IS NULL
                          AND created_at >= NOW() - INTERVAL '48 hours'
                      )::int AS backlog,
                      percentile_cont(0.5) WITHIN GROUP (
                        ORDER BY EXTRACT(EPOCH FROM (created_at - source_published_at))
                      ) FILTER (
                        WHERE source_published_at IS NOT NULL
                          AND created_at >= NOW() - INTERVAL '24 hours'
                      ) AS ingest_p50_sec,
                      percentile_cont(0.95) WITHIN GROUP (
                        ORDER BY EXTRACT(EPOCH FROM (created_at - source_published_at))
                      ) FILTER (
                        WHERE source_published_at IS NOT NULL
                          AND created_at >= NOW() - INTERVAL '24 hours'
                      ) AS ingest_p95_sec,
                      percentile_cont(0.5) WITHIN GROUP (
                        ORDER BY EXTRACT(EPOCH FROM (l1_completed_at - created_at))
                      ) FILTER (
                        WHERE l1_completed_at IS NOT NULL
                          AND created_at >= NOW() - INTERVAL '24 hours'
                      ) AS l1_p50_sec,
                      percentile_cont(0.95) WITHIN GROUP (
                        ORDER BY EXTRACT(EPOCH FROM (l1_completed_at - created_at))
                      ) FILTER (
                        WHERE l1_completed_at IS NOT NULL
                          AND created_at >= NOW() - INTERVAL '24 hours'
                      ) AS l1_p95_sec,
                      percentile_cont(0.5) WITHIN GROUP (
                        ORDER BY EXTRACT(EPOCH FROM (COALESCE(l1_completed_at, created_at) - source_published_at))
                      ) FILTER (
                        WHERE source_published_at IS NOT NULL
                          AND created_at >= NOW() - INTERVAL '24 hours'
                      ) AS feed_p50_sec,
                      percentile_cont(0.95) WITHIN GROUP (
                        ORDER BY EXTRACT(EPOCH FROM (COALESCE(l1_completed_at, created_at) - source_published_at))
                      ) FILTER (
                        WHERE source_published_at IS NOT NULL
                          AND created_at >= NOW() - INTERVAL '24 hours'
                      ) AS feed_p95_sec
                    FROM base
                    GROUP BY source_bucket
                    """
                )
                for row in cur.fetchall():
                    bucket = str(row[0] or "")
                    if not bucket:
                        continue
                    out[bucket] = {
                        "last_insert_gap_sec": int(row[1] or 0),
                        "last_insert_at": str(row[2] or ""),
                        "backlog": int(row[3] or 0),
                        "ingest_p50_sec": float(row[4] or 0.0),
                        "ingest_p95_sec": float(row[5] or 0.0),
                        "l1_p50_sec": float(row[6] or 0.0),
                        "l1_p95_sec": float(row[7] or 0.0),
                        "feed_p50_sec": float(row[8] or 0.0),
                        "feed_p95_sec": float(row[9] or 0.0),
                    }
    except Exception:
        return {}
    return out


def _format_ingest_hint(metrics: dict[str, dict[str, int | float | str]]) -> str:
    parts: list[str] = []
    for bucket in ("fl", "kwork", "tg"):
        row = metrics.get(bucket)
        if not row:
            continue
        gap_min = int(row.get("last_insert_gap_sec", 0)) // 60
        backlog = int(row.get("backlog", 0))
        last_insert = str(row.get("last_insert_at", "")).strip() or "n/a"
        ingest_p95 = int(float(row.get("ingest_p95_sec", 0.0)) // 60)
        l1_p95 = int(float(row.get("l1_p95_sec", 0.0)) // 60)
        feed_p95 = int(float(row.get("feed_p95_sec", 0.0)) // 60)
        parts.append(
            f"{bucket}: gap {gap_min}m / backlog {backlog} / last {last_insert} / "
            f"p95(in/l1/feed) {ingest_p95}/{l1_p95}/{feed_p95}m"
        )
    return " | ".join(parts)


def _exchange_ops_rows() -> list[dict[str, Any]]:
    sqlite = _resolve_sqlite_path()
    if sqlite is None:
        return []
    try:
        from exchange_health import build_ops_exchange_row, health_source_ids, load_all_health
        from radar_cycle_log import load_cycle_summary
        from storage import ProjectStorage

        storage = ProjectStorage(sqlite)
        summary = load_cycle_summary(storage)
        all_health = load_all_health(storage)
        ingest = _ingest_metrics_snapshot()
    except Exception:
        return []

    rows: list[dict[str, Any]] = []
    for sid in health_source_ids():
        health = all_health.get(sid) or {}
        st = summary.sources.get(sid) if summary else None
        fetch_failed = bool(st and st.fetch_error)
        rows.append(
            build_ops_exchange_row(
                sid,
                health,
                ingest.get(sid),
                fetch_failed=fetch_failed,
            )
        )
    return rows


def hide_lead(database_url: str, lead_id: int) -> bool:
    url = database_url.strip()
    if not url:
        return False
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE leads
                SET is_visible = FALSE,
                    delist_reason = 'owner_hide'
                WHERE id = %s AND is_visible = TRUE
                """,
                (int(lead_id),),
            )
            ok = cur.rowcount > 0
        conn.commit()
    return ok


def fetch_dashboard(database_url: str) -> dict[str, Any]:
    url = database_url.strip()
    today = datetime.now(timezone.utc).date()
    users: list[dict[str, Any]] = []
    pageviews: list[dict[str, Any]] = []
    today_visits = 0
    today_unique_visits = 0
    new_users_today = 0
    visible_count = 0
    push_subscribers = 0
    recent_leads: list[dict[str, Any]] = []
    match_push_enabled = os.environ.get("MATCH_PUSH_ENABLED", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )

    with psycopg.connect(url) as conn:
        ensure_admin_tables(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COALESCE(SUM(views), 0)::int, COALESCE(SUM(unique_visitors), 0)::int
                FROM admin_pageviews
                WHERE day = %s
                  AND (path = '/lenta' OR path LIKE '/lenta/%%'
                       OR path = '/cabinet' OR path LIKE '/cabinet/%%'
                       OR path = '/' OR path = '/pricing')
                """,
                (today,),
            )
            row = cur.fetchone()
            today_visits = int(row[0] or 0) if row else 0
            today_unique_visits = int(row[1] or 0) if row else 0

            cur.execute(
                """
                SELECT COUNT(*)::int FROM users
                WHERE created_at >= %s::date AND created_at < (%s::date + INTERVAL '1 day')
                """,
                (today, today),
            )
            row = cur.fetchone()
            new_users_today = int(row[0] or 0) if row else 0

            cur.execute(
                "SELECT COUNT(*)::int FROM leads WHERE is_visible = TRUE"
            )
            row = cur.fetchone()
            visible_count = int(row[0] or 0) if row else 0

            cur.execute(
                """
                SELECT COUNT(*)::int FROM users u
                INNER JOIN subscriptions s ON s.user_id = u.id
                WHERE u.tg_chat_id IS NOT NULL
                  AND COALESCE(u.push_enabled, TRUE) = TRUE
                  AND s.plan IN ('agent', 'pro', 'beta', 'owner')
                  AND (s.is_active = TRUE OR s.plan = 'owner')
                """
            )
            row = cur.fetchone()
            push_subscribers = int(row[0] or 0) if row else 0

            cur.execute(
                """
                SELECT id, source, title FROM leads
                WHERE is_visible = TRUE
                ORDER BY created_at DESC NULLS LAST
                LIMIT 15
                """
            )
            for lid, source, title in cur.fetchall():
                recent_leads.append(
                    {
                        "id": int(lid),
                        "source": str(source or ""),
                        "title": str(title or "")[:120],
                    }
                )

            cur.execute(
                """
                SELECT u.tg_username, u.created_at, s.plan, s.is_active,
                       COALESCE(u.push_enabled, TRUE), COALESCE(u.push_min_match, 60),
                       (SELECT COUNT(*)::int FROM user_tags ut WHERE ut.user_id = u.id)
                FROM users u
                LEFT JOIN subscriptions s ON s.user_id = u.id
                ORDER BY u.created_at DESC NULLS LAST
                LIMIT 500
                """
            )
            for row in cur.fetchall():
                created = row[1]
                users.append(
                    {
                        "tg_username": row[0],
                        "created_at": created.isoformat() if isinstance(created, datetime) else None,
                        "plan": row[2] or "free",
                        "is_active": bool(row[3]),
                        "push_enabled": bool(row[4]),
                        "push_min_match": int(row[5]),
                        "tags_count": int(row[6] or 0),
                    }
                )

            cur.execute(
                """
                SELECT day, path, views FROM admin_pageviews
                WHERE day >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY day DESC, views DESC
                LIMIT 200
                """
            )
            for day_val, path_val, views in cur.fetchall():
                pageviews.append(
                    {
                        "day": day_val.isoformat() if hasattr(day_val, "isoformat") else str(day_val),
                        "path": path_val,
                        "views": int(views),
                    }
                )

    return {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "today": {
            "visits": today_visits,
            "unique_visits": today_unique_visits,
            "new_users": new_users_today,
        },
        "radar": _radar_snapshot(),
        "feed": {"visible_count": visible_count, "recent": recent_leads},
        "bot": {
            "push_subscribers": push_subscribers,
            "match_push_enabled": match_push_enabled,
        },
        "problems": count_log_errors(),
        "users": users,
        "pageviews": pageviews,
        "exchanges": _exchange_ops_rows(),
    }


def _dot_html(level: str) -> str:
    lv = level if level in ("ok", "warn", "bad") else "ok"
    return f'<span class="dot dot--{lv}"></span>'


def _card_html(title: str, value: str, hint: str, level: str) -> str:
    hint_html = f'<p class="hint">{html.escape(hint)}</p>' if hint else ""
    return (
        f'<div class="card"><h2>{_dot_html(level)}{html.escape(title)}</h2>'
        f'<p class="val">{html.escape(value)}</p>{hint_html}</div>'
    )


def _render_cards(data: dict[str, Any]) -> str:
    t = data.get("today") or {}
    radar = data.get("radar") or {}
    feed = data.get("feed") or {}
    bot = data.get("bot") or {}
    prob = data.get("problems") or {}
    r_level = str(radar.get("level") or "warn")
    auth_e = int(prob.get("auth_errors_24h") or 0)
    fetch_e = int(prob.get("fetch_errors_24h") or 0)
    p_level = "bad" if auth_e + fetch_e > 5 else ("warn" if auth_e + fetch_e > 0 else "ok")
    push_hint = "Push выключен глобально" if bot.get("match_push_enabled") is False else "Match-уведомления"
    return (
        _card_html(
            "Сегодня на сайте",
            f"{int(t.get('visits') or 0)} просмотров",
            "Уникальных: "
            f"{int(t.get('unique_visits') or 0)} · Новых в кабинете: {int(t.get('new_users') or 0)}",
            "ok",
        )
        + _card_html("Радар", str(radar.get("status_label") or "—"), str(radar.get("hint") or ""), r_level)
        + _card_html("Лента", f"{int(feed.get('visible_count') or 0)} заказов", "Видимых на /lenta/", "ok")
        + _card_html("Бот", f"{int(bot.get('push_subscribers') or 0)} с push", push_hint, "ok")
        + _card_html("Проблемы за 24 ч", f"{auth_e} вход · {fetch_e} парсер", "Детали — radar.log", p_level)
    )


def _render_exchanges(data: dict[str, Any]) -> str:
    rows = data.get("exchanges") or []
    if not rows:
        return '<div class="card"><p class="hint">Нет данных о биржах (SQLite или Neon недоступны)</p></div>'
    parts: list[str] = []
    for row in rows:
        level = str(row.get("level") or "warn")
        name = str(row.get("name") or "—")
        status = str(row.get("status_label") or "—")
        gap = int(row.get("last_insert_ago_min") or 0)
        last_ins = str(row.get("last_insert_at") or "").strip()
        insert_hint = f"{last_ins} ({gap} мин назад)" if last_ins else "ещё не было"
        ingest_min = row.get("ingest_p50_min")
        feed_min = row.get("feed_p50_min")
        lag_parts: list[str] = []
        if ingest_min is not None:
            lag_parts.append(f"На бирже → к нам: {ingest_min} мин")
        if feed_min is not None:
            lag_parts.append(f"К нам → в ленту: {feed_min} мин")
        lag_hint = " · ".join(lag_parts) if lag_parts else "Тайминги — после накопления данных"
        what = html.escape(str(row.get("what_happened") or "—"))
        hint = html.escape(f"Последний заказ: {insert_hint} · {lag_hint} · {what}")
        parts.append(_card_html(name, status, hint, level))
    return "".join(parts)


def _render_controls() -> str:
    return (
        '<button class="btn rl-ctl" data-target="radar" data-action="pause">Radar: пауза</button>'
        '<button class="btn rl-ctl" data-target="radar" data-action="resume">Radar: продолжить</button>'
        '<button class="btn rl-ctl" data-target="radar" data-action="restart">Radar: перезапуск</button>'
        '<button class="btn rl-ctl" data-target="site" data-action="restart">Site: перезапуск</button>'
    )


def _run_systemctl(action: str, service: str) -> tuple[bool, str]:
    if action not in {"restart", "start", "stop"}:
        return False, "unsupported action"
    if service not in {"rawlead-radar", "rawlead-api", "nginx"}:
        return False, "unsupported service"
    cmd = ["systemctl", action, service]
    try:
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=15)
    except Exception as exc:
        return False, str(exc)
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout or f"exit {proc.returncode}")[:300]
    return True, f"{service}: {action} ok"


def run_ops_control(*, target: str, action: str) -> dict[str, Any]:
    t = (target or "").strip().lower()
    a = (action or "").strip().lower()
    if t == "radar" and a in {"pause", "resume"}:
        sqlite = _resolve_sqlite_path()
        if sqlite is None:
            return {"ok": False, "message": "SQLite not found for radar control"}
        storage = ProjectStorage(sqlite)
        storage.set_radar_paused(a == "pause")
        return {"ok": True, "message": "Radar paused" if a == "pause" else "Radar resumed"}
    if t == "radar" and a == "restart":
        ok, msg = _run_systemctl("restart", "rawlead-radar")
        return {"ok": ok, "message": msg}
    if t == "site" and a == "restart":
        ok_api, msg_api = _run_systemctl("restart", "rawlead-api")
        ok_ng, msg_ng = _run_systemctl("restart", "nginx")
        ok = ok_api and ok_ng
        return {"ok": ok, "message": f"{msg_api}; {msg_ng}"}
    return {"ok": False, "message": "Unsupported control target/action"}


def _render_leads_rows(data: dict[str, Any]) -> str:
    feed = data.get("feed") or {}
    rows: list[str] = []
    for lead in feed.get("recent") or []:
        lid = int(lead.get("id") or 0)
        source = html.escape(str(lead.get("source") or "—"))
        title = html.escape(str(lead.get("title") or "—")[:80])
        rows.append(
            f"<tr><td>{lid}</td><td>{source}</td><td>{title}</td>"
            f'<td><button class="btn rl-hide" data-id="{lid}">Скрыть</button></td></tr>'
        )
    return "".join(rows)


def _render_views_rows(data: dict[str, Any]) -> str:
    rows: list[str] = []
    for view in data.get("pageviews") or []:
        day = html.escape(str(view.get("day") or ""))
        path = html.escape(str(view.get("path") or ""))
        views = int(view.get("views") or 0)
        rows.append(f"<tr><td>{day}</td><td>{path}</td><td>{views}</td></tr>")
    return "".join(rows)


def ops_html(*, api_base: str, data: dict[str, Any] | None = None) -> str:
    base = (api_base or "").strip().rstrip("/") or "/wp-json/rawlead/v1"
    base_esc = html.escape(base, quote=True)
    if data is not None:
        updated = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")
        script = _OPS_SCRIPT_SSR.replace("__API_BASE__", base_esc)
        return (
            _OPS_HTML.replace("__LOGIN_BLOCK__", "")
            .replace("__STATUS__", f"Обновлено {updated}")
            .replace("__CARDS__", _render_cards(data))
            .replace("__EXCHANGES__", _render_exchanges(data))
            .replace("__CONTROLS__", _render_controls())
            .replace("__LEADS__", _render_leads_rows(data))
            .replace("__VIEWS__", _render_views_rows(data))
            .replace("__SCRIPT__", script)
        )
    script = (
        _OPS_SCRIPT_CLIENT.replace("__API_BASE__", base_esc).replace("__SSR__", "false")
    )
    return (
        _OPS_HTML.replace("__LOGIN_BLOCK__", _OPS_LOGIN_BLOCK)
        .replace("__STATUS__", "Нужен вход в кабинет (см. шаги ниже)")
        .replace("__CARDS__", "")
        .replace("__EXCHANGES__", "")
        .replace("__CONTROLS__", "")
        .replace("__LEADS__", "")
        .replace("__VIEWS__", "")
        .replace("__SCRIPT__", script)
    )
