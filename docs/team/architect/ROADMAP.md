# Дорожная карта

**Канон vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.9** · активный план Product: [`LEAD_PRODUCT_PROMPT.md`](../product/LEAD_PRODUCT_PROMPT.md)

**Ставка B (2026-05-24):** открытая лента `/feed` + ЛК `/cabinet` (Neon) + ИИ-агент; dogfood через TG-бот владельца.

---

## Фазы (сводка)

| Фаза | Статус | Суть |
|------|--------|------|
| **0** FL + Kwork | ✅ | Парсеры, фильтр, ИИ, бот |
| **1** TG acc1/2/3 | ⏳ | join, relay acc→@FLPARSINGBOT, стабильность |
| **1b** Пульт Tauri | ✅ принято владельцем 2026-05-25 | [`../ops/DESKTOP_LAUNCH.md`](../ops/DESKTOP_LAUNCH.md) |
| **2** ИИ «первое ЛС» | Потом | после MVP |
| **3b** Neon SaaS-ready | ✅ 2026-05-25 | `users`, `user_tags`, `is_visible`, без `contour` |
| **3c** REST API | ✅ 2026-05-25 | `api_server.py` :18766 |
| **3d** WP `/feed` + `/cabinet` | **→ сейчас** | страницы из API |
| **3d** WP `/cabinet` | → | `user_id=1`, REST к Neon |
| **3e** Habr Career | → | парсер в `src/` |
| **3f** ИИ-агент | → | цена + отклик + push TG |
| **3g** TG Login + multi-user | После 3f | |
| **3h** Биллинг | После 1-го внешнего юзера | |

Детали фаз 3b–3h: `PRODUCT_VISION.md` §4.

---

## Сейчас (2026-05-24)

| Приоритет | Что | Кто |
|-----------|-----|-----|
| **0** | Docs + vision v0.9 синхронизированы | Lead Architect ✅ |
| **1** | TG стабилен: relay + карточка, без дублей python | `@mechanic` § I/K · `@coder` приёмка § M |
| **2** | **3b** Neon | ✅ |
| **3** | UX спека `/feed` + `/cabinet` | ✅ Lead Design · [`feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) |
| **4** | **3c** API + `/feed` | `@coder` → [`CODER_PROMPT.md`](CODER_PROMPT.md) |
| **4b** | CSS лендинг + пульт | `@designer` → [`DESIGNER_PROMPT.md`](../design/DESIGNER_PROMPT.md) |
| **5** | **3d** `/cabinet` через API | Coder + Design handoff |
| **6** | Dogfood: отклики по боту | владелец |

**Отменено под v0.9:** демо `/cabinet` на JSON/localStorage (старый Coder § B) · витрина `/uslugi` до MVP · поле `contour` в Neon.

Блокеры: [`STATUS.md`](../common/STATUS.md) · очередь: [`TASKS.md`](../common/TASKS.md)

---

## Фаза 1 — TG (dogfood)

| Шаг | Статус |
|-----|--------|
| 3 acc, join, listen | ✅ волна 3 |
| Relay acc → бот → карточка ИИ | ⏳ приёмка § M |
| `/start` acc → бот | ⏳ § F |
| Пульт v2 | ✅ |

ТЗ: [`TZ_TG.md`](TZ_TG.md) · аккаунты: [`../ops/TELEGRAM_ACCOUNTS.md`](../ops/TELEGRAM_ACCOUNTS.md)

---

_Lead Architect · 2026-05-24 · из vision v0.9_
