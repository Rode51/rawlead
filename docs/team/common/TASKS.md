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
- [ ] После **3b** — дочистить `NEON_SCHEMA.md` (полная схема users/tags)
- [ ] После MVP — `PORTFOLIO.md` под ставку B

---

## Lead → Coder (одна активная линия)

**Промпт:** [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md)

| # | Трек | Статус |
|---|------|--------|
| 0 | Mechanic: дубли python, radar_control+psutil | ⏳ тикеты § I/K |
| 1 | TG § M — только если сбой relay+card | по тикету |
| 1b | **§ P** пульт: логи / лампа TG / статус acc | ✅ принято владельцем 2026-05-25 |
| 2 | **3b** Neon SaaS-ready | ✅ Lead 2026-05-25 |
| 3 | **3c** REST API | ✅ Lead 2026-05-25 |
| 4 | **3d** WP `/feed` + `/cabinet` | внутри активного `CODER_PROMPT` (после § W) |
| 5 | 3e Habr Career | очередь |
| 6 | 3f ИИ-агент | очередь |

**Снято с очереди:** `contour` owner/saas · демо `/cabinet` JSON (§ B старый) · [`SOURCES_SAAS.md`](../archive/SOURCES_SAAS.md) → архив

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
| 6 | **§ 3g** лента: бот-only + навыки + sort | **→ @coder** · [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md) |
| 7 | 3f ИИ-агент (отклик, цена) | после 3g |

---

## Отложено (после MVP)

- `/uslugi`, FL витрина, Habr-кейс, биллинг, multi-user, TG Login
- WooCommerce · VK/Avito ingest
