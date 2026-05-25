# ТЗ — HTTP API (RawLead backend)

Версия: **0.3g** · Lead · 2026-05-23 · Coder 2026-05-25

Связано: [`NEON_SCHEMA.md`](NEON_SCHEMA.md) · [`TZ_WP.md`](TZ_WP.md) · [`ARCHITECTURE.md`](ARCHITECTURE.md)

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

## 2. MVP эндпоинты

| Method | Path | Кто | Действие | Статус |
|--------|------|-----|----------|--------|
| `GET` | `/health` | мониторинг | ok + версия | ✅ 3c |
| `GET` | `/v1/skills/catalog` | WP | топ-50 `lead_tags` из лидов с `notified_at` | ✅ 3g |
| `GET` | `/v1/feed` | WP | лиды из бота + `skills` + `sort=time\|match` | ✅ 3g |
| `GET` | `/v1/leads/{id}` | WP | одна карточка + breakdown score | ✅ 3c |
| `GET` | `/v1/me/feed` | WP кабинет | персональная лента, sort `final_rank` DESC, `min_score` по `final_rank` | ✅ 3e |
| `PUT` | `/v1/me/tags` | WP | сохранить `user_tags[]` (replace, lowercase) | ✅ 3e |
| `GET` | `/v1/me/tags` | WP | текущие теги owner | ✅ 3e |
| `GET` | `/v1/me/subscription` | WP | заглушка `free` | ✅ 3e |
| `POST` | `/v1/internal/leads` | radar (API key) | upsert lead + ai_score + lead_tags | ✅ 3c |
| `GET` | `/v1/internal/digest` | bot (API key) | top-K leads per user where rank ≥ threshold | ⏳ 3e |

**3c–3e — файл:** `src/api_server.py`, `src/rank.py` · порт `18766` · `/internal/*` → `X-API-Key` · кабинет MVP → `X-RawLead-User-Id: 00000000-0000-0000-0000-000000000001` (без JWT).

**Логика read (v0.9 / 3g):** Read-ленты (`/v1/feed`, `/v1/me/feed`) — только `is_visible = true` **и** `notified_at IS NOT NULL` (заказ уже был в TG-боте). Ingest/радар до notify: `is_visible = false`. `/v1/feed`: `sort=time` → `created_at DESC`, `min_score` по **`ai_score`**; `sort=match` → `final_rank DESC`, `min_score` по **`final_rank`**; query `skills=python,fastapi` — фильтр `lead_tags ∩ skills ≠ ∅`, rank по skills. `/v1/me/feed` — rank по `user_tags` (или `skills` в query), те же `sort`/`skills`. Dogfood-бот — все лиды (включая `is_visible=false`, без notify). _Устарело: `contour` — не использовать._

---

## 3. `GET /v1/feed` (открытая, §3g)

**Query:** `limit`, `offset`, `min_score`, `skills` (comma-separated), `sort` (`time` | `match`, default `time`).

| `sort` | ORDER BY | `min_score` применяется к |
|--------|----------|---------------------------|
| `time` | `created_at DESC` | `ai_score` |
| `match` | `final_rank DESC` (в памяти, scan ≤500) | `final_rank` |

**`skills`:** если задан — только лиды с пересечением `lead_tags`; `keyword_match` и `final_rank` по весам skills (1.0 каждый). Без skills — все bot-лиды; `keyword_match=0`, `final_rank ≈ ai_score×0.6`.

**Response:** `items[]` с `final_rank`, `keyword_match`, `lead_tags`, … + `sort`, `skills[]`.

---

## 3a. `GET /v1/skills/catalog` (§3g)

**Response:** `{"skills":[{"tag":"python","count":12},…]}` — топ 50 тегов из `lead_tags` лидов с `notified_at IS NOT NULL`, по частоте.

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
