# Дорожная карта

| Фаза | Статус | Суть |
|------|--------|------|
| **0** Биржи FL + Kwork | ✅ Готово | Код на ПК, бот, ИИ |
| **1** TG-чаты | 🔜 Почти | join ✅ · 3 acc ✅ · бот «Статус» ✅ · **тест acc2** |
| **1b** Пульт (десктоп) | **Сейчас** | Coder: [`team/CODER_PROMPT.md`](team/CODER_PROMPT.md) — одно окно Старт/Стоп |
| **2** ИИ «первое ЛС» | Потом | |
| **3** WordPress пульт | После 1b | [`team/TZ_WP.md`](team/TZ_WP.md), [`ops/WP_OWNER_STEPS.md`](ops/WP_OWNER_STEPS.md) |
| **3b** Сайт-сервис (учёба) | Параллельно | Local WP: [`ops/WP_LOCAL_SKELETON.md`](ops/WP_LOCAL_SKELETON.md), [`team/VISION_SAAS_SITE.md`](team/VISION_SAAS_SITE.md) |
| **4** Аналитика / SaaS | Потом | [`team/VISION_SAAS_SITE.md`](team/VISION_SAAS_SITE.md), `TZ.md` §10 |

Детали фаз 1–4: [`team/PRODUCT_VISION.md`](team/PRODUCT_VISION.md)

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

**Сейчас:** десктоп-пульт ([`team/CODER_PROMPT.md`](team/CODER_PROMPT.md)) → затем WP ([`team/TZ_WP.md`](team/TZ_WP.md)).
