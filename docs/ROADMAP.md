# Дорожная карта

| Фаза | Статус | Суть |
|------|--------|------|
| **0** Биржи FL + Kwork | ✅ Готово | Код на ПК, бот, ИИ |
| **1** TG-чаты | ✅ | 3 acc · join · пересылка + разбор · пульт v2 ✅ |
| **1b** Пульт (десктоп) | ✅ | v2 Tauri — [`DESKTOP_LAUNCH.md`](ops/DESKTOP_LAUNCH.md) |
| **2** ИИ «первое ЛС» | Потом | |
| **3** WordPress кабинет | После API | [`team/TZ_WP.md`](team/TZ_WP.md) |
| **3b** Сайт маркетинг | ✅ MVP | Kadence · [`design/wp/REFERENCE.md`](design/wp/REFERENCE.md) |
| **3c** Neon + API + rank | → | [`NEON_SCHEMA.md`](team/NEON_SCHEMA.md) · [`TZ_API.md`](team/TZ_API.md) |
| **4** Подписки + бот SaaS | → | digest per user |
| **5** Аналитика / SaaS | Потом | [`team/VISION_SAAS_SITE.md`](team/VISION_SAAS_SITE.md) |

Детали: [`team/PRODUCT_VISION.md`](team/PRODUCT_VISION.md) v0.4 — **сайт + подписки + бот**, без mobile app.

---

## Фаза 0 — что в коде

| Модуль | Что делает |
|--------|------------|
| `fl_parser.py` | FL, до 3 страниц |
| `kwork_parser.py` | Kwork |
| `main.py` | Цикл, фильтр, ИИ, TG |
| `filters.py` | ← [`ops/FILTERS.md`](ops/FILTERS.md) |
| `ai_analyze.py` | ← [`ops/PROFILE.md`](ops/PROFILE.md) |

Запуск: [`ops/RUN.md`](ops/RUN.md)

---

## Фаза 1 — только Telethon ($0)

Без платного софта и триалов. ТЗ: [`team/TZ_TG.md`](team/TZ_TG.md).

| Шаг | Кто |
|-----|-----|
| API_ID + invite-ссылки чатов | Ты |
| `tg_join`, мониторинг, Supabase | Coder |
| Приёмка | Ты в боте |

| Статус сессий: [`team/STATUS.md`](team/STATUS.md)

**Сейчас:** v1 docs (Neon/API/rank) · волна 3 join · [`PRODUCT_VISION.md`](team/PRODUCT_VISION.md) v0.4.
