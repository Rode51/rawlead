# Дорожная карта

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.12**

**Снимок:** [`STATUS.md`](../common/STATUS.md) · **очередь:** [`TASKS.md`](../common/TASKS.md) · **реклама:** [`PRE_LAUNCH_MARKETING.md`](../../ops/PRE_LAUNCH_MARKETING.md)

---

## Сейчас (2026-06-05)

**Стадия:** продукт **на prod**, идём к **soft ads**. ИИ-gate и основной UI **закрыты**.

### ✅ Сделано (не возвращать в hot)

| Блок | § / факт |
|------|----------|
| **Ingest + VPS** | O99 browser FL/Kwork · P5-E2 VPS 24/7 · TG 21 каналов |
| **Лента + ЛК** | O94–O97 · O95-fix · O116 · O123-w1 · **O107 trial** · theme **1.18.17** |
| **ИИ quality** | O72e gate **send 71.8%** · O114 vacancy · O72e-regen-tail |
| **Support** | O116-W4 FAB + TG tickets |
| **Надёжность** | O117 · O120 · **O121-w0/w0b/w0c** ops `/ops/` |
| **Match UX** | O82 w1–w2 · O89 uniquify · O101 slots (код) |
| **Оплата (код)** | O105-w1 `premium_pay.py` · Stars · pending approve |

### ⏳ До soft ads (новый порядок — владелец 2026-06-05)

```
…код закрыт → O121-spec → O121-w1/w2 (панель) → E2E → stress → ads+portfolio (последним)
```

| # | Что | Статус |
|---|-----|--------|
| 1–4 | O123 · O107 · O122 · O121-w0* | ✅ |
| 5 | **O121 панель** | **→ Design + Coder** |
| 6 | E2E · stress | после панели v1 |
| 7 | **ads + portfolio** | **последним** |

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
