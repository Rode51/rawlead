# ТЗ — HTTP API (RawLead backend)

Версия: **0.4 (O39-docs)** · Lead · 2026-05-29 · sync post-O38  
Пред.: **0.3g** · Coder 2026-05-25

Связано: [`NEON_SCHEMA.md`](NEON_SCHEMA.md) · [`TZ_WP.md`](TZ_WP.md) · [`ARCHITECTURE.md`](ARCHITECTURE.md)

**Канон кода:** `src/api_server.py` · порт `RAWLEAD_API_PORT` (prod **8000**, local **18766**)

**Решение владельца:** сайт (WP) + подписки + Telegram-бот; **отдельного mobile app нет**.

---

## 1. Роль API

Единая точка между:

- **WordPress** (кабинет, теги, лента, оплата)
- **Neon** (лиды, пользователи)
- **Telegram-бот** (персональные дайджесты)
- **Рadar** (только ingest, не публичный)

```
[WP кабинет] ──REST──► [RawLead API] ◄── ingest ── [Рadar Python]
                            │
                            ▼
                       [Neon Postgres]
                            │
[TG Bot] ◄── poll/send ─────┘
```

---

## 2. MVP эндпоинты (сводная таблица)

| Method | Path | Кто | Действие | Статус |
|--------|------|-----|----------|--------|
| `GET` | `/health` | мониторинг | ok + версия | ✅ |
| `GET` | `/v1/skills/catalog` | WP | топ `lead_tags` | ✅ |
| `GET` | `/v1/feed` | WP | открытая лента | ✅ |
| `GET` | `/v1/leads/{id}` | WP | одна карточка | ✅ |
| `GET` | `/v1/me/feed` | WP кабинет | персональная лента | ✅ |
| `GET` | `/v1/me/tags` | WP | теги user | ✅ |
| `PUT` | `/v1/me/tags` | WP | replace тегов | ✅ |
| `GET` | `/v1/me/subscription` | WP | plan + pause | ✅ |
| `POST` | `/v1/me/subscription/pause` | WP/TG | пауза подписки | ✅ |
| `GET` | `/v1/me/notification-settings` | WP | push threshold | ✅ |
| `PATCH` | `/v1/me/notification-settings` | WP | push toggle/threshold | ✅ |
| `GET` | `/v1/me/leads/{id}/draft` | WP | **poll** async draft (O56/O58) | ✅ |
| `POST` | `/v1/me/leads/{id}/draft` | WP | submit draft → **202** pending / **200** ready | ✅ |
| `GET` | `/v1/me/replies` | WP cabinet | inbox откликов | ✅ |
| `DELETE` | `/v1/me/replies/{id}` | WP cabinet | soft-delete inbox | ✅ |
| `POST` | `/v1/auth/telegram` | WP | TG Login → user JWT/session | ✅ |
| `POST` | `/v1/internal/leads` | radar (API key) | ingest lead | ✅ |
| `GET` | `/v1/internal/digest` | bot (API key) | top-K digest | ⏳ |
| `GET` | `/ops/` | owner | HTML ops dashboard | ✅ O45 |
| `GET` | `/v1/admin/dashboard` | owner | JSON metrics | ✅ O45 |
| `POST` | `/v1/admin/pageview` | WP | pageview counter | ✅ O45 |

**Auth MVP:** заголовок `X-RawLead-User-Id: <uuid>` (default owner `00000000-0000-0000-0000-000000000001`). JWT — backlog multi-user.

**Draft (O56/O57/O58):** POST создаёт/возвращает job · GET poll до `ready` | `failed` · shared cache `leads.reply_draft` · rate limit **429** · AI off → **503** `ai unavailable`.

**Логика read (v0.9 / 3g):** Read-ленты (`/v1/feed`, `/v1/me/feed`) — только `is_visible = true` **и** `notified_at IS NOT NULL` (заказ уже был в TG-боте). Ingest/радар до notify: `is_visible = false`. `/v1/feed`: `sort=time` → `created_at DESC`, `min_score` по **`ai_score`**; `sort=match` → `final_rank DESC`, `min_score` по **`final_rank`**; query `skills=python,fastapi` — фильтр `lead_tags ∩ skills ≠ ∅`, rank по skills. `/v1/me/feed` — rank по `user_tags` (или `skills` в query), те же `sort`/`skills`. Dogfood-бот — все лиды (включая `is_visible=false`, без notify). _Устарело: `contour` — не использовать._

---

## 3d. Draft `GET`/`POST /v1/me/leads/{id}/draft` (O56–O58)

**Headers:** `X-RawLead-User-Id`

**POST:** fast path cache → **200** `{status:"ready", reply_draft, …}` · иначе enqueue → **202** `{status:"pending"}` · rate limit **429** · overlap km=0 → **403**.

**GET (poll):** `{status:"ready"|"pending"|"failed", reply_draft?, error?}` · HTTP **202** если pending · **200** если ready/failed body.

**Shared draft (O57):** первый L2 пишет `leads.reply_draft` · последующие users — cache hit без L2.

---

## 3e. Inbox `/v1/me/replies`

**GET** — список сохранённых откликов (не soft-deleted). **DELETE** `/{lead_id}` — `deleted_at`.

---

## 3f. Auth `/v1/auth/telegram`

Body: TG Login widget payload → upsert `users` (tg_user_id, …) → session token для WP.

---

## 3g. Admin / ops (owner)

| Path | Назначение |
|------|------------|
| `GET /ops/` | HTML dashboard |
| `GET /v1/admin/dashboard` | JSON stats |
| `POST /v1/admin/pageview` | `{path}` → `admin_pageviews` |

---

## 3. `GET /v1/feed` (открытая, §3g)

**Query:** `limit`, `offset`, `min_score`, `skills` (comma-separated), `category` (`dev,design` — OR), `sort` (`time` | `match`, default `time`).

| `sort` | ORDER BY | `min_score` применяется к |
|--------|----------|---------------------------|
| `time` | `created_at DESC` | `ai_score` |
| `match` | `final_rank DESC` (в памяти, scan ≤500) | `final_rank` |

**`skills`:** если задан — только лиды с пересечением `lead_tags`; `keyword_match` и `final_rank` по весам skills (1.0 каждый). Без skills — все bot-лиды; `keyword_match=0`, `final_rank ≈ ai_score×0.6`.

**Response:** `items[]` с `final_rank`, `keyword_match`, `lead_tags`, … + `sort`, `skills[]`.

---

## 3a. `GET /v1/skills/catalog` (§3g)

**Query:** `category` (optional, `dev,design`) — только группы выбранных специализаций.

**Response:** `{"groups":[…],"skills":[{"tag":"python","count":12},…]}` — топ тегов из `lead_tags` видимых лидов (`is_visible=true`).

---

## 3b. `GET /v1/me/feed` (кабинет)

**Headers:** `X-RawLead-User-Id` (MVP — owner UUID).

**Query:** как `/v1/feed` + `sort` (default `match`). **`min_score`:** при `sort=match` — `final_rank`; при `sort=time` — `ai_score`. Без query `skills` — rank по `user_tags` из БД.

**Response:** `items[]` с `final_rank`, `keyword_match`, `ai_score`, `lead_tags`, …

**Rank:** `keyword_match` = weighted overlap `lead_tags` ∩ `user_tags`; `final_rank = round(ai_score×0.6 + keyword_match×0.4)` — env `RANK_WEIGHT_*`.

---

## 3c. `GET` / `PUT /v1/me/tags`

- `GET` → `{"tags":["wordpress",…]}`
- `PUT` body `{"tags":[…]}` — replace всех тегов user, нормализация lowercase

---

## 4. Бот — персональная рассылка

| Сейчас (этап 0) | v1 SaaS |
|-----------------|---------|
| один `TELEGRAM_CHAT_ID` | `users.tg_chat_id` per подписчик |
| все лиды владельцу | digest: top-3 за 4 ч, `final_rank ≥ N` |
| | только `subscriptions.active_until > now()` |

Рadar **не** рассылает сам по 100 юзерам — **worker/cron** или цикл в `tg_main` extension вызывает `/v1/internal/digest` и `sendMessage` per user.

---

## 5. Безопасность

| Секрет | Где |
|--------|-----|
| `DATABASE_URL` | `.env` radar + API server |
| `RAWLEAD_API_KEY` | ingest + bot → internal routes |
| JWT secret WP↔API | WP plugin config, не Git |

Rate limit на `/v1/feed` — per user.

---

## 6. Деплой (этапы)

| Этап | Где API | Где radar |
|------|---------|-----------|
| Dev | localhost :18766 | ПК |
| v1 | тот же VPS что radar 24/7 | VPS |

Local WP (`radarzakaz.local`) → API на `localhost` или ngrok для отладки.

---

## 7. Очередь Coder

1. Расширить Neon schema ([`NEON_SCHEMA.md`](NEON_SCHEMA.md)).
2. `src/api/` или `scripts/rawlead_api.py` — FastAPI/Flask minimal.
3. Ingest из pipeline → `ai_score` + `lead_tags` в prompt ИИ.
4. WP plugin «кабинет» — REST client (фаза после API).

Приёмка: два тестовых user с разными тегами → разный порядок в `/v1/feed`.

---

_Coder — только по `CODER_PROMPT.md` от Lead._
