# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.12** · [`ROADMAP.md`](../architect/ROADMAP.md)

**Очередь:** [`TASKS.md`](TASKS.md)

> Hot ≤80 строк · детали → [`archive/STATUS_ARCHIVE.md`](../archive/STATUS_ARCHIVE.md)

---

## Сейчас prod (2026-06-14 · triage)

| Слой | Факт |
|------|------|
| **Сервисы** | `rawlead-api` · `rawlead-bot-poll` · `rawlead-radar` — **active** |
| **Сайт** | `/lenta/` 200 · theme **1.18.95** (O215 deploy 2026-06-14) |
| **FL** | last Neon insert **00:30 MSK Jun 14** (~13h) · `parsed=30 fresh=0` = возможно мало заказов в вс |
| **Kwork** | O213 ✅ prod — `parsed=36 pages=3` (2026-06-14 14:12 MSK) |
| **TG** | monitor слушает · O212 ✅ prod — `skip_entity=N`, старт без `ids=[…]` |
| **Ops** | **O214 ✅** — cycle_age из лога (не 154м) · residential badge when FL on fallback |

---

## 🚧 O216-QUIZ-TIER-UX (src + WP · 2026-06-14 · code done, deploy pending)

**Files changed:**
- `wordpress/rawlead-kadence-child/assets/js/rawlead-quiz.js` — localStorage split (SESSION_KEY / COMPLETED_KEY), retake flow, clear-on-exit, completed-on-reopen
- `wordpress/rawlead-kadence-child/template-parts/rawlead/quiz.php` — кнопка «Пройти ещё раз» (id `rl-quiz-retake-completed`)
- `wordpress/rawlead-kadence-child/assets/js/rawlead-feed.js` — `renderMatchBlock`: anon/expired_trial/free → locked bar (ранее anon возвращал `""`)
- `wordpress/rawlead-kadence-child/assets/js/rawlead-cabinet.js` — «Пройти тест заново» в блоке навыков
- `src/quiz_adaptive.py` — `quiz_pool_allowlist.json` support (allowlist filter в `_query_card`)
- `tests/test_o197_quiz_adaptive.py` — +4 теста allowlist

**pytest:** 16/16 (test_o197) · 8/8 (test_o195) ✅

**t6 — price smoke (VPS, ждём owner):**
> VPS: `PAY_PREMIUM_RUB=10` в `.env.site` → restart `rawlead-api` → YooKassa checkout 10 ₽ → owner test → **revert 790**
> `config.py` уже env-driven — менять нечего. bump `RAWLEAD_CHILD_VERSION` если UI pricing touched.

**t5 — quiz pool (data, ждём owner):**
> Нужно заполнить `data/quiz_pool_allowlist.json` — SQL audit по `leads` (is_visible=true, ai_score≥60) per niche. Механизм загрузки в `quiz_adaptive.py` ✅; без файла — поведение прежнее.

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
D9  pytest 16/16 quiz ✅
```

**Deploy:** `deploy-wp-theme-vps.py` · API if needed (quiz_adaptive change) · price env VPS (owner)

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
