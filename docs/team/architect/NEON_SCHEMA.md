# Neon Postgres — схема v1 (лиды + персональный rank)

Версия: **0.4 (O39-docs)** · Lead Architect · 2026-05-29  
Пред.: **0.3 (3b)** · 2026-05-25  
Решение владельца: **Neon** как облако; WP **не** ходит в Postgres напрямую.

> **v0.9:** поле **`contour`** (`owner`/`saas`) — **отменено**. Вместо него **`is_visible`** после ИИ-модерации — см. [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) §0c.

**Миграции:** `sql/001` … `sql/015` · apply через Neon SQL Editor или auto DDL в `draft_async._ensure_draft_tables`.

Черновик SQL: [`../../sql/001_neon_schema.sql`](../../sql/001_neon_schema.sql) + последующие `sql/00*.sql`.

---

## 1. Принцип

| Когда | Что считаем |
|-------|-------------|
| **Ingest** (радар Python) | `ai_score`, `ai_verdict`, `lead_tags` — один раз на вакансию |
| **Read** (API → WP / бот) | `keyword_match` + **итоговый rank** — per user, на лету (v0) |

---

## 2. Таблицы

### `leads` (канон в SQL; = `raw_leads` в vision)

| Колонка | Тип | Смысл |
|---------|-----|--------|
| `id` | BIGSERIAL PK | |
| `source` | TEXT | `fl`, `kwork`, `tg:{chat_id}` |
| `external_id` | TEXT | id на бирже / msg id |
| `title` | TEXT | |
| `body` | TEXT | полный текст / описание |
| `url` | TEXT | |
| `budget_text` | TEXT | |
| `ai_score` | SMALLINT 0–100 | базовая оценка ИИ («насколько заказ годный») |
| `ai_verdict` | TEXT | Брать / Сомнительно / Нет |
| `lead_tags` | JSONB | теги из ИИ: `["python","fastapi","parser"]` |
| `ai_reasons` | JSONB | 2–3 строки «почему score» (для UI); **O97:** опц. ключ `complexity` 1–5 **без DDL** |
| `is_visible` | BOOLEAN | `true` — в `/feed` и match; `false` — только dogfood-бот владельца |
| `content_hash` | TEXT | SHA-256 нормализованного текста (`listing_dedup`); NULL — дедуп только по `source`+`external_id` |
| `notified_at` | TIMESTAMPTZ | legacy / owner |
| `created_at` | TIMESTAMPTZ | момент **INSERT в Neon** (≠ дата на бирже) |
| `source_published_at` | TIMESTAMPTZ | когда опубликовано на бирже/TG (`sql/016`, O90) |
| `l1_completed_at` | TIMESTAMPTZ | когда L1 выставил score/visible (`sql/016`, O90) |
| `last_fetch_ok_at` | TIMESTAMPTZ | последний успешный fetch карточки (delist, O90) |
| `category` | TEXT | `dev` / `design` / … (`sql/002`) |
| `task_summary` | TEXT | L1 краткое описание (`sql/004`) |
| `tools_required` | JSONB | стек заказа L2 (`sql/005`) |
| `reply_draft` | TEXT | **shared** on-demand draft O57 (`sql/005`) |

**UNIQUE** `(source, external_id)` · **UNIQUE** `(content_hash)` где hash не NULL · индекс `created_at DESC` · **GIN** на `lead_tags`.

Ingest: `INSERT … ON CONFLICT (content_hash) DO NOTHING` — при дубле текста не слать в TG (см. `pg_storage.record_new_lead`).

### `users`

| Колонка | Тип | Смысл |
|---------|-----|--------|
| `id` | UUID PK | seed `00000000-0000-0000-0000-000000000001` = владелец (#1) |
| `wp_user_id` | BIGINT UNIQUE | связь с WP |
| `email` | TEXT | |
| `tg_chat_id` | BIGINT | для push в TG |
| `push_min_match` | INT default 60 | порог % для MATCH_PUSH (O30) |
| `push_enabled` | BOOL default TRUE | toggle push (O30) |
| `tg_user_id` | BIGINT | TG Login (`sql/003`) |
| `tg_username` | TEXT | |
| `tg_first_name` | TEXT | |
| `tg_photo_url` | TEXT | |
| `created_at` | TIMESTAMPTZ | |

### `user_tags`

| Колонка | Тип | Смысл |
|---------|-----|--------|
| `user_id` | UUID FK → users | |
| `tag` | TEXT | нормализованный lowercase |
| `weight` | REAL default 1.0 | приоритет тега |

**UNIQUE** `(user_id, tag)`.

### `subscriptions`

| Колонка | Тип | Смысл |
|---------|-----|--------|
| `user_id` | UUID FK | |
| `plan` | TEXT | `free` / `pro` / … |
| `active_until` | TIMESTAMPTZ | |
| `created_at` | TIMESTAMPTZ | |

### `user_lead_replies` (O23 · `sql/008`)

Per-user inbox / сохранённый отклик.

| Колонка | Тип | Смысл |
|---------|-----|--------|
| `user_id` | UUID FK | |
| `lead_id` | INT FK | |
| `reply_draft` | TEXT | текст отклика |
| `created_at` | TIMESTAMPTZ | |
| `deleted_at` | TIMESTAMPTZ | soft delete |

**PK** `(user_id, lead_id)`.

### `draft_jobs` (O56 · `sql/012`)

Per-user async draft job (legacy path; см. также `lead_draft_jobs`).

| Колонка | Тип | Смысл |
|---------|-----|--------|
| `user_id` | UUID FK | |
| `lead_id` | INT FK | |
| `status` | TEXT | `pending` \| `failed` |
| `error_msg` | TEXT | при fail |
| `created_at` / `updated_at` | TIMESTAMPTZ | |

### `lead_draft_jobs` (O57 · `sql/013`)

**Один** in-flight L2 на lead (shared draft thundering herd).

| Колонка | Тип | Смысл |
|---------|-----|--------|
| `lead_id` | INT PK FK | |
| `status` | TEXT | `pending` \| `failed` |
| `error_msg` | TEXT | |
| `created_at` / `updated_at` | TIMESTAMPTZ | |

### `match_push_log` (O28 · `sql/009`)

Dedupe TG push: **PK** `(user_id, lead_id)`.

### `admin_pageviews` (O45 · `sql/011`)

**PK** `(path, day)` · счётчик просмотров для `/ops/`.

### `auth_bot_sessions` (O84 · `sql/015`)

One-time deep-link login: `/cabinet/` → `@rawlead_bot?start=auth_<token>` → JWT.

| Колонка | Тип | Смысл |
|---------|-----|--------|
| `id` | UUID PK | |
| `token_hash` | TEXT UNIQUE | SHA-256 plain token (не хранить token) |
| `expires_at` | TIMESTAMPTZ | TTL **5 мин** |
| `tg_user_id` | BIGINT | после `/start auth_*` в боте |
| `tg_username` / `tg_first_name` / `tg_photo_url` | TEXT | из TG message |
| `authorized_at` | TIMESTAMPTZ | бот подтвердил |
| `consumed_at` | TIMESTAMPTZ | JWT выдан (`/v1/auth/bot-complete`) |
| `created_at` | TIMESTAMPTZ | |

---

## 3. Формула rank (v0)

**Внутри команды** — «match»; **наружу** — «совместимость» / «итоговый рейтинг».

```
keyword_match = f(lead_tags, user_tags)   → 0..100
final_rank    = round(ai_score * 0.6 + keyword_match * 0.4)
```

| Компонент | v0 |
|-----------|-----|
| `f(...)` | **F2:** совпавшие теги лида / `len(lead_tags)` × 100, cap 100 · «ИДЕАЛЬНО ✦» только при ≥2 тегах у лида и km=100 · user_tags max **12** |
| Веса 0.6 / 0.4 | в `settings` или env `RANK_WEIGHT_AI`, `RANK_WEIGHT_TAGS` |

**→ O82 (2026-06-01):** w1 UI breakdown (§4 ниже) · w2 **F2+** (weighted/synonyms/granular `ai_score`) · w3 embeddings — см. [`CODER_PROMPT.md`](CODER_PROMPT.md) § **O82** · **O46 не отменяется** до приёмки w2.

**Позже (w3):** эмбеддинги task_summary ↔ profile — отдельная задача.

---

## 4. Прозрачность в UI

Пользователю показывать:

```
Совместимость: 88%
  · Базовая оценка заказа: 92
  · Совпадение с вашими тегами: 82
  · Python, FastAPI — в тексте и профиле
```

---

## 5. Кто пишет / читает

| Актор | Доступ |
|-------|--------|
| **Рadar Python** | INSERT/UPDATE `leads` |
| **API (Python)** | SELECT + rank; CRUD `user_tags` по токену |
| **WordPress** | только HTTP → API (Bearer / HMAC) |
| **Бот** | через API: top-K per `user_id` + `tg_chat_id` |

WP на shared-хosting **без** `DATABASE_URL` к Neon.

---

_Coder: миграция + `pg_storage.py` — отдельный `CODER_PROMPT`._
