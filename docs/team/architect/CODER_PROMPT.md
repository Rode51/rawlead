# Coder — hot queue (active)

**→ Now:** **O271** Neon → VPS Postgres migration · O200 ⏸ · O268 фон

Full closed specs → [`CODER_PROMPT_ARCHIVE`](../archive/CODER_PROMPT_ARCHIVE.md) · prod snapshot → [`PROD_FACTS.md`](../common/PROD_FACTS.md) · **migrate:** [`MIGRATE_NEON_TO_VPS_POSTGRES.md`](../../ops/MIGRATE_NEON_TO_VPS_POSTGRES.md)

---

## § O271-NEON-TO-VPS-POSTGRES — **P0 owner go 2026-06-18**

**Owner:** миграция без оплаты Neon · полный dump если доступен · ветка `o271/pre-vps-postgres-migration` **перед** prod cutover.

**Runbook:** [`docs/ops/MIGRATE_NEON_TO_VPS_POSTGRES.md`](../../ops/MIGRATE_NEON_TO_VPS_POSTGRES.md)

### Deliverables

| # | Item |
|---|------|
| 1 | VPS: `postgresql` · DB `rawlead` · user `rawlead` |
| 2 | `pg_dump` off Neon → `/opt/rawlead/data/neon_pre_migration.dump` |
| 3 | `pg_restore` → local · `.env.site` `DATABASE_URL=127.0.0.1` |
| 4 | `scripts/migrate_neon_to_vps_postgres.py` — dry-run dump / restore / smoke |
| 5 | Daily backup timer · update `PROD_FACTS` · `purge_old_leads` smoke |
| 6 | Post: O270 circuit breaker still useful for local PG down |

**DoD:** `/health` ok · лента · TG login · subscription row intact · radar `neon_insert` in log.

---

## § O270-NEON-QUOTA-RETENTION — **P0 owner 2026-06-18** (superseded by O271 migrate)

**Symptom:** Neon **недоступен** · VPS `purge_old_leads --dry-run` → `Your account or project has exceeded the compute time quota` · O200 regen/judge **blocked**.

**Not missing:** autocleanup **есть** — `rawlead-purge-leads.timer` **active** · сегодня **03:15** удалено **607** old + **92** delisted.

**Owner unblock (сначала):** [console.neon.tech](https://console.neon.tech) → Billing / Usage → **upgrade plan** или дождаться reset квоты · при storage full — Console → **Delete branches** / shrink compute.

**When Neon accepts connections again (VPS):**
```bash
cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src .venv/bin/python scripts/purge_old_leads.py --apply
```

### Deliverables (@coder)

| # | Item |
|---|------|
| 1 | **`scripts/probe_neon_storage.py`** — row counts + `pg_total_relation_size` top tables · no secrets in output |
| 2 | **Circuit breaker** — on `compute time quota` / `storage limit` in `pg_storage` / radar: pause Neon writes **30–60 min** · log `neon:quota_pause` once · не спамить reconnect |
| 3 | **Ops** — `/ops/` или health: last purge timer result · Neon reachability ping |
| 4 | **Optional env** `LEADS_RETENTION_DAYS` (default 7) · document in `.env.example` |
| 5 | **Deploy** — ensure `rawlead-purge-leads.timer` enabled on VPS · `docs/problems/2026-06-18-neon-quota-exceeded.md` |

**Do not:** DELETE users/tags/subscriptions · не трогать YouDo O268 без отдельного тикета.

**Resume O200** только после Neon green + purge `--apply` ok.

---

## § O200-L2-CATEGORY-WAVE — **P0 owner go 2026-06-18**

**Owner:** «помчали» — regen + judge **≥70% × 4 категории** · гейт до ads (ROADMAP волна 4).

**Goal:** shared L2 `reply_draft` · judge `send_as_is` **≥70%** overall **и** по **dev / design / marketing / text** (n≥10 на категорию в выборке).

**Context:** L2 aggregate **71.8%** ✅ · per-category ⏳ · playbooks r2 в `l3_human_style.py` · `primary_category` в L2 payload · `deploy-o200-l2-vps.py`.

### Steps

| # | Action |
|---|--------|
| 1 | **Deploy** (if not on VPS): `python scripts/deploy-o200-l2-vps.py` |
| 2 | **Regen** stratified visible leads: `scripts/regen_shared_reply_drafts.py --profile site --apply --limit 80` |
| 3 | **Judge:** `scripts/preprod_ai_prod_audit.py --profile site --judge --judge-limit 40` (stratified, fresh drafts) |
| 4 | **Gate:** `send_as_is_pct ≥ 70` overall · **each** cat n≥10 → `send_as_is_pct ≥ 70` · `avg_combined_3 ≥ 4.0` |
| 5 | **Fail:** правки **Category playbooks** в `l3_human_style.py` · re-regen worst cat · pytest `test_l3_human_style.py -k o200` |
| 6 | **Artifacts:** `data/preprod_o200_judge.json` + `data/preprod_o200_judge_human.md` (таблица 4×cat %, worst 3/cat) |

**Pilot (optional first):** `--limit 40` regen + judge 40 (10×4) → если PASS, full 80.

**Constants:** `_JUDGE_L2_SEND_MIN_PER_CAT` сейчас **0.80** — для owner gate **70%** выставить **0.70** или явно в artifact «gate=70% owner».

**Do not break:** radar/API ingest · YouDo O268 · cabinet on-demand L2 — только **shared** `leads.reply_draft`.

**DoD:** artifact с ✅ по 4 категориям · Lead verify · `TASKS`/`STATUS` update.

---

## § O268 — ✅ closed (watch фон)

Ingest **14:26** `parsed=50` DC · O268 ephemeral carousel · spec → STATUS § O268 · backlog O269 RU-after-DC optional.

---

**Diagnosis:**

| Факт | Вывод |
|------|--------|
| 10:04 ok | one-shot camoufox · cold `goto` · old FL DC `.197` |
| 13:16–13:28 fail | sticky worker · persistent profile · reload 150s на SP stub |
| `youdo_sticky_worker`: cookies exist → **reload вместо goto** | «отравленный» profile после SP → reload trap |
| O264 pool | только `128.237` + `130.67` — **.197 не в primary** |
| RU off | нет seed burst когда DC мёртв |

**Goal:** вернуть pass rate «как раньше» (периодические ok на DC) **без** 24/7 RU · RU только budgeted burst.

**Do not break:** O254 ops hard reset · detail subprocess · `fetch_every_n=4` · playwright pin 1.58.

### Deliverables

| # | Item | Behaviour |
|---|------|-----------|
| **A** | **Profile poison fix** | On ServicePipe fail / `html_len<5000`: `_wipe_youdo_persistent_profiles(proxy_url)` · log `profile_wiped=sp` · **never** auto-reload when last sticky result was antibot (cookies alone ≠ warm) |
| **B** | **Fetch path order** | Slot 1 listing: **ephemeral cold goto** (10:04 path) · sticky+persistent **only after** first `html_len>100000` in session OR env `YOUDO_STICKY_AFTER_OK=1` |
| **C** | **Reload fast-fail** | On sticky reload: if still `_youdo_html_is_servicepipe` after **15s** → abort (not 150s) · rotate slot |
| **D** | **DC pool restore** | VPS: `YOUDO_DC_PROXY_URLS` = same 4 as `FL_PROXY_URLS` (incl. **`194.226.236.197`**) · `YOUDO_O191_DC_SLOTS=4` · keep new IPs in pool |
| **E** | **RU budget burst** | `YOUDO_RU_RETRY_MAX=1` · **only last** slot after all DC fail in fetch · `YOUDO_SERVICEPIPE_EARLY_RU=0` · env `YOUDO_RU_BURST_MAX_PER_DAY=2` (storage counter) · log `ru_burst=n/max` |
| **F** | **Profile rotate** | Optional env `YOUDO_PROFILE_GENERATION=2` → new dir suffix `youdo_{hint}_g2/` after wipe (owner «поменять профиль») |
| **G** | Deploy | `scripts/deploy-o268-youdo-recovery-vps.py` — wipe `data/youdo_*` once · patch env · restart radar |
| **H** | Tests | `tests/test_o268_youdo_recovery.py` — reload trap · wipe on SP · ephemeral-first · RU burst cap mock |
| **I** | Docs | `docs/problems/2026-06-16-youdo-antibot-browser.md` § O268 |

### VPS env (target)

```text
YOUDO_STICKY_SESSION=1
YOUDO_PERSISTENT_PROFILE=1
YOUDO_STICKY_AFTER_OK=1
YOUDO_GOTO_WAIT_UNTIL=domcontentloaded
YOUDO_SERVICEPIPE_WAIT_SEC=90
YOUDO_SOFT_SERVICEPIPE_BAN=1
YOUDO_STICKY_RELOAD_SP_ABORT_SEC=15
YOUDO_O191_DC_SLOTS=4
YOUDO_RU_RETRY_MAX=1
YOUDO_RU_BURST_MAX_PER_DAY=2
YOUDO_SERVICEPIPE_EARLY_RU=0
YOUDO_PROFILE_GENERATION=2
```

Revert `networkidle` default on slot 1 (too slow on SP stub).

### Accept / DoD

1. pytest O268 + O267 + O266 + `test_youdo_human.py` green.
2. VPS deploy → within **6h**: `youdo:ingest done=50` **or** trace `html_len>100000` on DC without RU.
3. RU traffic: ≤2 listing fetches/day unless owner raises cap.
4. Log shows `sticky_goto` or ephemeral slot1 before first ok; no 150s reload on 1712b.

---

## § O267-YOUDO-BROWSER-REGRESSION — **✅ code/deploy · ❌ prod DoD** (Lead 2026-06-18)

**Coder ✅:** persistent profile · soft SP ban · networkidle default · SP wait 90s · sticky worker `user_data_dir` · deploy script.

**Lead verify:**
| Check | Result |
|-------|--------|
| `pytest test_o267 + o266 + youdo_human` | ✅ **30/30** |
| Syntax `exchange_browser_fetch.py` | ✅ |
| VPS env O267 | ✅ `PERSISTENT_PROFILE=1` · `networkidle` · `SOFT_SERVICEPIPE=1` |
| VPS profile dirs | ✅ `data/youdo_128.237…` (Firefox profile files) |
| Prod `sticky_goto` / ingest | ❌ reload trap · last ok **10:04** ephemeral `.197` |
| **→** | **O268** recovery package |

---

## § O267-YOUDO-BROWSER-REGRESSION — spec (closed)

**Intent:** owner: «раньше YouDo **нормально работал**, падал периодически» → после O190–O266 pass rate упал · гипотеза: **холодный Camoufox каждый цикл** без cookies, не только ServicePipe lottery.

**Goal:** вернуть поведение **«теплый посетитель с profile на диске + reload»**, как до ephemeral-subprocess; O266 sticky — база, O267 — **persistent profile + мягче teardown + длиннее wait**.

**Do not break:** O254 ops hard reset · O266 sticky protocol · DC-only O264 (`128.237` + `130.67`) · **RU fallback off** · detail subprocess · `fetch_every_n=4`.

### Root cause (Lead triage)

| Было (~O156) | Стало (prod) |
|--------------|--------------|
| `_launch_youdo_persistent_context` · `user_data_dir` на диске | Camoufox **new context** каждый fetch / worker spawn |
| cookies между циклами | cold visitor → ServicePipe 1712b чаще |
| ingest `parsed=50` регулярно (09.06) | редкие окна (01:35, 10:04) на том же IP |

### Deliverables

| Item | Path / behaviour |
|------|------------------|
| **Persistent profile** | `YOUDO_PERSISTENT_PROFILE=1` · dir `data/youdo_{proxy_hint}/` per DC · reuse in **`youdo_sticky_worker.py`** (prefer `launch_persistent_context` or equivalent Camoufox profile dir) |
| **Sticky + profile** | worker spawn **once per proxy** · profile survives worker restart within TTL · `goto` only when no valid cookies / cold |
| **Stop double-cold** | remove / gate `(_youdo_is_camoufox() and slots_tried == 1)` → `_fetch_youdo_ephemeral` when sticky+persistent on |
| **Goto wait** | default `YOUDO_GOTO_WAIT_UNTIL=networkidle` slot 1 (env override ok) |
| **ServicePipe wait** | on 1712b stub: poll page up to **`YOUDO_SERVICEPIPE_WAIT_SEC=90`** DC before fail (reuse `_youdo_wait_servicepipe_clear`) |
| **Soft fail** | `YOUDO_SOFT_SERVICEPIPE_BAN=1`: first servicepipe on DC **in fetch** → no `_ban_url` / no hard_reset streak=1 · rotate slot ok · ban only on 2nd SP same fetch or hard antibot |
| **Env VPS** | see below |
| **Deploy** | `scripts/deploy-o267-youdo-regression-vps.py` |
| **Tests** | `tests/test_o267_youdo_persistent_profile.py` · extend O266 if needed |
| **Docs** | `docs/problems/2026-06-16-youdo-antibot-browser.md` § O267 · `.env.example` |

### VPS env (after deploy)

```text
YOUDO_STICKY_SESSION=1
YOUDO_PERSISTENT_PROFILE=1
YOUDO_GOTO_WAIT_UNTIL=networkidle
YOUDO_SERVICEPIPE_WAIT_SEC=90
YOUDO_SOFT_SERVICEPIPE_BAN=1
YOUDO_MAX_DC_BANS_PER_FETCH=1
YOUDO_O191_DC_SLOTS=2
YOUDO_RU_RETRY_MAX=0
YOUDO_SERVICEPIPE_EARLY_RU=0
```

Keep O264 DC URLs unchanged.

### Accept / DoD

1. `pytest tests/test_o267*.py tests/test_o266*.py tests/test_youdo_human.py -q` green.
2. Sticky worker uses **same profile dir** on 2 sequential listing fetches (unit: path stable · mock).
3. **VPS deploy** → within **24h** at least one:
   - `youdo:trace stage=sticky_goto` · `html_len>100000` · **or**
   - `youdo:ingest done=50` · **or**
   - next allowed cycle: `stage=sticky_reload` · `goto_ms` **<** cold baseline (~10s vs 30s+).
4. No regression: ops `youdo_hard_reset` still tears down profile + sticky worker.
5. Lead verify: grep `sticky_` + `html_len=1` in `radar_site.log`.

**Not in scope:** RU burst · new DC IPs · night window scheduler (→ backlog if O267 insufficient).

**Ticket:** [`2026-06-16-youdo-antibot-browser.md`](../../problems/2026-06-16-youdo-antibot-browser.md)

---

## § O266a-YOUDO-STICKY-TEST-FIX — ✅ (Lead 2026-06-18)

**Fix:** `test_youdo_human.py` setUp `YOUDO_STICKY_SESSION=0` · `_youdo_fetch_tier_plan` patch on slot tests.

**Verify:** `pytest tests/test_youdo_human.py tests/test_o266_youdo_sticky_session.py -q` → **19/19** ✅

---

## § O266-YOUDO-STICKY-SESSION — **✅ code · ⏳ prod ingest** (Lead 2026-06-18)

**Coder ✅ code:** `youdo_sticky_worker.py` · sticky manager in `exchange_browser_fetch.py` · `youdo_parser` hard_reset skip when warm · pytest **9/9** · deploy script.

**Lead verify:**
| Check | Result |
|-------|--------|
| `pytest tests/test_o266_youdo_sticky_session.py` | ✅ **9/9** |
| `exchange_browser_fetch.py` syntax | ✅ compiles |
| VPS deploy + env `YOUDO_STICKY_SESSION=1` | ✅ radar **active** |
| `test_youdo_human.py` + O266 | ✅ **19/19** (O266a) |
| Prod `sticky_goto` / `sticky_reload` | ⏳ watch — ServicePipe 1712b блокирует warm |

---

## § O266-YOUDO-STICKY-SESSION — spec (closed)

**Intent:** [`OWNER_INTENT.md`](OWNER_INTENT.md) backlog YouDo ingest · owner: «зайти на страницу, пробиться, дальше **обновлять**, не выходить».

**Problem:** prod Camoufox = **one-shot** `youdo_fetch_worker.py` subprocess каждый `fetch_every_n` цикл → cold `goto` → ServicePipe 1712b снова. Успех **10:04** был на **2-м slot retry** после fail (270 KB), не на RU.

**Goal:** после первого **valid listing HTML** (`html_len≥8000`, not servicepipe, has cards) — **держать browser session** на активном DC proxy; следующие listing fetch = **`page.reload()`** (warm path), не новый subprocess + goto.

**Do not break:** O254 ops hard reset · traffic_guard · `fetch_every_n=4` · DC-only pool (O264: `128.237` + `130.67`, RU fallback off) · detail fetch subprocess ok separate.

### Design (recommended)

**A. Sticky worker subprocess** (extends O190, avoids asyncio in uvicorn):

| Piece | Path / behaviour |
|-------|------------------|
| Worker | `scripts/youdo_sticky_worker.py` — long-lived Camoufox AsyncCamoufox **one page** per `--proxy` |
| Protocol | stdin/stdout **JSON lines**: `{"cmd":"goto"|"reload"|"teardown","url":...}` → `{"html":...,"stage":"sticky_goto"|"sticky_reload",...}` or `{"error":...}` |
| Parent | `exchange_browser_fetch.py`: manager keeps worker PID + proxy binding; spawn on first listing fetch; reuse while warm |
| Fallback | `YOUDO_STICKY_SESSION=0` or worker dead → existing one-shot `youdo_fetch_worker.py` |

**Warm path:** session warm iff last listing returned valid HTML for **same** `proxy_url` within `YOUDO_STICKY_MAX_AGE_SEC` (default **3600**).

**Listing fetch logic:**

1. **Cold (`sticky_goto`):** current camoufox path — goto listing URL · servicepipe wait · list_view if needed · validate HTML.
2. **Warm (`sticky_reload`):** `page.reload(wait_until=...)` · `_youdo_wait_listing_ready_async` · validate · **no** new browser launch.
3. On reload antibot/servicepipe → **one** cold retry same cycle; then normal slot rotate / ban (existing O260).

**Hard reset / teardown policy (critical):**

| Event | Sticky worker |
|-------|---------------|
| `youdo_hard_reset` ops / manual | **kill** sticky + existing teardown |
| `fail_streak=1` servicepipe on **cold** fetch | **do not** kill sticky if worker not started yet |
| Valid HTML → fail on **parse** only | keep sticky |
| `_validate_youdo_html` antibot / servicepipe on **warm reload** | kill sticky · cold next cycle |
| Proxy URL change (DC rotate) | kill sticky · spawn for new proxy |
| `YOUDO_STICKY_MAX_AGE_SEC` exceeded | kill · cold goto |
| `youdo_browser_teardown()` | kill sticky always |

**Trace (radar log):** `youdo:trace stage=sticky_goto|sticky_reload|sticky_teardown` · `proxy_hint` · `html_len` · `warm=1|0`.

### Env (VPS `.env.site` after deploy)

```text
YOUDO_STICKY_SESSION=1
YOUDO_STICKY_MAX_AGE_SEC=3600
YOUDO_STICKY_RELOAD_WAIT_UNTIL=domcontentloaded
```

Keep O264: `YOUDO_O191_DC_SLOTS=2` · `YOUDO_RU_RETRY_MAX=0` · `YOUDO_SERVICEPIPE_EARLY_RU=0`.

### Files

| File | Change |
|------|--------|
| `scripts/youdo_sticky_worker.py` | **new** — long-lived worker |
| `scripts/youdo_fetch_worker.py` | optional shared helpers import; keep one-shot for detail / fallback |
| `src/exchange_browser_fetch.py` | sticky manager · wire listing fetch · teardown hooks · **fix IndentationError ~3055** if present locally |
| `src/youdo_parser.py` | trace stages · narrow auto `youdo_hard_reset` when sticky warm (no teardown on streak=1 alone) |
| `tests/test_o266_youdo_sticky_session.py` | env gate · warm/cold selection · teardown rules · mock protocol |
| `scripts/deploy-o266-youdo-sticky-vps.py` | deploy worker + src + restart radar |
| `.env.example` | document env keys |
| `docs/problems/2026-06-16-youdo-antibot-browser.md` | § O266 note |

### Accept / DoD

1. `pytest tests/test_o266_youdo_sticky_session.py -q` green.
2. Local smoke: two sequential listing fetches same proxy → 2nd uses `sticky_reload` in trace (mock or headed optional).
3. **VPS deploy** → within 2 cycles after first `html_len>100k`: next allowed fetch logs **`sticky_reload`** and `parsed=50` without full 30s cold goto (compare goto_ms).
4. Ops «Restart YouDo» / `youdo_hard_reset` still kills sticky worker (verify PID gone).
5. No regression: `tests/test_youdo_human.py` · `test_exchange_browser_fetch.py` youdo worker paths.

**Probe after deploy:** `grep 'sticky_' /opt/rawlead/data/radar_site.log | tail -20` · `youdo:ingest done`.

**Ticket:** [`2026-06-16-youdo-antibot-browser.md`](../../problems/2026-06-16-youdo-antibot-browser.md)

---

## § O218-PLAYWRIGHT-QUIZ-E2E — ✅ prod (2026-06-18)

Gate pre-ads **green** · desktop 8/8 · mobile 5/5 · theme `ver=1.19.20` · full spec → archive / git history.

---

## § O218-PLAYWRIGHT-QUIZ-E2E — spec (closed)

**Intent:** [`OWNER_INTENT.md`](OWNER_INTENT.md) § **O218-w** · automated Playwright **quiz lifecycle + tier match bars** · multi-persona · **desktop + mobile 390** · no shared `localStorage` between personas.

**Why:** manual tier smoke misses regressions (Monica trial % vs anon lock · retake vs first profile · Neon tag import · quiz mid-exit restore).

**Do not duplicate:** `scripts/preprod_playwright/ux_audit.py` (O37c U1–U10 pixel audit) · `ux_journey.py` J1–J11 feed/draft journeys — **reuse** `feed_ui.py` helpers only.

### Deliverables

| Item | Path |
|------|------|
| Runner | `scripts/preprod_playwright/quiz_e2e.py` |
| Shared helpers | extend `feed_ui.py` **or** `quiz_ui.py` in same dir (quiz nav, answer loop, result assert) |
| CI hook | `tests/test_o218_quiz_e2e.py` — **skip** unless `RAWLEAD_O218_E2E=1` (prod URL, slow) |
| Artifact | `data/preprod_quiz_e2e.json` + `data/preprod_quiz_e2e/` screenshots on fail |
| Docs | append runbook to `docs/ops/PREPROD_STRESS_RUN.md` § O218 (commands only) |

### CLI

```text
.venv\Scripts\python.exe scripts\preprod_playwright\quiz_e2e.py --base-url https://rawlead.ru
.venv\Scripts\python.exe scripts\preprod_playwright\quiz_e2e.py --viewport mobile --ids j1,j2,j5
.venv\Scripts\python.exe scripts\preprod_playwright\quiz_e2e.py --headed --slow-mo 100
```

Exit **0** iff all selected scenarios pass · exit **1** on any fail · JSON always written.

### Scenarios (isolated browser context each run)

| id | Scenario | Viewports | Isolation / notes |
|----|----------|-----------|-------------------|
| **j1** | Anon: exit mid-quiz → reopen → intro restored (not stuck on card N) | 1280 + **390×844** | fresh context · no JWT |
| **j2** | Anon: complete → result modal → «ещё раз» / restart → new session | 1280 + 390 | fresh context |
| **j3** | Anon complete → login → tags persisted in Neon | 1280 | **separate** test user (not Monica) · after complete call `GET /v1/quiz/...` or Neon read tag count ↑ · prefer `preprod_mint_token.py` JWT inject **after** anon quiz if TG widget blocked headless — document in runner |
| **j4** | Retake: finish → profile update; retake abandon → first profile kept | 1280 | logged-in JWT · `sessionStorage rawlead_quiz_retake` · assert `rawlead_quiz_completed_v1` backup behaviour per `rawlead-quiz.js` |
| **j5** | Logged-in Monica vs anon: real `.rl-match` bar · anon locked only | 1280 + 390 | **Monica prod state ✅ 2026-06-17** — plan **agent** active until **2026-07-15** · 27 quiz tags · **no Neon wipe** · `feed_ui.assert_match_for_tier(card, "premium")` for Monica · `"anon"` for anon context |
| **j6** | Cabinet «Пройти тест заново» opens overlay / retake flow | 1280 | logged-in context · `/cabinet/` |
| **j7** | Synthetic quiz cards visible (`source=synthetic` or PM title substring in card) | 1280 + 390 | DOM assert on `#rl-quiz-card-source` / title · badge hidden per O219 |

**Persona rule:** one context = one persona (anon A / anon B / Monica / acc1 JWT) — **never** reuse storage across rows in same process without `browser.new_context()`.

**Quiz entry:** canonical **`/lenta/#quiz`** (not legacy `/quiz/` only) · open overlay via hash or CTA consistent with prod.

**Answer loop:** click `#rl-quiz-like` / `#rl-quiz-nope` until `rl-quiz-stage--cards` ends · timeout per scenario ≤3 min · handle `#rl-quiz-early-btn` if shown.

**API asserts (where applicable):** `GET /wp-json/rawlead/v1/quiz/start` · `POST .../next` status 200 · after j3 logged-in import — optional Neon `user_tags` count via existing probe script (env `DATABASE_URL` local only — **no secrets in artifact**).

### Env / accounts

| Env | Use |
|-----|-----|
| `RAWLEAD_PREPROD_ACCESS_TOKEN` | acc1 JWT — j4/j6 |
| `RAWLEAD_MONICA_TOKEN` | Monica JWT — j5 logged-in half · mint via `grant_premium_local.py --username RawLead --plan agent` (do **not** change her Neon sub) · write to `.env.site` in Coder session |
| `DATABASE_URL` | optional Neon verify j3/j4 — skip if unset |

**Monica (O218 j5):** tg **8688264540** · Neon `user_id` **`8d5afb3d-e8bd-4970-a33d-21c3ddeafdef`** · `@RawLead` display · **agent premium OK** (same feed tier `premium` + real match bar as trial). Full wipe only for **auto-trial smoke** in `FOR_YOU.md`, not for O218 j5.

See [`docs/ops/PREPROD_ACCOUNTS.md`](../../ops/PREPROD_ACCOUNTS.md) · **never** owner JWT `164786fe-…`.

### Accept

1. `quiz_e2e.py` green on prod URL for **j1–j7** desktop; **j1,j2,j5,j7** also pass at **390×844**.
2. Artifact JSON lists each scenario: `id`, `viewport`, `pass`, `ms`, `error`, optional `screenshot`.
3. `pytest tests/test_o218_quiz_e2e.py -q` — skip by default · 1 smoke test that imports runner module.
4. No regression to existing `smoke.py` / `ux_journey.py`.

**Order:** owner deferred Metrika smoke · YouDo ⏸ · **O218 blocks M1 ads** per `ROADMAP.md` wave 6.

---

## § O262k-YOUDO-DC-DIAG — ✅ VPS probe (2026-06-17)

**DC slot 1** (`185.147.131.15:8000`) · Camoufox · `html_len=1712` · **servicepipe** · `data_id=0` · не map/list.

**Scripts:** `probe_youdo_dc_page.py` · `deploy-o262k-youdo-dc-probe-vps.py` · `data/o262k_dc_probe.json`

**Env VPS:** `YOUDO_O191_DC_SLOTS=4` · `YOUDO_DC_PROXY_URLS` restored · `dc_alive=3/4`

**Ticket:** [`2026-06-16-youdo-antibot-browser.md`](../../problems/2026-06-16-youdo-antibot-browser.md)

---

## § O262k-YOUDO-DC-DIAG — spec (closed)

**Owner decision:** RU-only **не вариант** (дорого). DC **раньше заходил нормально** — была «карта + клик», не антибот. Нужен **DC probe**: во что упирается сейчас (HTML/текст), **без RU carousel**.

**Tasks:**

1. Script `scripts/probe_youdo_dc_page.py`: DC proxy slot 1 · listing URL · **Camoufox** (prod) · опц. **Playwright Chromium** compare.
2. Output: `html_len`, snippet 500–800 chars, flags (`servicepipe`, `pokazat_spiskom`, `data_id_count`, map vs list) · save HTML to `data/debug_listings/`.
3. **Не трогать** radar ingest / RU fallback / wall-clock в этом §.
4. Env note: после probe вернуть **DC-first** (`YOUDO_O191_DC_SLOTS=4`, keep `YOUDO_DC_PROXY_URLS`).

**Accept:** один прогон VPS → owner видит **что отдаёт YouDo на DC**.

**Ticket:** [`2026-06-16-youdo-antibot-browser.md`](../../problems/2026-06-16-youdo-antibot-browser.md) § O262k

---

## § O262j — ❌ cancelled (owner: RU дорого, DC path)

~~RU-only / DC_SLOTS=0 / unset YOUDO_DC_PROXY_URLS~~ — отменено.

---

## § O262i-YOUDO-3-CONFLICTS — ⚠️ partial verify (2026-06-17)

**Symptom:** feed YouDo stale · `youdo:ingest done=0 new=0` all evening.

**Prod evidence:**

1. **`YOUDO_O191_DC_SLOTS=0` ineffective** — `_youdo_dc_slot_count()` uses `max(1, int(raw))` → still DC. Cycle 13 `21:15:54 tier=dc`.
2. **`RADAR_CYCLE_WALL_SEC=600` < YouDo outer 750s** — `21:24:08 цикл:watchdog:kill` mid-fetch on RU.
3. **Orphan parse** — `20:12 outcome=ok parsed=50` + wall kill → `youdo:ingest done=0`.

**Last ok:** `19:19:49` RU when `dc_alive=0/4`.

**Lead verify:** pytest **16/16** · deploy ✅ · conflict **#2 fixed** (no watchdog>600 on long RU) · conflict **#1 still broken** on prod → **O262j**.

**Tasks:** allow DC_SLOTS=0 · cycle wall ≥900 · ingest regression test · deploy script.

**Files:** `exchange_proxy.py` · `main.py` · `tests/test_o262i_youdo_conflicts.py`

**Ticket:** [`2026-06-16-youdo-antibot-browser.md`](../../problems/2026-06-16-youdo-antibot-browser.md) § O262i

---

## § O262h-YOUDO-WALL-CLOCK-RACE — ✅ prod deploy (2026-06-17)

**Deploy Lead:** `deploy-o262h-youdo-wall-clock-vps.py` ✅ · env carousel=150 grace=90 · radar+api active.

**Ingest watch:** `grep 'youdo:ingest done'` · `YouDo │ скачано 50` · fetch_every_n=4 (~15–20 мин).

**Ticket:** [`2026-06-16-youdo-antibot-browser.md`](../../problems/2026-06-16-youdo-antibot-browser.md) § O262h

---

## § O262g-YOUDO-STUCK-LEADS — ✅ prod deploy (2026-06-17)

**Deploy Lead:** `deploy-o262g-youdo-stuck-vps.py` ✅ · requeue **500/1000** (limit) · radar+api active · `YOUDO_DETAIL_FETCH=0`.

**Diag prod:** invisible=1000 · was `МИМО:981` `OK:13` `l1_failed:6` · backlog drain `конвейер:L1=20–24`.

**Smoke:** `/lenta/` youdo · повтор requeue для оставшихся 500 при необходимости.

---

## § O262f-YOUDO-FULL-RECOVERY — ✅ deploy (2026-06-17)

**Verify+deploy Lead:** pytest **8/8** ✅ · deploy ✅ `deploy-o262f-youdo-recovery-vps.py` · env O262f on VPS · `ru_early` in code.

**Ingest watch:** last ok probe **17:36** `parsed=50` · post-deploy cycles may still fail — smoke `ru_early` + `kind=ok` 2–3 cycles.

**Ticket:** [`2026-06-16-youdo-antibot-browser.md`](../../problems/2026-06-16-youdo-antibot-browser.md) § O262f

---

## § O262e-YOUDO-ANTIBOT-INGEST — ✅ mechanic partial (2026-06-17)

**Mechanic ✅:** ServicePipe detect/wait + fast-fail · pytest **4/4** · deploy ✅ VPS · `goto_ms` **~4.6s** (было ~98s).

**Prod ingest ❌:** после deploy всё ещё `html_len=1701` · `parsed=0` · last `kind=ok` **14:29** `new=0`. Лог `servicepipe_wait` пока не виден — fast-fail работает.

**Triage ✅:** PG **474** visible youdo · свежие insert часто `is_visible=false` (L1) · owner «нет в ленте» = ingest 🔴 + мало fresh visible.

**→ Full fix owner P0:** § **O262f** above.

**Ticket:** [`2026-06-16-youdo-antibot-browser.md`](../../problems/2026-06-16-youdo-antibot-browser.md) § O262e

---

## § O265b-TG-DRAFT-RATE-LIMIT — ✅ prod (2026-06-17)

**Verify Lead:** pytest **16/16** O265+O50 ✅ · deploy ✅ Lead · VPS `draft_rate_limit_retry_after` in TG path.

---

## § O265-MATCH-PUSH-BOT-4BTN — ✅ prod (2026-06-17)

**Verify Lead:** pytest **16/16** ✅ · deploy ✅ `scripts/deploy-o265-match-push-bot-vps.py` · api+bot-poll active · `o265_ok`.

**Smoke owner:** следующий match-push → 4 кнопки · «Не моё» → `tg:push:nope` · «Отклик» 6-й/час = лимит.

---

## § O262d-YOUDO-LIST-VIEW-SELECTOR — ✅ prod verify (2026-06-17)

**Verify Lead:** pytest **25/25** · deploy ✅ (~15:00 MSK) · prod ingest still 🟡 antibot shell 1712b · last ok **14:29** `new=0` · **→ Mechanic** if next cycles fail after DC unban.

---

## § O262b-YOUDO-LIST-VIEW-TRACE — ⚠️ verify (trace ✅ · click ❌ prod 2026-06-17)

**Verify Lead 2026-06-17 ~14:20 MSK:** pytest **5/5** · deploy ✅ · log `youdo:trace stage=list_view clicked=0 selector=none` (6+ cycles) · `parsed=0` · antibot shell **1712b** (0× «списком»).

**Корень:** клик сразу после `goto` — HTML ещё **1712b** → `force=false` · кнопки нет в DOM. SPA потом не догоняется вторым кликом. **→ O262c** wait+retry.

---

## § O262c-YOUDO-LIST-VIEW-WAIT-RETRY — ✅ prod verify (2026-06-17)

**Verify Lead:** pytest **19/19** · deploy ✅ · **14:29:53** `clicked=1 data_id=50 parsed=50` · intermittent · **→ O262d** selector gate + pass2 on false click.

---

## Closed index (hot summary)

| § | Status |
|---|--------|
| **O265b** TG draft rate limit | ✅ prod **2026-06-17** |
| **O265** match-push bot 4 кнопки | ✅ prod **2026-06-17** |
| **O262f** YouDo full recovery (RU early + carousel) | ⏳ **P0** owner |
| **O262e** YouDo ServicePipe wait/fast-fail | ✅ mechanic partial |
| **O262c** YouDo list-view wait+retry | ✅ prod **2026-06-17** · parsed=50 @14:29 |
| **O262b** YouDo list-view trace + force click | ✅ prod |
| **O262** YouDo map→list click «Показать списком» | ✅ prod · trace ❌ → **O262b** |
| **O261** Parser auto-recovery (FL rotate + YouDo ban-limit + ops) | ✅ prod **2026-06-17** |
| **O254b** ops cache-bust + re-bind | ✅ deploy |
| **O255** YouDo hard reset @ fail 1 + rate cap | ✅ prod |
| **O252** TG content dedup | ✅ prod **2026-06-17** |
| **O250d** push km parity | ✅ prod |
| **O253** JWT session heal | ✅ prod |
| **O250c** push debug/proxy | ✅ prod |
| **O250b** push match parity | ✅ prod |
| **O250** UUID crash | ✅ prod |
| **O237** Yandex Metrika | ✅ prod **1.19.20** · owner smoke ⏸ |
| **O251** repo hygiene | ✅ |
| **O248** TG join v4 | ✅ prod |
| **O247b** quota toolbar | ✅ prod |
| **O247-HOTFIX** | ✅ **1.19.18** |
| **O249** perfect badge | ✅ **1.19.19** prod |
| **O244–O246** | ✅ **1.19.16** |
| **O233** FL auto-recovery | ✅ prod |
| **O256** FL soft antibot + html_snip | ✅ prod |
| **O257** parser stability audit + fixes | ✅ prod **2026-06-16** |
| **O258** playwright chromium + probe cron | ✅ prod **2026-06-16** |
| **O259** YouDo DC carousel (FL pool) | ✅ prod **2026-06-16** |
| **O260** YouDo DC-first tier canon | ✅ prod **2026-06-16** |

---

## § O262-YOUDO-LIST-VIEW — ✅ prod (2026-06-17)

**Intent (owner):** `/tasks-all-opened-all` открывается как **карта**; задания видны только после **«Показать списком»**. Радар ждал `data-id` на карте → `parsed=0`.

**Fix:** `_youdo_click_list_view_if_needed(_async)` перед `_youdo_wait_listing_ready` · log `fetch:youdo stage=list_view_click` · env `YOUDO_LIST_VIEW_CLICK=1` (default).

**Tests:** `tests/test_o262_youdo_list_view.py` **6/6**

**Post-deploy (2026-06-17):** antibot shell **1712b** на VPS **не содержит** «Показать списком» (0× grep) → клик не срабатывает пока antibot. O262 сработает когда страница грузится полностью.

**Deploy:** вместе с O261 (`exchange_browser_fetch.py` + env patch).

---

## § O261-PARSER-AUTO-RECOVERY — ✅ prod (2026-06-17)

**Intent (owner):** парсеры падают и не поднимаются без ручного вмешательства.
Два конкретных бага по логам:
1. **FL** — `ERR_PROXY_CONNECTION_FAILED` на одном DC · пул `alive=4/4` но сайт не открывается · нет авто-rotate
2. **YouDo** — один listing-fetch банит **все 4 DC + node** → `dc_alive=0/4` на **1 час** TTL; авто-unban есть, но ждёт TTL без recovery

Дополнительно:
3. **Кнопка «Сбросить баны» в `/ops/`** вызывает `clear_all_bans()` — сбрасывает **все** биржи включая YouDo. Но кнопка помечена как «FL» — вводит в заблуждение. Нужно добавить **отдельную кнопку «Сбросить баны YouDo»**.

**Ticket:** [`docs/problems/2026-06-16-youdo-antibot-browser.md`](../../problems/2026-06-16-youdo-antibot-browser.md) § O261

**Логи подтверждающие баги:**
```
# FL bug (2026-06-17):
fetch:fl  ERR_PROXY_CONNECTION_FAILED  proxy_hint=194.226.236.204:8000  alive=4/4
fetch:fl  stage=fallback httpx  outcome=fail  cascade exhausted
listing:fl  parsed=0  (7 циклов подряд, слот не переключился)

# YouDo bug (2026-06-17):
dc_alive=0/4 · youdo_bans=8 (4 DC + 3 node) · TTL left ~35 min
один fetch: DC1→DC2→DC3→DC4→node1 все SPA → dc_alive=0 на 1ч
```

**Read first:** `exchange_proxy.py` `_ban_url`, `_prune_expired_bans`, `youdo_dc_alive_urls`, `_BAN_TTL_SEC` ·
`exchange_browser_fetch.py` `fetch_listing_html_browser_slots` ·
`fl_parser.py` `_fl_allow_httpx_fallback` ·
`proxy_ops.py` `run_proxy_control` `clear-bans` ·
`owner_admin.py` рендер кнопок прокси (`_render_proxy_slot_actions`, `rl-proxy-clear-bans`)

### Scope

**Fix 1 — FL connection failed → rotate DC**

- В `exchange_browser_fetch.py` slot loop (FL path): `ERR_PROXY_CONNECTION_FAILED` или `net::ERR_PROXY` → treat as dead-slot → **ban FL slot** (short TTL `FL_DEAD_PROXY_BAN_TTL_SEC` default **300** сек) + **retry next DC** (как YouDo carousel)
- Не путать с antibot (которое сейчас жжёт через `_fl_browser_antibot_fail` с hard reset)
- Log: `fetch:fl stage=dead_proxy_rotate slot=N proxy_hint=…`
- httpx fallback тоже должен пробовать **следующий DC** если cascade exhausted on same slot

**Fix 2 — YouDo: max 1 DC-ban per listing fetch**

- В slot loop YouDo: если SPA → ban **только текущий слот** · stop after `YOUDO_MAX_DC_BANS_PER_FETCH=2` bans in one fetch (не выжигать весь пул)
- Оставшиеся DC: попробовать в **следующем цикле** (через `fetch_every_n`), не в этом же fetch
- Log: `fetch:youdo stage=dc_ban_limit_reached bans_this_fetch=N dc_alive=M/4`

**Fix 3 — YouDo: auto-unban DC при dc_alive=0**

- В `youdo_parser.py` или `exchange_proxy.py`: если `dc_alive=0` **более `YOUDO_AUTO_UNBAN_MIN` минут** (default **20**) → вызвать `clear_youdo_source_bans(dc_only=True)` + `youdo_hard_reset` + log `fetch:youdo tier=dc_auto_unban`
- `dc_only=True` — не сбрасывать node-proxy баны (они отдельные, менее ценные)
- Таймер: SQLite key `youdo_dc_banned_since` — пишем при переходе `dc_alive 1→0`, читаем при каждом fetch_begin

**Fix 4 — Ops кнопки: YouDo bans отдельно**

- `proxy_ops.py`: добавить action `"clear-youdo-bans"` → вызывает `clear_youdo_source_bans()` + `youdo_hard_reset`
- `owner_admin.py`: рядом с существующей кнопкой «Сбросить баны» (которая all) добавить кнопку **«Сбросить баны YouDo»** — action `clear-youdo-bans` · только в секции YouDo или proxies
- JS: `ops-pult.js` — обработчик для новой кнопки (как у `rl-proxy-clear-bans`)
- Log на сервере: `ops: youdo bans cleared N`

### Tests

`tests/test_o261_parser_auto_recovery.py`:
- FL dead proxy → ban short TTL + rotate to next DC (не antibot path)
- YouDo: после `YOUDO_MAX_DC_BANS_PER_FETCH=1` — второй DC не банится в том же fetch
- YouDo: `dc_alive=0` > `YOUDO_AUTO_UNBAN_MIN` → auto-unban + hard_reset triggered
- Ops `clear-youdo-bans` → только youdo:* bans cleared · fl:* intact

### Deploy

`scripts/deploy-o261-parser-auto-recovery-vps.py`:
- Upload `src/exchange_proxy.py` · `src/exchange_browser_fetch.py` · `src/youdo_parser.py` · `src/proxy_ops.py` · `src/owner_admin.py` · `src/static/ops-pult.js`
- `.env.site` patch: `YOUDO_MAX_DC_BANS_PER_FETCH=2` · `YOUDO_AUTO_UNBAN_MIN=20` · `FL_DEAD_PROXY_BAN_TTL_SEC=300`
- Restart radar · verify: `fetch:fl tier=dc` on all 4 slots · `fetch:youdo dc_alive` not 0 after clear

**Do not break:** O260 DC-first · O255 hard reset rate cap · O257 httpx fallback · O259 carousel · FL antibot path (soft reset streak)

**DoD:**
- FL: `ERR_PROXY_CONNECTION_FAILED` → log `dead_proxy_rotate` + next DC · no manual action needed
- YouDo: single fetch бан ≤ `YOUDO_MAX_DC_BANS_PER_FETCH` DC · `dc_alive=0` > 20 мин → auto clear + log
- `/ops/` кнопка «Сбросить баны YouDo» работает отдельно от FL
- pytest `test_o261_*` green · `.env.example` documented

---

## § O260-YOUDO-DC-FIRST-CANON — ✅ prod (2026-06-16)

**Intent (owner):** после O259 карусель DC работает на retry, но **первый слот listing = node-proxy** (`gate.node-proxy.com`) — жжёт residential-трафик · нет денег на постоянный RU. Канон: **DC primary (4 как FL) → RU/node только если все DC в ban или исчерпаны в fetch → автоматически обратно на DC когда ban TTL прошёл**.

**Symptom (prod 2026-06-16 post-O259):**
```
fetch:youdo proxy=gate.node-proxy.com:10004 slot=6/26 alive=26/26   # log
youdo:trace stage=slot_retry proxy_hint=194.226.236.204:8000      # DC only on retry
fetch:youdo outcome=ok parsed=50                                  # sometimes on node, not DC
```
Owner policy (unchanged): residential **extreme fallback only** · node-proxy слоты делят **общий traffic quota** — не жечь RU · при «банах летят» на DC → **hard reset + следующий DC**, не node.

**Root cause (Lead verify):**
1. `_active_slot["youdo"]` индексирует **полный** `YOUDO_PROXY_URLS` (DC+26×node) — persisted slot=6 → node в `proxy_log_hint` / ops.
2. `exchange_primary_proxy_url("youdo")` частично чинит fetch (возвращает `dc_alive[0]`), но **логи/ops/funnel** показывают node · `_slot_index` на full list может снова выбрать RU когда node не banned.
3. После RU-fallback **нет realign** на DC при `_prune_expired_bans` / новом цикле — остаёмся на node tier.
4. `youdo_browser_slot_urls()` append `ru_alive` в тот же список — при `YOUDO_SLOT_RETRY_ON_TIMEOUT=3` RU может попасть в retry **до** исчерпания всех DC (если dc_alive мало).

**Ticket:** [`docs/problems/2026-06-16-youdo-antibot-browser.md`](../../problems/2026-06-16-youdo-antibot-browser.md) § O260

**Read first:** `exchange_proxy.py` — `_youdo_dc_pool`, `_youdo_ru_pool`, `youdo_browser_slot_urls`, `exchange_primary_proxy_url`, `proxy_log_hint`, `_pool_status_slice`, `_prune_expired_bans`, `youdo_browser_slot_fail` · `exchange_browser_fetch.py` slot loop ~2118 · O259 tests.

### Canon (must implement)

```
Listing fetch:
  tier=dc  → rotate YOUDO_DC_PROXY_URLS (4 FL DC) · ban youdo:host on SPA
  DC fetch исчерпан (все слоты fetch fail) но dc_alive>0:
    → youdo_hard_reset (camoufox teardown) + следующий alive DC · log tier=dc_hard_reset
    → НЕ tier=ru · не ждать пока dc_alive=0 если ещё есть живые DC
  tier=ru  → ONLY if youdo_dc_alive=0/4 (все DC в ban) · max 1 node slot за fetch · log tier=ru_fallback
    (node slots share traffic quota — один порт, не карусель по RU)
  ban TTL expires (EXCHANGE_PROXY_BAN_TTL_SEC, default 1h):
    → realign active slot to first alive DC · log fetch:youdo tier=dc_restored
  NEVER: node/RU as slot 1 when youdo_dc_alive>0
```

### Scope

1. **Separate tier indexing (code)**
   - `_active_slot` для youdo: индекс только в **DC pool** (`_youdo_dc_pool`), не в full `YOUDO_PROXY_URLS`.
   - Новый helper `youdo_listing_slot_urls(*, include_ru: bool)` → ordered `[dc…]` или `[dc…]+[ru…]` только когда `include_ru=True`.
   - `exchange_primary_proxy_url("youdo")` → first alive DC from DC pool rotation; **never** RU if `youdo_dc_alive_urls()` non-empty.
   - `proxy_log_hint("youdo")` → `host:port tier=dc slot=i/4 alive=a/4` (DC pool metrics) · отдельно `ru_alive=n` if needed · **не** slot=6/26 full list.

2. **Fetch slot builder**
   - Phase 1 = **DC only** (up to `YOUDO_DC_RETRY_MAX=4` or `YOUDO_SLOT_RETRY_ON_TIMEOUT`).
   - Phase 1 all failed **and** `youdo_dc_alive>0` → **`youdo_hard_reset`** (O255 rate cap ok) + **one** retry pass on next alive DC(s) in same cycle — log `tier=dc_hard_reset` · **no RU**.
   - Phase 2 = **max 1 RU slot** (`YOUDO_RU_RETRY_MAX=1`) **only if** `youdo_dc_alive=0/4` after phase 1 + hard reset retry.
   - Log each attempt: `fetch:youdo tier=dc|dc_hard_reset|ru|dc_restored proxy_hint=… slot=n`.

3. **Hard reset vs RU (owner 2026-06-16)**
   - Revise O259 `_on_youdo_fetch_fail`: skip hard reset **only** while DC carousel still has untried slots **in current fetch**; after all DC slots in fetch failed → **allow hard reset even if `dc_alive>0`** (баны полетели — новое лицо + другой DC).
   - Hard reset **never** substitutes for RU when `dc_alive=0` — там tier=ru (1 slot max).
   - RU pool: **no multi-slot carousel** — shared traffic quota; one attempt per fetch max.

4. **DC restore after ban TTL**
   - In `_prune_expired_bans()` or `exchange_fetch_begin("youdo")`: if `youdo_dc_alive_urls()` became non-empty after prune → `youdo_realign_to_dc_tier()`.
   - Log: `fetch:youdo tier=dc_restored dc_alive=N/4`.

5. **youdo_browser_slot_fail**
   - DC fail → ban + advance within DC pool only.
   - RU fail → ban RU slot · **do not** set active DC index to RU position in full list.
   - When last DC banned → allow RU for **this fetch only** (max 1); next cycle after TTL → dc_restored.

6. **Ops / status**
   - `_pool_status_slice` / cascade for youdo: show **DC pool** (4) + `ru_pool_alive` separately — not merged 26/26 misleading green.

7. **Deploy + VPS env**
   - `scripts/deploy-o260-youdo-dc-first-vps.py`:
     - Upload touched `src/` · patch `.env.site` if needed:
       - `YOUDO_DC_PROXY_URLS` = FL 4 DC (already from O259)
       - `YOUDO_O191_DC_SLOTS=4`
       - optional `YOUDO_RU_RETRY_MAX=1`
     - On deploy: run `youdo_realign_to_dc_tier()` once (or reset active slot) · restart radar.
     - Verify: next `fetch:youdo` log shows `tier=dc` · **not** `gate.node-proxy` as slot 1 unless `dc_alive=0/4`.

8. **Tests** `tests/test_o260_youdo_dc_first.py`
   - dc_alive>0 → primary + slot1 never in `_youdo_ru_pool`.
   - all DC slots fail in fetch but dc_alive>0 → `tier=dc_hard_reset` · no RU.
   - all DC banned (dc_alive=0) → one RU retry · log tier=ru_fallback.
   - simulate ban expiry → `dc_restored` · primary back to DC.
   - `proxy_log_hint` shows dc slot 1/4 not 6/26.
   - FL bans untouched · O259 carousel tests still green.

**Do not break:** O259 DC carousel · O255 rate cap / hourly cap · O257 ru_pool_dead skip · probe cron.

**DoD:**
- Prod: `dc_alive>=1` → **zero** `tier=ru` on slot 1 · hard reset ok when DC fetch exhausted (`tier=dc_hard_reset`).
- `dc_alive=0/4` → max 1 `tier=ru` · after TTL → `tier=dc_restored`.
- pytest `test_o260_*` + `test_o259_*` green.
- `.env.example` document tier env vars.

---

## § O259-YOUDO-DC-CAROUSEL — ✅ prod (2026-06-16)

**Intent (owner):** YouDo падает `SPA shell without task cards` на **том же camoufox + DC IP** после O255 hard_reset. Имеет смысл **крутить те же 4 DC, что FL**, до RU tier — не жечь residential.

**Context (prod 2026-06-16):**
```
fetch:youdo outcome=fail reason=browser  # SPA shell
youdo:trace stage=hard_reset fail_streak=1
fetch:youdo proxy=185.147…  # часто 1 DC; FL крутит 4
```
FL и YouDo bans **раздельные** (`fl:host:port` vs `youdo:host:port`) — общий физический IP ok.

**Ticket:** [`docs/problems/2026-06-16-youdo-antibot-browser.md`](../../problems/2026-06-16-youdo-antibot-browser.md) § O259

**Read first:** `exchange_proxy.py` `_youdo_dc_pool` · `youdo_browser_slot_urls` · `youdo_browser_slot_fail` · `exchange_browser_fetch.py` `_is_youdo_slot_retryable` · slot loop ~L2119–2240 · O255 hard_reset in `youdo_parser.py`.

### Scope

1. **DC pool = FL DC (env, не merge в коде)**
   - На VPS `.env.site`: `YOUDO_DC_PROXY_URLS` = те же 4 URL, что `FL_PROXY_URLS` (copy-paste, без RU).
   - `YOUDO_O191_DC_SLOTS=4` (или auto = `len(YOUDO_DC_PROXY_URLS)`).
   - `YOUDO_PROXY_URLS` = DC×4 + RU tail (node-proxy) без изменения RU policy.
   - **Do not** share ban tables with FL · **do not** auto-ban FL when YouDo fails.

2. **Carousel policy (DC before hard_reset)**
   - При `SPA shell` / antibot HtmlFetchError на listing: **ban `youdo:slot` + slot_retry следующий DC** в том же fetch (до `YOUDO_SLOT_RETRY_ON_TIMEOUT`, default 3).
   - Fix if missing: `_is_youdo_slot_retryable` must match **`spa shell`** (сейчас `SPA shell without task cards` может **не** matсhить `antibot` marker — verify in code).
   - `youdo_browser_slot_fail`: ban/advance по **DC pool** (`_youdo_dc_pool`), не по full `YOUDO_PROXY_URLS` — иначе RU попадает в carousel раньше policy O191.
   - **Hard reset (O255)** только после исчерпания DC retry в цикле **или** все `youdo_dc_alive=0` — не на fail@1 с тем же единственным DC.
   - Log: `fetch:youdo stage=dc_rotate slot=N proxy_hint=… reason=spa_shell` · `fetch:youdo dc_alive=N/4`.

3. **Residential tier (unchanged)**
   - RU только после DC exhausted / `slot_retry` на RU (O191) · если `youdo_ru_alive_urls()` empty → `fetch:youdo reason=ru_pool_dead` (O257).
   - **No** поднятие RU в primary из-за SPA на одном DC.

4. **Tests**
   - `tests/test_o259_youdo_dc_carousel.py`:
     - DC pool 4 · fail slot1 SPA → ban youdo:1 · retry slot2 without hard_reset.
     - `SPA shell without task cards` → retryable.
     - DC all banned → hard_reset path or pool_exhausted (mock).
     - FL ban table untouched when YouDo bans same host:port.
   - Extend O255/O257 suites · green.

5. **Deploy**
   - `scripts/deploy-o259-youdo-dc-carousel-vps.py`:
     - Patch `.env.site` lines (YOUDO_DC*, YOUDO_O191_DC_SLOTS) — **no secrets in script**; read from local `.env` or prompt owner vars.
     - Upload touched `src/` · restart radar · one `restart_radar_youdo_cycle.py` or wait 1 cycle.
     - Print: `youdo_dc_alive=` · last 5 `fetch:youdo` lines.

**Do not break:** O255 rate cap / hourly cap · O254 camoufox teardown · O257 fetch outcome logs · FL DC pool / httpx fallback · probe cron O258.

**DoD:**
- Prod: при SPA на DC1 log показывает rotate на DC2+ **до** `hard_reset` (или `parsed>0` на другом DC).
- `youdo_dc_alive` до 4/4 на старте · RU не используется пока жив хотя бы 1 DC.
- pytest `test_o259_*` green · `.env.example` documented.

---

## § O258-PLAYWRIGHT-PROBE-CRON — ✅ prod (2026-06-16)

**Intent (owner):** после O257 FL живёт на httpx fallback · на VPS **нет** Playwright chromium (`BrowserType.launch: Executable doesn't exist`). Нужно: (1) починить browser-path · (2) **cron probe** → алерт в **@FLPARSINGBOT** до того как owner заметит утром.

**Context (O257 prod):**
```
fetch:fl outcome=fail reason=browser_error err=... chromium_headless_shell-1208 ... Executable doesn't exist
fetch:fl stage=fallback httpx outcome=ok → parsed=30
```
Residential **не трогать** — DC primary · res только когда `alive=0` DC (TTL 1h) · см. `exchange_proxy.py` `_fl_pool_triple`.

**Ticket:** [`docs/problems/2026-06-16-parser-stability-audit.md`](../../problems/2026-06-16-parser-stability-audit.md) § O258

### Scope

1. **Playwright chromium on VPS (site profile)**
   - In deploy script: `sudo -u rawlead` from `/opt/rawlead`: `.venv/bin/playwright install chromium` (+ `install-deps` if needed, non-interactive).
   - Smoke: `sudo -u rawlead .venv/bin/python -c "from playwright.sync_api sync_playwright; ... launch chromium"` → OK.
   - Pin/note playwright version in deploy output (match `requirements.txt`).
   - **Do not** reinstall on every deploy — idempotent check (skip if binary exists).

2. **Probe alert script**
   - Extend `scripts/probe_parsers_health_vps.py` **or** add `scripts/probe_parsers_health_alert_vps.py`:
     - Run existing probe logic (read `radar_site.log` tail · `fetch:{fl,kwork,youdo} outcome=`).
     - If `status=fail` OR source `outcome=fail` with `reason` not in allowlist (`browser_error` ok if subsequent httpx ok in same cycle — see below) → send via `health_check.send_flparsing_admin_text`.
     - Message prefix: `FLPARSING · парсеры` · include per-source: outcome, reason, parsed, last line snippet.
     - Cooldown: `PARSER_PROBE_ALERT_COOLDOWN_SEC` default **1800** (30 min) via SQLite setting or file lock — no spam.
     - **FL special:** if last line is `outcome=fail reason=browser_error` but same cycle has `stage=fallback httpx outcome=ok` → treat FL as **ok** (O257 design).

3. **Cron / systemd timer on VPS**
   - Add `scripts/install-parser-probe-cron-vps.py` or document in deploy script:
     - Run every **15 min**: `sudo -u rawlead env RADAR_PROFILE=site PYTHONPATH=... python scripts/probe_parsers_health_alert_vps.py`
     - Log to `/opt/rawlead/data/parser_probe.log` (rotate ok).
   - Deploy script runs install once.

4. **Tests**
   - `tests/test_o258_probe_alert_logic.py` — mock log lines: browser fail + httpx ok → no alert; sustained fail → alert payload.
   - pytest green with O257 suite.

5. **Deploy**
   - `scripts/deploy-o258-playwright-probe-vps.py` — chromium install if missing · upload probe/alert scripts · install cron · run probe once · print summary.

**Do not break:** O257 httpx auto fallback · residential tier rules · O255/O254 YouDo · FLPARSING bot identity check in `send_flparsing_admin_text`.

**DoD:**
- VPS: `playwright install chromium` OK for rawlead · FL browser subprocess succeeds OR explicit log if still fail.
- Cron active · manual run sends **no** alert when FL ok via httpx.
- Manual run **does** alert when e.g. `fetch:youdo outcome=fail` sustained 30+ min (use test log fixture in unit test; prod verify optional).
- `.env.example` lines for cooldown env if added.

---

## § O257-PARSER-STABILITY-AUDIT — ✅ prod (2026-06-16)

**Intent (owner):** parsers fall daily · need **audit + prod-grade stability** · clear logs · no silent `parsed=0` · fewer orphan processes · tools to catch before owner wakes up.

**Ticket:** [`docs/problems/2026-06-16-parser-stability-audit.md`](../../problems/2026-06-16-parser-stability-audit.md)

**Read first:** ticket TL;DR · `fl_parser.py` `_fl_allow_httpx_fallback` · `main.py` `restart_source_*` · `exchange_browser_fetch.py` `fl_hard_reset` · prod log samples in ticket.

### Phase 1 — Audit (deliverable: update ticket § A–D)

1. Map fetch/recovery/process paths for **fl / kwork / youdo** (table in ticket).  
2. List **conflicting recovery** (e.g. O256 → `fl_hard_reset` → `restart_source_fl` → context close every cycle while subprocess still empty).  
3. Add **`scripts/audit_parser_processes_vps.py`** — SSH/local safe · counts worker/camoufox/chromium pids · no secrets · stdout report.

### Phase 2 — FL P0 fixes (must ship)

1. **Auto httpx fallback** when browser/subprocess returns `None`/empty OR raises `HtmlFetchError` — **do not rely on** `FL_HTTPX_FALLBACK=1` env alone. Log: `fetch:fl stage=fallback httpx outcome=ok|fail`.  
   - Rationale: VPS curl 200 ~330KB · `FL_LISTING_SUBPROCESS=1` currently **disables** httpx (O210) — mismatch with `FOR_YOU.md` / `RUN.md`.  
2. **Fix restart loop:** `fl_hard_reset` / O256 soft reset — teardown inline; **do not** set `restart_source_fl=1` if that causes pre-fetch context wipe loop without fixing subprocess. Document chosen behavior in ticket.  
3. **Pipeline log every FL failure:** `fetch:fl outcome=fail reason=<code> proxy_hint=... stderr_tail=...` in `radar_site.log` (not journal-only).  
4. Subprocess fail: include last JSON line / stderr tail in pipeline log.

### Phase 3 — Observability (same PR if small)

1. Standard **`fetch:{src} outcome=... reason=...`** for fl/kwork/youdo listing fetch end.  
2. **`/ops/`** exchanges row: expose `last_fail_reason` (from health/settings or last log parse).  
3. **`scripts/probe_parsers_health_vps.py`** — runs listing smoke (or reads last 3 cycles from log) · exit 0/1 · JSON for Lead · document in ticket § E.

### Phase 4 — YouDo hardening (same PR or follow-up commit)

1. Before RU slot_retry: if `youdo_ru_alive_urls()` empty or probe fails → **skip RU tier** · log `fetch:youdo reason=ru_pool_dead`.  
2. `youdo:trace fetch_end` include `reason=` when `parsed=0` (browser_empty, antibot, cooldown, …).

### Tests

- `tests/test_o257_fl_httpx_fallback_on_browser_fail.py` — mock browser fail → httpx returns HTML → parsed>0  
- `tests/test_o257_fetch_outcome_log.py` — pipeline line format  
- `tests/test_o257_restart_source_no_loop.py` — soft reset does not infinite restart_source  
- Extend existing FL/YouDo tests · do not break O255/O256 suites

### Deploy

- **`scripts/deploy-o257-parser-stability-vps.py`** — upload touched `src/` + scripts · restart radar · run probe · print last 5 `fetch:* outcome=` lines  
- **`.env.example`** — document new env if any; prefer **sensible defaults** over owner manual flags

**Do not break:** O255 YouDo rate cap · O254 teardown · O252 scope · TG · push · ops restart buttons

**DoD:**

- Ticket § A–D filled · § Verify checkboxes ticked by Coder  
- Prod: `listing:fl parsed>=25` ≥3 cycles **or** explicit `outcome=fail reason=` with actionable text  
- `pytest tests/test_o257_* -q` green · probe script documented  
- Lead can run deploy script + probe without reading code

---

## § O256-FL-ANTIBOT-SOFT-DETECT — ✅ prod (2026-06-16)

**Intent (owner):** FL крутится вхолостую при `parsed=0 alive=4/4` — freelance.ru отдаёт antibot HTML, прокси не банится, O233 не триггерит. Нужен детект «soft antibot» и hard reset без ban.

**Ticket:** [`docs/problems/2026-06-16-fl-parsed-zero-no-proxy-ban.md`](../../problems/2026-06-16-fl-parsed-zero-no-proxy-ban.md)

**Also write deploy script:** `scripts/deploy-o256-fl-antibot-vps.py` (uploads `fl_parser.py` + `radar_status.py` + restart radar) — Coder пишет, Lead деплоит.

**Scope:**

1. **`fl_parser.py`:** при `parsed=0 streak >= 5 AND bans_cleared == 0` → вызвать `fl_hard_reset()` + выставить `restart_source_fl` в storage (как при proxy ban). Log: `fl_listing:soft_antibot_reset streak=N`.
2. **`fl_parser.py`:** при каждом `parsed=0` (browser fetch) — log первые 300 байт ответа: `fl_listing:html_snip snip=<encoded[:300]>`. Позволяет за 5 сек понять «captcha» vs «пустая выдача».
3. **`radar_status.py`:** `parsed=0 streak > 10 AND bans_cleared=0` → статус 🔴 `antibot_soft` (отдельно от `pool_exhausted`).
4. **`deploy-o256-fl-antibot-vps.py`:** загрузить `src/fl_parser.py` + `src/radar_status.py` → restart radar → verify `listing:fl` в логе.

**Do not break:** O233 auto-recovery (ban path) · O215 two-tier proxy · O222 hard reset on ban · proxy ban TTL.

**Files:** `src/fl_parser.py` · `src/radar_status.py` · `scripts/deploy-o256-fl-antibot-vps.py` · tests

**DoD:** `listing:fl parsed=0 streak=5 bans_cleared=0` → log `fl_listing:soft_antibot_reset` + `restart_source_fl` установлен · log `fl_listing:html_snip` при каждом parsed=0 · 🔴 antibot_soft в /ops/ при streak>10.

---

## § O255-YOUDO-HARD-RESET-1 — ✅ code · deploy ⏳ (P1, owner 2026-06-16)

**Intent (owner):** как FL browser fail — **с первого провала** hard reset («новое лицо»), без 30+30 мин cooldown на fail 1–2. **Подстраховка** от бесконечного hammering.

**Ticket:** [`docs/problems/2026-06-16-youdo-antibot-browser.md`](../../problems/2026-06-16-youdo-antibot-browser.md)

**Scope:**

1. **Default** `YOUDO_HARD_RESET_FAILS=1` (env override ok) · убрать ветку `set_youdo_cooldown(30min)` когда срабатывает auto hard reset.
2. **Rate limit между auto hard reset:** `YOUDO_HARD_RESET_MIN_SEC` (default **120**). SQLite `youdo_last_hard_reset_at`. Если fail → hard reset, но с прошлого reset < MIN_SEC → **короткий cooldown** `YOUDO_SHORT_COOLDOWN_MIN` (default **5**), log `hard_reset_rate_limited` · **не** 30 min.
3. **Hourly cap:** `YOUDO_HARD_RESET_MAX_PER_HOUR` (default **8**). Счётчик в settings (rolling hour ok). При превышении → существующий **traffic_guard** (~90 min), log `hard_reset_hourly_cap` · **не** hard reset.
4. На каждом успешном auto hard reset: bump hourly counter · update `youdo_last_hard_reset_at` · existing teardown unchanged.
5. **`.env.example`** + prod `.env.site` lines (deploy note for Lead):
   - `YOUDO_HARD_RESET_FAILS=1`
   - `YOUDO_HARD_RESET_MIN_SEC=120`
   - `YOUDO_HARD_RESET_MAX_PER_HOUR=8`
   - `YOUDO_SHORT_COOLDOWN_MIN=5`
6. **pytest** `tests/test_o254_youdo_restart.py` extend or `tests/test_o255_youdo_hard_reset_rate.py` — fail@1 reset · rate limit → short cooldown · hourly cap → guard.

**Do not break:** ops `/ops/` manual restart · O254 teardown · traffic_guard on non-reset path · `fetch_every_n`.

**Already in place (no code):** `fetch_every_n=4` · `invalidate_browser_slot` on fail · ops button + radar restart.

**Files:** `src/youdo_parser.py` · `.env.example` · tests

**DoD:** deploy radar · log on fail: `hard_reset reason=auto_fail_streak=1` OR `hard_reset_rate_limited` · no 30min cooldown on first browser/antibot fail.

---

## § O254b-OPS-RESTART-CACHE-BUST — ✅ deploy (2026-06-16)

**Ticket:** [`docs/problems/2026-06-16-youdo-antibot-browser.md`](../../problems/2026-06-16-youdo-antibot-browser.md) § post-deploy triage

**Symptom:** O254 deploy ✅ · owner: кнопка «Перезапустить источник» мёртвая · nginx **0×** `POST /ops/control` · `hard_reset` в journal нет.

**Root cause (Lead verify):** prod отдаёт новый JS, но вкладка до deploy держит старый `ops-pult.js` (polling funnel не reload script). Delegation bind один раз при load — после hydrate не перепривязывается (belt: re-bind).

**Scope:**
1. `owner_admin.py` — `<script src="/ops/static/ops-pult.js?v=…">` (`_VERSION` или mtime)
2. `ops-pult.js` — вызов `bindRestartSourceDelegation()` в конце `hydrateDashboardFallback` `.then` (после `exEl.innerHTML = renderExchangesHtml`)
3. pytest не обязателен · smoke: deploy api → owner Ctrl+Shift+R → POST в nginx · journal `fetch:youdo hard_reset`

**Do not break:** O205 shell hydrate · existing `.rl-ctl` handlers

**Files:** `src/owner_admin.py` · `src/static/ops-pult.js`

---

## § O254-OPS-YOUDO-RESTART — ✅ deploy (smoke partial)

**Ticket:** [`docs/problems/2026-06-16-youdo-antibot-browser.md`](../../problems/2026-06-16-youdo-antibot-browser.md)

**Prod:** 5 files · api+radar restart 04:36 UTC · grep OK · prod JS has delegation.

**Owner smoke:** ❌ button · YouDo ingest still `Connection closed` → **O254b** + **@mechanic**

---

## § O252-TG-CONTENT-DEDUP — ✅ code · deploy ⏳ (P1)

**Symptom:** duplicate TG cards same text · [`2026-06-15-push-down-tg-dedup.md`](../../problems/2026-06-15-push-down-tg-dedup.md)

**Scope:** content_hash conflict → `dup_abort` · no `content_hash=""` retry · pytest · deploy API+radar.

**DoD:** one post → one card in `/lenta/`.

**Files:** `lead_pipeline.py` · `tests/test_tg_content_dedup_o252.py`

---

## § O237-YANDEX-METRIKA — ✅ code · theme deploy ⏳

**Counter:** `109860210` · owner snippet → [`FOR_YOU.md`](../../FOR_YOU.md).

**Scope:** `inc/yandex-metrika.php` · goals quiz/trial/checkout · theme **1.19.20** · skip local + `/ops/`.

**Deploy:** `scripts/deploy-o237-metrika-vps.py` or `deploy-wp-theme-vps.py` · wp-config `YANDEX_METRIKA_ID`.

**DoD:** view-source `/lenta/` → tag id 109860210 · goals fire in Metrika.

---

## § O200-L2 — queued (волна 4)

Regen judge ≥70%×4 · see archive § O200.

---

## Archive pointer

O250/O250b/O250c/O250d/O253 full specs → [`CODER_PROMPT_ARCHIVE`](../archive/CODER_PROMPT_ARCHIVE.md) (hot trim 2026-06-16).

O251 REPO_HYGIENE → [`docs/ops/REPO_HYGIENE.md`](../../ops/REPO_HYGIENE.md) ✅ done.
