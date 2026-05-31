# Дорожная карта

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.11** · [`LEAD_PRODUCT_PROMPT.md`](../product/LEAD_PRODUCT_PROMPT.md) § MARKET-INTEL-B

**Снимок / очередь:** [`STATUS.md`](../common/STATUS.md) · [`TASKS.md`](../common/TASKS.md) · **реклама:** [`PRE_LAUNCH_MARKETING.md`](../../ops/PRE_LAUNCH_MARKETING.md)

---

## Сейчас (2026-05-30)

| # | Что | Кто | Статус |
|---|-----|-----|--------|
| **Owner draft** | 9/10 OK | владелец | **⚠️ условно** |
| **O72** | Аудит ИИ + промпт (draft + L1 + tools) | @coder | **→** |
| **O75** | Закрытые + >7d в ленте | @coder | **📋** |
| **O74** | TG ссылка на заказ | @coder | **📋** |
| **O63** | 4 парсера | @coder | **📋** |
| **O73** | Heatmap | владелец/coder | **📋** |
| **Реклама** | soft-launch | владелец | **⏸ после O72** |

**Порядок:** **O72** → O75 verify → soft ads → O63 + O74 parallel.

---

## O72 — AI draft quality audit

**Цель:** на реальных лидах из Neon понять качество **reply_draft** и **tools_required** (не только fixtures 12/12).

| Фаза | Суть |
|------|------|
| **1** | auto-metrics: validators + tools vs catalog + эвристики |
| **2** | LLM judge 20–30 samples (релевантность, tools match) |

**Accept:** ≥85% auto-pass · judge avg ≥3.5/5 · top fail cases для промпта.

Coder: [`CODER_PROMPT.md`](CODER_PROMPT.md) § **O72**

---

## O63 — новые парсеры (решение владельца 2026-05-30)

**Gate:** не блокирует pre-launch · parallel backlog.

| source_id | Биржа | URL (старт) | Приоритет |
|-----------|-------|-------------|-----------|
| `youdo` | YouDo | https://youdo.com/ | P1 |
| `freelance_ru` | Freelance.ru | https://freelance.ru/project/ | P1 |
| `freelancejob` | FreelanceJob | URL уточнить | P1 |
| `pchyol` | Пчёл.нет | URL уточнить | P1 |

**Dedup:** `content_hash` + усилить нормализацию · fuzzy — O63b.

**Coder:** [`CODER_PROMPT.md`](CODER_PROMPT.md) § **O63**

---

## Фазы (сводка vision §4)

| Фаза | Статус | Суть |
|------|--------|------|
| **0** Радар ПК | ✅ | FL, Kwork, TG, пульт, legacy/site |
| **0b** Биржи v2 | **📋 O63** | YouDo · Freelance.ru · … |
| **3b–3d** Neon + API + WP | ✅ | `/lenta/`, `/cabinet/` |
| **E0–E5** PRE-LAUNCH-UX | ✅ | фильтры, каталог, REVOLUTION UI |
| **3x** «Горячий» | ✅ | badge &lt; 5 мин |
| **P5 E2** VPS радары | **✅** | 24/7 Site + Legacy |
| **3f** ИИ-агент | **→** | draft + tools · **O72 метрики** |
| **3g–3h** Auth + биллинг | → | один тариф |
| **4** Аналитика поведения | **→ O73** | Metrika/Clarity |
| **5** Портфолио | потом | после метрик |

Coder ТЗ: [`CODER_PROMPT.md`](CODER_PROMPT.md) · решения: [`OWNER_INTENT.md`](OWNER_INTENT.md).

---

## Отменено / не приоритет

| Было | Решение |
|------|---------|
| Ставка A «только портфолио» | Plan B (2026-05-24) |
| Цена «от 300 ₽» | **590–990 ₽** (2026-05-28) |
| Freelancehunt | снят (O3) |
| 25 источников сразу | волнами после MVP |

---

_Lead Architect · O72/O73 pre-launch · 2026-05-30_
