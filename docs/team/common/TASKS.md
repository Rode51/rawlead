# TASKS (активное)

**Снимок:** [`STATUS.md`](STATUS.md) · **карта:** [`ROADMAP.md`](../architect/ROADMAP.md)

**Фаза:** **Launch path** · prod theme **1.18.34**

---

## Где мы

| ✅ | ⏳ до ads |
|----|----------|
| O121 ops · O126 · O127 · **O128** · **W1** · **O131** | **Wave 2 rerun** → ads |
| ИИ gate · VPS · O125 on-demand | **ads последним** |

---

## Шаги

| # | Что | Кто | Статус |
|---|-----|-----|--------|
| 1–8c | … · O121-w3-acc2 | — | ✅ |
| **9a** | **O126** category API + backfill | @coder | ✅ prod |
| **9b–9c** | **O127-D/WP** + theme deploy | @coder | ✅ **1.18.34** |
| **9d** | **O124-w2** BrowserSync tail | owner | ✅ минимально |
| **9e** | **O128 L2 voice B** | @coder | ✅ **36/36** · VPS |
| **10** | **Stress Wave 1** (PREPROD) | owner | ✅ **2026-06-07** |
| **10b** | **O129 stress v2** orchestrator + journey harness | @coder | ✅ pytest · journey partial |
| **10c** | **O131-PERF** | @coder + Lead deploy | ✅ **2026-06-07** |
| **11** | **Wave 2 rerun** · sign-off · **ads** | **⏸** после draft smoke |
| **11a** | **O132-STABILITY** radar OOM | **deploy ✅** |
| **11b** | **O134-INGEST-SLA** | **deploy ✅** |
| **11c** | **O135-DRAFT** отклик timeout | **deploy ✅** · owner OR proxy |

---

## L2 smoke (owner, после deploy)

1. Premium → лид **без** `reply_draft` → «Написать отклик» → cold L2 **≤ 90s** (1-й user L2-only)
2. Повторный клик / 2-й user → cache или L3 **≤ 20s**
3. `/ops/` → radar active · `openrouter:proxy=direct|host:port` в api log

---

## ⏸ После ads

O113 · O123-w2 · O105-w2

---

_W1 ✅ · O131 deploy ✅ **2026-06-07** · owner: Wave 2 rerun **→** ads_
