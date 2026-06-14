# Coder — hot queue (active)

**→ Now:** § **O220-QUIZ-DEDUP** + § **O220-QUIZ-BAR-ALIGN**  
**Next:** § **O220-L1-PROMPT-R2** · O218 Playwright · mass retag **нет**

---

## ✅ O220-MATCH-CODE — CLOSED (Lead verify + deploy 2026-06-14)

Theme **1.19.02** prod · API `lead_coverage_match` · bar only · feed ≡ cabinet · pytest **21/21** · archive [`CODER_PROMPT_ARCHIVE`](../archive/CODER_PROMPT_ARCHIVE.md) § O220-MATCH-CODE

---

## ✅ O220-JS-SYNTAX-HOTFIX — CLOSED (Lead verify 2026-06-14)

Theme **1.19.01** prod · `node --check` ✅ · ticket [`2026-06-14-feed-cabinet-js-syntax.md`](../../problems/2026-06-14-feed-cabinet-js-syntax.md) · UI stray `"` → § O220-MATCH-CODE u1

---

## § O220-QUIZ-DEDUP — same card 4× on retake (P1)

**Ticket:** [`docs/problems/2026-06-14-quiz-duplicate-card-o217.md`](../../problems/2026-06-14-quiz-duplicate-card-o217.md)

**Root:** `quiz_next_response` drops string JSON `card_id` when building `shown_ids` (`int()` fail) → dedup broken.

### DoD

| Step | Action |
|------|--------|
| 1 | `quiz_adaptive.py`: shown set from history **as strings** for O217 JSON |
| 2 | Test: 2× `/v1/quiz/next` with same synthetic id in history → next card **≠** first |
| 3 | Deploy API · owner retake smoke (no 4× amoCRM) |

---

## § O220-QUIZ-BAR-ALIGN — result bars same left edge (P2 UI)

**Symptom:** «Разработка» / «Маркетинг» — жёлтые полоски начинаются с разного X (label width auto).

**Fix:** `rawlead.css` `.rl-quiz__category-bar` — fixed label column (e.g. `grid-template-columns: 7.5rem 1fr` or `minmax(7.5rem,7.5rem) 1fr`); verify overlay result modal (owner screenshot).

Bump theme if CSS-only · deploy with dedup or separate patch OK.

---

## § O220-L1-PROMPT-R2 — L1 few-shot after pilot judge (P1 · optional re-pilot 6 ids)

**Canon:** `data/preprod_ai_prod_audit_judge.md` § L1 Top prompt-fix · pilot `data/o220_l1_retag_pilot.json`  
**Pilot result:** l1_usable **80%** ✅ · tags avg **1.7–2.1** (target 2.5) · **6** leads still `<2` tags (3 empty)

**Goal:** Surgical `_LITE_SYSTEM` / `_LITE_FEWSHOT_BLOCK` in `src/ai_analyze.py` — **no model change**, no Neon schema.

### Requirements (from judge worst L1)

| id | Fix |
|----|-----|
| **r2-1** | **dev vs marketing:** cold TG outreach / «рассылка в тг» / lead gen scripts → `primary_category=marketing`, not dev (ref #24202) |
| **r2-2** | **infographic / slides / visual for cards** → `design`, not marketing (#24638, #24580) |
| **r2-3** | **Tags match subject:** marketplace product card / furniture → product/visual tags, not `landing_page_design`/`ui_ux` when subject is physical goods (#24776) |
| **r2-4** | **Min tags enforce:** if `feed_visible=true` and L1 returns `<2` lead_tags after sanitize → **retry 1×** with user hint «need ≥2 canonical_tag» (extend existing retry path ~L1843) |
| **r2-5** | **Optional:** Xmind / diagram / scheme software → document in few-shot (judge: dev vs text #23959 — pick **one** line, align with `lead_category` canon) |

### Files

```
src/ai_analyze.py          — _LITE_SYSTEM / few-shot only
tests/test_ai_analyze.py   — or extend existing L1 smoke if present
```

### Do not break

- L1 model · judge infra · `sanitize_l1_*` guards · ingest pipeline

### DoD

| # | Check |
|---|--------|
| R1 | 3–5 new few-shot lines (RU examples) in prompt |
| R2 | Retry when feed_visible + `<2` tags after sanitize |
| R3 | pytest green |
| R4 | **No VPS deploy required for verify** — owner may re-run 6 thin ids via `o220_l1_retag_pilot.py --lead-ids …` if script extended, or manual replay 6 ids |

**Deploy:** `ai_analyze.py` → VPS `/opt/rawlead/src/` + restart **`rawlead-radar`** (L1 on ingest) · API optional same file

**Not in scope:** mass retag 2264 · L2 prompt (separate track if owner wants design send 65%)

---

## Closed index

| § | Status |
|---|--------|
| **O220-MATCH-CODE** | ✅ deploy **1.19.02** · `lead_coverage_match` · bar only 2026-06-14 |
| **O220-FEED** | ✅ deploy 1.19.00+ |
| **O219** | ✅ deploy 1.18.97 · archive `CODER_PROMPT_ARCHIVE` |
| **O220-L1-RETAG** | ✅ code · owner apply+judge ⏳ |

---

**Owner batch (one deploy):** cabinet UX · anon locked match bar · auto trial on first TG login · hide synthetic badge · canonical quiz on `/lenta/#quiz`.

### Requirements

| id | Fix | Detail |
|----|-----|--------|
| **r1** | **Yellow square in LK** | Stray `#rl-cabinet-trial-badge` or skeleton chip under header — hide when empty; do not render yellow block without trial text |
| **r2** | **Hide user skills in LK** | Quiz-first (O208): hide `#rl-cabinet-tags`, label «Твои навыки», «+ Добавить», skills modal entry from head · keep tags in Neon/API |
| **r3** | **Retake button** | «Пройти ещё раз» / «Пройти тест заново» — **not** black `rl-cabinet-tag` chip · use `rl-btn rl-btn--ghost` · place **directly under** `.rl-cabinet-head__lead` (after «Отклики с ленты…»), not in tags row · opens `/lenta/#quiz` retake (`rawleadQuizApp.retake`) |
| **r4** | **Anon match bar** | Locked compat bar on every feed card for **anon** · root cause: CSS hides `.rl-row--auth-only` for `[data-tier="anon"]` (`rawlead.css` ~8144) while `renderMatchBlock` wraps bar in that class — fix class/CSS so anon sees lock bar |
| **r5** | **Tier match bars** | **Trial + active Premium:** real `%` bar, no lock · **Anon + expired trial + expired premium (no access):** locked bar · `free` logged-in without access: locked (upsell) |
| **r6** | **Auto trial first TG login** | **O208-B4 / O107 amended:** on `auth_telegram` + `_complete_bot_auth`, if `trial_used_at IS NULL` and no active premium → `start_trial()` + `notify_trial_started()` · skip owner/beta · Monica test after full wipe |
| **r7** | **Hide synthetic badge** | `rawlead-quiz.js`: `source=synthetic` → no visible pill (API field stays for O218 j7) |
| **r8** | **Canonical quiz URL** | Single entry: **`/lenta/#quiz`** overlay · `/quiz/` → **301** (or `template_redirect`) to `/lenta/#quiz` · update `quizUrl` in `functions.php` + PHP/JS links (`rawlead_page_url('quiz')` → lenta hash or helper `rawlead_quiz_url()`) · do **not** delete WP page without redirect |

### Files

```
wordpress/rawlead-kadence-child/page-cabinet.php
wordpress/rawlead-kadence-child/assets/js/rawlead-cabinet.js
wordpress/rawlead-kadence-child/assets/js/rawlead-feed.js
wordpress/rawlead-kadence-child/assets/js/rawlead-quiz.js
wordpress/rawlead-kadence-child/assets/css/rawlead.css
wordpress/rawlead-kadence-child/functions.php
wordpress/rawlead-kadence-child/page-quiz.php          ← redirect stub OK
wordpress/rawlead-kadence-child/template-parts/rawlead/hero.php
wordpress/rawlead-kadence-child/template-parts/rawlead/feed-strip.php
src/api_server.py                                      ← r6 auto trial
src/trial_subscription.py                              ← reuse start_trial
tests/test_trial_subscription.py                       ← extend auto-start on auth
tests/test_o197_quiz_adaptive.py                       ← if quiz URL touched
```

### Steps

**t1 — Cabinet head (`page-cabinet.php` + `rawlead-cabinet.js` + CSS)**
- Hide skills block (r2); move retake button under lead (r3); fix trial badge empty state (r1).

**t2 — Feed match bar (`rawlead-feed.js` + CSS)**
- `renderMatchBlock`: lock only `anon | expired_trial | free-without-access`; trial/premium → `renderCompatMatchBar`.
- Remove/adjust `.rl-lead-card[data-tier="anon"] .rl-row--auth-only { display:none }` or use `.rl-row--match-tier` for match row (r4,r5).

**t3 — Auto trial (`api_server.py`)**
- After `_upsert_telegram_user` in both auth paths: try `start_trial`; on success commit + notify; swallow `TrialStartError` for already_used/premium.

**t4 — Quiz URL (`functions.php` + links)**
- `rawlead_quiz_url()` → `/lenta/#quiz`; redirect `/quiz/`; retake/cabinet links use hash overlay.

**t5 — Synthetic badge (`rawlead-quiz.js`)** — r7.

### Do not break

- O216 quiz lifecycle · retake rules · `importQuizTags` · expired-trial banner · O217 synthetic API · Monica wipe is **ops** (owner), not code.

### DoD

| # | Check |
|---|--------|
| D1 | LK logged-in: **no** skill chips row · retake = normal ghost button under lead text |
| D2 | LK: **no** yellow stray square under header |
| D3 | Anon `/lenta/`: **locked** compat bar on cards (visible, with lock icon) |
| D4 | Trial Monica after wipe + TG login: `plan=trial` · real match % · no lock |
| D5 | Expired trial/premium: locked bar returns |
| D6 | `/quiz/` → redirects to `/lenta/#quiz` · overlay works · no duplicate standalone quiz UX |
| D7 | Quiz card: no «synthetic» pill · pytest green · bump `RAWLEAD_CHILD_VERSION` |

**Deploy:** theme rsync + restart API if t3 · owner re-tests Monica first-login.

---

**Next:** owner tier smoke · **O218 Playwright** after O219 deploy

## § O218-PLAYWRIGHT-QUIZ-E2E — human-like UI/quiz journeys (P1 · pre-ads gate · after O219)

**Owner 2026-06-14:** Playwright · multi-user · quiz scenarios · **mobile 390 + desktop** · no state bleed.

**Spec:** [`OWNER_INTENT.md`](OWNER_INTENT.md) § **O218-w** · accounts [`PREPROD_ACCOUNTS.md`](../../ops/PREPROD_ACCOUNTS.md)

### Scenarios (min)

| id | Flow | assert |
|----|------|--------|
| j1 | anon abandon mid-quiz → reopen intro | empty history · no resume |
| j2 | anon complete → result + retake button | `COMPLETED_KEY` set |
| j3 | anon complete → TG login | Neon `user_tags` import |
| j4 | retake done vs retake abandon | profile replace vs keep first |
| j5 | anon locked match bar · trial real % | tier-specific DOM |
| j6 | cabinet retake link | overlay opens retake |
| j7 | synthetic card title on prod | `source=synthetic` in **API/Network** only · **no visible badge**

### Implementation

| # | Task |
|---|------|
| t1 | `tests/e2e/` or extend preprod script — **separate browser context per persona** |
| t2 | Viewports: **1280 desktop** + **390 mobile** (duplicate critical paths j1,j2,j5,j7) |
| t3 | Use Monica + dedicated anon JWT users · reset subscription SQL hook or fixture between runs |
| t4 | Output `data/preprod_quiz_e2e.json` · fail screenshots |
| t5 | CI/local: `pytest` marker or standalone playwright cmd documented in TASKS |

**Do not break:** O37c unrelated flows · production data (use test tg ids only).

**DoD:** all j1–j7 green desktop + j1,j2,j5,j7 green mobile · Lead verify before ads gate.

---

## § O217-DEPLOY — VPS API + quiz_cards_v1.json (P0 · code ✅)

**Lead verify 2026-06-14:** local code ✅ · prod quiz **still Neon** (`source=kwork`, card_id=23958) until this deploy.

| Step | Task |
|------|------|
| d1 | `python scripts/deploy-o217-quiz-vps.py` |
| d2 | Prod: `/wp-json/rawlead/v1/quiz/start` → `card.source=synthetic` · title from PM pack |
| d3 | Owner: incognito quiz — PM titles, not Kwork junk |

**DoD:** script prints `DEPLOY OK` · `quiz_cards_v1=56` · `quiz_source=synthetic`

---

## § O217-QUIZ-SYNTHETIC-CODE — summary ✅ code (Lead verify 2026-06-14)

| Area | Result |
|------|--------|
| `data/quiz_cards_v1.json` | ✅ **56** (14/niche: 8+2+4) · pilot 20 ids present |
| Tag lint | ✅ all `skills_on_like` ∈ CANONICAL_TAGS |
| `quiz_adaptive.py` | ✅ JSON-first · Neon fallback if file missing |
| pytest | ✅ **59/59** (o217 + o197 + o195) |
| `.gitignore` | ✅ `!data/quiz_cards_v1.json` |
| **Deploy prod** | ❌ API still allowlist/Neon on prod |

---

## § O216-DEPLOY — VPS + gitignore (P0 · after code ✅)

**Lead verify 2026-06-14:** O216 + O216b **code accepted** · prod still **1.18.95** · allowlist **not in git** (`.gitignore data/*`).

| Step | Task |
|------|------|
| d0 | `.gitignore`: add `!data/quiz_pool_allowlist.json` (whitelist curated pool for repo + CI) |
| d1 | `python scripts/deploy-o216-quiz-vps.py` — theme **1.18.96** + API + allowlist |
| d2 | Prod curl: `rawlead-quiz.js` has `COMPLETED_KEY` · `/lenta/` `ver=1.18.96` |
| d3 | Owner: `PAY_PREMIUM_RUB=10` in `.env.site` → restart API → checkout smoke → revert **790** |

**DoD:** deploy script prints `DEPLOY OK` · owner D1–D9 from STATUS · pytest **26/26** unchanged.

**Do not break:** O215 CSS/UX · locked bar only anon/expired/free · trial = premium match bar.

---

## § O216 + O216b — summary ✅ code (Lead verify 2026-06-14)

| Area | Result |
|------|--------|
| Quiz lifecycle · retake · clear-on-exit | ✅ `rawlead-quiz.js` + `quiz.php` |
| Feed locked bar anon/expired/free; trial → premium tier | ✅ `renderMatchBlock` |
| Cabinet «Пройти тест заново» | ✅ `rawlead-cabinet.js` |
| Allowlist loader + SQL filter | ✅ `quiz_adaptive.py` |
| **`data/quiz_pool_allowlist.json`** | ✅ **64 ids** local · ⚠️ **gitignored** — d0 |
| `scripts/quiz_pool_audit.py` | ✅ export script |
| pytest test_o197 + test_o195 | ✅ **26/26** |
| **Deploy prod** | ❌ still **1.18.95**, no `COMPLETED_KEY` on prod |
| **PAY_PREMIUM_RUB=10** | ❌ not set · pricing PHP **790** (OK until smoke) |

---

**O216 code ✅ deploy 1.18.96** — details → [`CODER_PROMPT_ARCHIVE.md`](../archive/CODER_PROMPT_ARCHIVE.md) · follow-up UX → **§ O219** above.

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
