# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.12** · [`ROADMAP.md`](../architect/ROADMAP.md)

**Очередь:** [`TASKS.md`](TASKS.md)

> Hot ≤80 строк · детали → [`archive/STATUS_ARCHIVE.md`](../archive/STATUS_ARCHIVE.md)

---

## Снимок prod (2026-06-09)

| Контур | Факт |
|--------|------|
| **WP theme** | **1.18.50** · O159 deploy ✅ **2026-06-08** |
| **OR L2 draft** | **acc2 US** `38.154.16.60` · `OPENROUTER_HTTP_PROXY` · L1 direct |
| **API O148** | warm endpoint · deploy ✅ 2026-06-08 |
| **ИИ gate** | L2 send **71.8%** · combined **4.28** · L1 **83.1%** · L3 **92%** |
| **VPS** | **2 GB RAM** · swap 0 · radar **0 OOM** post-O132 |
| **Бот** | @rawlead_bot · O120 failover · **O105 pay ✅** |
| **Админка** | `/ops/` · O152 trace · **O155 HC** · O160 watchdog |
| **TG** | acc2 listen 6 чатов · acc1 proxy **38.154** spare |
| **Feed env** | fl,kwork,youdo,freelance_ru,… + **21× tg** |
| **Ingest** | per-source lock · wall-clock FL/YouDo · cycle watchdog · `WatchdogSec=660` ✅ **O160** |

**Judge freeze:** [`preprod_ai_prod_audit_judge_o72e_a_freeze.md`](../../data/preprod_ai_prod_audit_judge_o72e_a_freeze.md)

---

## Закрыто недавно ✅

| § | Суть |
|---|------|
| **O160-RADAR-INGEST** | per-source lock · FL/YouDo wall-clock · `_CycleWatchdog` · `WatchdogSec=660` · **deploy ✅ 2026-06-09** |
| **O159-DRAFT-BURST** | OR sem · queue UI · **3/3 burst ✅** · theme **1.18.50** · deploy ✅ 2026-06-08 |
| **O158-MATCH-UX** | push dedup · match bar · ?lead= · **1.18.49** · deploy ✅ 2026-06-08 |
| **O155–O157** | HC pulse · YouDo human · traffic · deploy ✅ 2026-06-08 |
| **O152-EXCHANGE-TRACE** | trace jsonl · /ops/ · deploy ✅ 2026-06-08 |
| **O153–O154** | card chips + grid neighbor · **1.18.48** · Lead smoke ✅ |
| **O121-w2b** | `/ops/` timeout 90s · owner smoke ✅ 2026-06-08 |
| **O141-EXCHANGE-PARITY** | detail all web · TG labels · deploy ✅ 2026-06-08 |
| **O131-PERF** | pooler · feed boot · deploy 2026-06-07 |

---

## До soft ads ⏳

| Шаг | Статус |
|-----|--------|
| O131–O160 | ✅ deploy 2026-06-09 |
| **Wave 2 sign-off** | ✅ owner 2026-06-08 (draft ~30s · O158 ok) |
| **Ingest 24h smoke** | ⏸ owner · `── Цикл ──` без gap >15 min |
| **Perf gate** | load@50 p95 <2s ⏸ (сейчас 2549 ms @20 VU) |
| **ads + portfolio** | **последним** |

---

## Gaps / фон

| Тема | Статус |
|------|--------|
| **Perf** | p95 2549 ms @20 VU · backlog после ingest smoke |
| **YouDo banы** | 0/3 alive → owner `/ops/` **Сбросить баны** |
| **O133 TZ downloader** | backlog P1 · cookies session |
| **HC fail URL** | `HEALTHCHECKS_SITE_FAIL_URL` — настроить в `.env` на VPS |
| **O144–O145** | deploy ✅ 2026-06-08 · `CODER_PROMPT_ARCHIVE` |

**После ads:** O113-seo · O123-w2 copy · O105-w2 crypto

---

_Lead **2026-06-09** · O160 deploy ✅ · docs sync ✅_
