"""O45: /ops/ owner dashboard — users list + pageview stats."""

from __future__ import annotations

import html
import os
from datetime import date, datetime, timezone
from typing import Any

import psycopg

_OPS_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>RawLead Ops</title>
<style>
body{font-family:system-ui,sans-serif;margin:1.5rem;background:#0f1419;color:#e8eaed}
h1{font-size:1.25rem} table{border-collapse:collapse;width:100%;margin:1rem 0;font-size:.875rem}
th,td{border:1px solid #2a3544;padding:.4rem .6rem;text-align:left}
th{background:#1a2332}.err{color:#f87171}.muted{color:#94a3b8;font-size:.875rem}
</style>
</head>
<body>
<h1>RawLead /ops/</h1>
<p class="muted" id="rl-ops-status">Загрузка…</p>
<h2>Пользователи</h2>
<table id="rl-ops-users"><thead><tr>
<th>TG</th><th>Создан</th><th>План</th><th>Навыки</th><th>Push</th>
</tr></thead><tbody></tbody></table>
<h2>Визиты (7 дней)</h2>
<table id="rl-ops-views"><thead><tr><th>День</th><th>Путь</th><th>Просмотры</th></tr></thead><tbody></tbody></table>
<script>
(function () {
  var API = "__API_BASE__";
  var token = localStorage.getItem("rawlead_access_token") || "";
  var statusEl = document.getElementById("rl-ops-status");
  if (!token) {
    statusEl.textContent = "Войди через /cabinet/ (owner TG), затем обнови эту страницу.";
    statusEl.className = "err";
    return;
  }
  fetch(API + "/v1/admin/dashboard", {
    headers: { "Authorization": "Bearer " + token, "Accept": "application/json" }
  }).then(function (r) {
    if (r.status === 403) throw new Error("Доступ только владельцу (TELEGRAM_CHAT_ID)");
    if (!r.ok) throw new Error("HTTP " + r.status);
    return r.json();
  }).then(function (data) {
    statusEl.textContent = "Обновлено " + new Date().toLocaleString("ru-RU");
    var ub = document.querySelector("#rl-ops-users tbody");
    ub.innerHTML = "";
    (data.users || []).forEach(function (u) {
      var tr = document.createElement("tr");
      tr.innerHTML = "<td>" + (u.tg_username ? "@" + u.tg_username : "—") + "</td>"
        + "<td>" + (u.created_at || "—") + "</td>"
        + "<td>" + (u.plan || "—") + (u.is_active ? " ✓" : "") + "</td>"
        + "<td>" + (u.tags_count || 0) + "</td>"
        + "<td>" + (u.push_enabled === false ? "off" : "on") + " ≥" + (u.push_min_match || 60) + "%</td>";
      ub.appendChild(tr);
    });
    var vb = document.querySelector("#rl-ops-views tbody");
    vb.innerHTML = "";
    (data.pageviews || []).forEach(function (v) {
      var tr = document.createElement("tr");
      tr.innerHTML = "<td>" + v.day + "</td><td>" + v.path + "</td><td>" + v.views + "</td>";
      vb.appendChild(tr);
    });
  }).catch(function (e) {
    statusEl.textContent = e.message || String(e);
    statusEl.className = "err";
  });
})();
</script>
</body>
</html>"""


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
    conn.commit()


def record_pageview(database_url: str, *, path: str, day: date | None = None) -> None:
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
        conn.commit()


def fetch_dashboard(database_url: str) -> dict[str, Any]:
    url = database_url.strip()
    users: list[dict[str, Any]] = []
    pageviews: list[dict[str, Any]] = []
    with psycopg.connect(url) as conn:
        ensure_admin_tables(conn)
        with conn.cursor() as cur:
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
    return {"users": users, "pageviews": pageviews}


def ops_html(*, api_base: str) -> str:
    base = (api_base or "").rstrip("/") or ""
    return _OPS_HTML.replace("__API_BASE__", html.escape(base, quote=True))
