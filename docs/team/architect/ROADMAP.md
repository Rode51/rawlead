# Дорожная карта

**Канон vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.10** · [`LEAD_PRODUCT_PROMPT.md`](../product/LEAD_PRODUCT_PROMPT.md) §0i

**Аудитория:** **Digital-специалисты** — 4 категории (не «все фрилансеры»).

**Ставка B:** `/lenta` + `/cabinet` + ИИ-агент; dogfood — TG-бот владельца.

---

## Сейчас (2026-05-26) — Vision v0.10

| # | Что | Кто |
|---|-----|-----|
| **V10.1** | FILTERS §0i в коде | `@coder` |
| **V10.2** | PROFILE пороги ai_score по категории | `@coder` |
| **V10.3** | Skills catalog — 4 группы в `/lenta/` | `@coder` |
| **V10.4** | Лендинг «Для кого» — 4 карточки | `@coder` |
| — | P3a приёмка W2 | владелец |
| — | P7 `leads.category` + API | после V10 |
| — | P5 деплой 24/7 | [`DEPLOY_BUDGET.md`](../../ops/DEPLOY_BUDGET.md) |
| — | 3f ИИ-агент | после V10 |

**⏸ отменено как приоритет:** ingest «все специальности», 25 источников сразу, § P1.3 без категорий.

---

## Фазы (сводка)

| Фаза | Статус | Суть |
|------|--------|------|
| **0** FL + Kwork + TG | ✅ | dogfood |
| **3b–3d** Neon + API + WP | ✅ | `/lenta`, `/cabinet` |
| **P3a** UX лента | ✅ | accordion, «Задача» |
| **V10** 4 категории Digital | **→** | FILTERS, PROFILE, skills, копирайт |
| **3f** ИИ-агент | → | |
| **3i** Агрегаторы | волнами | только релевантные категории |
| **3k** TG raw owner-only | → | |
| **3g–3h** Auth + биллинг | потом | |

Блокеры: [`STATUS.md`](../common/STATUS.md) · [`TASKS.md`](../common/TASKS.md) · Coder [`CODER_PROMPT.md`](CODER_PROMPT.md) § V10

---

_Lead Architect · 2026-05-26 · v0.10_
