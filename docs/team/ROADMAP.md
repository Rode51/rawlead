# Дорожная карта

| Фаза | Статус | Суть |
|------|--------|------|
| **0** Биржи FL + Kwork | ✅ | Код на ПК, бот, ИИ |
| **1** TG-чаты | ⏳ почти | 3 acc · join волна 3 · пересыл acc→@FLPARSINGBOT · **блокер § F** `/start` только кодом |
| **1b** Пульт (десктоп) | ✅ | v2 Tauri — ✕/■/логи — [`../ops/DESKTOP_LAUNCH.md`](../ops/DESKTOP_LAUNCH.md) |
| **2** ИИ «первое ЛС» | Потом | |
| **3** WordPress кабинет | ⏳ MVP | Демо `/cabinet` для портфолио **до** Neon API — [`CODER_PROMPT.md`](CODER_PROMPT.md) § B |
| **3b** Сайт маркетинг | ✅ | Kadence · [`../design/wp/REFERENCE.md`](../design/wp/REFERENCE.md) |
| **3c** Neon + API + rank | → | [`NEON_SCHEMA.md`](NEON_SCHEMA.md) · [`TZ_API.md`](TZ_API.md) |
| **4** Подписки + бот SaaS | → | digest per user |
| **5** Аналитика / SaaS | Потом | [`PRODUCT_VISION.md`](PRODUCT_VISION.md) |

Детали: [`PRODUCT_VISION.md`](PRODUCT_VISION.md) v0.4 — **сайт + подписки + бот**, без mobile app.

---

## Сейчас (2026-05-24)

| Приоритет | Что | Кто |
|-----------|-----|-----|
| **0** | **`.venv\Scripts\pythonw.exe` = launcher, не venv** — заменить в `start-radar-desktop.bat` на явный `Python311\pythonw.exe` + `PYTHONPATH` к venv packages · тикет: [`../problems/2026-05-24-radar-control-double-start-race.md`](../problems/2026-05-24-radar-control-double-start-race.md) | `@mechanic` |
| **1** | TG § F: `/start` acc→@FLPARSINGBOT через Telethon (нет телефонов acc) | `@coder` |
| **2** | WP `/cabinet` — демо ЛК для портфолио | `@coder` § B |
| **3** | Контур 1 стабилен: пульт ▶, join волна 3, отклики с пн | ты |
| **4** | Neon + API + rank | позже |

Блокеры и сдачи: [`STATUS.md`](STATUS.md) · очередь: [`TASKS.md`](TASKS.md)

---

## Фаза 0 — что в коде

| Модуль | Что делает |
|--------|------------|
| `fl_parser.py` | FL, до 3 страниц |
| `kwork_parser.py` | Kwork |
| `main.py` | Цикл, фильтр, ИИ, TG |
| `filters.py` | ← [`../ops/FILTERS.md`](../ops/FILTERS.md) |
| `ai_analyze.py` | ← [`../ops/PROFILE.md`](../ops/PROFILE.md) |

Запуск: [`../ops/RUN.md`](../ops/RUN.md)

---

## Фаза 1 — Telethon ($0)

Без платного софта. ТЗ: [`TZ_TG.md`](TZ_TG.md).

| Шаг | Статус |
|-----|--------|
| 3 acc, join очередь, listen | ✅ волна 3 идёт |
| Пересыл acc → бот → ты | ⏳ § F |
| Карточка: бюджет, #msg, ссылка | ✅ § E |
| Пульт v2 | ✅ |
| Приёмка TG end-to-end | после § F |

Сессии: [`../ops/TELEGRAM_ACCOUNTS.md`](../ops/TELEGRAM_ACCOUNTS.md) · карта: [`PROJECT_MAP_VISUAL.md`](PROJECT_MAP_VISUAL.md)

---

_Lead · обновлять при смене фаз/приоритетов · последнее: 2026-05-24_
