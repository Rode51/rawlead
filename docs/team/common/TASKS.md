# TASKS (активное)

Архив: [`archive/TASKS_HISTORY.md`](archive/TASKS_HISTORY.md)  
Vision: [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) v0.9 · план Product: [`LEAD_PRODUCT_PROMPT.md`](../product/LEAD_PRODUCT_PROMPT.md)

---

## Владелец

| # | Задача | Статус |
|---|--------|--------|
| 1 | Пульт ▶ стабильно, VPN выкл, `tg_smoke` ok | ⏳ |
| 2 | Приёмка TG: пересыл + **карточка ИИ** в @FLPARSINGBOT | ⏳ [`2026-05-24-tg-forward-not-via-bot.md`](../problems/2026-05-24-tg-forward-not-via-bot.md) |
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
| 1 | TG § M — приёмка relay+card | ⏳ |
| 2 | **3b** Neon SaaS-ready | **→ сейчас** |
| 3 | 3c REST + `/feed` | очередь |
| 4 | 3d `/cabinet` REST | очередь |
| 5 | 3e Habr Career | очередь |
| 6 | 3f ИИ-агент | очередь |

**Снято с очереди:** `contour` owner/saas · демо `/cabinet` JSON (§ B старый) · [`SOURCES_SAAS.md`](../archive/SOURCES_SAAS.md) → архив

---

## Lead → Designer

**Промпт:** [`LEAD_DESIGN_PROMPT.md`](LEAD_DESIGN_PROMPT.md) → [`DESIGNER_PROMPT.md`](DESIGNER_PROMPT.md)

| # | Трек | Статус |
|---|------|--------|
| 1 | UX `/feed` + `/cabinet` (спека) | **→ сейчас** |

---

## Отложено (после MVP)

- `/uslugi`, FL витрина, Habr-кейс, биллинг, multi-user, TG Login
- WooCommerce · VK/Avito ingest
