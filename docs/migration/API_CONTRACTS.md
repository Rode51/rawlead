# RawLead — API contracts (frontend)

**Источник истины:** `src/api_server.py` · WP прокси: `wordpress/.../inc/rawlead-api.php`.

## Base URLs

| Среда | База | Примечание |
|-------|------|------------|
| **Next (цель)** | `https://api.rawlead.ru` | Прямые вызовы `/v1/*` |
| WP сейчас | `/wp-json/rawlead/v1/*` | same-origin → прокси на API |
| Health | `GET /health` | без `/v1` |

## Auth (все protected routes)

| Header | Значение |
|--------|----------|
| `Authorization` | `Bearer <JWT>` |
| Rotation | ответ может содержать `X-Rawlead-Access-Token` → заменить в `localStorage` |

**localStorage key:** `rawlead_access_token` (как `rawlead-feed.js`).

**CORS (после cutover):** `RADAR_CORS_ORIGINS` должен включать `https://rawlead.ru`.

---

## Легенда

- **Auth:** JWT required (`401` без токена)
- **Public:** без токена
- **MVP:** нужен для gate до рекламы
- **Later:** после MVP

---

## Public / anon

### `GET /v1/feed` · MVP

Публичная лента. С валидным JWT в `Authorization` — без 30m delay + персонализация.

**Query:**

| Param | Type | Default | Notes |
|-------|------|---------|-------|
| `limit` | int | 20 | 1–100 |
| `offset` | int | 0 | |
| `min_score` | int | 0 | 0–100 |
| `min_match` | int | 0 | 0, 50, 60, 70, 80, 90 |
| `skills` | string | "" | comma-separated tags |
| `category` | string | "" | dev, design, marketing, text |
| `sort` | string | `time` | `time` \| `match` |
| `source` | string | "" | filter by exchange |

**Response 200:**

```json
{
  "items": [/* LeadItem */],
  "limit": 20,
  "offset": 0,
  "count": 20,
  "today_count": 847,
  "sort": "time",
  "min_match": 0,
  "skills": [],
  "category": [],
  "source": [],
  "feed_delayed": true
}
```

**LeadItem** (ключевые поля):

| Field | Type | Notes |
|-------|------|-------|
| `id` | int | |
| `source` | string | fl, kwork, tg, … |
| `title` | string | |
| `body` | string | |
| `task_summary` | string | L1 кратко |
| `url` | string | ссылка на биржу |
| `budget_text` | string \| null | |
| `ai_score` | int | |
| `keyword_match` | int \| null | % для auth+tags |
| `final_rank` | int | |
| `category` | string | |
| `lead_tags` | string[] | |
| `lead_tag_labels` | object | tag → label |
| `tools_required` | string[] | |
| `difficulty` | string \| null | |
| `tz_attachment` | object \| null | |
| `created_at` | ISO8601 | |
| `is_hot` | bool | |
| `display_views` | int | |
| `display_replies` | int | |
| `reply_draft` | string | **пусто** в public feed (O60a) |

---

### `GET /v1/leads/{lead_id}` · MVP

Одна карточка. Bearer optional → `keyword_match` если есть user.

**Response 200:** один `LeadItem`. **404** если нет лида.

---

### `GET /v1/public/site-stats` · P1 home

WP REST: `/wp-json/rawlead/v1/site-stats`.

```json
{
  "radar_online": true,
  "leads_week": 812,
  "leads_week_display": "800+"
}
```

---

### `GET /v1/skills/catalog` · MVP (filter UI)

Каталог навыков для filter bar (не ручной picker профиля).

**Query:** `category`, `limit`, … (см. `api_server.py`).

**Response:** `{ "groups": [...], "skills": [{ "tag", "label", ... }] }`

---

## Auth

### `POST /v1/auth/bot-session` · MVP

**Body:** `{}`  
**Response 200:**

```json
{
  "auth_token": "plain-one-time-token",
  "deep_link": "https://t.me/rawlead_bot?start=auth_...",
  "expires_at": "2026-06-19T12:00:00+00:00"
}
```

Flow: open deep link → poll `bot-complete` → save JWT.

---

### `GET /v1/auth/bot-complete?auth={token}` · MVP  
### `POST /v1/auth/bot-complete` · MVP

**Body (POST):** `{ "auth_token": "..." }`

**Response 200 (success):**

```json
{
  "access_token": "jwt...",
  "token_type": "bearer",
  "user_id": "uuid",
  "tg_user_id": 123456789,
  "username": "handle",
  "first_name": "Name",
  "avatar_url": "https://...",
  "has_avatar": true
}
```

**Errors:** `401` awaiting bot · `404` session · `410` expired/consumed.

---

### `POST /v1/auth/telegram` · legacy

Telegram Login Widget — prod редко; cabinet.js fallback. Same shape JWT response.

---

## Profile & tags

### `GET /v1/me` · MVP

```json
{
  "user_id": "uuid",
  "tg_user_id": 123,
  "username": "x",
  "first_name": "X",
  "avatar_url": "...",
  "has_avatar": true,
  "can_ops_admin": false
}
```

---

### `GET /v1/me/tags` · MVP

```json
{
  "tags": ["python", "wordpress_dev"],
  "weights": { "python": 3.0, "wordpress_dev": 2.5 }
}
```

---

### `POST /v1/me/tags/import` · MVP

Quiz finish → Neon.

**Body:**

```json
{
  "tags": { "python": 3.0, "react": 2.0 },
  "cx_pref": 1.2,
  "niches": ["dev", "design"]
}
```

**Response:** `{ "ok": true, "imported": 5 }`

---

### `POST /v1/me/tags/weight_delta` · Later

Поведенческие веса (draft, expand, delete). Сервер часто сам шлёт с draft — дублировать осторожно.

**Body:** `{ "event": "draft", "tags": ["python"] }`

---

### `PUT /v1/me/tags` · deprecated

Ручной PUT тегов — **не использовать** в quiz-first UI.

---

## Quiz

### `GET /v1/quiz/start` · MVP

**Response:** `{ "done": false, "card": { ... } }` или `{ "done": true, "profile": { ... } }`

### `POST /v1/quiz/next` · MVP

**Body:**

```json
{
  "history": [
    { "card_id": "...", "action": "like", "tags": ["python"] }
  ]
}
```

**Response (card):** `{ "done": false, "card": { "id", "title", "body", "tags", ... } }`  
**Response (done):** `{ "done": true, "profile": { "tags", "niches", "leads_per_week", ... } }`

---

## Feed prefs

### `GET /v1/me/feed-prefs` · MVP  
### `PUT /v1/me/feed-prefs` · MVP

Сохранённые фильтры/сортировка пользователя. См. `rawlead-feed.js` `restFeedPrefs`.

---

## Draft & inbox

### `GET /v1/me/draft/quota` · MVP

```json
{
  "draft_hourly_limit": 5,
  "draft_used": 1,
  "draft_remaining": 4,
  "draft_retry_after_sec": 0
}
```

---

### `POST /v1/me/leads/{lead_id}/draft` · MVP

Создать / запросить L2 черновик.

**Response:** `200` ready · `202` pending · `429` rate limit · `503` AI off.

```json
{
  "status": "ready",
  "lead_id": 123,
  "reply_draft": "Текст отклика...",
  "tools_required": [],
  "keyword_match": 85
}
```

Pending:

```json
{ "status": "pending", "queued": true, "queue_ahead": 2 }
```

---

### `GET /v1/me/leads/{lead_id}/draft` · MVP

Poll async draft (same body shapes).

---

### `POST /v1/me/leads/{lead_id}/draft/warm` · Later

Pre-warm on premium expand — без создания inbox row.

---

### `GET /v1/me/replies` · MVP

Inbox `/cabinet/`.

**Query:** `limit`, `offset`

**Response:**

```json
{
  "items": [/* LeadItem + replied_at */],
  "limit": 20,
  "offset": 0,
  "count": 20,
  "total": 42
}
```

`replied_at` — ISO8601 на каждом item.

---

### `DELETE /v1/me/replies/{lead_id}` · MVP

Soft-delete отклика из inbox.

---

## Subscription & pay

### `GET /v1/me/subscription` · MVP

```json
{
  "plan": "trial",
  "plan_label": "Trial Premium",
  "is_active": true,
  "active_until": "...",
  "status": "active",
  "effective_access": true,
  "yookassa_available": true,
  "trial_used_at": null
}
```

`plan`: `free` | `trial` | `agent` | `pro` | `owner` · UI смотрит **`effective_access`**.

---

### `POST /v1/me/subscription/checkout` · MVP

**Body:** `{ "kind": "trial" | "subscription" }`

**Response:** `{ "confirmation_url": "https://yookassa...", ... }` — redirect user.

---

### `POST /v1/me/subscription/confirm` · MVP

После оплаты / bot deep link.

---

### `POST /v1/me/subscription/trial-start` · alias

Legacy → checkout kind=trial.

---

## Notifications · Later (cabinet has UI)

### `GET /v1/me/notification-settings`  
### `PATCH /v1/me/notification-settings`

Push threshold, enabled flag.

---

## Support · Later

| Method | Path |
|--------|------|
| POST | `/v1/support/ticket` |
| GET | `/v1/support/thread` |
| GET | `/v1/support/unread` |

---

## Analytics · P1

### `POST /v1/admin/pageview` · public from WP

**Body:** `{ "path": "/lenta", "visitor_id": "..." }`  
**Response:** `204`

---

## Out of scope (не вызывать из product UI)

| Prefix | Назначение |
|--------|------------|
| `/v1/admin/*` | owner ops (кроме pageview) |
| `/v1/ops/*` | ops dashboard |
| `/ops/*` | HTML pult |

---

## Client events (не API, но обязательно)

| Event | Когда | Действие |
|-------|-------|----------|
| `rawlead-tags-imported` | после quiz import | refetch tags + feed |
| `rawlead-quiz-complete` | quiz done | avoid stale reload |

**localStorage:** `rawlead_user_tags_rev` — revision для sync.

---

## Errors (общее)

| Code | Meaning |
|------|---------|
| 401 | нет / невалидный JWT |
| 403 | нет прав |
| 404 | не найдено |
| 409 | trial already used |
| 429 | draft rate limit |
| 503 | AI / payment unavailable |

Детали часто в `{ "detail": "..." }` или `{ "detail": { ... } }` для 429.

---

## Референс в коде

| Что | Где |
|-----|-----|
| WP REST map | `rawlead-api.php` `register_rest_route` |
| FastAPI | `src/api_server.py` |
| Feed client | `rawlead-feed.js` |
| Cabinet client | `rawlead-cabinet.js` |
| Quiz client | `rawlead-quiz.js` |

_Lead Architect · 2026-06-19_
