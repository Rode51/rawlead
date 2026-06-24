# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.12** · [`ROADMAP.md`](../architect/ROADMAP.md)

**→ Now:** retention **2d** (owner 2026-06-24) · M1 ads watch · AI-IMAP dedup ✅

---

## AI token spend — fix ✅ (2026-06-24)

**Проблема:** IMAP ~90s re-L1 на invisible YouDo (`refresh_invisible` ×325 на один id).

**Fix:** `lead_imap_poll_skip` → `l1_done` · poller `skip_l1_done` · pipeline skip neon_replay если L1 есть.

**Smoke:** `skip_l1_done=4` · `refresh_invisible=0` · pytest 30 passed.

**Watch 24h:** OpenRouter DeepSeek ~$11/day → должен падать · [`2026-06-23-ai-token-spend.md`](../../problems/2026-06-23-ai-token-spend.md)

---

## YouDo IMAP-only — steady state

**model B:** last 30 + PG dedup · listing/browser **off** · timer `rawlead-youdo-imap` active.

**Watch:** oneshot ingest >2 мин → `systemctl kill rawlead-youdo-imap.service`

---

## M1 + YouDo — риск для посетителей

| Источник | Риск |
|----------|------|
| FL · Kwork · TG | ✅ низкий |
| YouDo | ⚠️ snippet — отклик менее точный |

Mitigation: snippet-режим · detail gate в backlog · [`2026-06-22-youdo-m1-day.md`](../problems/2026-06-22-youdo-m1-day.md)

---

## Недавно на prod

| Что | Когда |
|-----|-------|
| RETENTION-2D — лента/purge/site-stats 2 дня | 2026-06-24 |
| AI-IMAP dedup — skip l1_done invisible | 2026-06-24 |
| LENTA deep link race fix | 2026-06-23 |
| TG draft copy + buttons hotfix | 2026-06-23 |
| NEXT-UI anti-flicker + draft UX | 2026-06-23 |
| YOUDO-IMAP-ONLY deploy | 2026-06-23 |
| QUIZ-REDESIGN deploy | 2026-06-23 |
| FEED-FILTER-TG-STUCK-v2 | 2026-06-22 |
| PRE-ADS-GATE → M1 | 2026-06-21 |

Детали → [`PROD_FACTS.md`](PROD_FACTS.md) · артефакты → `data/preprod_*`

---

## Index (архив)

Закрытые волны YouDo · L1-TILDA · CABINET · G0–G10 → [`STATUS_ARCHIVE`](../archive/STATUS_ARCHIVE.md) · [`problems/`](../../problems/)
