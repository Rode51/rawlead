# Дорожная карта

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.12**

**Снимок:** [`STATUS.md`](../common/STATUS.md) · **очередь:** [`TASKS.md`](../common/TASKS.md) · **реклама:** [`PRE_LAUNCH_MARKETING.md`](../../ops/PRE_LAUNCH_MARKETING.md)

---

## Сейчас (2026-06-12)

**Стадия:** prod live · **YouDo+FL subprocess ✅** · **TG wave4** · **ads ⏸**

### ✅ Сделано (не возвращать в hot)

| Блок | § / факт |
|------|----------|
| **YouDo+FL ingest** | **O190+O191+O193** subprocess · stable cycles |
| **Pay + pre-launch** | O174 ЮKassa smoke · O185 w1–w3/t5b/t6 |
| **Feed + delist** | O175–O178 · O180–O182b |
| **Ingest + VPS** | O99 · O160 locks · VPS **4 GB** |
| **ИИ quality** | O72e gate · O164 L2 grounding |

### ⏳ До soft ads

| # | Что | Статус |
|---|-----|--------|
| 1 | **O188** TG join 127 channels | wave ⏳ |
| 2 | **O186** security audit | backlog |
| 3 | **ads + portfolio** | **последним** ⏸ |

### ⏸ После ads / фон

| # | Что |
|---|-----|
| **O113-seo** | органика |
| **O105-w2** | crypto auto-check |
| **O110** | FL 403 отдельный пул — по триггеру |
| **O92b** | pending_tags review |
| **O82-w3** | embeddings match |

---

## Фазы vision §4 (сжато)

| Фаза | Статус |
|------|--------|
| **0** · dogfood радар | ✅ |
| **E0–E5** · WP site + auth + cabinet | ✅ |
| **3f** · ИИ draft + L2/L3 | ✅ gate passed |
| **Launch** · pay + trial + E2E | **→ сейчас** |
| **GTM** · soft ads | после launch |
| **v1** · multi-user scale · billing polish | backlog |

**Отменено:** mobile app · отдельный маркет-сайт · Freelancehunt

---

## O72e gate (закрыт)

| Слой | Gate | Факт |
|------|------|------|
| L2 | send ≥70% | **71.8%** ✅ |
| L2 | combined ≥4.0 | **4.28** ✅ |
| L1 | usable ≥70% | **83.1%** ✅ |
| L3 | smoke | **92%** ✅ |

Детали: [`OWNER_INTENT.md`](OWNER_INTENT.md) · judge MD в `data/`

---

## Парсеры (O63)

| source | Статус |
|--------|--------|
| FL · Kwork · TG | ✅ prod |
| FR.ru · FreelanceJob · Пчёл | ✅ secondary VPS |
| YouDo | ⏳ chromium/proxy — не блокер launch |

---

Coder ТЗ: [`CODER_PROMPT.md`](CODER_PROMPT.md) · решения: [`OWNER_INTENT.md`](OWNER_INTENT.md)

---

_Lead Architect · 2026-06-05 · sync с STATUS/TASKS_
