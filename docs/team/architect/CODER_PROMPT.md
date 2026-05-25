# Coder — ✅ § 3g сдано (приёмка владельца)

**Дата:** 2026-05-25 · Lead Architect  
**Следующий:** **3f** (ИИ-отклик в кабинете) — после OK владельца

**Не в scope:** JWT, оплата, кнопка «Сгенерировать отклик» (3f), Habr.

---

## Цель (простыми словами)

1. **`/lenta/`** показывает **только заказы, которые уже пришли в TG-бот** — не весь Neon.
2. **Навыки** — не ввод руками: каталог из реальных заказов; пользователь **выбирает чипы** → «совместимость» = пересечение с `lead_tags` лида.
3. **Сортировка:** по времени **или** по совместимости (`final_rank`).

Кабинет `/cabinet/` — тот же пул «из бота» + те же теги (единый `user_tags`), логика rank уже есть.

---

## Перед стартом

| # | Файл |
|---|------|
| 1 | [`NEON_SCHEMA.md`](NEON_SCHEMA.md) §3 — `notified_at`, `lead_tags` |
| 2 | [`TZ_API.md`](TZ_API.md) — допишешь §3g |
| 3 | [`feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) §2.2 — сортировка |
| 4 | `src/pg_storage.py` — `update_on_notify` / `record_new_lead` |

---

## § 3g1 — Пайплайн Neon (только «как в боте»)

| # | Готово когда |
|---|----------------|
| g1 | `record_new_lead`: **`is_visible = false`** при INSERT (лид в БД есть, в ленту не попадает) |
| g2 | `update_on_notify`: после отправки в TG — `notified_at = now()`, `is_visible` по вердикту (как сейчас), **`lead_tags`** заполнены (см. g3) |
| g3 | ИИ возвращает **`lead_tags`**: массив 3–8 навыков lowercase (`python`, `wordpress`, `telegram bot`, …) — поле в JSON ответа + `AiAnalysis` + запись в Neon |
| g4 | `GET /v1/feed` и `GET /v1/me/feed`: **`WHERE notified_at IS NOT NULL`** (и `is_visible = true`) |
| g5 | Разовая чистка: SQL в комментарии в `RUN.md` или скрипт: `UPDATE leads SET is_visible=false WHERE notified_at IS NULL` |

**Критерий владельца:** в `/lenta/` нет заказов, которых не было в боте.

---

## § 3g2 — API: каталог навыков + фильтр + сортировка

| # | Endpoint / параметр | Поведение |
|---|---------------------|-----------|
| g6 | `GET /v1/skills/catalog` | Топ N (50) тегов из `lead_tags` лидов с `notified_at IS NOT NULL`, сортировка по частоте; ответ `{"skills":[{"tag":"python","count":12},…]}` |
| g7 | `GET /v1/feed?skills=python,fastapi` | Только лиды, у которых `lead_tags` ∩ skills ≠ ∅; в ответе **`keyword_match`** + **`final_rank`** (формула NEON §3, веса env) |
| g8 | `GET /v1/feed?sort=time` | `ORDER BY created_at DESC` (default) |
| g9 | `GET /v1/feed?sort=match` | `ORDER BY final_rank DESC` (при пустых skills — match=0, ≈ ai_score×0.6) |
| g10 | `GET /v1/me/feed` | те же `skills`, `sort`; rank по `user_tags` из БД (как сейчас) |

`min_score` на `/v1/feed` при `sort=match` — по **`final_rank`**, при `sort=time` — по **`ai_score`** (зафиксировать в `TZ_API.md`).

---

## § 3g3 — WordPress `/lenta/`

| # | Готово когда |
|---|----------------|
| w1 | Sidebar: блок **«Навыки»** — чипы из `GET /v1/skills/catalog` (не text input) |
| w2 | Выбор навыков → `PUT /v1/me/tags` (owner UUID через REST-прокси, как кабинет) **или** query `skills=` в feed — **один источник правды: `user_tags`** |
| w3 | Сортировка: radio **«Новые»** / **«По совместимости»** → `sort=time` / `sort=match` |
| w4 | Подпись полоски: **«Совместимость»** + % = `final_rank` (если навыки выбраны) |
| w5 | Пустой каталог навыков — текст «Пока нет навыков в ленте — дождитесь заказов из бота» |
| w6 | `/cabinet/` — без регрессии; теги в шапке и в ленте **синхронны** (`user_tags`) |

**Файлы:** `rawlead-feed.js`, `page-lenta.php`, `inc/rawlead-api.php`, `rawlead.css` при необходимости.

---

## § 3g4 — ИИ-промпт

| # | Действие |
|---|----------|
| p1 | `docs/team/architect/AI.md` + парсер `ai_analyze.py`: поле `lead_tags` в JSON-схеме |
| p2 | Примеры тегов: `python`, `fastapi`, `wordpress`, `парсер`, `telegram bot`, `excel` — **без** `#`, lowercase |

---

## Как проверить (владелец)

1. Радар + бот: дождаться 1–2 карточек в TG.
2. `uvicorn` :18766 → `/lenta/`: **только** эти заказы (не старый мусор).
3. Блок «Навыки» — список из каталога; выбрал `python` → лента сузилась, % совместимости меняется.
4. Сортировка «Новые» / «По совместимости» — порядок карточек меняется.
5. `/cabinet/` — те же теги, что выбрал на ленте.

---

## Файлы (можно трогать)

| Путь |
|------|
| `src/pg_storage.py`, `src/ai_analyze.py`, `src/api_server.py`, `src/rank.py` |
| `wordpress/rawlead-kadence-child/` |
| `docs/team/architect/TZ_API.md`, `docs/team/architect/AI.md` |
| `docs/ops/RUN.md` |
| `docs/team/common/STATUS.md` |

## Не трогать

- `docs/ops/FILTERS.md` (расширение стоп-списка — отдельно, если понадобится)
- `git push` без владельца

---

## Закрыто

§ P · § 3b · § 3c · § W · § 3d · § 3e · **§ 3g**

---

_Lead Architect · 2026-05-25 · владелец: только бот в ленте + навыки из каталога + sort_
