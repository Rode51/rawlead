# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.12** · [`ROADMAP.md`](../architect/ROADMAP.md)

**Очередь:** [`TASKS.md`](TASKS.md)

> Hot ≤80 строк · детали → [`archive/STATUS_ARCHIVE.md`](../archive/STATUS_ARCHIVE.md)

**Next:** @coder **O220-QUIZ-DEDUP** + **BAR-ALIGN**

---

## ✅ O220-MATCH-CODE — deploy (2026-06-14)

**Theme prod:** **1.19.02** · **API:** `lead_coverage_match` · `rawlead-api` **active**

| DoD | Result |
|-----|--------|
| pytest `test_match_push` | ✅ **21/21** (100/67/50/0% + synonym) |
| `node --check` | ✅ feed + cabinet |
| UI | bar only · no band copy · feed ≡ cabinet · «ОТКЛИК ✓» in LK |
| VPS verify | ✅ `1.19.02` · 0× «Не ваша ниша» in prod JS · feed **200** |

**Deploy:** Lead 2026-06-14 — `rank.py` + `api_server.py` rsync · theme rsync · restart API

**Ticket:** [`2026-06-14-match-ui-stray-quote.md`](../../problems/2026-06-14-match-ui-stray-quote.md) ✅

---

## ✅ O220-JS-SYNTAX-HOTFIX — feed + cabinet (2026-06-14)

**Fix:** trailing `'` в `renderMatchBreakdown` · feed **2011** · cabinet **4175**  
**Theme prod:** **1.19.01** · `node --check` ✅ · smoke `/lenta/` `ver=1.19.01` · JS line OK  
**Ticket:** [`2026-06-14-feed-cabinet-js-syntax.md`](../../problems/2026-06-14-feed-cabinet-js-syntax.md)

---

## ✅ O220 — deploy 2026-06-14 (partial match)

**Theme prod:** **1.19.01** · **API:** `priority_keyword_match` (**не** PM `lead_coverage_match`) · `rawlead-api` **active**

| Блок | На prod |
|------|---------|
| **Match** | bands A-min · syn F · B null lead · **D wrong formula** · UI `"` bug |
| **Feed UX** | quiz lock · 10/ч · max 5 draft · restore · layout ✅ |

**Lead deploy 2026-06-14:** theme rsync ✅ · API 7 files + restart ✅

**Next:** § **O220-L1-PROMPT-R2** ✅ code → Lead deploy `ai_analyze.py` → **O218** Playwright

---

## ✅ O220-L1-PROMPT-R2 — few-shot + thin-tag retry (2026-06-14)

**Файлы:** `src/ai_analyze.py` · `tests/test_ai_analyze.py` (NEW)

| DoD | Result |
|-----|--------|
| R1 | +4 few-shot (TG leadgen→marketing, MP cards→design, furniture tags, XMind→text) + anti-errors 5–7 |
| R2 | retry 1× when `feed_visible` + `<2` tags after sanitize (hint `need ≥2 canonical_tag`) |
| R3 | pytest **11/11** (`test_ai_analyze` + `test_l1_complexity_canon`) |

**Deploy:** `ai_analyze.py` → VPS ✅ 2026-06-14 (`rawlead-radar` + API restart) · owner optional re-pilot 6 thin ids

**Как проверить:**
```bash
pytest tests/test_ai_analyze.py tests/test_l1_complexity_canon.py -q
# optional: scripts/o220_l1_retag_pilot.py --lead-ids … (6 thin ids from pilot JSON)
```

---

## ✅ O220-L1-RETAG-PILOT — apply + judge (2026-06-14)

**Apply:** 14:32 UTC · **40 лидов** · `data/o220_l1_retag_pilot.json`  
**Judge:** 14:40 UTC · **`preprod_ai_prod_audit_judge.md`** — те же 40 id (`--lead-ids`)

| Метрика | Результат |
|---------|-----------|
| Теги avg | dev 1.2→**1.7** · design 1.4→**1.8** · mkt 1.5→**2.1** · text 1.1→**1.9** |
| ≥2 тега | **85%** (34/40) · gate avg **FAIL** (dev <2.5) |
| **L1 judge** | **l1_usable 80%** ✅ · category_ok **85%** · complexity **100%** ✅ |
| **L2 judge** (bonus) | send **75%** ✅ · balanced cats **FAIL** (design 65%) |

**Вывод:** промпт **жить можно** · точность L1 ок · **кол-во тегов** — подкрутить (dev + 6 thin) · категории/infographic — few-shot из judge § L1 fix

**Next:** @coder **O220-L1-PROMPT-R2** (few-shot) **или** сразу **O218** — на выбор владельца

---

## ✅ O219 — cabinet/quiz UX batch (deploy 2026-06-14)

**Theme:** **1.18.97** · API auto-trial on TG login · Lead deploy

**Lead verify 2026-06-14:** code ✅ · deploy ✅ · prod `ver=1.18.97` · API `active` · auto-trial fn on VPS

**Owner smoke:** Monica wipe → tier checklist `FOR_YOU.md` · **O220** feed bugs → `TASKS` **67–68**

---

## Сейчас prod (2026-06-14 · triage)

| Слой | Факт |
|------|------|
| **Сервисы** | `rawlead-api` · `rawlead-bot-poll` · `rawlead-radar` — **active** |
| **Сайт** | `/lenta/` 200 · theme **1.19.00** · O220 deploy ✅ |
| **FL** | last Neon insert **00:30 MSK Jun 14** (~13h) · `parsed=30 fresh=0` = возможно мало заказов в вс |
| **Kwork** | O213 ✅ prod — `parsed=36 pages=3` (2026-06-14 14:12 MSK) |
| **TG** | monitor слушает · O212 ✅ prod — `skip_entity=N`, старт без `ids=[…]` |
| **Ops** | **O214 ✅** — cycle_age из лога (не 154м) · residential badge when FL on fallback |

---

## 🚧 O217 — quiz JSON pack **✅ deploy 2026-06-14** (`deploy-o217-quiz-vps.py`)

**Deploy ✅ Lead 2026-06-14:** VPS `quiz_source=synthetic` · `quiz_cards_v1=56` · API active

**Files changed:**
- `data/quiz_cards_v1.json` — **NEW** 56 карточек (4 ниши × 14: 8 anchor + 2 boundary + 4 trap)
- `src/quiz_adaptive.py` — O217: `_load_json_cards()`, `_query_card_json()`, `_card_payload_json()`; `fetch_card_categories` ищет в JSON map сначала; `fetch_quiz_card` → JSON-first, Neon-fallback only if JSON missing
- `tests/test_o217_quiz_cards.py` — **NEW** 25 тестов: lint 56 карточек + JSON source integration
- `.gitignore` — `!data/quiz_cards_v1.json`
- `scripts/deploy-o217-quiz-vps.py` — **NEW** deploy script

**pytest:** 59/59 (test_o217 + test_o197 + test_o195) ✅

**DoD:**
```
quiz_source=synthetic  — /v1/quiz/start возвращает source=synthetic
56 cards             — quiz_cards_v1.json на VPS
owner smoke          — /lenta/ incognito: PM titles (не FL-мусор)
pytest green         — 59/59 quiz
```

**Deploy:** `python scripts/deploy-o217-quiz-vps.py`

---

## 🚧 O216 — code ✅ · O216b pool ✅ · **deploy ✅ 1.18.96** (2026-06-14)

**O216b ✅ Lead verify 2026-06-14:** `data/quiz_pool_allowlist.json` — **64 ids**; `scripts/quiz_pool_audit.py`; pytest **26/26**.

**Deploy ✅ 2026-06-14:** theme 1.18.96 live · allowlist 64 ids on VPS · quiz /start 200

**O217 deploy next:** `python scripts/deploy-o217-quiz-vps.py` (swap to JSON pack)

**Files changed (O216 + O216b):**
- `wordpress/rawlead-kadence-child/assets/js/rawlead-quiz.js` — localStorage split (SESSION_KEY / COMPLETED_KEY), retake flow, clear-on-exit, completed-on-reopen
- `wordpress/rawlead-kadence-child/template-parts/rawlead/quiz.php` — кнопка «Пройти ещё раз»
- `wordpress/rawlead-kadence-child/assets/js/rawlead-feed.js` — anon/expired_trial/free → locked bar
- `wordpress/rawlead-kadence-child/assets/js/rawlead-cabinet.js` — «Пройти тест заново»
- `wordpress/rawlead-kadence-child/functions.php` — `RAWLEAD_CHILD_VERSION` **1.18.96**
- `src/quiz_adaptive.py` — allowlist filter в `_query_card`
- `data/quiz_pool_allowlist.json` — **NEW** 64 curated ids (dev/design/marketing/text, 12+4 each)
- `scripts/quiz_pool_audit.py` — **NEW** one-off export script
- `tests/test_o197_quiz_adaptive.py` — +6 тестов allowlist (26/26 ✅)

**pytest:** 18/18 (test_o197) · 8/8 (test_o195) ✅

**t6 — price smoke (VPS, ждём owner):**
> VPS: `PAY_PREMIUM_RUB=10` в `.env.site` → restart `rawlead-api` → YooKassa checkout 10 ₽ → owner test → **revert 790**

**Как проверить (DoD):**
```
D1  incognito: exit mid-quiz → reopen → intro (empty history)
D2  anon complete → login → tags in Neon
D3  anon complete → reopen quiz → result modal + «Пройти ещё раз»
D4  retake done → profile updates; retake abandon → first profile kept
D5  anon /lenta/: locked compat bar visible; trial: real % bar
D6  trial feed: no delay · match sort · % visible
D7  cabinet: «Пройти тест заново» link visible
D8  YooKassa 10₽ checkout (owner, after VPS env change)
D9  pytest 26/26 quiz ✅
```

**Deploy:** `python scripts/deploy-o216-quiz-vps.py` (theme 1.18.96 + API + allowlist file)

**Корень Kwork/FL:** Kwork → **O213** pagination + filter (src ✅) · FL: воскресенье, мало постинга — мб норма.  
[`2026-06-14-kwork-fl-zero-new.md`](../../problems/2026-06-14-kwork-fl-zero-new.md)

---

## ✅ O213 Kwork coverage (src · 2026-06-14)

**Fix:** `kwork_parser.py` — pages 1–3 (`KWORK_MAX_PAGES`, default 3), dedup, log `pages=N` · `filters.py` — `EXCHANGE_SAFE_STOPS` bypass for kwork/fl only (TG unchanged)  
**pytest:** 38/38 (`test_kwork_parser` + `test_filters` + `test_o207b` + `test_o171` + O117 httpx fallback)  
**Deploy:** ✅ `deploy-o213-o212-vps.py` 2026-06-14 · VPS `parsed=36 fresh=0 pages=3`

**Как проверить (VPS):**
```bash
grep 'listing:kwork' data/radar_site.log | tail -3   # parsed>12 pages=2-3
grep skip_entity data/radar_site.log | tail -3         # summary, no ids=[…]
```

---

## Сейчас prod (baseline)

---

## ✅ O200 L2 — закрыто (owner 2026-06-13)

Pilot r5 + batch2: judge **85% / 95%** · cat playbooks deployed.  
**Решение:** regen/judge **пауза** до первых платных · точечно по id · full regen **нет**

---

## ✅ O209 match-first (WP · 2026-06-14)

**Theme:** `1.18.84` · deploy ✅ Lead 2026-06-14 · spec [`wave-o209-match-brief.md`](../../design/wp/wave-o209-match-brief.md)

| Зона | Сделано |
|------|---------|
| **P0 /quiz/** | intro → cards (exit anim, early-cta ≥5) → finale (category bars, TG, trial chip) |
| **P1 lenta** | anon strip 30 мин · quiz banner · expired banner · match label · slots только premium |
| **P1 cabinet** | copy · trial badge · expired banner · skills UI hidden |
| **P1 marketing** | hero/pricing/FAQ/how · tier table |

**Хвосты (косметика):** FAQ дубль «% совпадения» в `marketing.php` · `viewsHeadHtml` в refresh (не в initial render)

---

## ✅ O215 WP polish (theme · 2026-06-14)

**Theme:** **1.18.95** · deploy ✅ · owner accept BrowserSync session

| Check | Result |
|-------|--------|
| prod `ver=1.18.95` | ✅ |
| `/v1/quiz/start` | ✅ 200 |
| Monica reset (first-login) | ✅ free · 0 tags |

**Next:** tier smoke → Perf

---

## ✅ FL-PROXY-STABILITY (src · 2026-06-14)

DC tier · residential fallback · FL browser multi-slot · httpx max 1 ban · ops 🟡 при parsed≥25  
**Deploy:** api+radar ✅ · residential **25 slots** ✅ `patch-vps-fl-residential-env.py`

---

## ✅ O211 ops truth metrics (src · 2026-06-14)

Footer: `сегодня N · за 24ч M` (MSK) · parsed в tooltip · YouDo 🟡 при visible_24h>0  
**Verify:** pytest **15/15** · **deploy API** ✅ `deploy-o211-ops-footer-vps.py` 2026-06-14 (Lead verify VPS)

---

## ✅ O206 t2b sync chat_ids (src · 2026-06-14)

**Fix:** `tg_sync_chat_ids.py` + `config.py` — merge **all** `TG_JOIN_QUEUE*.csv` (v1+v2+v3), not single `TG_JOIN_QUEUE_CSV`.  
**VPS:** acc1 file **72** · startup peers **70** (2 `get_entity` skip: `1621850024`, `1031532699`) · audit **`ok: true`**  
**pytest:** 4/4 (`test_o206_tg_sync_chat_ids` + audit)  
**Deploy:** `deploy-o206-t2b-sync-vps.py` ✅

---

## ✅ O207 TG funnel proof (scripts · 2026-06-14)

**t1:** `tg_funnel_audit.py` — `days_7` / `days_30`, per-account, `data/tg_funnel_audit_human.md`  
**t2:** `tg_history_sample.py` — read-only Telethon, no Neon  
**t3:** `tg_filter_replay.py` — offline spam+filter replay, `owner_label` field  
**t4:** owner how-to → `docs/problems/2026-06-13-tg-feed-volume.md` § Owner labeling  
**pytest:** 7/7 (`test_o207_tg_funnel_audit` + `test_o207_tg_filter_replay`)  
**Deploy:** `deploy-o207-tg-funnel-vps.py` ✅ · **owner labels** ✅ 120/120 (canvas 2026-06-14) · replay on VPS

**Replay:** pass **91** · filter **22** · spam **7** · **8 vacancy** wrongly blocked → O207b

**Как проверить (VPS):**
```bash
cd /opt/rawlead && .venv/bin/python scripts/tg_funnel_audit.py --log data/radar_site.log
.venv/bin/python scripts/tg_history_sample.py --account acc1 --max-chats 3 --per-chat 5
.venv/bin/python scripts/tg_filter_replay.py --in data/tg_history_sample.json
```

**Filter rules:** не менялись (replay only).

---

## ✅ O207b TG filter tune (src · 2026-06-14)

**Fix:** `FILTER_WIDE` + FILTERS stop ловил skill-слова в реальных TG-вакансиях. Для `tg:*` + `is_tg_order_post` — soft bypass `TG_WIDE_SOFT_STOPS` (figma, монтаж, логотип, баннер, вебинар, va, иллюстратор); team-hiring «в команду» — bypass off. Расширены order markers (`задача:`, `откликнуться`, `ищем … дизайнера`).

| Метрика | before | after |
|---------|-------:|------:|
| `vacancy_blocked` | 8 | **0** |
| noise filter | 14 | 14 |
| noise pass | 69 | 69 |
| replay pass / filter / spam | 91/22/7 | **99/14/7** |

**pytest:** 49/49 (`test_o207b` + `test_o207` + `test_tg_spam_filter`)  
**Deploy:** ✅ `deploy-o207b-radar-vps.py` 2026-06-14 · VPS replay **99/14/7** · radar **active** (Lead verify VPS)

**Как проверить:**
```bash
python scripts/tg_filter_replay.py --in data/tg_history_sample_labeled.json --out data/tg_filter_replay.json
pytest tests/test_o207b_tg_filter_tune.py tests/test_o207_tg_filter_replay.py tests/test_tg_spam_filter.py -q
```

---

## ✅ O212 ops log truth (src · 2026-06-14)

**Fix:** TG startup log — `чатов/file/filter` без `ids=[…]` · skip → `skip_entity=N` · ops «сегодня N» из Neon · cycle `parsed/fresh` · TG 🔴 из `tg_pult_lamp_state` · log line prefer `handler_ok`  
**pytest:** 20/20 (`test_o212` + `test_o171`)  
**Deploy:** ✅ bundled in `deploy-o213-o212-vps.py` 2026-06-14 · radar+api **active**

**Как проверить (VPS):**
```bash
grep 'тг:монитор:старт' data/radar_site.log | tail -3   # no ids=[…]
grep skip_entity data/radar_site.log | tail -5
curl -s -b cookie.txt /ops/dashboard | jq '.exchanges[] | {source_id,today_new_ids,cycle_hint,exchange_level}'
# TG card 🟢 when handler_ok + pulse fresh even if Neon TG insert 0
pytest tests/test_o212_ops_log_truth.py tests/test_o171_ops_funnel.py -q
```

---

## ✅ O214 ops truth (src · 2026-06-14)

**Fix:** `ops_funnel.py` — cycle_age fallback из `── Цикл` в логе если SQLite >30м · FL `fl_tier=residential` + 🟡 при parsed≥25 · `exchange_proxy.py` — residential badge в proxy group · `owner_admin` + `ops-pult.js` — tier hint + clear-bans tooltip  
**pytest:** 4/4 (`test_o214`) + 20/20 regression  
**Deploy:** ✅ `deploy-o214-ops-truth-vps.py` 2026-06-14 · Lead verify VPS: `cycle_age_min=3` · `radar_lamp=ok` (was 154м)

**Как проверить (VPS):**
```bash
curl -s -b cookie.txt /ops/dashboard | jq '{cycle_age: .funnel.cycle_age_min, fl: .funnel.sources[]|select(.source_id=="fl")|{lamp,meta}}'
grep '── Цикл' data/radar_site.log | tail -1
# /ops/ FL card: «резидентский fallback: N/25 alive» · proxy group: residential note
pytest tests/test_o214_ops_truth.py -q
```

---

## 🔴 Next

| Волна | What | Who |
|-------|------|-----|
| **1** | ~~**O214** ops truth~~ · owner accept | ✅ 2026-06-14 |
| **2** | ~~**O215** WP design polish~~ · theme **1.18.95** deploy | ✅ owner accept 2026-06-14 |
| **2a** | **Tier smoke** (FOR_YOU) · T1 → **O216** fixes | owner + @coder · **→ сейчас** |
| **2b** | **Perf** lenta/home/quiz load | after tier smoke · @lead-designer → @coder |
| **3** | «Платформа для учебного центра» в ленте | monitor / owner spot-check |
| **4–6** | L2 70% · stress · ads | ROADMAP |

---

t3c deployed · ops/spam ok · O215 theme **1.18.95** deploy 2026-06-14
