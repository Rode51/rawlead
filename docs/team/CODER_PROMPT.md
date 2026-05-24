# Coder — 3b Neon SaaS-ready (vision v0.9)

**Дата:** 2026-05-24 · Lead Architect  
**Vision:** [`PRODUCT_VISION.md`](PRODUCT_VISION.md) v0.9 · [`LEAD_PRODUCT_PROMPT.md`](LEAD_PRODUCT_PROMPT.md) acceptance #2  
**ROADMAP:** фаза **3b** → затем 3c–3f

---

## Перед стартом

1. [`docs/README.md`](../README.md) → [`PROJECT_MAP.md`](PROJECT_MAP.md) § «Зоны»
2. **Не начинать 3c–3f** в этом промпте — одна фаза за сдачу

### Блокеры (не 3b, если не закрыты)

| Что | Кто | Тикет |
|-----|-----|--------|
| Дубли `main.py` / radar_control | **Mechanic** | [`2026-05-24-duplicate-python-processes.md`](../problems/2026-05-24-duplicate-python-processes.md) |
| Приёмка relay + карточка ИИ | владелец + § M ниже | [`2026-05-24-tg-forward-not-via-bot.md`](../problems/2026-05-24-tg-forward-not-via-bot.md) |

§ **B** (демо `/cabinet` на JSON) — **отменён** v0.9; кабинет = фаза **3d** через REST.

---

## Цель 3b

Neon-схема **SaaS-ready с дня 1** (`PRODUCT_VISION` §0a, §0c):

| # | Готово когда |
|---|----------------|
| 3b1 | Таблицы: `users`, `user_tags`, `subscriptions` (минимум для MVP); лиды — `raw_leads` или эволюция `leads` с полями из [`NEON_SCHEMA.md`](NEON_SCHEMA.md) |
| 3b2 | Колонка **`is_visible`** (bool) после ИИ-модерации; **`contour` не добавлять** (модель отменена) |
| 3b3 | `user_id` во всех user-scoped таблицах; seed `users.id=1` для владельца |
| 3b4 | `content_hash` UNIQUE + ingest ON CONFLICT — согласовано с § O (допилить если не в схеме) |
| 3b5 | `sql/001_neon_schema.sql` + [`NEON_SCHEMA.md`](NEON_SCHEMA.md) синхронны |
| 3b6 | `pg_storage.py` / ingest: пишет `is_visible`, `ai_score`, `lead_tags` (заглушки ok, если ИИ-модерация в 3f) |

**Не в 3b:** REST `/v1/feed`, WP страницы, Habr парсер, ИИ-агент UI, биллинг, multi-user auth.

---

## § M — приёмка TG (если владелец ещё не закрыл)

| # | Готово когда |
|---|----------------|
| M1 | prompt-test → @FLPARSINGBOT: **пересыл + карточка**; лог `увед=1` |

**Файлы:** `src/tg_forward.py`, `src/lead_pipeline.py` — только если при приёмке найден баг.

---

## Файлы (можно трогать)

| Путь | Зачем |
|------|--------|
| `sql/001_neon_schema.sql` | 3b |
| `docs/team/NEON_SCHEMA.md` | 3b |
| `src/pg_storage.py` | ingest Neon |
| `src/lead_pipeline.py` | `is_visible` при записи |
| `src/listing_dedup.py` | hash |
| `docs/team/STATUS.md` | сдача |
| `src/tg_forward.py`, `src/telegram_control.py` | только § M |

## Файлы (не трогать)

- `wordpress/` (3c–3d)
- `TASKS.md`, `FOR_YOU.md`, `ROADMAP.md`, `PRODUCT_VISION.md`
- `scripts/radar_control.py` — Mechanic
- `git commit` / `push` — Lead Architect

---

## Как проверить

1. SQL в Neon Console — таблицы созданы, `users` id=1 есть  
2. Ingest тестового лида → строка с `is_visible`, без `contour`  
3. § M: один пост в prompt-test → карточка в боте  

---

_Lead Architect · 2026-05-24 · следующий промпт после сдачи: **3c REST + `/feed`**_
