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
| **Feed env** | fl,kwork + **4× secondary** + **28× tg** (вкл. test_bots) |
| **Ingest** | per-source lock · wall-clock FL/YouDo · cycle watchdog · `WatchdogSec=660` ✅ **O160** |

**Judge freeze:** [`preprod_ai_prod_audit_judge_o72e_a_freeze.md`](../../data/preprod_ai_prod_audit_judge_o72e_a_freeze.md)

---

## Закрыто недавно ✅

| § | Суть |
|---|------|
| **O133-TZ-BACKFILL** | `backfill_tz_attachments.py` · idempotent · pytest **8/8** · 2026-06-09 |
| **O133-TZ-SMOKE** | FL `PHPSESSID`/id+pwd cookies · deploy script · pytest **57/57** · 2026-06-09 |
| **DROP-FREELANCEHUNT** | parser out · env/scripts clean · `listing.py` label only · 2026-06-09 |
| **O164-L2-PROMPT** | off-topic attachment ignore · deploy VPS · pytest **39/39** · 2026-06-09 |
| **O162-L2-GROUNDING** | `_FILE_CLAIM_RE` +pdf-claim · L2 last-attempt attach fail → None · `sanitize_tools_for_tz` drop tg off-TZ · pytest **22/22** · 2026-06-09 |
| **O163-TG-NOTIFY** | gate `feed_visible+public_feed` · raw forward убран · `tg_spam_filter.py` (promo/CV) · pytest **31/31** · 2026-06-09 |
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
| **O161-OPS-PRO** | ✅ deploy 2026-06-09 · pytest 5/5 |
| **O133-TZ-DOWNLOADER** | ✅ deploy 2026-06-09 · `tz_session.py` · FL/Kwork creds на VPS |
| **O133-FILTER** | ✅ FL+Kwork legal · pytest **50/50** · deploy ✅ · smoke Kwork PDF ⏸ |
| **O133-KW-AUTH-HTML** | ✅ deploy · cookies owner local ✅ |
| **O133-TZ-SMOKE** | **✅ smoke PASS** Neon #19944 · kwork #3193806 · body **8279** · extracted PDF |
| **O133-TZ-BACKFILL** | ✅ VPS `--apply` · Lead verify Neon **2026-06-09** |
| **DROP-FREELANCEHUNT** | ✅ код **2026-06-09** · FH purge в deploy script |
| **O164-L2-PROMPT** | ✅ deploy **2026-06-09** · off-topic TZ в L2 · pytest **39/39** |
| **O169-SECONDARY-FEED** | ✅ deploy **2026-06-09** · web=6+tg · guard `_SECONDARY_WEB` · pytest **2/2** |
| **O165-TG-TEST** | join **3/3** `5177575757` · peer `tg:-1005177575757` в feed ✅ · **owner post** → Neon smoke ⏸ |
| **O166 match bar** | ❌ не сдано — `.rl-live-preview .rl-match__fill` без `width` |
| **O167 sort source** | ❌ не сдано — `buildSortOptionsHtml` только date/match |
| **O168 pre-ads** | stress FAIL · L2 quality · perf p95 |
| **ads + portfolio** | **⏸ owner: рано** |

---

## Gaps / фон

| Тема | Статус |
|------|--------|
| **Perf** | p95 2549 ms @20 VU · backlog после ingest smoke |
| **YouDo banы** | 0/3 alive → owner `/ops/` **Сбросить баны** |
| **O133 TZ downloader** | ✅ deploy 2026-06-09 · auth session on VPS |
| **HC fail URL** | `HEALTHCHECKS_SITE_FAIL_URL` — настроить в `.env` на VPS |
| **O144–O145** | deploy ✅ 2026-06-08 · `CODER_PROMPT_ARCHIVE` |

**После ads:** O113-seo · O123-w2 copy · O105-w2 crypto

---

_Lead **2026-06-09** · O169 ✅ · O165 join+feed OK · owner: пост в Тест Ботов → Neon_
