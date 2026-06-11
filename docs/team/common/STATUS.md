# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.12** ? [`ROADMAP.md`](../architect/ROADMAP.md)

**???????:** [`TASKS.md`](TASKS.md)

> Hot ?80 ????? ? ?????? ? [`archive/STATUS_ARCHIVE.md`](../archive/STATUS_ARCHIVE.md)

---

## ?????? prod (2026-06-09)

| ?????? | ???? |
|--------|------|
| **WP theme** | **1.18.56** O178 deploy **2026-06-11** |
| **OR L2 draft** | **acc2 US** `38.154.16.60` ? `OPENROUTER_HTTP_PROXY` ? L1 direct |
| **API O148** | warm endpoint ? deploy ? 2026-06-08 |
| **?? gate** | L2 send **71.8%** ? combined **4.28** ? L1 **83.1%** ? L3 **92%** |
| **VPS** | **2 GB RAM** ? swap 0 ? radar **0 OOM** post-O132 |
| **???** | @rawlead_bot ? O120 failover ? **O105 pay ?** |
| **???????** | `/ops/` ? O152 trace ? **O155 HC** ? O160 watchdog |
| **TG** | acc2 listen 6 ????? ? acc1 proxy **38.154** spare |
| **Feed env** | fl,kwork + **4? secondary** + **28? tg** (???. test_bots) |
| **Ingest** | per-source lock ? wall-clock FL/YouDo ? cycle watchdog ? `WatchdogSec=660` ? **O160** |

**Judge freeze:** [`preprod_ai_prod_audit_judge_o72e_a_freeze.md`](../../data/preprod_ai_prod_audit_judge_o72e_a_freeze.md)

---

## ??????? ??????? ?

| ? | ???? |
|---|------|
| **O133-TZ-BACKFILL** | `backfill_tz_attachments.py` ? idempotent ? pytest **8/8** ? 2026-06-09 |
| **O133-TZ-SMOKE** | FL `PHPSESSID`/id+pwd cookies ? deploy script ? pytest **57/57** ? 2026-06-09 |
| **DROP-FREELANCEHUNT** | parser out ? env/scripts clean ? `listing.py` label only ? 2026-06-09 |
| **O164-L2-PROMPT** | off-topic attachment ignore ? deploy VPS ? pytest **39/39** ? 2026-06-09 |
| **O162-L2-GROUNDING** | `_FILE_CLAIM_RE` +pdf-claim ? L2 last-attempt attach fail ? None ? `sanitize_tools_for_tz` drop tg off-TZ ? pytest **22/22** ? 2026-06-09 |
| **O163-TG-NOTIFY** | gate `feed_visible+public_feed` ? raw forward ????? ? `tg_spam_filter.py` (promo/CV) ? pytest **31/31** ? 2026-06-09 |
| **O160-RADAR-INGEST** | per-source lock ? FL/YouDo wall-clock ? `_CycleWatchdog` ? `WatchdogSec=660` ? **deploy ? 2026-06-09** |
| **O159-DRAFT-BURST** | OR sem ? queue UI ? **3/3 burst ?** ? theme **1.18.50** ? deploy ? 2026-06-08 |
| **O166-HOME-MATCH-BAR** | live-preview match fill ? `rawlead.css` width rule ? theme **1.18.51** ? **deploy ?** ? 2026-06-09 |
| **O158-MATCH-UX** | push dedup ? match bar ? ?lead= ? **1.18.49** ? deploy ? 2026-06-08 |
| **O155?O157** | HC pulse ? YouDo human ? traffic ? deploy ? 2026-06-08 |
| **O152-EXCHANGE-TRACE** | trace jsonl ? /ops/ ? deploy ? 2026-06-08 |
| **O153?O154** | card chips + grid neighbor ? **1.18.48** ? Lead smoke ? |
| **O121-w2b** | `/ops/` timeout 90s ? owner smoke ? 2026-06-08 |
| **O141-EXCHANGE-PARITY** | detail all web ? TG labels ? deploy ? 2026-06-08 |
| **O131-PERF** | pooler ? feed boot ? deploy 2026-06-07 |

---

## ?? soft ads ?

| ??? | ?????? |
|-----|--------|
| O131?O160 | ? deploy 2026-06-09 |
| **Wave 2 sign-off** | ? owner 2026-06-08 (draft ~30s ? O158 ok) |
| **O161-OPS-PRO** | ? deploy 2026-06-09 ? pytest 5/5 |
| **O133-TZ-DOWNLOADER** | ? deploy 2026-06-09 ? `tz_session.py` ? FL/Kwork creds ?? VPS |
| **O133-FILTER** | ? FL+Kwork legal ? pytest **50/50** ? deploy ? ? smoke Kwork PDF ? |
| **O133-KW-AUTH-HTML** | ? deploy ? cookies owner local ? |
| **O133-TZ-SMOKE** | **? smoke PASS** Neon #19944 ? kwork #3193806 ? body **8279** ? extracted PDF |
| **O133-TZ-BACKFILL** | ? VPS `--apply` ? Lead verify Neon **2026-06-09** |
| **DROP-FREELANCEHUNT** | ? ??? **2026-06-09** ? FH purge ? deploy script |
| **O164-L2-PROMPT** | ? deploy **2026-06-09** ? off-topic TZ ? L2 ? pytest **39/39** |
| **O169-SECONDARY-FEED** | ? deploy **2026-06-09** ? web=6+tg ? guard `_SECONDARY_WEB` ? pytest **2/2** |
| **O165-TG-TEST** | ? smoke ? join+feed+Neon |
| **O170-TG-L1-FILTER** | ??? ? pytest **31/31** ? pre-L1+L1 TG+post-guard ? **deploy VPS ?** ? delist #20170 ? |
| **O166-HOME-MATCH-BAR** | ? deploy **2026-06-09** ? `.rl-live-preview .rl-match__fill` ? theme **1.18.51** |
| **O167-SORT-SOURCE** | deploy **2026-06-09** buildSortOptionsHtml + sheet theme **1.18.52** |
| **O168-PRE-ADS-GATES** | ✅ load **1462ms** · L2 **80%** judge **2026-06-10** |
| **O174a-FOOTER** | ✅ FIO+ИНН footer · theme **1.18.53** · deploy **2026-06-10** |
| **O174b-YOOKASSA** | prep ⏸ · trial 1₽ · автопродление 790₽ · keys owner |
| **O175-FEED-INBOX** | ✅ API+WP **2026-06-11** · O175b `source` proxy · theme **1.18.55** |
| **O176-YOUDO-TRACE** | ✅ deploy **2026-06-11** · `youdo:trace` funnel · radar restart |
| **O177/O179 YouDo** | **✅ deploy 2026-06-11** · listing **50 cards @16:11** · L1 ingest · owner smoke |
| **O178-FEED-SOURCE-SORT** | ✅ deploy **2026-06-11** · source/sort API · banner · theme **1.18.56** |
| **O180-DELIST-WEB** | **✅ round 3** **2026-06-11** · #17048 `source_gone` · youdo gone markers + ephemeral browser delist · pytest **18/18** · radar `checked=80` · deploy VPS |
| **O181-DELIST-CLOSED** | **✅ smoke 2026-06-11** · YouDo «Закрыто для откликов» · #16797 `source_gone` · not in feed · `purge_delisted` dry-run **456** · pytest **19/19** · deploy VPS |
| **O182-DELIST-INPROGRESS** | **✅ smoke 2026-06-11** · YouDo «Выполняется»/SBR · #16149 `source_gone` · not in feed · pytest **21/21** · deploy VPS |
| **O182b-YOUDO-IMPORT** | **✅ hotfix 2026-06-11** · `fetch_youdo_detail_html` import · pytest **32/32** · deploy `deploy-o182b-vps.py` · post-deploy fetch **no NameError** · `health:youdo fail kind=browser` (listing antibot, not import) |
| **ads + portfolio** | **→ после smoke O174b** |

---

## Gaps / ???

| ???? | ?????? |
|------|--------|
| **O168 stress** | ✅ **2026-06-10** |
| **O174 pay** | O174a ✅ · O174b prep ⏸ · PM/Design параллельно |
| **O175 feed/inbox** | ✅ O175b WP `source` proxy **2026-06-11** |
| **O176 YouDo** | trace ✅ · O179 deploy ✅ · **listing OK 16:11** |
| **O178 feed UX** | ✅ source filter + sort API · banner · deploy **2026-06-11** |
| **YouDo ingest** | **⏳** US proxy **2026-06-11** · listing OK @20:10 · antibot/cooldown cycles · O182b import ✅ |
| **Delist / битые** | ✅ O182 **2026-06-11** · #16149 in-progress/SBR · O181 #16797 · O180 #17048 |
| **Ops/admin UX** | O171 rebuild `/ops/` + FLPARSING · **после O168** (owner 10.06) |
| **O133 TZ downloader** | ? deploy 2026-06-09 ? auth session on VPS |
| **HC fail URL** | `HEALTHCHECKS_SITE_FAIL_URL` ? ????????? ? `.env` ?? VPS |
| **O144?O145** | deploy ? 2026-06-08 ? `CODER_PROMPT_ARCHIVE` |

**????? ads:** O113-seo ? O123-w2 copy ? O105-w2 crypto

---

_O175b **2026-06-11**: WP REST `/feed` пробрасывает `source=tg,youdo` · theme **1.18.55** · deploy ✅_

_O176 **2026-06-11**: `youdo:trace` cycle_decision→fetch_start→browser→parse→fetch_end · `parse_empty` health kind · deploy VPS ✅_

_O178 **2026-06-11**: feed `source=fl,youdo|tg|fl,tg,youdo` 200 · match+source · sticky banner fix · theme **1.18.56** · deploy ✅_

_O179 **2026-06-11**: deploy `deploy-o179-vps.py` · VPS grep youdo_source_fetch_wall_sec=1 · traffic_guard=8 · goto_attempt=3 · radar restart · post-deploy fetch_allowed=0 (guard/cooldown) · ingest DoD → Lead_

_O181 **2026-06-11**: YouDo markers `закрыто/закрыт для откликов` · `purge_delisted` in `purge_old_leads.py` · #16797 `source_gone` · feed miss · dry-run purge **456** · pytest **19/19** · deploy `deploy-o181-delist-closed-vps.py`_

_O182 **2026-06-11**: YouDo `taskStatuses.isInProcess` + SBR `зарезервировано` + status-chip `>Выполняется<` (no bare body match) · #16149 `source_gone` · feed miss · pytest **21/21** · deploy `deploy-o182-delist-inprogress-vps.py`_

_O182b **2026-06-11**: `fetch_youdo_detail_html` import in `youdo_parser.py` · pytest **32/32** · deploy `deploy-o182b-vps.py` · cycle 697 post-deploy: no NameError · listing browser antibot (3 slots) → `health:youdo fail kind=browser`_

_O168 **2026-06-10**: g2 deploy — psycopg_pool + catalog/today_count TTL cache + warm · p95 **2013ms** (↓268ms) · ads ⏸_
