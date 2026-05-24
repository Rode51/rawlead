# Neon Postgres — схема v1 (лиды + персональный rank)

Версия: **0.2 (черновик 3b)** · Lead Architect · 2026-05-24  
Решение владельца: **Neon** как облако; WP **не** ходит в Postgres напрямую.

> **v0.9:** поле **`contour`** (`owner`/`saas`) — **отменено**. Вместо него **`is_visible`** после ИИ-модерации — см. [`PRODUCT_VISION.md`](PRODUCT_VISION.md) §0c. Coder: [`CODER_PROMPT.md`](CODER_PROMPT.md) § 3b.

Черновик SQL для Coder: [`../../sql/001_neon_schema.sql`](../../sql/001_neon_schema.sql) — расширить по этому документу.

---

## 1. Принцип

| Когда | Что считаем |
|-------|-------------|
| **Ingest** (радар Python) | `ai_score`, `ai_verdict`, `lead_tags` — один раз на вакансию |
| **Read** (API → WP / бот) | `keyword_match` + **итоговый rank** — per user, на лету (v0) |

---

## 2. Таблицы

### `raw_leads` (или эволюция `leads`)

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
| `ai_reasons` | JSONB | 2–3 строки «почему score» (для UI) |
| `is_visible` | BOOLEAN | `true` — в `/feed` и match; `false` — только dogfood-бот владельца |
| `content_hash` | TEXT | SHA-256 нормализованного текста (`listing_dedup`); NULL — дедуп только по `source`+`external_id` |
| `notified_at` | TIMESTAMPTZ | legacy / owner |
| `created_at` | TIMESTAMPTZ | |

**UNIQUE** `(source, external_id)` · **UNIQUE** `(content_hash)` где hash не NULL · индекс `created_at DESC` · **GIN** на `lead_tags`.

Ingest: `INSERT … ON CONFLICT (content_hash) DO NOTHING` — при дубле текста не слать в TG (см. `pg_storage.record_new_lead`).

### `users`

| Колонка | Тип | Смысл |
|---------|-----|--------|
| `id` | UUID PK | |
| `wp_user_id` | BIGINT UNIQUE | связь с WP |
| `email` | TEXT | |
| `tg_chat_id` | BIGINT | для персональной рассылки бота |
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

---

## 3. Формула rank (v0)

**Внутри команды** — «match»; **наружу** — «совместимость» / «итоговый рейтинг».

```
keyword_match = f(lead_tags, user_tags)   → 0..100
final_rank    = round(ai_score * 0.6 + keyword_match * 0.4)
```

| Компонент | v0 |
|-----------|-----|
| `f(...)` | weighted overlap: сумма весов совпавших тегов / сумма весов user_tags × 100, cap 100 |
| Веса 0.6 / 0.4 | в `settings` или env `RANK_WEIGHT_AI`, `RANK_WEIGHT_TAGS` |

**Позже:** синонимы (`python` ↔ `питон`), эмбеддинги — отдельная задача.

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
| **Рadar Python** | INSERT/UPDATE `raw_leads` |
| **API (Python)** | SELECT + rank; CRUD `user_tags` по токену |
| **WordPress** | только HTTP → API (Bearer / HMAC) |
| **Бот** | через API: top-K per `user_id` + `tg_chat_id` |

WP на shared-хosting **без** `DATABASE_URL` к Neon.

---

_Coder: миграция + `pg_storage.py` — отдельный `CODER_PROMPT`._
