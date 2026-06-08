# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.12** · [`ROADMAP.md`](../architect/ROADMAP.md)

**Очередь:** [`TASKS.md`](TASKS.md)

> Hot ≤80 строк · детали → [`archive/STATUS_ARCHIVE.md`](../archive/STATUS_ARCHIVE.md)

---

## Снимок prod (2026-06-08)

| Контур | Факт |
|--------|------|
| **WP theme** | **1.18.49** · O158 deploy ✅ **2026-06-08** |
| **OR L2 draft** | **acc2 US** `38.154.16.60` · `OPENROUTER_HTTP_PROXY` · L1 direct |
| **API O148** | warm endpoint · deploy ✅ 2026-06-08 |
| **ИИ gate** | L2 send **71.8%** · combined **4.28** · L1 **83.1%** · L3 **92%** |
| **VPS** | **2 GB RAM** · swap 0 · radar **0 OOM** post-O132 |
| **Бот** | @rawlead_bot · O120 failover · **O105 pay ✅** |
| **Админка** | `/ops/` · O152 trace · **O155 HC** deploy ✅ |
| **TG** | acc2 listen 6 чатов · acc1 proxy **38.154** spare (45.152 мёртв) |
| **Feed env** | fl,kwork,youdo,freelance_ru,… + **21× tg** · TG visible **~6%** (L1) |

**Judge freeze:** [`preprod_ai_prod_audit_judge_o72e_a_freeze.md`](../../data/preprod_ai_prod_audit_judge_o72e_a_freeze.md)

---

## Закрыто недавно ✅

| § | Суть |
|---|------|
| **O131-PERF** | pooler · feed boot · deploy **2026-06-07** |
| **O132** | radar OOM · MemoryMax · browser cleanup |
| **O134** | fresh-only listing · ingest SLA в `/ops/` |
| **O135-DRAFT** | L2-only 1-й · draft restart · OR proxy env |
| **O136-TRACE** | draft stage logs · journal INFO |
| **O137-FEED** | Premium sort time/match · scan 500 · pagination |
| **O138-PARSER** | parsed/fresh · red при parsed=0 · `/ops/` listing line |
| **O139-FL-PINNED** | filter unseen · pinned FL не блокируют ingest |
| **O141-EXCHANGE-PARITY** | detail all web · TG labels · L2 guard | **deploy ✅ 2026-06-08** |
| **O145-FEED-CAT** | personal+category+time → scan 500 · pytest ✅ |
| **O146-DRAFT-CARD-UX** | flip lock · inflight · btn shimmer · **1.18.39** · 3 UX регресса → O147 |
| **O147-FEED-FLIP-MATCH** | syncMatchFill · trial hide · **1.18.44** (flip → O149) |
| **O148-DRAFT-OR** | deploy ✅ · smoke частично → **O150** |
| **O149-NO-FLIP** | **1.18.45** deploy ✅ · smoke частично → **O150** |
| **O150-DRAFT-UX-POLISH** | **1.18.46** deploy ✅ · owner smoke ⏸ |
| **O151-OR-ACC2-UX** | **1.18.47** deploy ✅ · owner smoke ⏸ |
| **O153-CARD-CHIPS** | syncCardChips · **1.18.48** · Lead smoke ✅ |
| **O154-GRID-NEIGHBOR** | grid start · **1.18.48** · Lead smoke ✅ |
| **O152-EXCHANGE-TRACE** | trace jsonl · /ops/ · deploy ✅ **2026-06-08** |
| **O155-O157** | HC pulse · YouDo human · traffic · deploy ✅ **2026-06-08** |
| **O158-MATCH-UX** | push dedup · match bar · ?lead= km · **1.18.49** · deploy ✅ **2026-06-08** |
| **O121-w2b** | `/ops/` timeout 90s · pytest **4/4** · deploy ⏸ Lead |

---

## До soft ads ⏳

**Порядок:** UI ✅ → L2 ✅ → **O141 parity** → Wave 2 → ads

| Шаг | Статус |
|-----|--------|
| O131–O141 | ✅ **deploy 2026-06-08** |
| **O144-RFP** | deploy ✅ **2026-06-08** |
| **O145-FEED-CAT** | deploy ✅ **2026-06-08** |
| **Wave 2 rerun** · sign-off | **✅ owner 2026-06-08** (draft ~30s · O158 ok) |
| **Perf gate** | load@20 p95 **2549 ms** vs <2s ⏸ |
| **O132 watch** | 24h 0 oom-kill ⏸ |
| **ads + portfolio** | **последним** |

---

## Gaps / фон

| Тема | Статус |
|------|--------|
| **O141 deploy** | `deploy-o141-exchange-parity-vps.py` · VPS youdo body>500 · push **YouDo** |
| **Perf** | p95 2549 ms · app pool backlog |
| **O133 TZ downloader** | backlog P1 · cookies session для вложений |
| **TG в ленте** | ingest 93 · visible 6 — **L1**, не PUBLIC_FEED_SOURCES |
| **O115** | tg judge pilot — не гоняли |
| **O105-w1-r3** | ⏸ по симптому Stars |
| **O155-O157** | **deploy ✅** · HC URL в `.env` · YouDo **0/3** → owner smoke **Сбросить баны** |

**После ads:** O113-seo · O123-w2 copy · O105-w2 crypto

---

## Архив · O141 сдача

O116 · O72e · O108 — [`STATUS_ARCHIVE.md`](../archive/STATUS_ARCHIVE.md)

**O141 Coder:** detail all web (`exchange_detail` + parsers) · Kwork always detail · legacy re-fetch · TG `SOURCE_LABELS` · secondary=1 · L2 bot-vague guard · `pytest tests/test_exchange_detail_parity.py`

**O144 Coder:** `_rfp_defer_instead_of_ideas` guard · RFP-блок в `build_shared_l2_system` · `tests/test_o144_rfp_draft.py` 10/10 · `deploy-o144-rfp-vps.py`

**O145 Coder:** `_personal_feed_page` sort=time+categories → `_feed_scan_limit` 500 · slice offset · `tests/test_personal_feed_time.py` 2/2 · `deploy-o145-feed-cat-vps.py`

**O146 Coder:** `onDraftReady`→`showDraftFlip` · `draft-done` · match #d4d4d4/#0a0a0a · trial hide premium · **1.18.39**

**O147 Coder:** `syncMatchFill`+IO · trial guard · flip (superseded O149) · **1.18.44**

**O148 Coder:** `POST …/draft/warm` · `tools_from_tz_text` hot path · `DRAFT_WARM_HOURLY_CAP` · btn >40s · poll 150s

**O149 Coder:** no flip DOM/CSS · inline expand + skeleton · btn shimmer kept · **1.18.45** · `deploy-wp-theme-vps.py` ⏸

**O150 Coder:** pending без skeleton · btn 20s · banner · preload · poll 180s · L2 direct · **1.18.46** · deploy ✅

**O151 Coder:** L2 via OR proxy if env · hideFeedBanner · no «ИИ пишет…» · **1.18.47** · deploy ✅

**O152 Lead deploy ✅ 2026-06-08:** `deploy-o152-exchange-trace-vps.py` · radar+api active · jsonl `/opt/rawlead/data/exchange_trace.jsonl` (freelancejob/pchyol traces ok)

**O153–O154 Lead smoke ✅ 2026-06-08:** prod `/lenta/` · expand/collapse chips + сосед стабилен

**O155–O157 Lead deploy ✅ 2026-06-08:** pytest **18/18** · `deploy-o155-o157-vps.py` · HC URL в VPS `.env` · radar active · YouDo **0/3 proxy** → owner **Сбросить баны** `/ops/`

**O158 Lead deploy ✅ 2026-06-08:** `deploy-o158-vps.py` · api+radar active · theme **1.18.49** · owner smoke ⏸

**O121-w2b Coder ✅ 2026-06-08:** `rawlead-api.php` `/ops/control` · clear-bans/restart **90s** · delist **120s** · pytest **4/4** · `deploy-o121-w2b-vps.py` · owner smoke `/ops/` ⏸

_Lead **2026-06-08** · O158 prod ✅_

_Lead **2026-06-08** · O152 deploy ✅ · owner `/ops/` smoke ⏸_
