# TASKS (активное)

Архив: [`archive/TASKS_HISTORY.md`](archive/TASKS_HISTORY.md)  
Vision: [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) v0.9 · план Product: [`LEAD_PRODUCT_PROMPT.md`](../product/LEAD_PRODUCT_PROMPT.md)

---

## Владелец

| # | Задача | Статус |
|---|--------|--------|
| 1 | Пульт ▶ стабильно, VPN выкл, `tg_smoke` ok | ⏳ |
| 2 | TG: acc → бот, /start авто | ✅ владелец 2026-05-25 |
| 3 | С **пн 2026-05-26:** отклики по вердикту «Брать», 1–2/день | ⏳ |

→ детали запуска: [`../FOR_YOU.md`](../FOR_YOU.md)

---

## Lead Architect

- [x] Принять vision v0.9 · `ROADMAP` · `LEAD_DESIGN_PROMPT` · ревизия docs 2026-05-24
- [x] Уборка docs: `PROJECT_MAP` § агентам, `ARCHITECTURE`/`TZ_API`/`SOURCES_POOLS`, архив SOURCES_SAAS, без дублей в корне `docs/`
- [x] Волна 2: приёмка Lead Design → очередь Product
- [ ] После копирайта Product — `CODER_PROMPT` § волна 2
- [ ] После **3b** — дочистить `NEON_SCHEMA.md` (полная схема users/tags)
- [ ] После MVP — `PORTFOLIO.md` под ставку B

---

## Волна 2 — лендинг UX + тексты (**→ @coder**)

**Порядок:** Design ✅ · Product ✅ · Architect ✅ · **Coder**

| Шаг | Кто | Статус |
|-----|-----|--------|
| 0–2 | Владелец · Lead Design · Lead Product | ✅ 2026-05-25 |
| 3 | **@lead-architect** → `CODER_PROMPT` § W2 | ✅ |
| 4 | **@coder** § W2 | ✅ Coder 2026-05-25 · приёмка владельцем ⏳ |
| 4b | **@coder** § 3h | ✅ |
| 4c | **@coder** § 3i | ✅ |
| 4d | **@coder** § 3j | ✅ Lead задеплоил тему 2026-05-25 |
| 5 | Ingest 25 источников (PDF) | 📋 [`docs/archive/INGEST_SOURCES_SNG_25.json`](../archive/INGEST_SOURCES_SNG_25.json) · очередь P1 сайты → Coder 3i |

### Бриф владельца (2026-05-25)

- **«Смотреть тарифы»** — не на `/pricing`, а **автоскролл** к блоку тарифов внизу главной (`#тариф` / `pricing-preview`).
- **Навигация:** возможно убрать пункт **«Главная»** (логотип RawLead → home).
- **Главная:** возможно явная кнопка **«Лента»** → `/lenta/` — решение Design.
- **§ 3h** (карточки ленты = как на главной, multi-навыки) — **после** волны 2 или параллельно после Design OK.

---

## Lead → Coder

**Промпт:** [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md) — **§ W2** (старт) · **§ 3h** после W2

| # | Трек | Статус |
|---|------|--------|
| … | § 3g | ✅ `54ba7d5` |
| … | **§ W2** лендинг | ✅ Coder · ⏳ владелец |
| … | **§ 3j** 2 колонки + wheel + пульт | **→ @coder** |
| … | 3f ИИ-агент | после W2+3h |

---

## Lead → Designer

**Промпт:** [`LEAD_DESIGN_PROMPT.md`](LEAD_DESIGN_PROMPT.md) → [`DESIGNER_PROMPT.md`](DESIGNER_PROMPT.md)

| # | Трек | Статус |
|---|------|--------|
| 1 | Концепция `/feed` + `/cabinet` | ✅ Lead Designer 2026-05-25 |
| 2 | Handoff лендинг + пульт | ✅ Designer → [`DESIGN_BRIEF.md`](design/DESIGN_BRIEF.md) §195 |
| 3 | § W в коде | ✅ Lead 2026-05-25 |
| 4 | **3d** `/lenta` + каркас `/cabinet` | ✅ |
| 5 | **3e** ЛК | ✅ принято владельцем 2026-05-25 |
| 6 | **§ 3g** лента | ✅ commit `54ba7d5` |
| 7 | Лента WP load | ✅ отбой |
| 8 | **Волна 2** UX | ✅ Lead Designer · `REFERENCE` §3 |
| 9 | **Волна 2** копирайт | ✅ Lead Product |
| 10 | **§ W2** в коде | ✅ |
| 11 | **§ 3h** в коде | ✅ |

---

## Отложено (после MVP)

- `/uslugi`, FL витрина, Habr-кейс, биллинг, multi-user, TG Login
- WooCommerce · VK/Avito ingest
- **3i** парсеры сайтов-агрегаторов · **3j** площадки напрямую · **3k** скрыть TG raw из `/lenta/` — `PRODUCT_VISION.md` §0h v2
