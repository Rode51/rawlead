# Coder — hot queue (active)

**→ Now:** § **O216-QUIZ-TIER-UX** — quiz lifecycle · match bar tiers · trial feed · smoke price 10 ₽

---

## § O216-QUIZ-TIER-UX — Quiz lifecycle + tier match bars + trial feed (owner 2026-06-14)

**Context:** Owner tier smoke stopped at **T1 (Trial)**. Batch of UX fixes from BrowserSync session + product rules below.

**Lead verify (read-only, root cause anon quiz):**
- Quiz progress is **`localStorage` key `rawlead_quiz_session`** — **per browser**, **not IP**, **not server-side shared state**.
- `beginQuizPlay()` calls `readSession()` → **resumes partial `history`** → can finish with 1 niche bar only (confidence filter in `renderCategoryBars` shows max 3 niches with `pct>0`).
- **Not** «one quiz for all users» — but **same browser** shares session (acceptable); must **not resume incomplete** on re-entry (see t2).

### Owner requirements

| # | Requirement |
|---|-------------|
| r1 | **Quiz cards:** curated **universal** pool from **Neon `leads`** — plain-language titles/tasks any freelancer understands; **exclude** niche jargon from *other* fields (medicine, law, obscure tech) **and** confusing dev-only terms. **Not** a denylist-only hack — **audit DB → pick best exemplars per niche** (dev/design/marketing/text), ship as allowlist / `quiz_pool` table. |
| r2 | **Cabinet:** all logged-in users can **retake quiz** (entry in LK). |
| r3 | **Feed match bar:** **anon** sees **locked** compat bar (like current `rl-match--free-locked`); **trial** gets **real % bar** like premium — **remove** lock from trial. |
| r4 | **Trial feed:** same experience as **premium** — personal sort + **keyword_match %** on cards (API + JS). |
| r5 | **Quiz exit:** if user **leaves before finish** → next open **starts from intro** (clear in-progress session). **No** resume mid-quiz. |
| r6 | **Quiz complete (anon):** persist **completed profile** locally; on TG login → import to Neon (existing `importQuizTags`). |
| r7 | **Quiz re-open after complete:** show **result modal** (screenshot: «Готово. Вот что мы узнали») — **not** restart cards silently. Add link/button **«Пройти ещё раз»** → starts fresh run. |
| r8 | **Retake rules:** if retake **finished** → **replace** profile (Neon tags + local completed snapshot). If retake **abandoned** → keep **first completed** profile. |
| r9 | **Smoke price:** temporarily **`PAY_PREMIUM_RUB=10`** on VPS + checkout amount; UI price display should match API (use existing pattern / script `scripts/_tmp_o185_t1b_smoke_price.py` if still valid). **Revert to 790** after owner payment smoke — document in STATUS. |

### Files (expected)

```
wordpress/rawlead-kadence-child/assets/js/rawlead-quiz.js
wordpress/rawlead-kadence-child/assets/js/rawlead-feed.js
wordpress/rawlead-kadence-child/assets/js/rawlead-cabinet.js
wordpress/rawlead-kadence-child/template-parts/rawlead/quiz.php
wordpress/rawlead-kadence-child/assets/css/rawlead.css
src/quiz_adaptive.py                    ← card pool / jargon filter if needed
src/api_server.py                       ← trial feed parity (delay/sort/match) if gap
src/config.py                           ← pay_premium_rub already env-driven
wordpress/.../pricing-card.php        ← price from API/config, not hardcoded 790 during smoke
scripts/_tmp_o185_t1b_smoke_price.py    ← reuse for VPS 10 ₽ if applicable
tests/test_o195_quiz.py tests/test_o197_quiz_adaptive.py  ← extend
```

### Implementation notes

**t1 — localStorage model (quiz.js)**
- Split keys e.g. `rawlead_quiz_session` (in-progress, cleared on exit/close overlay without done) vs `rawlead_quiz_completed_v1` (canonical completed profile + category bars snapshot + `completed_at`).
- On overlay/page **close** without `done` → `clearSession()` only (drop in-progress).
- On `showResult` / API `done` → write **completed** snapshot; clear in-progress.
- On quiz open: if **completed** exists → show **result screen** immediately (+ «Пройти ещё раз»).
- Retake: set flag `retake_pending`; on new **done** → overwrite completed + `importQuizTags` if logged in; on abandon retake → restore completed from backup taken at retake start.

**t2 — Feed match bar (rawlead-feed.js `renderMatchBlock`)**
- **anon:** render `renderFreeLockedMatchBar()` (currently anon returns `""` — **change**).
- **trial** (`subscriptionState.is_trial` or `status==='trial'` with `effective_access`): treat as **premium** for match bar — `renderCompatMatchBar`, no lock.
- **free logged-in** (no trial access): keep lock OR clarify with owner — default: lock only **anon + expired_trial**; trial ≠ lock.

**t3 — Trial feed parity**
- Verify `/v1/feed` for trial JWT: `apply_delay=false`, match sort available, `keyword_match` populated when user has quiz tags.
- If trial lacks tags until import — use quiz completed local tags for anon→login path; logged-in trial must show % after profile import.

**t4 — Cabinet retake**
- Button/link «Пройти тест заново» / «Настроить ленту» → opens quiz overlay (`rawleadQuizApp.open`) with retake flow (r8).

**t5 — Universal quiz pool (Neon audit → curated set)**
- **Step A (data):** SQL/script over `leads` (`is_visible=true`, `ai_score>=60`, has `task_summary` or readable `title`): score **universality** — short title, everyday wording, category in QUIZ_NICHES, no cross-domain jargon (owner examples: medical/legal terms, hyper-specific stack when task is generic).
- **Step B:** Pick **N cards per niche** (e.g. 8–12 each) + backup alternates; store IDs in repo `data/quiz_pool_allowlist.json` (or SQL seed) — **single source** for `fetch_quiz_card` / `_query_card`.
- **Step C:** Adaptive logic unchanged (phase1/2) but **only** pulls from allowlisted ids (+ fallback query only if pool exhausted — log warning).
- Owner can spot-check list before deploy; optional export CSV for review.
- Do **not** change 4 result category labels without Design OK.

**t6 — Price 10 ₽ smoke**
- VPS: `PAY_PREMIUM_RUB=10` in `.env.site` · restart `rawlead-api`.
- WP checkout uses API amount · bump `RAWLEAD_CHILD_VERSION` if pricing UI touched.
- Owner note in STATUS: «revert 790 after smoke».

### Do not break

- O215 visual polish (NEO tokens) · quiz overlay on `/lenta/` · TG auth import · expired-trial mandatory banner · Monica/trial auto-start on first login.
- Do **not** remove completed profile on anon exit after **successful** finish.
- Do **not** store quiz state server-side keyed by IP.

### DoD

| # | Check |
|---|--------|
| D1 | Incognito anon: exit quiz mid-way → reopen → **intro**, empty history |
| D2 | Anon complete quiz → result modal → login → tags in Neon |
| D3 | Anon complete → open quiz again → **result modal** + «Пройти ещё раз» |
| D4 | Retake complete → profile updates; retake abandon → first profile kept |
| D5 | Anon `/lenta/` cards show **locked** compat bar; trial shows **real %** |
| D6 | Trial feed: no 30m delay · match sort · % visible (T1 smoke) |
| D7 | Cabinet: retake entry for logged-in user |
| D8 | YooKassa checkout **10 ₽** on prod (owner test) · revert documented |
| D9 | pytest quiz + feed tier tests green |

**Deploy:** theme `deploy-wp-theme-vps.py` · API if backend touched · price env on VPS.

---

## § O215-WP-POLISH — CLOSED ✅ (Lead verify+deploy 2026-06-14)

**Theme:** **1.18.95** · `deploy-wp-theme-vps.py` · prod HTML `ver=1.18.95` ✅

| Check | Result |
|-------|--------|
| VPS theme version | ✅ 1.18.95 |
| `/lenta/` HTTP | ✅ 200 |
| `/v1/quiz/start` | ✅ 200 |
| Owner accept O215 | ✅ |

**Next:** tier smoke all plans · Monica reset for first-login trial test.

---

**Deploy:** `deploy-o214-ops-truth-vps.py` · API restarted

| Check | Result |
|-------|--------|
| `_cycle_ts_from_log` on VPS | ✅ |
| `cycle_age_min` live | ✅ **3м** (was 154м) · `radar_lamp=ok` |
| `residential_active` in proxy groups | ✅ |
| clear-bans tooltip | ✅ |
| pytest 19/19 (O214 + O171) | ✅ |

**Note:** `fl_tier=residential` badge shows **only when DC exhausted** and FL on fallback. If DC alive again → badge hidden, FL 🟢 — correct.

---

## § O213-O212-DEPLOY — CLOSED ✅ (Lead verify VPS 2026-06-14)

**Deploy:** `deploy-o213-o212-vps.py` · radar + API restarted

| Check | Result |
|-------|--------|
| `listing:kwork parsed=36 pages=3` | ✅ 14:12 MSK |
| `EXCHANGE_SAFE_STOPS` on VPS | ✅ |
| TG `skip_entity=N` | ✅ acc1/2/3 |
| TG start без `ids=[…]` after 14:12 | ✅ |
| `/ops/` HTTP | ✅ 200 |

---

## § O213-KWORK-COVERAGE — Kwork page2-3 + exchange filter scope [CODE ✅]

**Ticket:** [`2026-06-14-kwork-fl-zero-new.md`](../../problems/2026-06-14-kwork-fl-zero-new.md)

**Owner symptoms:** sees orders on kwork.ru (screenshot + URLs) but not in RawLead lenta/ops.

**Owner repro URLs (Lead verify 2026-06-14):**
| external_id | title | in Neon? | visible | ingested MSK |
|-------------|-------|----------|---------|--------------|
| **3194789** | Сделать лендинг | ✅ | True | 2026-06-10 15:03 |
| **3196704** | Парсинг сайтов | ✅ | True | 2026-06-13 18:50 |

→ These two **are already in DB**. If owner «не видит» — likely feed scroll/sort (7-day window, newer on top), not parser miss. **Do not re-ingest.**

**Screenshot items (Lead Neon grep):**
| title fragment | in Neon? |
|----------------|----------|
| «Переписать промпт для Gemini» (3196630) | ✅ visible |
| «Поправить выгрузку фида» (3196662) | ✅ visible |
| «Посадка сайта на wordpress» | ✅ (similar titles exist) |
| **«Платформа для учебного центра»** | ❌ **NOT FOUND** — real gap |

**Root causes:**
1. `kwork_parser.py` fetches **page 1 only** (12 items). Orders outside top-12 never fetched → e.g. «Платформа для учебного центра».
2. Some fresh page-1 items blocked by shared L2 filter (`pipeline:skip filter kwork:id=…`).
3. Ops «0 новых» was UX bug (O212) — `fresh=0` = dedup of known ids, not «Kwork empty».

### Filter architecture (do NOT confuse with TG)

| Layer | File | Applies to |
|-------|------|------------|
| **TG spam / CV / seller** | `src/tg_spam_filter.py` (`is_tg_spam`, `is_tg_order_post`) | **TG only** (post-L1 guard) |
| **TG wide soft bypass** | `filters.py` → `tg_filter_soft_bypass()` + `TG_WIDE_SOFT_STOPS` | **TG only** (`source.startswith('tg:')`) — O207b |
| **Shared L2 word filter** | `filters.py` → `ListingWordFilter` from `docs/ops/FILTERS.md` | **kwork, fl, youdo, tg** — stop/take words |

**Kwork does NOT use `tg_spam_filter`.** It uses shared L2 only. Problem: stop words in FILTERS.md were tuned for TG noise; same list blocks valid Kwork orders.

**Fix t2:** add **exchange-safe bypass** for kwork+fl (NOT tg): when `source in ('kwork','fl')`, skip applying selected stop tokens. Do **not** weaken TG path.

### t1 — Kwork multi-page fetch

**File:** `src/kwork_parser.py`

- Mirror FL: pages 1–3 (env `KWORK_MAX_PAGES` default `3`)
- URL: probe pagination (`?page=2` or site pattern) — confirm `"wants":[` in HTML
- Merge pages, dedup by `pid`, then `trim_listing_at_known`
- Log: `listing:kwork parsed=N fresh=M pages=P`

**Acceptance probe after deploy:** «Платформа для учебного центра» appears in log as fresh within 2 cycles OR explain why (filter) with logged id.

### t2 — Exchange-safe L2 stops (kwork + fl only)

**File:** `src/filters.py` · **pipeline:** pass `project.source` into stop logic

Start set `_EXCHANGE_SAFE_STOPS` (conservative): `вебинар`, `логотип`, `баннер`, `дизайн макета`, `figma`, `фигма`, `монтаж`, `монтаж рилс`, `иллюстратор`

- If `source in ('kwork','fl')` and matched stop ∈ `_EXCHANGE_SAFE_STOPS` → **allow** (continue to category check)
- TG path unchanged: `tg_filter_soft_bypass` still only for `tg:*`

Log on allow: `pipeline:filter:exchange_safe kwork:id=… stop=…` (one line, no spam)

### t3 — Tests

- `test_kwork_parser.py`: multi-page mock, dedup, `pages=2`
- `test_filters.py`: kwork passes «логотип» in title; TG post with «логотип» still blocked (no soft bypass unless order markers)
- Regression: `test_o207b_filter.py`, `test_o171_ops_funnel.py` green

### DoD

- VPS: `listing:kwork parsed>12 pages=2-3` within 2 cycles
- «Платформа для учебного центра» ingested OR logged why skipped
- 3194789/3196704 unchanged (already in DB)
- TG filter regression: replay baseline unchanged
- pytest green

**Deploy:** `kwork_parser.py` + `filters.py` → restart **`rawlead-radar`**

---

## § O212-OPS-LOG-TRUTH — TG log noise + ops «0 новых» / TG 🔴 [PENDING DEPLOY]

**Ticket:** [`2026-06-14-ops-log-spam-tg-lamp.md`](../../problems/2026-06-14-ops-log-spam-tg-lamp.md)

**Owner symptoms:** log «помойка» (all chat ids) · FL/Kwork/TG show «0 новых» / TG 🔴 while radar alive.

**Facts (VPS 2026-06-14):** all units **active** · FL `parsed=30 fresh=0` · Kwork `parsed=12 fresh=0` · TG `handler_ok` + messages · **not a crash**.

### t1 — Stop chat-id log dump

**File:** `src/tg_monitor.py`

- `тг:монитор:старт` (~895): log `чатов=N file=F filter=K` — **remove** `ids=[sorted(...)]`
- `пропуск чата {id}` (~454): do **not** log every skip on reload; either:
  - increment counter + one summary line per reload (`skip_entity=N`), or
  - log only at DEBUG / first occurrence per account per hour

**Do not break:** O206 t3c watchdog · handler_ok line · join audit counts in storage

### t2 — Ops exchange cards truth

**Files:** `src/owner_admin.py` · optionally `src/static/ops-pult.js`

1. **`today_new_ids`:** use Neon `new_today` from `_lead_counts_by_source` (same MSK day as O211 footer), not `health.last_new_ids`
2. **Secondary line:** show last-cycle `parsed` / `fresh` from health (tooltip or sub-line): «за цикл: parsed=30 fresh=0»
3. **TG status lamp:** for `source_id=tg`, use `tg_pult_lamp_state` / fresh `тг:пульс` — **not** only Neon insert gap for `last_ok_at`
4. **`_last_log_line_for_source('tg')`:** exclude `бот_start:.*skip` · prefer `handler_ok|тг:пульс|listing:tg|health:tg`

### t3 — Tests

- Unit: `_last_log_line_for_source` picks handler_ok over bot_start skip (fixture lines)
- Unit: exchange row maps `today_new_ids` from Neon mock, not health `last_new_ids`
- Existing: `test_o171_ops_funnel.py` green

### DoD

- Restart radar once on VPS → log has **no** multi-line `ids=[…]` block
- `/ops/` FL/Kwork: «сегодня N» matches Neon (may still be 0) + visible parsed/fresh hint
- TG card **not** 🔴 when `handler_ok` + pulse <15m even if Neon TG insert 0
- pytest green

**Deploy:** `tg_monitor.py` → restart **`rawlead-radar`** · API files → restart **`rawlead-api`**

---

## Closed ✅ (hot index)

| § | DoD | deploy |
|---|-----|--------|
| **O214-DEPLOY** | cycle_age 3м not 154м · residential badge · pytest 19/19 | ✅ 2026-06-14 |
| **O213-DEPLOY** | parsed=36 pages=3 on VPS | ✅ 2026-06-14 |
| **O212-DEPLOY** | skip_entity · no ids dump · ops 200 | ✅ 2026-06-14 |
| **O213** | pages 1–3 + EXCHANGE_SAFE_STOPS · pytest 42/42 | ✅ |
| **O212** | log truth + ops cards · pytest 20/20 | ✅ |
| **O211-DEPLOY** | footer сегодня/24ч | ✅ |
| **O207b** | replay 99/14/7 | ✅ |
| **O209** | WP 1.18.84 | ✅ |

**Archive:** [`CODER_PROMPT_ARCHIVE.md`](../archive/CODER_PROMPT_ARCHIVE.md)
