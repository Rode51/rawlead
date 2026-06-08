# Дорожная карта

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.12**

**Снимок:** [`STATUS.md`](../common/STATUS.md) · **очередь:** [`TASKS.md`](../common/TASKS.md) · **реклама:** [`PRE_LAUNCH_MARKETING.md`](../../ops/PRE_LAUNCH_MARKETING.md)

---

## Сейчас (2026-06-08)

**Стадия:** продукт **на prod**, ingest/ops/draft **закрыты** · идём к **Wave 2 sign-off** → soft ads.

### ✅ Сделано (не возвращать в hot)

| Блок | § / факт |
|------|----------|
| **Ingest + VPS** | O99 · P5-E2 · TG 21 каналов · **O134 fresh-only** · **O138 parsed/fresh** |
| **Лента + ЛК** | O94–O97 · O116 · O123-w1 · O107 trial · **O137 feed sort** · theme **1.18.35** |
| **ИИ quality** | O72e gate · O114 · O128 L2 voice · **O135 draft L2-only** |
| **Support / ops** | O121 `/ops/` · O132 stability · O120 TG failover |
| **Оплата** | O105-w1 Stars · pending approve |

### ⏳ До soft ads

```
код Launch sprint ✅ → Wave 2 owner (journey + draft burst + stress) → ads последним
```

| # | Что | Статус |
|---|-----|--------|
| 1–7 | O131–O138 deploy | ✅ |
| 8 | **Wave 2 sign-off** | **→ owner** |
| 9 | **ads + portfolio** | **последним** |

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
