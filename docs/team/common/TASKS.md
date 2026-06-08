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
| **11** | **Wave 2 rerun** · sign-off · **ads** | **⏸** O132 deploy |
| **11a** | **O132-STABILITY** radar OOM | **код ✅** · **owner deploy** |

---

## L2 smoke (owner, после deploy)

1. Premium → лид **без** `reply_draft` → «Написать отклик» → tools + draft за ≤30s
2. Повторный клик → cache, без LLM
3. `/ops/` → radar active · env `TOOLS_BACKLOG_DRAIN=0` · models = `gemini-2.5-pro`

---

## ⏸ После ads

O113 · O123-w2 · O105-w2

---

_W1 ✅ · O131 deploy ✅ **2026-06-07** · owner: Wave 2 rerun **→** ads_
