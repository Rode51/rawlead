"""O45/O78: /ops/ owner dashboard — plain-language health + visits."""

from __future__ import annotations

import html
import logging
import os
import re
import subprocess
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import psycopg
from src.storage import ProjectStorage

logger = logging.getLogger(__name__)

_OPS_PULT_JS = Path(__file__).resolve().parent / "static" / "ops-pult.js"


def _ops_pult_js_version() -> str:
    try:
        return str(int(_OPS_PULT_JS.stat().st_mtime))
    except OSError:
        return "0"


_LOG_TS = re.compile(
    r"^(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?)"
)
_AUTH_ERR = re.compile(r"bot_(?:auth|login):(?:fail|err)\b")
_FETCH_ERR = re.compile(r"fetch_error|fetch:(?:fl|kwork).*?(?:err|HTTP\s+[45])", re.I)

_RAWLEAD_BOT_USERNAME = "@rawlead_bot"
_FLPARSING_BOT_USERNAME = "@FLPARSINGBOT"

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
.ops-nav{position:sticky;top:0;z-index:20;display:flex;flex-wrap:nowrap;gap:.35rem;padding:.55rem 0;margin:0 0 .85rem;background:var(--bg);border-bottom:1px solid var(--line);overflow-x:auto;-webkit-overflow-scrolling:touch}
.ops-nav .chip{font-size:.78rem;padding:.45rem .65rem;min-height:44px;border-radius:999px;border:1px solid var(--line);background:#121820;color:var(--muted);cursor:pointer;flex-shrink:0}
.ops-nav .chip.is-active{background:#243044;color:var(--txt);border-color:#3d5166}
.ops-proxy-toolbar{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;margin-bottom:.65rem}
.ops-proxy-badge{font-size:.75rem;padding:.25rem .55rem;border-radius:999px;background:#132a1a;color:#86efac;border:1px solid #22543d}
.ops-proxy-group{margin:1rem 0}
.ops-proxy-group h4{margin:0 0 .45rem;font-size:.92rem}
.ops-proxy-group__help{margin:0 0 .55rem;font-size:.78rem;color:var(--muted);line-height:1.35}
.ops-proxy-table-wrap{display:block}
.ops-proxy-cards{display:none;gap:.55rem}
.ops-proxy-row.is-active,.ops-proxy-card.is-active{outline:1px solid #3d5166;background:#121820}
.ops-proxy-row td,.ops-proxy-card{padding:.45rem .5rem}
.ops-status-dot{display:inline-block;width:.55rem;height:.55rem;border-radius:50%;margin-right:.25rem;vertical-align:middle}
.ops-status-dot--ok{background:var(--ok)} .ops-status-dot--warn{background:var(--warn)} .ops-status-dot--bad{background:var(--bad)}
.ops-proxy-actions{display:flex;flex-wrap:wrap;gap:.35rem}
.ops-proxy-actions .btn{min-height:44px;min-width:44px;padding:.45rem .55rem}
.ops-proxy-probe{display:none;margin:.35rem 0 .55rem;padding:.45rem .6rem;border:1px solid var(--line);border-radius:8px;background:#121820;font-size:.78rem;color:var(--muted)}
.ops-proxy-probe.is-open{display:block}
.login-box{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:1rem;margin:1rem 0}
.login-box ol{margin:.5rem 0 0 1.1rem;padding:0}
.login-box a{color:#7dd3fc}
.login-page{max-width:420px;margin:2rem auto}
.login-logo{font-size:1.5rem;font-weight:700;margin:0 0 1rem;text-align:center}
.login-form label{display:block;font-size:.85rem;color:var(--muted);margin-bottom:.35rem}
.login-form input[type=password]{width:100%;padding:.55rem .65rem;border-radius:8px;border:1px solid var(--line);background:#121820;color:var(--txt);font-size:1rem;margin-bottom:.75rem}
.login-form button[type=submit]{width:100%;padding:.55rem;border-radius:8px;border:0;background:#2563eb;color:#fff;font-size:1rem;cursor:pointer}
.login-err{color:var(--bad);font-size:.85rem;margin:0 0 .65rem}
.ops-header{display:flex;flex-wrap:wrap;align-items:center;gap:.65rem;margin-bottom:.35rem}
.ops-header h1{margin:0;flex:1 1 auto}
.ops-header .sub{margin:0}
.ops-header .btn-logout{font-size:.75rem;padding:.3rem .55rem;margin-left:auto}
.ops-log-toolbar{display:flex;gap:.5rem;align-items:center;margin-bottom:.45rem}
.ops-log-pre{font-family:ui-monospace,monospace;font-size:.72rem;line-height:1.35;background:#0a0e14;border:1px solid var(--line);border-radius:8px;padding:.55rem;height:400px;overflow-y:auto;white-space:pre-wrap;word-break:break-all;margin:0}
.ops-log-pre .log-cycle{color:#60a5fa;font-weight:700}
.ops-log-pre .log-fetch{color:#fb923c}
.ops-log-pre .log-listing{color:#4ade80}
.ops-log-pre .log-warn{color:#f87171;font-weight:700}
.ops-log-pre .log-err{color:#ef4444}
.ops-log-pre .log-tg{color:#c084fc}
.ops-log-pre .log-neon{color:#86efac;font-weight:400}
.exchange-card .exchange-title{font-size:1rem;font-weight:700;margin:0 0 .35rem}
.exchange-card .exchange-meta{font-size:.82rem;color:var(--muted);margin:.25rem 0}
.exchange-card .exchange-actions{display:flex;flex-wrap:wrap;gap:.35rem;margin-top:.55rem}
.rl-toast{position:fixed;bottom:1rem;right:1rem;z-index:100;max-width:min(360px,calc(100vw - 2rem));padding:.65rem .85rem;border-radius:10px;background:#1e293b;border:1px solid #334155;color:var(--txt);font-size:.85rem;box-shadow:0 8px 24px rgba(0,0,0,.35);opacity:0;transform:translateY(8px);transition:opacity .2s,transform .2s;pointer-events:none}
.rl-toast.is-visible{opacity:1;transform:translateY(0)}
@media (max-width:640px){
  .ops-proxy-table-wrap{display:none}
  .ops-proxy-cards{display:grid}
}
.ops-lamp-bar{display:flex;flex-wrap:nowrap;gap:.5rem;overflow-x:auto;padding:.5rem 0;margin-bottom:.75rem;align-items:center}
.ops-lamp{display:inline-flex;align-items:center;gap:.35rem;padding:.35rem .55rem;border-radius:6px;border:1px solid var(--line);font-size:.78rem;white-space:nowrap;flex-shrink:0;cursor:pointer;background:#121820}
.ops-lamp--ok{border-color:var(--ok)} .ops-lamp--warn{border-color:var(--warn)} .ops-lamp--bad{border-color:var(--bad)}
.ops-lamp__l1{margin-left:auto;flex-shrink:0;font-size:.78rem;color:var(--muted)}
.ops-diagnosis{padding:.65rem .85rem;border-radius:8px;border-left:3px solid var(--bad);background:#2a1a1a;margin-bottom:.75rem}
.ops-diagnosis--warn{border-left-color:var(--warn);background:#2a2418}
.ops-diagnosis__action{margin-top:.5rem}
.ops-diagnosis__action .btn{min-height:44px}
.ops-funnel-grid{display:grid;gap:.65rem;grid-template-columns:repeat(2,1fr)}
.ops-funnel-card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:.85rem}
.ops-funnel-card__head{display:flex;justify-content:space-between;align-items:center;margin-bottom:.35rem;font-weight:600;font-size:.88rem}
.ops-truth-ladder{display:flex;gap:.2rem;margin:.45rem 0}
.ops-truth-step{flex:1;text-align:center;min-width:0}
.ops-truth-step__label{font-size:.62rem;color:var(--muted);text-transform:uppercase}
.ops-truth-step__dot{width:.6rem;height:.6rem;border-radius:50%;margin:.2rem auto 0;display:inline-block}
.ops-truth-step__dot--ok{background:var(--ok)} .ops-truth-step__dot--warn{background:var(--warn)}
.ops-truth-step__dot--bad{background:var(--bad)} .ops-truth-step__dot--na{background:var(--line)}
.ops-truth-step.is-break .ops-truth-step__dot{box-shadow:0 0 0 2px var(--bad)}
.ops-funnel-meta{font-size:.78rem;color:var(--muted)}
.ops-tg-botapi{padding:.75rem;border:1px solid var(--line);border-radius:10px;margin-bottom:1rem;background:#151d28}
.ops-tg-table{width:100%;font-size:.82rem}
.ops-tg-card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:.85rem;margin-bottom:.5rem}
.ops-tg-card__title{font-weight:600;margin-bottom:.35rem}
.ops-tg-card__row{font-size:.82rem;color:var(--muted);margin:.15rem 0}
.ops-tg-table-wrap{display:block}
.ops-tg-cards{display:none;gap:.5rem}
.btn-ghost{background:transparent;border:1px dashed var(--line)}
@media (max-width:767px){
  .ops-funnel-grid{grid-template-columns:1fr}
  .ops-truth-ladder{flex-direction:column;gap:.25rem}
  .ops-truth-step{display:flex;justify-content:space-between;align-items:center;text-align:left}
  .ops-truth-step__label{text-transform:none;font-size:.8rem}
  .ops-truth-step__dot{margin:0}
  .ops-lamp__l1{margin-left:0}
  .ops-tg-table-wrap{display:none}
  .ops-tg-cards{display:grid}
  .ops-tg-card .btn{width:100%;min-height:44px}
  .ops-diagnosis__action .btn{width:100%}
}
@media (min-width:768px){
  .ops-tg-cards{display:none}
}
</style>
</head>
<body>
<div class="ops-header">
<h1>Пульт RawLead</h1>
__HEADER_META__
__LOGOUT_BTN__
</div>
__LOGIN_BLOCK__
<nav class="ops-nav" id="rl-ops-mini-nav" aria-label="Разделы пульта">
<button type="button" class="chip is-active" data-target="ops-summary">Сводка</button>
<button type="button" class="chip" data-target="ops-bots">Боты</button>
<button type="button" class="chip" data-target="ops-exchanges">Биржи</button>
<button type="button" class="chip" data-target="ops-tg">TG</button>
<button type="button" class="chip" data-target="ops-proxies">Прокси</button>
<button type="button" class="chip" data-target="ops-controls">Управление</button>
<button type="button" class="chip" data-target="ops-logs">Логи</button>
<button type="button" class="chip" data-target="ops-leads">Лента</button>
</nav>
<section id="ops-summary">
<h3>Сводка</h3>
<p class="sub">Жив ли радар · где обрыв воронки · что делать</p>
<div class="ops-lamp-bar" id="rl-ops-lamp-bar">__FUNNEL_LAMPS__</div>
<div id="rl-ops-diagnosis-wrap">__FUNNEL_DIAGNOSIS__</div>
<div class="ops-funnel-grid" id="rl-ops-funnels">__FUNNEL_CARDS__</div>
<p class="sub ctl-hint" id="rl-ops-funnel-hint">__FUNNEL_HINT__</p>
</section>
<section id="ops-bots"><h3>Боты</h3>
<div class="grid" id="rl-ops-bots">__BOTS__</div>
<div class="ctl" style="margin-top:.5rem" id="rl-ops-bots-ctl">__BOTS_CTL__</div>
</section>
<section id="ops-exchanges"><h3>Биржи и скорость</h3>
<div class="grid" id="rl-ops-ingest-sla">__INGEST_SLA__</div>
<div class="grid" id="rl-ops-exchanges">__EXCHANGES__</div>
</section>
<section id="ops-tg"><h3>Telegram</h3>
<p class="sub">Аккаунты парсинга · Bot API · без SSH</p>
__TG_SECTION__
</section>
<section id="ops-proxies"><h3>Прокси</h3>
__PROXIES__
</section>
<section id="ops-controls"><h3>Управление</h3><div class="ctl" id="rl-ops-controls">__CONTROLS__</div><p class="sub" id="rl-ops-delist-stats" style="margin:.35rem 0 0">__DELIST_STATS__</p><div id="rl-ops-control-status" class="ctl-status"><span class="dot"></span><span>Ожидание команд</span></div></section>
<section id="ops-logs"><h3>Логи радара</h3>
<div class="ops-log-toolbar">
<button type="button" class="btn" id="rl-ops-log-pause">⏸ Пауза</button>
<span class="sub" id="rl-ops-log-status">Live</span>
</div>
<pre id="rl-ops-log" class="ops-log-pre" aria-live="polite"></pre>
</section>
<section id="ops-leads"><h3>Последние заказы в ленте</h3>
<table id="rl-ops-leads"><thead><tr><th>#</th><th>Источник</th><th>Заголовок</th><th></th></tr></thead><tbody>__LEADS__</tbody></table>
</section>
<section><h3>Посещения (7 дней)</h3>
<p class="sub" style="margin-top:0">По страницам — где открывали сайт. /lenta = лента, /cabinet = кабинет, / = главная.</p>
<table id="rl-ops-views"><thead><tr><th>День</th><th>Страница</th><th>Просмотры</th></tr></thead><tbody>__VIEWS__</tbody></table>
</section>
<section><h3>Поддержка (тикеты)</h3>
<p class="sub" style="margin-top:0">Ответ уходит в окно «Поддержка» на сайте у пользователя.</p>
<div id="rl-ops-support"></div>
</section>
<div id="rl-toast" class="rl-toast" role="status" aria-live="polite"></div>
__SCRIPT__
</body>
</html>"""


_OPS_LOGIN_PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>RawLead — вход в пульт</title>
<style>
:root{--bad:#ef4444;--bg:#0f1419;--card:#1a2332;--line:#2a3544;--txt:#e8eaed;--muted:#94a3b8}
*{box-sizing:border-box} body{font-family:system-ui,sans-serif;margin:0;padding:1.25rem;background:var(--bg);color:var(--txt)}
.login-page{max-width:420px;margin:2rem auto}
.login-logo{font-size:1.5rem;font-weight:700;margin:0 0 1rem;text-align:center}
.login-form label{display:block;font-size:.85rem;color:var(--muted);margin-bottom:.35rem}
.login-form input[type=password]{width:100%;padding:.55rem .65rem;border-radius:8px;border:1px solid var(--line);background:#121820;color:var(--txt);font-size:1rem;margin-bottom:.75rem}
.login-form button[type=submit]{width:100%;padding:.55rem;border-radius:8px;border:0;background:#2563eb;color:#fff;font-size:1rem;cursor:pointer}
.login-err{color:var(--bad);font-size:.85rem;margin:0 0 .65rem}
</style>
</head>
<body>
<div class="login-page">
<p class="login-logo">RawLead</p>
<div class="login-form">
__ERROR__
<form method="post" action="/ops/login">
<label for="rl-ops-password">Пароль</label>
<input id="rl-ops-password" type="password" name="password" autocomplete="current-password" required autofocus/>
<button type="submit">Войти</button>
</form>
</div>
</div>
</body>
</html>"""


def ops_login_html(*, show_error: bool = False) -> str:
    err = '<p class="login-err">Неверный пароль</p>' if show_error else ""
    return _OPS_LOGIN_PAGE.replace("__ERROR__", err)


_OPS_SETUP_PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>RawLead — пульт не настроен</title>
<style>
:root{--bg:#0f1419;--card:#1a2332;--line:#2a3544;--txt:#e8eaed;--muted:#94a3b8}
*{box-sizing:border-box} body{font-family:system-ui,sans-serif;margin:0;padding:1.25rem;background:var(--bg);color:var(--txt)}
.login-page{max-width:480px;margin:2rem auto}
.login-logo{font-size:1.5rem;font-weight:700;margin:0 0 1rem;text-align:center}
.login-box{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:1rem 1.1rem}
.login-box p{margin:.35rem 0;line-height:1.45}
.login-box code{font-size:.9rem;color:#cbd5e1}
</style>
</head>
<body>
<div class="login-page">
<p class="login-logo">RawLead</p>
<div class="login-box">
<p><strong>Пульт не настроен</strong></p>
<p>Задай <code>RAWLEAD_OPS_KEY=…</code> в <code>/opt/rawlead/.env.site</code> на VPS и перезапусти <code>rawlead-api</code>.</p>
<p class="sub" style="color:var(--muted);font-size:.85rem">После этого открой <code>/ops/</code> снова — появится форма пароля.</p>
</div>
</div>
</body>
</html>"""


def ops_setup_html() -> str:
    return _OPS_SETUP_PAGE


def _human_ago(ts: float | None) -> str:
    if ts is None:
        return "нет данных"
    delta = max(0, time.time() - ts)
    if delta < 60:
        return "только что"
    mins = int(delta // 60)
    if mins < 60:
        return f"{mins} минут назад"
    hours = int(mins // 60)
    if hours < 24:
        return f"{hours} часов назад"
    return "больше суток назад (!)"


def _human_error_text(err: str, kind: str) -> str:
    low = (err or "").lower()
    k = (kind or "").lower()
    if k == "403" or "403" in low or "forbidden" in low:
        return "403 — заблокирован прокси"
    if k == "timeout" or "timeout" in low or "timed out" in low or "wall-clock" in low:
        return "timeout — завис, перезапустил"
    if k == "antibot" or "antibot" in low or "captcha" in low:
        return "antibot — сайт распознал бота"
    if err.strip():
        return err.strip()[:120]
    return ""


def _exchange_status_from_ok_at(ok_epoch: float | None) -> tuple[str, str, str]:
    if ok_epoch is None:
        return "bad", "🔴", "Не отвечает — нужна проверка"
    mins = max(0, int((time.time() - ok_epoch) // 60))
    if mins < 15:
        return "ok", "🟢", "Работает"
    if mins <= 60:
        return "warn", "🟡", "Задержка — ждём следующего цикла"
    return "bad", "🔴", "Не отвечает — нужна проверка"


def _tg_exchange_status_from_pult(lamp: str, reason: str) -> tuple[str, str, str]:
    reason = (reason or "").strip()
    if lamp == "ok":
        return "ok", "🟢", reason or "Работает"
    if lamp == "warn":
        return "warn", "🟡", reason or "Задержка — ждём следующего цикла"
    if lamp == "error":
        return "bad", "🔴", reason or "Не отвечает — нужна проверка"
    return "bad", "🔴", reason or "Не отвечает — нужна проверка"


_TG_LOG_LINE_EXCLUDE = re.compile(r"бот_start:.*skip", re.I)
_TG_LOG_LINE_PREFER = (
    "handler_ok",
    "тг:пульс",
    "listing:tg",
    "health:tg",
    "тг:сообщ",
)


def _last_log_line_for_source(source_id: str) -> str:
    path = _resolve_log_path()
    if path is None:
        return ""
    needles = {
        "fl": ("fetch:fl", "listing:fl"),
        "kwork": ("fetch:kwork", "listing:kwork"),
        "youdo": ("fetch:youdo", "listing:youdo"),
        "tg": ("тг:", "tg:"),
    }
    keys = needles.get(source_id, (f"fetch:{source_id}", f"listing:{source_id}"))
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    fallback = ""
    for line in reversed(lines[-800:]):
        if not any(n in line for n in keys):
            continue
        if source_id == "tg" and _TG_LOG_LINE_EXCLUDE.search(line):
            continue
        stripped = line.strip()[:160]
        if source_id == "tg" and any(p in line for p in _TG_LOG_LINE_PREFER):
            return stripped
        if not fallback:
            fallback = stripped
    return fallback


def _parse_health_ok_epoch(health: dict[str, Any]) -> float | None:
    try:
        from exchange_health import _parse_ts_epoch

        ok_ts = str(health.get("last_ok_at") or "").strip()
        return _parse_ts_epoch(ok_ts) if ok_ts else None
    except Exception:
        return None


_OPS_LOGIN_BLOCK = """<div class="login-box">
<p><strong>Сначала войди в кабинет</strong> — в <em>этом же браузере</em> (Chrome или Safari на телефоне, не панель Cursor):</p>
<ol>
<li><a href="/cabinet/">Открыть /cabinet/</a></li>
<li>Нажать «Войти через Telegram»</li>
<li>Вернуться сюда и обновить страницу (F5)</li>
</ol>
</div>"""

def _ops_script_block(api_base: str) -> str:
    """External ops JS (CSP-safe) — see src/static/ops-pult.js."""
    base = html.escape((api_base or "").strip().rstrip("/") or "/ops", quote=True)
    v = _ops_pult_js_version()
    return (
        f'<meta name="rl-ops-api-base" content="{base}"/>'
        f'<script src="/ops/static/ops-pult.js?v={v}"></script>'
    )


_OPS_SCRIPT_CLIENT = """<script>
(function () {
  var API = "__API_BASE__";
  var SSR = __SSR__;
  if (SSR) return;
  function ctlFetchErr(r, body) {
    if (body && typeof body.detail === "string" && body.detail) return body.detail;
    if (body && typeof body.message === "string" && body.message) return body.message;
    return "HTTP " + r.status;
  }
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
          return r.json().catch(function () { return null; }).then(function (body) {
            if (!r.ok) throw new Error(ctlFetchErr(r, body));
            return body;
          });
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
    if (statusEl) {
      statusEl.textContent = "Обновлено " + new Date().toLocaleString("ru-RU");
      statusEl.className = "sub";
    }
    if (!cardsEl) {
      location.reload();
      return;
    }
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
        "@rawlead_bot: " + (bot.bot_poll_status || "unknown") + " · @FLPARSINGBOT: "
        + (bot.legacy_radar_status || "unknown") + " · "
        + (bot.match_push_enabled === false ? "Push выключен глобально" : "Match-уведомления"),
        ((bot.bot_poll_status === "active" && bot.legacy_radar_status === "active") ? "ok"
          : ((bot.bot_poll_status === "failed" || bot.bot_poll_status === "inactive"
            || bot.legacy_radar_status === "failed" || bot.legacy_radar_status === "inactive") ? "bad" : "warn")))
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
        fetch(API + "/leads/" + id + "/hide", {
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
        '<button class="btn rl-ctl" data-target="site" data-action="restart">Site: перезапуск</button>' +
        '<button class="btn rl-ctl" data-target="delist" data-action="run">Проверить ссылки</button>';
    }
    var delistStatsEl = document.getElementById("rl-ops-delist-stats");
    if (delistStatsEl) {
      var delist = data.delist || {};
      if (delist.last_run_at) {
        delistStatsEl.textContent = "Ссылки: последний прогон " + delist.last_run_at
          + " — проверено " + (delist.checked || 0) + ", снято " + (delist.delisted || 0);
      } else {
        delistStatsEl.textContent = "Ссылки: автопроверка FL/Kwork ещё не запускалась";
      }
    }
    function renderBotCards(bots) {
      if (!bots || !bots.length) {
        return '<div class="card"><p class="hint">Нет данных о ботах</p></div>';
      }
      return bots.map(function (b) {
        var hint = "is-active: " + (b.is_active || "unknown");
        if (b.last_cmd) hint += " · " + b.last_cmd;
        return '<div class="card"><h2>' + dot(b.level || "warn") + (b.username || "—") + '</h2>'
          + '<p class="val">' + (b.is_active || "unknown") + '</p>'
          + '<p class="hint">' + hint + '</p>'
          + '<button class="btn rl-ctl" data-target="' + (b.target || "") + '" data-action="restart">Перезапуск</button></div>';
      }).join("");
    }
    var botsEl = document.getElementById("rl-ops-bots");
    if (botsEl) botsEl.innerHTML = renderBotCards(data.bots || []);
    var botsCtl = document.getElementById("rl-ops-bots-ctl");
    if (botsCtl && !botsCtl.innerHTML.trim()) {
      botsCtl.innerHTML =
        '<button class="btn rl-ctl" data-target="bots-both" data-action="restart">Перезапуск обоих ботов</button>';
    }
    function proxyDot(status) {
      var lv = (status === "ok" || status === "warn" || status === "bad") ? status : "warn";
      return '<span class="ops-status-dot ops-status-dot--' + lv + '"></span>';
    }
    function switchable(gid) {
      return gid === "tg-bot" || gid === "exchange-fl" || gid === "exchange-kwork" || gid === "exchange-pool";
    }
    function proxyGroupHelp(gid) {
      var map = {
        "tg-bot": "@rawlead_bot ходит в Telegram через этот прокси. Красный = бот может молчать или не слать push.",
        "telethon": "Радар читает TG-группы через acc1/2/3. Переключить кнопкой пока нельзя — только «Проверить».",
        "exchange-fl": "Заказы с FL.ru качаются через этот прокси. Жёлтый/красный = FL в ленте может пропасть.",
        "exchange-kwork": "Заказы с Kwork — то же.",
        "exchange-pool": "Запасной пул для бирж."
      };
      return map[gid] || "";
    }
    function switchBtn(gid, sn, active, banned) {
      if (!switchable(gid)) return "";
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
      var help = proxyGroupHelp(gid);
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
        var sw = switchBtn(gid, sn, active, banned);
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
      var helpHtml = help ? '<p class="ops-proxy-group__help">' + help + '</p>' : "";
      var resNote = "";
      if (group.residential_active) {
        var ra = group.res_alive || 0;
        var rt = group.res_total || 0;
        resNote = '<p class="ops-proxy-group__help ops-proxy-residential">FL сейчас работает через residential ('
          + ra + "/" + rt + " слотов)</p>";
      }
      return '<div class="ops-proxy-group" data-group="' + gid + '"><h4>' + title + '</h4>' + helpHtml + resNote
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
    if (data.proxies) window.rlOpsRenderProxies(data.proxies);
    bindControls(token);
    var supportEl = document.getElementById("rl-ops-support");
    if (supportEl) {
      fetch(API + "/ops/support/tickets", {
        credentials: "same-origin",
        headers: { "Authorization": "Bearer " + token }
      }).then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      }).then(function (data) {
        var tickets = (data && data.tickets) || [];
        if (!tickets.length) {
          supportEl.innerHTML = "<p class=\\"sub\\">Тикетов пока нет.</p>";
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
            fetch(API + "/ops/support/tickets/" + id + "/reply", {
              method: "POST",
              credentials: "same-origin",
              headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token
              },
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
        supportEl.innerHTML = "<p class=\\"err\\">Поддержка: нет доступа.</p>";
      });
    }
  }).catch(function (e) {
    if (timer) clearTimeout(timer);
    if (e && e.name === "AbortError") {
      fail("Таймаут. Отключи блокировщик рекламы для rawlead.ru или войди через Chrome/Safari.");
      return;
    }
    fail((e && e.message) || String(e));
  });
  __NAV_PROXY_JS__
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


def _resolve_data_log(name: str) -> Path | None:
    p = Path(__file__).resolve().parent.parent / "data" / name
    return p if p.is_file() else None


def _last_log_line_matching(path: Path | None, *, needle: str) -> str | None:
    if path is None:
        return None
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    for line in reversed(lines[-500:]):
        if needle in line:
            return line.strip()[:200]
    return None


def _status_level(is_active: str) -> str:
    st = (is_active or "").strip().lower()
    if st == "active":
        return "ok"
    if st in {"failed", "inactive"}:
        return "bad"
    return "warn"


def _bot_poll_last_cmd() -> str | None:
    return _last_log_line_matching(_resolve_data_log("radar_site.log"), needle="тг:команда:")


def _legacy_bot_last_cmd() -> str | None:
    return _last_log_line_matching(_resolve_data_log("radar_legacy.log"), needle="тг:команда:")


def _bots_snapshot() -> list[dict[str, Any]]:
    poll_st = _bot_poll_status()
    legacy_st = _legacy_radar_status()
    return [
        {
            "username": _RAWLEAD_BOT_USERNAME,
            "service": "rawlead-bot-poll",
            "target": "rawlead-bot",
            "is_active": poll_st,
            "level": _status_level(poll_st),
            "last_cmd": _bot_poll_last_cmd(),
        },
        {
            "username": _FLPARSING_BOT_USERNAME,
            "service": "rawlead-radar-legacy",
            "target": "flparsing-bot",
            "is_active": legacy_st,
            "level": _status_level(legacy_st),
            "last_cmd": _legacy_bot_last_cmd(),
        },
    ]


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
                      ) AS feed_p95_sec,
                      COUNT(*) FILTER (
                        WHERE source_published_at IS NOT NULL
                          AND created_at >= NOW() - INTERVAL '24 hours'
                          AND EXTRACT(
                            EPOCH FROM (
                              COALESCE(l1_completed_at, created_at) - source_published_at
                            )
                          ) <= 300
                      )::int AS feed_within_5m,
                      COUNT(*) FILTER (
                        WHERE source_published_at IS NOT NULL
                          AND created_at >= NOW() - INTERVAL '24 hours'
                      )::int AS feed_measurable_24h
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
                        "feed_within_5m": int(row[10] or 0),
                        "feed_measurable_24h": int(row[11] or 0),
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


def _exchange_ops_rows(
    *,
    _ingest: dict[str, dict[str, int | float | str]] | None = None,
) -> list[dict[str, Any]]:
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
        ingest = _ingest if _ingest is not None else _ingest_metrics_snapshot()
    except Exception:
        return []

    rows: list[dict[str, Any]] = []
    lead_counts: dict[str, dict[str, int]] = {}
    try:
        from config import load_config
        from ops_funnel import _lead_counts_by_source

        db_url = (load_config().database_url or os.environ.get("DATABASE_URL", "")).strip()
        if db_url:
            lead_counts = _lead_counts_by_source(db_url)
    except Exception:
        lead_counts = {}

    tg_process_alive = False
    try:
        from health_check import is_tg_monitor_active

        tg_process_alive = is_tg_monitor_active()
    except Exception:
        tg_process_alive = False

    for sid in health_source_ids():
        health = all_health.get(sid) or {}
        st = summary.sources.get(sid) if summary else None
        fetch_failed = bool(st and st.fetch_error)
        row = build_ops_exchange_row(
            sid,
            health,
            ingest.get(sid),
            fetch_failed=fetch_failed,
        )
        ok_epoch = _parse_health_ok_epoch(health)
        row["last_ok_ago"] = _human_ago(ok_epoch)
        neon_today = int((lead_counts.get(sid) or {}).get("new_today", 0) or 0)
        row["today_new_ids"] = neon_today
        parsed = row.get("last_parsed_cards")
        fresh = int(row.get("last_fresh_cards") or 0)
        if parsed is not None and int(parsed) >= 0:
            row["cycle_hint"] = f"за цикл: parsed={int(parsed)} fresh={fresh}"
        else:
            row["cycle_hint"] = ""
        row["last_log_line"] = _last_log_line_for_source(sid)
        row["error_kind"] = str(health.get("last_error_kind") or "ok")
        row["error_short"] = str(health.get("last_error_short") or "")
        if sid == "tg":
            try:
                from radar_status import tg_pult_lamp_state

                lamp, reason = tg_pult_lamp_state(
                    storage,
                    process_alive=tg_process_alive,
                )
                lvl, icon, status_ru = _tg_exchange_status_from_pult(lamp, reason)
            except Exception:
                lvl, icon, status_ru = _exchange_status_from_ok_at(ok_epoch)
        else:
            lvl, icon, status_ru = _exchange_status_from_ok_at(ok_epoch)
        row["exchange_level"] = lvl
        row["exchange_icon"] = icon
        row["exchange_status_ru"] = status_ru
        if sid == "fl":
            try:
                from exchange_proxy import FL_DC_PARSED_INGEST_OK, fl_on_residential_tier, fl_residential_counts

                if fl_on_residential_tier():
                    alive, total = fl_residential_counts()
                    row["fl_tier"] = "residential"
                    row["fl_res_alive"] = alive
                    row["fl_res_total"] = total
                    row["residential_hint"] = f"резидентский fallback: {alive}/{total} alive"
                    parsed_n = int(parsed or 0)
                    if parsed_n >= FL_DC_PARSED_INGEST_OK and row["exchange_level"] == "bad":
                        row["exchange_level"] = "warn"
                        row["exchange_icon"] = "🟡"
            except Exception:
                pass
        err_human = _human_error_text(row["error_short"], row["error_kind"])
        if err_human and lvl != "ok":
            row["error_human"] = err_human
        else:
            row["error_human"] = ""
        rows.append(row)
    return rows


def hide_lead(
    database_url: str,
    lead_id: int,
    *,
    delist_reason: str = "owner_hide",
) -> bool:
    url = database_url.strip()
    if not url:
        return False
    reason = (delist_reason or "owner_hide").strip()[:64] or "owner_hide"
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE leads
                SET is_visible = FALSE,
                    delist_reason = %s
                WHERE id = %s AND is_visible = TRUE
                """,
                (reason, int(lead_id)),
            )
            ok = cur.rowcount > 0
        conn.commit()
    return ok


def _degraded_funnel_payload(reason: str) -> dict[str, Any]:
    text = (reason or "ошибка загрузки воронки").strip()[:240]
    return {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "sources": [],
        "lamps": {},
        "l1": {"status": "warn", "queue": 0, "label": "ошибка"},
        "diagnosis": {"level": "warn", "text": text, "action": None},
    }


def _degraded_tg_payload(reason: str) -> dict[str, Any]:
    return {
        "accounts": [],
        "botapi": {"level": "warn", "label": (reason or "ошибка TG")[:120]},
        "queue": {},
    }


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

    # Compute ingest once and share with _exchange_ops_rows to avoid a second Neon connection.
    # funnel and tg are fetched separately by ops-pult.js (/ops/funnel + /ops/tg in parallel)
    # so there is no need to duplicate that work here — removing them drops ~6s from this call.
    ingest = _ingest_metrics_snapshot()
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
            "bot_poll_status": _bot_poll_status(),
            "legacy_radar_status": _legacy_radar_status(),
        },
        "bots": _bots_snapshot(),
        "problems": count_log_errors(),
        "users": users,
        "pageviews": pageviews,
        "exchanges": _exchange_ops_rows(_ingest=ingest),
        "ingest": ingest,
        "delist": _delist_snapshot(),
        "proxies": _proxies_snapshot(),
    }


def _safe_ops_funnel(database_url: str) -> dict[str, Any]:
    try:
        return fetch_ops_funnel(database_url)
    except Exception as exc:
        logger.exception("ops funnel: %s", exc)
        return _degraded_funnel_payload(str(exc))


def _safe_ops_tg() -> dict[str, Any]:
    try:
        return fetch_ops_tg()
    except Exception as exc:
        logger.exception("ops tg: %s", exc)
        return _degraded_tg_payload(str(exc))


def _proxies_snapshot() -> dict[str, Any]:
    try:
        from proxy_ops import collect_proxies_payload, strip_internal_urls

        return strip_internal_urls(collect_proxies_payload())
    except Exception:
        return {"auto_failover": True, "last_probe_at": None, "groups": []}


def _dot_html(level: str) -> str:
    lv = level if level in ("ok", "warn", "bad") else "ok"
    return f'<span class="dot dot--{lv}"></span>'


def _lamp_icon(status: str) -> str:
    return {"ok": "🟢", "warn": "🟡", "bad": "🔴"}.get(status, "🟡")


def fetch_ops_funnel(database_url: str) -> dict[str, Any]:
    sqlite = _resolve_sqlite_path()
    if sqlite is None:
        return {
            "sources": [],
            "lamps": {},
            "l1": {"status": "warn", "queue": 0, "label": "нет SQLite"},
            "diagnosis": None,
        }
    from ops_funnel import build_funnel_payload

    try:
        return build_funnel_payload(sqlite, database_url=database_url)
    except Exception as exc:
        logger.exception("build_funnel_payload: %s", exc)
        return _degraded_funnel_payload(str(exc))


def fetch_ops_tg() -> dict[str, Any]:
    sqlite = _resolve_sqlite_path()
    if sqlite is None:
        return {"accounts": [], "botapi": {}, "queue": {}}
    from ops_funnel import build_tg_payload

    try:
        return build_tg_payload(sqlite)
    except Exception as exc:
        logger.exception("build_tg_payload: %s", exc)
        return _degraded_tg_payload(str(exc))


def _render_funnel_lamps(funnel: dict[str, Any]) -> str:
    lamps = funnel.get("lamps") or {}
    l1 = funnel.get("l1") or {}
    parts: list[str] = []
    for key in ("radar", "fl", "kwork", "youdo", "tg"):
        item = lamps.get(key) or {}
        st = str(item.get("status") or "warn")
        label = html.escape(str(item.get("label") or key))
        parts.append(
            f'<span class="ops-lamp ops-lamp--{html.escape(st)}">'
            f"{_lamp_icon(st)} {label}</span>"
        )
    l1_st = str(l1.get("status") or "warn")
    l1_label = html.escape(str(l1.get("label") or ""))
    parts.append(
        f'<span class="ops-lamp__l1">L1 {_lamp_icon(l1_st)} {l1_label}</span>'
    )
    return "".join(parts)


def _render_funnel_diagnosis(funnel: dict[str, Any]) -> str:
    diag = funnel.get("diagnosis")
    if not diag or not diag.get("text"):
        return '<div class="ops-diagnosis" id="rl-ops-diagnosis" hidden></div>'
    level = str(diag.get("level") or "bad")
    text = html.escape(str(diag.get("text") or ""))
    action = diag.get("action") or {}
    act_html = ""
    if action.get("label"):
        tgt = str(action.get("target") or "").strip()
        act = str(action.get("action") or "").strip()
        if tgt and act:
            act_html = (
                f'<div class="ops-diagnosis__action">'
                f'<button type="button" class="btn rl-funnel-action" '
                f'data-target="{html.escape(tgt)}" data-action="{html.escape(act)}">'
                f'{html.escape(str(action.get("label") or ""))}</button></div>'
            )
        else:
            act_html = (
                f'<div class="ops-diagnosis__action">'
                f'<button type="button" class="btn rl-funnel-action" '
                f'data-scroll="{html.escape(str(action.get("scroll_to") or ""))}" '
                f'data-group="{html.escape(str(action.get("group") or ""))}">'
                f'{html.escape(str(action.get("label") or ""))}</button></div>'
            )
    icon = "🔴" if level == "bad" else "🟡"
    cls = "ops-diagnosis" if level == "bad" else "ops-diagnosis ops-diagnosis--warn"
    return f'<div class="{cls}" id="rl-ops-diagnosis">{icon} {text}{act_html}</div>'


def _render_funnel_cards(funnel: dict[str, Any]) -> str:
    parts: list[str] = []
    for src in funnel.get("sources") or []:
        sid = html.escape(str(src.get("source_id") or ""))
        name = html.escape(str(src.get("name") or sid))
        headline = html.escape(str(src.get("headline") or ""))
        steps_html: list[str] = []
        for st in src.get("steps") or []:
            step_id = html.escape(str(st.get("id") or ""))
            status = html.escape(str(st.get("status") or "na"))
            label = html.escape(str(st.get("label") or step_id))
            tip = html.escape(str(st.get("tooltip") or ""))
            brk = " is-break" if st.get("is_break") else ""
            steps_html.append(
                f'<div class="ops-truth-step{brk}" title="{tip}">'
                f'<span class="ops-truth-step__label">{label}</span>'
                f'<span class="ops-truth-step__dot ops-truth-step__dot--{status}"></span>'
                f"</div>"
            )
        meta = src.get("meta") or {}
        meta_line = (
            f"parsed {meta.get('parsed', '—')} · new {meta.get('new', '—')}"
            + (f" · lag {meta.get('lag_min')} мин" if meta.get("lag_min") is not None else "")
        )
        muted = src.get("muted_note")
        muted_html = (
            f'<p class="ops-funnel-meta">{html.escape(str(muted))}</p>' if muted else ""
        )
        tg_link = (
            ' · <button type="button" class="btn btn-ghost rl-scroll-tg">Подробнее → TG</button>'
            if str(src.get("source_id") or "") == "tg"
            else ""
        )
        parts.append(
            f'<div class="ops-funnel-card" id="ops-funnels-{sid}">'
            f'<div class="ops-funnel-card__head"><span>{name}</span><span>{headline}</span></div>'
            f'<div class="ops-truth-ladder">{"".join(steps_html)}</div>'
            f'<p class="ops-funnel-meta">{html.escape(meta_line)}{tg_link}</p>{muted_html}'
            f"</div>"
        )
    return "".join(parts) if parts else '<p class="sub">Нет данных воронки</p>'


def _render_funnel_hint(funnel: dict[str, Any]) -> str:
    age = funnel.get("cycle_age_min")
    if age is None:
        return "Обновлено при загрузке"
    return f"Обновлено при загрузке · цикл радара {int(age)} мин назад"


def _render_tg_section(tg: dict[str, Any]) -> str:
    bot = tg.get("botapi") or {}
    q = tg.get("queue") or {}
    slot = int(bot.get("active_slot") or 0)
    free = int(bot.get("free") or 0)
    total = int(bot.get("total") or 0)
    auto = "вкл" if bot.get("auto_failover") else "выкл"
    last_sw = bot.get("last_switch_at")
    last_html = (
        f'<p class="sub">Последнее переключение: {html.escape(str(last_sw))}</p>'
        if last_sw
        else ""
    )
    botapi = (
        f'<div class="ops-tg-botapi" id="rl-ops-tg-botapi">'
        f"<p><strong>Bot API:</strong> слот {slot} ● активен · Авто: {auto} · "
        f"свободно {free} из {total}</p>{last_html}"
        f'<button type="button" class="btn btn-ghost rl-scroll-proxy-tg">'
        f"Открыть прокси TG →</button></div>"
    )
    from ops_funnel import TG_LISTEN_TOOLTIP, TG_MSGS_TOOLTIP, tg_listen_line_ru, tg_queue_hint_ru

    rows: list[str] = []
    cards: list[str] = []
    for acc in tg.get("accounts") or []:
        aid = html.escape(str(acc.get("id") or ""))
        lamp = str(acc.get("lamp") or "warn")
        state_label = html.escape(str(acc.get("state_label") or ""))
        lamp_reason = html.escape(str(acc.get("lamp_reason_ru") or ""))
        listen_title = html.escape(str(acc.get("listen_title") or TG_LISTEN_TOOLTIP))
        listen_line = html.escape(
            str(
                acc.get("listen_line")
                or tg_listen_line_ru(
                    int(acc.get("peers_count") or acc.get("listen_count") or 0),
                    int(acc.get("file_count") or 0),
                    int(acc.get("filter_count") or 0),
                )
            )
        )
        msg_bits: list[str] = []
        msgs_line = html.escape(
            str(acc.get("msgs_line") or "—")
        )
        msgs_title = html.escape(str(acc.get("msgs_title") or TG_MSGS_TOOLTIP))
        join_label = html.escape(str(acc.get("join_label") or "—"))
        strikes = html.escape(str(acc.get("strikes") or "0/3"))
        if acc.get("join_status") == "pending":
            actions = (
                f'<button type="button" class="btn rl-tg-ctl" data-action="tg-join-tick" '
                f'data-target="tg">Докрутить join</button>'
            )
        else:
            actions = (
                f'<button type="button" class="btn rl-tg-ctl" data-action="tg-join-restart" '
                f'data-target="tg">Перезапустить join</button>'
            )
        actions += ' <button type="button" class="btn" disabled title="Скоро">CRUD</button>'
        rows.append(
            f'<tr><td title="Номер TG на VPS: acc1/acc2/acc3">{aid}</td>'
            f'<td title="{lamp_reason}">{_lamp_icon(lamp)} {state_label}</td>'
            f'<td title="{listen_title}">{listen_line}</td>'
            f'<td title="{msgs_title}">{msgs_line}</td>'
            f'<td title="Статус очереди join для этого acc">{join_label}</td>'
            f'<td title="3 подряд fail → пауза вступлений">{strikes}</td>'
            f"<td>{actions}</td></tr>"
        )
        cards.append(
            f'<div class="ops-tg-card"><p class="ops-tg-card__title" title="{lamp_reason}">{aid.upper()} · '
            f"{_lamp_icon(lamp)} {state_label}</p>"
            f'<p class="ops-tg-card__row" title="{listen_title}">{listen_line}</p>'
            f'<p class="ops-tg-card__row" title="{msgs_title}">{msgs_line} · вступления {join_label}</p>'
            f'<p class="ops-tg-card__row">Ошибки join {strikes}</p>{actions}</div>'
        )
    table = (
        '<div class="ops-tg-table-wrap"><table class="ops-tg-table">'
        '<thead><tr><th title="Номер TG на VPS: acc1/acc2/acc3">Аккаунт</th>'
        "<th>Состояние</th>"
        '<th title="Сейчас в эфире / Вступили / После фильтра — три числа">Слушают</th>'
        '<th title="Сессия = с последнего рестарта радара · Всего = накопительно">Сообщения</th>'
        '<th title="Статус очереди join для этого acc">Вступления</th>'
        '<th title="3 подряд fail → пауза вступлений">Ошибки join</th>'
        "<th>Действия</th></tr></thead>"
        f'<tbody id="rl-ops-tg-tbody">{"".join(rows)}</tbody></table></div>'
    )
    cards_html = f'<div class="ops-tg-cards" id="rl-ops-tg-cards">{"".join(cards)}</div>'
    hint = html.escape(
        str(
            q.get("hint_ru")
            or tg_queue_hint_ru(
                int(q.get("done") or 0),
                int(q.get("pending") or 0),
                int(q.get("fail") or 0),
                int(q.get("max_per_hour") or 0),
            )
        )
    )
    status = (
        '<div id="rl-ops-tg-status" class="ctl-status"><span class="dot"></span>'
        "<span>Ожидание</span></div>"
    )
    return botapi + table + cards_html + (
        f'<p class="sub ctl-hint" id="rl-ops-tg-queue-hint" '
        f'title="Статус CSV-очереди join по всем аккаунтам">{hint}</p>'
    ) + status


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
    poll_status = str(bot.get("bot_poll_status") or "unknown")
    legacy_status = str(bot.get("legacy_radar_status") or "unknown")
    poll_level = "ok" if poll_status == "active" and legacy_status == "active" else (
        "bad" if poll_status in {"failed", "inactive"} or legacy_status in {"failed", "inactive"} else "warn"
    )
    push_hint = "Push выключен глобально" if bot.get("match_push_enabled") is False else "Match-уведомления"
    bot_hint = (
        f"{_RAWLEAD_BOT_USERNAME}: {poll_status} · "
        f"{_FLPARSING_BOT_USERNAME}: {legacy_status} · {push_hint}"
    )
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
        + _card_html("Бот", f"{int(bot.get('push_subscribers') or 0)} с push", bot_hint, poll_level)
        + _card_html("Проблемы за 24 ч", f"{auth_e} вход · {fetch_e} парсер", "Детали — radar.log", p_level)
    )


def _ingest_sla_level(row: dict[str, int | float | str]) -> str:
    measurable = int(row.get("feed_measurable_24h", 0) or 0)
    feed_p50 = float(row.get("feed_p50_sec", 0.0) or 0.0)
    within = int(row.get("feed_within_5m", 0) or 0)
    if measurable < 5:
        return "warn"
    pct = (within / measurable * 100.0) if measurable else 0.0
    if feed_p50 <= 300 and pct >= 50:
        return "ok"
    if feed_p50 <= 600 or pct >= 25:
        return "warn"
    return "bad"


def _render_ingest_sla(data: dict[str, Any]) -> str:
    metrics = data.get("ingest") or {}
    if not metrics:
        return (
            '<div class="card"><p class="hint">Ingest SLA — нет данных Neon</p></div>'
        )
    parts: list[str] = []
    for bucket, label in (("fl", "FL.ru"), ("kwork", "Kwork")):
        row = metrics.get(bucket)
        if not row:
            continue
        gap_min = int(row.get("last_insert_gap_sec", 0) or 0) // 60
        feed_p50 = int(float(row.get("feed_p50_sec", 0.0) or 0.0) // 60)
        within = int(row.get("feed_within_5m", 0) or 0)
        measurable = int(row.get("feed_measurable_24h", 0) or 0)
        pct = int(within * 100 / measurable) if measurable else 0
        level = _ingest_sla_level(row)
        hint = (
            f"gap {gap_min} мин · feed p50 {feed_p50} мин · "
            f"≤5 мин {within}/{measurable} ({pct}%)"
        )
        parts.append(_card_html(f"Ingest SLA · {label}", f"≤5m {pct}%", hint, level))
    if not parts:
        return (
            '<div class="card"><p class="hint">Ingest SLA — ждём FL/Kwork с published_at</p></div>'
        )
    return "".join(parts)


def _render_exchanges(data: dict[str, Any]) -> str:
    rows = data.get("exchanges") or []
    if not rows:
        return '<div class="card"><p class="hint">Нет данных о биржах (SQLite или Neon недоступны)</p></div>'
    parts: list[str] = []
    restart_sources = {"fl", "kwork", "youdo", "tg"}
    for row in rows:
        sid = str(row.get("source_id") or "")
        name = html.escape(str(row.get("name") or "—"))
        icon = html.escape(str(row.get("exchange_icon") or "🟡"))
        status_ru = html.escape(str(row.get("exchange_status_ru") or "—"))
        level = str(row.get("exchange_level") or row.get("level") or "warn")
        ago = html.escape(str(row.get("last_ok_ago") or "нет данных"))
        today_new = int(row.get("today_new_ids") or 0)
        cycle_hint = html.escape(str(row.get("cycle_hint") or ""))
        cycle_block = (
            f'<p class="exchange-meta">{cycle_hint}</p>' if cycle_hint else ""
        )
        tier_hint = html.escape(str(row.get("residential_hint") or ""))
        tier_block = (
            f'<p class="exchange-meta">{tier_hint}</p>' if tier_hint else ""
        )
        last_line = html.escape(str(row.get("last_log_line") or row.get("listing_line") or "—"))
        err_human = html.escape(str(row.get("error_human") or ""))
        err_block = f'<p class="exchange-meta err">{err_human}</p>' if err_human else ""
        restart_btn = ""
        if sid in restart_sources:
            restart_btn = (
                f'<button type="button" class="btn rl-restart-source" data-target="{html.escape(sid)}">'
                f"Перезапустить источник</button>"
            )
        parts.append(
            f'<div class="card exchange-card">'
            f'<h2>{_dot_html(level)}</h2>'
            f'<p class="exchange-title">{icon} {name} — {status_ru}</p>'
            f'<p class="exchange-meta">Последний цикл: {ago}</p>'
            f'<p class="exchange-meta">Сегодня найдено новых заказов: {today_new}</p>'
            f"{cycle_block}"
            f"{tier_block}"
            f'<p class="exchange-meta">Последнее: {last_line}</p>'
            f"{err_block}"
            f'<div class="exchange-actions">{restart_btn}</div>'
            f"</div>"
        )
    return "".join(parts)


def _render_bots(data: dict[str, Any]) -> str:
    parts: list[str] = []
    for bot in data.get("bots") or []:
        username = str(bot.get("username") or "—")
        is_active = str(bot.get("is_active") or "unknown")
        level = str(bot.get("level") or _status_level(is_active))
        target = html.escape(str(bot.get("target") or ""))
        hint = f"is-active: {is_active}"
        last_cmd = str(bot.get("last_cmd") or "").strip()
        if last_cmd:
            hint += f" · {last_cmd}"
        parts.append(
            f'<div class="card"><h2>{_dot_html(level)}{html.escape(username)}</h2>'
            f'<p class="val">{html.escape(is_active)}</p>'
            f'<p class="hint">{html.escape(hint)}</p>'
            f'<button class="btn rl-ctl" data-target="{target}" data-action="restart">'
            f"Перезапуск</button></div>"
        )
    if not parts:
        return '<div class="card"><p class="hint">Нет данных о ботах</p></div>'
    return "".join(parts)


def _render_bots_ctl() -> str:
    return (
        '<button class="btn rl-ctl" data-target="bots-both" data-action="restart">'
        "Перезапуск обоих ботов</button>"
    )


def _render_delist_stats(data: dict[str, Any] | None = None) -> str:
    delist = (data or {}).get("delist") or {}
    if delist.get("last_run_at"):
        return html.escape(
            f"Ссылки: последний прогон {delist['last_run_at']} — "
            f"проверено {int(delist.get('checked') or 0)}, "
            f"снято {int(delist.get('delisted') or 0)}"
        )
    return "Ссылки: автопроверка FL/Kwork ещё не запускалась"


def _render_controls() -> str:
    return (
        '<button class="btn rl-ctl" data-target="radar" data-action="pause">Radar: пауза</button>'
        '<button class="btn rl-ctl" data-target="radar" data-action="resume">Radar: продолжить</button>'
        '<button class="btn rl-ctl" data-target="radar" data-action="restart">Radar: перезапуск</button>'
        '<button class="btn rl-ctl" data-target="site" data-action="restart">Site: перезапуск</button>'
        '<button class="btn rl-ctl" data-target="delist" data-action="run">Проверить ссылки</button>'
    )


def _delist_snapshot() -> dict[str, Any]:
    sqlite = _resolve_sqlite_path()
    if sqlite is None:
        return {"last_run_at": None, "checked": 0, "delisted": 0, "skipped": 0}
    from delist_checker import load_delist_last_stats

    return load_delist_last_stats(ProjectStorage(sqlite))


def _run_delist_batch_ops() -> tuple[bool, str]:
    sqlite = _resolve_sqlite_path()
    if sqlite is None:
        return False, "SQLite not found for delist"
    db_url = os.environ.get("DATABASE_URL", "").strip()
    if not db_url:
        return False, "DATABASE_URL not configured"
    saved_profile = os.environ.get("RADAR_PROFILE")
    try:
        os.environ["RADAR_PROFILE"] = "site"
        from config import load_config, load_radar_env
        from delist_checker import run_delist_batch, save_delist_run
        from pg_storage import NeonLeadStorage

        load_radar_env()
        cfg = load_config()
        pg = NeonLeadStorage(cfg.database_url or db_url)
        if not pg.enabled:
            return False, "Neon not available"
        storage = ProjectStorage(sqlite)
        errors: list[str] = []
        stats = run_delist_batch(cfg, pg, errors=errors, limit=15)
        save_delist_run(storage, stats)
        msg = (
            f"delist: checked={stats['checked']} delisted={stats['delisted']} "
            f"skipped={stats['skipped']}"
        )
        if errors:
            msg += f" · errors={len(errors)}"
        return True, msg
    except Exception as exc:
        return False, f"delist failed: {exc}"
    finally:
        if saved_profile is None:
            os.environ.pop("RADAR_PROFILE", None)
        else:
            os.environ["RADAR_PROFILE"] = saved_profile


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_RADAR_CTL_SCRIPT = _PROJECT_ROOT / "deploy" / "radar-ctl.sh"
_BOT_CTL_SCRIPT = _PROJECT_ROOT / "deploy" / "bot-ctl.sh"
_UNIT_OK_STATES = frozenset({"active", "activating"})


def _unit_status_note(status: str) -> str:
    return " (ещё поднимается)" if status == "activating" else ""


def _unit_restart_ok(status: str) -> bool:
    return status in _UNIT_OK_STATES


def _run_sudo_ctl(script: Path, *args: str) -> tuple[bool, str]:
    if not script.is_file():
        return False, f"{script.name} не найден (ожидается VPS)."
    cmd = ["sudo", str(script), *args]
    try:
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=30)
    except Exception as exc:
        return False, str(exc)[:200]
    out = (proc.stdout or proc.stderr or "").strip()
    if proc.returncode != 0:
        return False, (out or f"exit {proc.returncode}")[:300]
    return True, out or "ok"


def _systemctl_is_active(service: str) -> str:
    if service == "rawlead-radar-legacy":
        ok, state = _run_sudo_ctl(_RADAR_CTL_SCRIPT, "status", "legacy")
        return state if ok else "unknown"
    if service == "rawlead-radar":
        ok, state = _run_sudo_ctl(_RADAR_CTL_SCRIPT, "status", "site")
        return state if ok else "unknown"
    if service == "rawlead-bot-poll":
        ok, state = _run_sudo_ctl(_BOT_CTL_SCRIPT, "status")
        return state if ok else "unknown"
    try:
        proc = subprocess.run(
            ["systemctl", "is-active", service],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return "unknown"
    return (proc.stdout or proc.stderr or "unknown").strip() or "unknown"


def _bot_poll_status() -> str:
    """systemctl is-active rawlead-bot-poll — active/inactive/failed/unknown."""
    return _systemctl_is_active("rawlead-bot-poll")


def _legacy_radar_status() -> str:
    """systemctl is-active rawlead-radar-legacy — @FLPARSINGBOT poll + dogfood."""
    return _systemctl_is_active("rawlead-radar-legacy")


def _run_systemctl(action: str, service: str) -> tuple[bool, str]:
    if action not in {"restart", "start", "stop"}:
        return False, "unsupported action"
    if service == "rawlead-bot-poll":
        ok, msg = _run_sudo_ctl(_BOT_CTL_SCRIPT, action)
        return ok, f"rawlead-bot-poll: {action} {msg}"
    if service == "rawlead-radar":
        ok, msg = _run_sudo_ctl(_RADAR_CTL_SCRIPT, action, "site")
        return ok, f"rawlead-radar: {action} {msg}"
    if service == "rawlead-radar-legacy":
        ok, msg = _run_sudo_ctl(_RADAR_CTL_SCRIPT, action, "legacy")
        return ok, f"rawlead-radar-legacy: {action} {msg}"
    if service not in {"rawlead-api", "nginx"}:
        return False, "unsupported service"
    cmd = ["systemctl", action, service]
    try:
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=15)
    except Exception as exc:
        return False, str(exc)
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout or f"exit {proc.returncode}")[:300]
    return True, f"{service}: {action} ok"


def _drain_legacy_tg_queue() -> str:
    """Stop legacy, advance getUpdates offset (съесть queued /stop без выполнения)."""
    _run_sudo_ctl(_RADAR_CTL_SCRIPT, "stop", "legacy")
    time.sleep(1)
    saved_profile = os.environ.get("RADAR_PROFILE")
    drained = 0
    try:
        os.environ["RADAR_PROFILE"] = "legacy"
        from config import load_config, load_radar_env
        from storage import storage_from_config
        from tg_proxy_pool import tg_http_request

        import requests

        load_radar_env()
        cfg = load_config()
        storage = storage_from_config(cfg)
        bot_token = cfg.telegram_bot_token.strip()
        if not bot_token:
            return "tg-drain:skip no_token"
        offset = storage.get_tg_update_offset(bot_token=bot_token)
        api_url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        session = requests.Session()
        session.trust_env = False
        for _ in range(5):
            try:
                resp = tg_http_request(
                    "GET",
                    api_url,
                    session=session,
                    params={"offset": offset, "timeout": 0},
                    timeout=25.0,
                )
            except Exception:
                break
            if resp.status_code != 200:
                break
            try:
                body = resp.json()
            except ValueError:
                break
            if not body.get("ok"):
                break
            updates = body.get("result")
            if not isinstance(updates, list) or not updates:
                break
            next_offset = offset
            for upd in updates:
                if not isinstance(upd, dict):
                    continue
                update_id = upd.get("update_id")
                if isinstance(update_id, int):
                    next_offset = max(next_offset, update_id + 1)
            if next_offset <= offset:
                break
            storage.set_tg_update_offset(next_offset, bot_token=bot_token)
            drained += len(updates)
            offset = next_offset
    except Exception as exc:
        return f"tg-drain:err {type(exc).__name__}"[:120]
    finally:
        if saved_profile is None:
            os.environ.pop("RADAR_PROFILE", None)
        else:
            os.environ["RADAR_PROFILE"] = saved_profile
    return f"tg-drain={drained}"


def _restart_bot_poll() -> tuple[bool, str]:
    ok, msg = _run_systemctl("restart", "rawlead-bot-poll")
    time.sleep(2)
    poll_st = _bot_poll_status()
    ok_final = ok and _unit_restart_ok(poll_st)
    note = _unit_status_note(poll_st)
    return ok_final, f"{msg}; bot-poll is-active={poll_st}{note}"


def _restart_legacy_radar_unit() -> tuple[bool, str]:
    """Stop → drain TG queue → start legacy; recovery if still down."""
    drain = _drain_legacy_tg_queue()
    ok_start, msg_start = _run_sudo_ctl(_RADAR_CTL_SCRIPT, "start", "legacy")
    time.sleep(2)
    legacy_st = _legacy_radar_status()
    recovery = ""
    if not _unit_restart_ok(legacy_st):
        ok_rec, msg_rec = _run_sudo_ctl(_RADAR_CTL_SCRIPT, "start", "legacy")
        time.sleep(2)
        legacy_st = _legacy_radar_status()
        recovery = f"; recovery: {msg_rec}"
        ok_start = ok_start or ok_rec
    ok = ok_start and _unit_restart_ok(legacy_st)
    note = _unit_status_note(legacy_st)
    msg = f"{drain}; {msg_start}{recovery}; legacy is-active={legacy_st}{note}"
    return ok, msg


def _restart_both_bots() -> tuple[bool, str]:
    ok_poll, msg_poll = _restart_bot_poll()
    ok_legacy, msg_legacy = _restart_legacy_radar_unit()
    ok = ok_poll and ok_legacy
    msg = f"{msg_poll}; {msg_legacy}"
    return ok, msg


def _restart_radar_units(*, unpause: bool = True) -> tuple[bool, str]:
    """
    Restart site + legacy. После restart legacy может съесть queued /stop и выйти —
    тогда второй start (очередь уже без stop).
    """
    if unpause:
        sqlite = _resolve_sqlite_path()
        if sqlite is not None:
            ProjectStorage(sqlite).set_radar_paused(False)

    ok_site, msg_site = _run_systemctl("restart", "rawlead-radar")
    ok_legacy, msg_legacy = _restart_legacy_radar_unit()
    ok = ok_site and ok_legacy
    msg = f"{msg_site}; {msg_legacy}"
    return ok, msg


def run_ops_control(
    *,
    target: str,
    action: str,
    group: str = "",
    slot: int | None = None,
) -> dict[str, Any]:
    t = (target or "").strip().lower()
    a = (action or "").strip().lower()
    if t == "proxy":
        from proxy_ops import run_proxy_control, strip_internal_urls

        result = run_proxy_control(action=a, group=group, slot=slot)
        if result.get("ok") and a in {"clear-bans", "clear-youdo-bans"}:
            import threading

            def _restart_after_clear_bans() -> None:
                ok_radar, msg_radar = _run_systemctl("restart", "rawlead-radar")
                ok_bot, msg_bot = _restart_bot_poll()
                if not ok_radar:
                    logger.warning("ops clear-bans: radar restart failed: %s", msg_radar)
                if not ok_bot:
                    logger.warning("ops clear-bans: bot restart failed: %s", msg_bot)

            threading.Thread(target=_restart_after_clear_bans, daemon=True).start()
            result = dict(result)
            parts = [str(result.get("message") or "")]
            parts.append("Радар и бот перезапускаются в фоне (~30 с).")
            result["message"] = " ".join(p for p in parts if p)
            from proxy_ops import collect_proxies_payload

            result["proxies"] = strip_internal_urls(collect_proxies_payload())
        elif result.get("ok") and "proxies" in result:
            result = dict(result)
            result["proxies"] = strip_internal_urls(result["proxies"])
        return result
    if t == "radar" and a in {"pause", "resume"}:
        sqlite = _resolve_sqlite_path()
        if sqlite is None:
            return {"ok": False, "message": "SQLite not found for radar control"}
        storage = ProjectStorage(sqlite)
        storage.set_radar_paused(a == "pause")
        return {"ok": True, "message": "Radar paused" if a == "pause" else "Radar resumed"}
    if t == "radar" and a == "restart":
        ok, msg = _restart_radar_units(unpause=True)
        return {"ok": ok, "message": msg}
    if t == "site" and a == "restart":
        ok_api, msg_api = _run_systemctl("restart", "rawlead-api")
        ok_ng, msg_ng = _run_systemctl("restart", "nginx")
        ok = ok_api and ok_ng
        return {"ok": ok, "message": f"{msg_api}; {msg_ng}"}
    if t == "rawlead-bot" and a == "restart":
        ok, msg = _restart_bot_poll()
        return {"ok": ok, "message": msg}
    if t == "flparsing-bot" and a == "restart":
        ok, msg = _restart_legacy_radar_unit()
        return {"ok": ok, "message": msg}
    if t in {"bots-both", "bots"} and a == "restart":
        ok, msg = _restart_both_bots()
        return {"ok": ok, "message": msg}
    if t in {"bot-poll", "bot"} and a == "restart":
        ok, msg = _restart_bot_poll()
        return {"ok": ok, "message": msg}
    if t == "delist" and a == "run":
        import threading

        def _run_delist_bg() -> None:
            ok, msg = _run_delist_batch_ops()
            if not ok:
                logger.warning("ops delist background: %s", msg)

        threading.Thread(target=_run_delist_bg, daemon=True).start()
        return {"ok": True, "message": "Проверка ссылок запущена в фоне (~2 мин)."}
    if a == "restart_source" and t in {"fl", "kwork", "youdo", "tg"}:
        sqlite = _resolve_sqlite_path()
        if sqlite is None:
            return {"ok": False, "message": "SQLite not found for restart_source"}
        storage = ProjectStorage(sqlite)
        storage.set_setting(f"restart_source_{t}", "1")
        labels = {
            "fl": "FL.ru",
            "kwork": "Kwork",
            "youdo": "YouDo",
            "tg": "Telegram",
        }
        if t == "youdo":
            from youdo_parser import youdo_hard_reset

            youdo_hard_reset(reason="ops_restart_source", storage=storage)

            import threading

            def _restart_youdo_radar_bg() -> None:
                ok_radar, msg_radar = _run_systemctl("restart", "rawlead-radar")
                if not ok_radar:
                    logger.warning("ops restart_source youdo: radar restart failed: %s", msg_radar)

            threading.Thread(target=_restart_youdo_radar_bg, daemon=True).start()
            return {
                "ok": True,
                "message": (
                    "YouDo: сброс cooldown/guard, радар перезапускается (~30 с)"
                ),
            }
        return {
            "ok": True,
            "message": f"{labels[t]} перезапустится на следующем цикле (~2 мин)",
        }
    if t == "tg" and a == "tg-join-tick":
        try:
            from health_check import is_tg_monitor_active
        except Exception:
            def is_tg_monitor_active() -> bool:
                return False

        if is_tg_monitor_active():
            return {
                "ok": True,
                "message": "TG монитор активен — join идёт автоматически в tg_main",
            }
        return {
            "ok": True,
            "message": "Join tick: запустите tg_main / радар для автоматического join",
        }
    if t == "tg" and a == "tg-join-restart":
        try:
            from config import load_tg_join_config

            cfg = load_tg_join_config()
            if cfg.state_path.is_file():
                import json

                state = json.loads(cfg.state_path.read_text(encoding="utf-8"))
                if isinstance(state, dict):
                    for acc in state.values():
                        if isinstance(acc, dict):
                            acc["joins_this_hour"] = 0
                    cfg.state_path.write_text(
                        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
        except Exception as exc:
            return {"ok": False, "message": f"join restart failed: {exc}"}
        return {"ok": True, "message": "Join лимиты сброшены — следующий тик продолжит очередь"}
    return {"ok": False, "message": "Unsupported control target/action"}


def _proxy_status_dot(status: str) -> str:
    lv = status if status in ("ok", "warn", "bad") else "warn"
    return f'<span class="ops-status-dot ops-status-dot--{lv}"></span>'


def _proxy_switchable(group_id: str) -> bool:
    return group_id in {"tg-bot", "exchange-fl", "exchange-kwork", "exchange-pool"}


def _render_proxy_slot_actions(
    group_id: str,
    slot: int,
    active: bool,
    *,
    banned: bool = False,
) -> str:
    gid = html.escape(group_id)
    switch_btn = ""
    if _proxy_switchable(group_id):
        if banned:
            switch_btn = (
                f'<button type="button" class="btn rl-proxy-switch" data-group="{gid}" '
                f'data-slot="{slot}" disabled>Забанен — сначала сброс</button>'
            )
        else:
            switch_label = "Активен" if active else "→ Активировать"
            switch_disabled = " disabled" if active else ""
            switch_btn = (
                f'<button type="button" class="btn rl-proxy-switch" data-group="{gid}" '
                f'data-slot="{slot}"{switch_disabled}>{switch_label}</button>'
            )
    return (
        f'<div class="ops-proxy-actions">'
        f'<button type="button" class="btn rl-proxy-probe" data-group="{gid}" data-slot="{slot}">'
        f"Проверить</button>{switch_btn}</div>"
    )


def _render_proxy_probe_box(group_id: str, slot: int) -> str:
    gid = html.escape(group_id)
    return (
        f'<div class="ops-proxy-probe" id="ops-probe-{gid}-{slot}" '
        f'data-group="{gid}" data-slot="{slot}"></div>'
    )


def _render_proxy_group(group: dict[str, Any]) -> str:
    from proxy_ops import PROXY_GROUP_HELP

    gid = str(group.get("id") or "")
    title = html.escape(str(group.get("title") or gid))
    help_text = PROXY_GROUP_HELP.get(gid, "")
    help_html = (
        f'<p class="ops-proxy-group__help">{html.escape(help_text)}</p>' if help_text else ""
    )
    res_note = ""
    if group.get("residential_active"):
        alive = int(group.get("res_alive") or 0)
        total = int(group.get("res_total") or 0)
        res_note = (
            f'<p class="ops-proxy-group__help ops-proxy-residential">'
            f"FL сейчас работает через residential ({alive}/{total} слотов)</p>"
        )
    slots = group.get("slots") or []
    if not slots:
        return f'<div class="ops-proxy-group"><h4>{title}</h4><p class="sub">Слотов нет</p></div>'

    table_rows: list[str] = []
    cards: list[str] = []
    for slot in slots:
        sn = int(slot.get("slot") or 0)
        mask = html.escape(str(slot.get("mask") or "—"))
        status = str(slot.get("status") or "warn")
        active = bool(slot.get("active"))
        banned = bool(slot.get("banned_until"))
        label = html.escape(str(slot.get("status_label") or "—"))
        row_cls = "ops-proxy-row is-active" if active else "ops-proxy-row"
        card_cls = "ops-proxy-card is-active" if active else "ops-proxy-card"
        actions = _render_proxy_slot_actions(gid, sn, active, banned=banned)
        probe_box = _render_proxy_probe_box(gid, sn)
        table_rows.append(
            f'<tr class="{row_cls}">'
            f"<td>{sn}</td>"
            f"<td>{_proxy_status_dot(status)}{mask}</td>"
            f"<td>{label}</td>"
            f"<td>{actions}</td></tr>"
            f"<tr><td colspan=\"4\">{probe_box}</td></tr>"
        )
        cards.append(
            f'<div class="{card_cls} card">'
            f"<p><strong>{_proxy_status_dot(status)}Слот {sn}</strong></p>"
            f"<p>{mask}</p><p class=\"hint\">{label}</p>{actions}{probe_box}</div>"
        )

    cards_html = "".join(cards)
    rows_html = "".join(table_rows)
    return (
        f'<div class="ops-proxy-group" data-group="{html.escape(gid)}">'
        f"<h4>{title}</h4>{help_html}{res_note}"
        f'<div class="ops-proxy-table-wrap"><table><thead><tr>'
        f"<th>#</th><th>Прокси</th><th>Что значит</th><th></th></tr></thead><tbody>"
        f"{rows_html}</tbody></table></div>"
        f'<div class="ops-proxy-cards">{cards_html}</div></div>'
    )


def _render_proxies(data: dict[str, Any] | None) -> str:
    proxies = (data or {}).get("proxies") or {}
    auto = proxies.get("auto_failover")
    badge = (
        '<span class="ops-proxy-badge" title="Если прокси падает, система сама пробует следующий">'
        "Авто-переключение: вкл</span>"
        if auto
        else '<span class="ops-proxy-badge">Авто-переключение: выкл</span>'
    )
    last = proxies.get("last_probe_at")
    last_hint = (
        f'<span class="sub">Последняя проверка: {html.escape(str(last))}</span>'
        if last
        else ""
    )
    toolbar = (
        f'<div class="ops-proxy-toolbar">{badge}{last_hint}'
        f'<button type="button" class="btn rl-proxy-probe-all">Проверить все</button>'
        f'<button type="button" class="btn rl-proxy-clear-bans" '
        f'title="Все биржи + TG — полный сброс банов">'
        f"Сбросить баны</button>"
        f'<button type="button" class="btn rl-proxy-clear-youdo-bans" '
        f'title="Только YouDo DC + node — FL/Kwork не трогаем">'
        f"Сбросить баны YouDo</button>"
        f"</div>"
        f'<div id="rl-ops-proxy-status" class="ctl-status"><span class="dot"></span>'
        f"<span>Ожидание команд прокси</span></div>"
        f'<div id="rl-ops-proxies-body">'
    )
    groups_html = "".join(_render_proxy_group(g) for g in (proxies.get("groups") or []))
    if not groups_html:
        groups_html = '<p class="sub">Нет настроенных прокси в env</p>'
    return toolbar + groups_html + "</div>"


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


def _proxy_shell_html() -> str:
    return (
        '<div class="ops-proxy-toolbar">'
        '<span class="ops-proxy-badge" title="Если прокси падает, система сама пробует следующий">'
        "Авто-переключение: вкл</span>"
        '<button type="button" class="btn rl-proxy-probe-all">Проверить все</button>'
        '<button type="button" class="btn rl-proxy-clear-bans" '
        'title="Все биржи + TG — полный сброс банов">'
        "Сбросить баны</button>"
        '<button type="button" class="btn rl-proxy-clear-youdo-bans" '
        'title="Только YouDo DC + node — FL/Kwork не трогаем">'
        "Сбросить баны YouDo</button>"
        "</div>"
        '<div id="rl-ops-proxy-status" class="ctl-status"><span class="dot"></span>'
        "<span>Ожидание команд прокси</span></div>"
        '<div id="rl-ops-proxies-body"><p class="sub">Загрузка прокси…</p></div>'
    )


def ops_html(
    *,
    api_base: str,
    data: dict[str, Any] | None = None,
    ops_authenticated: bool = False,
    database_url: str = "",
) -> str:
    base = (api_base or "").strip().rstrip("/") or "/ops"
    logout_btn = (
        '<a href="/ops/logout" class="btn btn-logout">Выйти</a>' if ops_authenticated else ""
    )
    if data is not None:
        updated = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")
        header_meta = f'<p class="sub" id="rl-ops-updated">Обновлено {updated}</p>'
        db_url = database_url.strip() or os.environ.get("DATABASE_URL", "").strip()
        funnel = data.get("funnel") or fetch_ops_funnel(db_url)
        tg = data.get("tg") or fetch_ops_tg()
        script = _ops_script_block(base)
        return (
            _OPS_HTML.replace("__LOGIN_BLOCK__", "")
            .replace("__HEADER_META__", header_meta)
            .replace("__LOGOUT_BTN__", logout_btn)
            .replace("__FUNNEL_LAMPS__", _render_funnel_lamps(funnel))
            .replace("__FUNNEL_DIAGNOSIS__", _render_funnel_diagnosis(funnel))
            .replace("__FUNNEL_CARDS__", _render_funnel_cards(funnel))
            .replace("__FUNNEL_HINT__", _render_funnel_hint(funnel))
            .replace("__BOTS__", _render_bots(data))
            .replace("__BOTS_CTL__", _render_bots_ctl())
            .replace("__INGEST_SLA__", _render_ingest_sla(data))
            .replace("__EXCHANGES__", _render_exchanges(data))
            .replace("__TG_SECTION__", _render_tg_section(tg))
            .replace("__PROXIES__", _render_proxies(data))
            .replace("__CONTROLS__", _render_controls())
            .replace("__DELIST_STATS__", _render_delist_stats(data))
            .replace("__LEADS__", _render_leads_rows(data))
            .replace("__VIEWS__", _render_views_rows(data))
            .replace("__SCRIPT__", script)
        )
    if ops_authenticated:
        script = _ops_script_block(base)
        return (
            _OPS_HTML.replace("__LOGIN_BLOCK__", "")
            .replace("__HEADER_META__", '<p class="sub" id="rl-ops-updated">Загрузка…</p>')
            .replace("__LOGOUT_BTN__", logout_btn)
            .replace("__FUNNEL_LAMPS__", "")
            .replace(
                "__FUNNEL_DIAGNOSIS__",
                '<div class="ops-diagnosis" id="rl-ops-diagnosis" hidden></div>',
            )
            .replace("__FUNNEL_CARDS__", '<p class="sub">Загрузка воронки…</p>')
            .replace("__FUNNEL_HINT__", "Загрузка…")
            .replace("__BOTS__", "")
            .replace("__BOTS_CTL__", "")
            .replace("__INGEST_SLA__", "")
            .replace("__EXCHANGES__", "")
            .replace(
                "__TG_SECTION__",
                '<div id="rl-ops-tg-botapi"></div>'
                '<div class="ops-tg-table-wrap"><table><tbody id="rl-ops-tg-tbody"></tbody></table></div>'
                '<div class="ops-tg-cards" id="rl-ops-tg-cards"></div>'
                '<p class="sub" id="rl-ops-tg-queue-hint">Загрузка TG…</p>',
            )
            .replace("__PROXIES__", _proxy_shell_html())
            .replace("__CONTROLS__", _render_controls())
            .replace("__DELIST_STATS__", "")
            .replace("__LEADS__", "")
            .replace("__VIEWS__", "")
            .replace("__SCRIPT__", script)
        )
    return (
        _OPS_HTML.replace("__LOGIN_BLOCK__", "")
        .replace("__HEADER_META__", '<p class="sub" id="rl-ops-updated">Нужен вход</p>')
        .replace("__LOGOUT_BTN__", "")
        .replace("__FUNNEL_LAMPS__", "")
        .replace("__FUNNEL_DIAGNOSIS__", '<div class="ops-diagnosis" id="rl-ops-diagnosis" hidden></div>')
        .replace("__FUNNEL_CARDS__", "")
        .replace("__FUNNEL_HINT__", "Нужен вход")
        .replace("__BOTS__", "")
        .replace("__BOTS_CTL__", "")
        .replace("__INGEST_SLA__", "")
        .replace("__EXCHANGES__", "")
        .replace("__TG_SECTION__", '<p class="sub">Нужен вход</p>')
        .replace("__PROXIES__", _proxy_shell_html())
        .replace("__CONTROLS__", "")
        .replace("__DELIST_STATS__", "")
        .replace("__LEADS__", "")
        .replace("__VIEWS__", "")
        .replace("__SCRIPT__", "")
    )
