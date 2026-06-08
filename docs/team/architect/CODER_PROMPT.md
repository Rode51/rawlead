# Coder — горячий контур (активное)

**→ Сейчас:** **O135 ✅ deploy** · owner smoke draft + OR proxy env · Wave 2 **⏸**

---

## § O135-DRAFT ✅ (2026-06-08)

| A L2-only 1-й | B draft_async restart | C OR proxy | Deploy |
|---------------|----------------------|------------|--------|
| skip L3 cold · `first_user_l2_only` | `lead_draft_jobs` + `draft:restart` | `OPENROUTER_HTTP_PROXY` / `OPENROUTER_PROXY_URLS` | **`deploy-o135-vps.py` ✅** |

**Verify Lead:** pytest **18/18** (o135 + draft_async + shared_draft) · spec **5/5** ✅

**Owner next:** опц. `OPENROUTER_HTTP_PROXY=<1-й YOUDO_PROXY_URLS>` · smoke `/lenta/?lead=15146` · `preprod_draft_burst --max-leads 3`

---

## § O135-DRAFT — archive spec (**✅ закрыто**)

**Симптом owner 2026-06-08:** Premium `/lenta/?lead=15146` → **«ИИ не успел — повторите»** (poll 120s) · lead #15146 kwork OK visible · `reply_draft` NULL · log `Черновик ещё не запущен` после restart API.

**Корень (Lead):**
1. **1-й пользователь:** L2 (human, pro) + **лишний L3** → p95 ~105s · UI timeout
2. **draft_async:** in-memory worker теряется при restart API · GET poll → failed «не запущен»
3. **OpenRouter:** `DIRECT_REQUESTS_PROXIES` с IP Beget VPS · без прокси · возможен latency/rate-limit

**Решение owner:** 1-й Premium = **только L2** · 2-й+ = L3 · OpenRouter proxy **без новых покупок** — `YOUDO_PROXY_URLS` (residential RU) или **acc2/acc3** Telethon · **не** bot `TG_PROXY_URL`.

### Copy-paste для @coder

```
@coder O135-DRAFT

Спека: docs/team/architect/CODER_PROMPT.md § O135-DRAFT
Lead verify: lead #15146 · journalctl rawlead-api | grep lenta:draft

Контекст: L2 уже human (l3_human_style shared L2). Сейчас 1-й user = L2+L3 = слишком долго.
Не трогать: FL/Kwork listing proxy · radar ingest · WP theme copy · mass regen.

## A — 1-й пользователь: L2-only (skip L3)
Файл: src/match_push.py `generate_and_store_lead_draft`

После успешного cold L2 + UPDATE leads.reply_draft:
- INSERT user_lead_replies с **текстом L2 as-is**
- **НЕ** вызывать `_build_personalized_reply` для первого user на этом lead
- Log: `lenta:draft:{id}:first_user_l2_only`

2-й+ без изменений: `shared` есть → только L3 (`fast_shared`).

DoD: cold lead p95 target **< 75s** (1 LLM) · warm **< 20s** (L3 only).

## B — draft_async: не терять job после restart
Файл: src/draft_async.py (+ api_server если нужно)

1. `poll_draft` GET: status failed «Черновик ещё не запущен» → **pending + auto `_start_worker`** (или 202, не terminal fail)
2. POST idempotent: если `lead_draft_jobs.pending` и worker dead → restart worker
3. Wire `_insert_lead_pending` / `_set_lead_job_failed` / `_delete_lead_job` (сейчас dead code)
4. Worker `max_retries=2` (не 4) — как hot path O131

Log: `draft:restart lead=N` · `draft:worker_done lead=N ms=M`

## C — OpenRouter proxy (отдельный пул, owner без новых IP)

Файлы: `src/config.py` · `src/ai_analyze.py` (`_openrouter_chat` + L3 POST)

**Owner constraint:** новых прокси нет. Кандидаты (owner пропишет в `.env` **вручную**, код только читает):

| Приоритет | Env | Откуда |
|-----------|-----|--------|
| **1** | `OPENROUTER_HTTP_PROXY=` | **1-й слот `YOUDO_PROXY_URLS`** (residential RU, node-proxy) |
| **2** | `OPENROUTER_PROXY_URLS=` | `TELETHON_PROXY_ACC2` и/или `ACC3` (rotate on 429) |

**Запрещено:**
- автоподключать `tg_proxy_pool` / failover бота — OpenRouter **свой** пул, не трогает active Bot slot
- **`TG_PROXY_URL` / acc1 primary** — бот живёт там
- **`EXCHANGE_PROXY_URLS`** / FL listing pool
- менять `.env` из кода

Поведение:
- L2/L3 on-demand → proxy если env · иначе DIRECT VPS
- Startup API: `openrouter:proxy=hint|direct` (host:port без creds)
- Log fail: `OpenRouter HTTP N via hint`

Owner smoke после deploy: с `OPENROUTER_HTTP_PROXY=<youdo slot>` → draft #15146 < 90s. Если хуже direct — unset, оставить A+B.

## D — hot path L2 trim (если всё ещё >75s)
- `analyze_shared_reply_draft` on-demand: max **2** outer attempts (не 4) когда вызов из `generate_and_store_lead_draft`
- `timeout_sec=90` оставить · smell-retry **1** retry max on hot path
- Не трогать backlog/regen path

## E — deploy + tests
- scripts/deploy-o135-vps.py → rawlead-api restart
- tests: first_user_l2_only skips L3 · poll restart · openrouter proxy from env (mock requests)
- pytest O135 green

## Verify owner (Lead)
.venv\Scripts\python.exe -m pytest tests/test_o135_draft.py -q
.venv\Scripts\python.exe scripts\deploy-o135-vps.py
Premium smoke: /lenta/?lead=15146 → отклик **< 90s** · no «не успел»
journalctl -u rawlead-api | grep -E 'first_user_l2_only|fast_shared|draft:restart'
```

**Не в scope:** pre-warm L2 на все visible · смена модели · Wave 2.

---

## § O132-STABILITY — radar OOM (**✅**)

**Инцидент:** [`problems/2026-06-08-radar-oom-site-down.md`](../../problems/2026-06-08-radar-oom-site-down.md)

**Owner ✅ 2026-06-08:** Beget **2 GB RAM** · swap **0** post-reboot · radar **0 OOM**.

### Copy-paste для @coder

```
@coder O132-STABILITY

Спека: docs/team/architect/CODER_PROMPT.md § O132-STABILITY
Тикет: docs/problems/2026-06-08-radar-oom-site-down.md

Контекст: 1 GB → OOM 8×/night (chrome-headless). Owner **2 GB** ✅.
Не трогать: proxy/env acc1 · mass regen · WP theme.

## 1 — systemd rawlead-radar.service
MemoryMax=1400M · MemoryHigh=1200M · OOMScoreAdjust=200 · KillMode=mixed

## 2 — orphan Playwright cleanup
Конец цикла + startup: kill stale chrome-headless/playwright PIDs (user rawlead)
Log: browser:cleanup killed=N

## 3 — serialize browser
Max 1 Playwright fetch одновременно (FL xor Kwork). Close context after fetch.

## 4 — deploy
scripts/deploy-o132-vps.py · restart rawlead-radar · smoke free -h

DoD: 24h 0 oom-kill · NRestarts stable.
```

**Не в scope:** O134 ingest SLA · O133 TZ downloader · Wave 2.

**Verify Lead 2026-06-08:** pytest **8/9** (1 flaky UA random) · spec **4/4** ✅ · VPS **не задеплоен** (grep cleanup=0, MemoryMax=∞).

**Owner next:** `.venv\Scripts\python.exe scripts\deploy-o132-vps.py` → 24h мониторинг 0 oom-kill.

---

## § O131-PERF ✅ (2026-06-07)

| A L2 | B pooler | C feed boot | D `/v1/feed` | Deploy |
|------|----------|-------------|--------------|--------|
| retries 2 · poll 120s · `fast_shared` | `check_neon_pooler.py` · `db:` log | `Promise.all` · **1.18.35** | scan limit · inline `today_count` | **`deploy-o131-vps.py` ✅** |

**Verify Lead:** pytest **29/31** (2 test env quirks) · load@20 p95 **2549 ms** ⏸ · smoke feed **1818 ms** · pooler local **OK**.

**Owner next:** `preprod_draft_burst` · `ux_journey J5` · `preprod_stress_v2`.

---

## § O131-PERF — archive spec (**✅ закрыто**)

**Решение владельца (2026-06-07):** четыре пункта **до** полного `preprod_stress_v2` + `ux_journey` rerun.

**Контекст (факты):** HTML ~450 ms OK · `/v1/feed` ~1.5 s · draft p95 ~105 s · UI poll **90 s** → ложный «ИИ временно недоступен». Load@50 p95 2396 ms FAIL. Runbook S3-pre: Neon **pooler**.

**Не трогать:** proxy/env acc1 · mass regen · judge · WP theme copy.

### Copy-paste для @coder

```
@coder O131-PERF

Спека: docs/team/architect/CODER_PROMPT.md § O131-PERF
Runbook verify: docs/ops/PREPROD_STRESS_RUN.md § S3-pre + Wave 2

## A — L2 hot path (draft по клику)

Уже есть: `match_push.generate_and_store_lead_draft` — если `leads.reply_draft` не пуст → **skip L2**, только L3 uniquify (стр. ~629).

Доработать:
1. On-demand `_analyze_shared_ondemand`: **max_retries=2** (не 4) · backoff короче · timeout 90s оставить
2. On-demand L3 `rephrase_reply_draft_per_user`: **2 attempt** max в hot path (smell-retry — только 1 retry, не 3)
3. UI safety: `rawlead-feed.js` **`DRAFT_POLL_MAX_MS` 90000 → 120000** · сообщение при timeout: «ИИ не успел — повторите» (не generic ai_unavailable)
4. Log: `lenta:draft:{id}:fast_shared` когда взяли shared без L2

DoD: premium клик на lead **с** `reply_draft` → ready **< 15 s** (L3 only) · lead **без** shared → p95 target **< 75 s** в `preprod_draft_burst.py --max-leads 5`

## B — Neon pooler (VPS ops + guard)

Owner на VPS: `DATABASE_URL` → host `*-pooler.*` или порт **6543** (Neon dashboard → Connection pooling). Direct URL при 50 VU = FAIL S3.

Coder:
1. `scripts/check_neon_pooler.py` (или расширить deploy probe): read env · warn если нет `pooler`/`6543` в URL · exit 1 в CI optional
2. `rawlead-api` startup log: one line `db: pooler|direct` (без секретов)
3. Строка в `docs/ops/PREPROD_STRESS_RUN.md` § S3-pre — «проверено скриптом»

DoD: owner grep / script → `pooler` · load@50 p95 **< 2500 ms** или явный fail с hint «direct DB»

## C — Feed boot parallel (`rawlead-feed.js`)

Сейчас waterfall: `loadSubscription` → `mergeFeedPrefsOnLogin` → `loadTags+loadCatalog` → `resetAndLoad`.

Цель: параллельный boot:
```javascript
Promise.all([
  loadSubscription(),
  isLoggedIn() ? mergeFeedPrefsOnLogin() : Promise.resolve(),
  loadTags(),
  loadCatalog()
]).then(/* applyFeedShellMode, applyFeedTierUi, resetAndLoad once */)
```

Правила:
- Один `resetAndLoad` после всех prefs/tags/catalog/subscription
- Ошибка одного leg — не блокировать feed (catch per leg, как сейчас)
- Mirror minimal в `rawlead-cabinet.js` если тот же паттерн

DoD: DevTools Network — feed не ждёт serial chain > 1 RTT сверх max(subscription, tags, catalog)

## D — `/v1/feed` API (`api_server.py`)

1. **`today_count`:** один round-trip — CTE/window или subquery в том же `execute`, не второй full scan после page query
2. **Scan limit:** `_ME_FEED_SCAN_LIMIT=500` только при `categories` или `sort=match`+skills; time sort без filter → `limit+offset+20` buffer
3. Tests: `tests/test_api_feed.py` или extend existing — today_count present · scan limit regression

DoD: anon `GET /v1/feed?limit=20` p95 **< 1200 ms** (local probe или `preprod_load_feed.py --workers 20`) · один SQL round-trip для count+page где возможно

## Verify (owner после deploy VPS + WP JS bump)

```powershell
python scripts/check_neon_pooler.py   # или owner SSH grep DATABASE_URL
.venv\Scripts\python.exe scripts\preprod_load_feed.py --api-url https://api.rawlead.ru --workers 20 --duration 120
.venv\Scripts\python.exe scripts\preprod_draft_burst.py --max-leads 5 --concurrency 2
.venv\Scripts\python.exe scripts\preprod_playwright\ux_journey.py --journeys J5
.venv\Scripts\python.exe scripts\preprod_stress_v2.py --no-mint --skip-journey
```

Target gates: load@50 p95 < 2s · draft p95 < 90s · J5 pass · stress v2 draft gate green.
```

---

## § O129-JOURNEY-FIX — harness + draft burst feed (**⏸ после O131**)

### Copy-paste для @coder

```
@coder O129-JOURNEY-FIX

Контекст: ux_journey прогон 2026-06-07 → data/preprod_ux_journey.json — 6/10, 3 critical.
O129-W2 orchestrator + skills_mismatch + tier mint — ✅ (pytest 7/7).
Не трогать: proxy/env, VPS deploy, WP theme, mass regen.

## Fail 1 — J4/J5/J6 empty feed (critical)

Симптом: после J3 (design + skill filter) J4 ждёт `#rl-feed-list .rl-lead-card[data-id]` 45s timeout.
Root: фильтры J3 остаются в UI/localStorage; J4 `_goto_lenta` не сбрасывает.

Fix:
- `scripts/preprod_playwright/feed_ui.py` — `reset_feed_filters(page)` (category all · skills clear · sort/time · min_match default)
- `ux_journey.py` — в начале J4, J5, J6 вызвать reset (или shared helper `_lenta_fresh(ctx)`)
- Mirror: тот же паттерн что ux_audit desktop flake U2→U4 (если есть — reuse)

DoD: J4–J6 pass на prod с chromium+token.

## Fail 2 — J8 cabinet inbox (critical/warn)

Симптом: click на `.rl-lead-card--skeleton`, `#rl-cabinet-list` intercepts pointer events.
Fix:
- `j8_cabinet_logged`: ждать `#rl-inbox-list .rl-lead-card[data-id]:not(.rl-lead-card--skeleton)` (timeout 45s)
- optional scroll / force click только после real card
- не кликать skeleton

DoD: J8 pass.

## Fail 3 — draft_burst empty lead ids

Симптом: `preprod_draft_burst.py` → `feed returned no lead ids` для premium JWT acc1.
API: anon `/v1/feed?limit=5` → 5 items; premium bearer без skills → 0 items (`_personal_feed_page`, user_tags без km>0).

Fix в `fetch_feed_lead_ids`:
1. auth feed как сейчас
2. if empty → fallback anon feed (те же lead_id, draft всё равно с premium token)
3. или fallback `?skills=<one visible tag>` чтобы обойти personal-only path
4. fail loud с hint если оба пусты

DoD: `preprod_draft_burst.py --max-leads 5 --concurrency 2` → pass (не skipped).

## Tests

- extend `tests/test_preprod_stress_v2.py` или новый `tests/test_preprod_draft_burst.py`: mock empty auth feed → fallback ids
- optional: unit for reset_feed_filters selectors (minimal)

## Verify (owner после merge)

.venv\Scripts\python.exe scripts\preprod_playwright\ux_journey.py --base-url https://rawlead.ru
.venv\Scripts\python.exe scripts\preprod_draft_burst.py --max-leads 5 --concurrency 2

Target: journeys 0 critical (J10 mobile optional), draft_burst pass.
```

---

## § O129-W2 orchestrator ✅ (2026-06-07)

`preprod_stress_v2.py` · `preprod_draft_burst.py` · tier mint · skills `fl` · skipped gates ⏭ · pytest **7/7**.
Owner verify: `preprod_stress_v2_r2.json` — tier/skills/tz/parsers ✅ · load@50/draft p95 ⏸ infra.

---

| Gate | Result | Artifact |
|------|--------|----------|
| UX anon/free/premium | **24/24** each | `preprod_ux_audit_{anon,free,premium}.json` |
| Smoke | **5/5** | `preprod_playwright_report.json` |
| Load S3 | p95 **1846ms** · 0% err · 20×180s | `preprod_load_summary.json` |
| AI S5 | **96%** draft+tools | `preprod_ai_prod_audit.json` |
| Radar S4 | FL **alive=4/4** post ban-clear + O110-B | `radar_site.log` |

**Не в W1:** `ux_journey` J1–J11 · LLM human.md · load 50 VU → **O129 v2**.

---

## § O110-B ✅ (2026-06-07)

`invalidate_browser_slot` · wipe profile on ban · failover cooldown 5–15s · random Chrome/Firefox UA · default HTTP UA Chrome 122 · VPS `deploy_ingest_coupled_src` ✅.

---

## § O129-PREMIUM-UX-r2 ✅ (2026-06-07)

**Harness:** `ux_audit.py` + `feed_ui.py` · U10b rate-limit · U5→U12 reuse · U7 backdrop close.

---

## § O129-STRESS-V2 — полная симуляция наплыва (**→ Coder**)

### Copy-paste для @coder

```
@coder O129-STRESS-V2

Wave 1 ✅ 2026-06-07 (commits 4d8caf3, 63b63a1). Prod theme 1.18.34, O110-B на VPS.
Спека: docs/team/architect/CODER_PROMPT.md § O129-STRESS-V2
Runbook: docs/ops/PREPROD_STRESS_RUN.md § Wave 2

Контекст infra (не трогать env):
- TG acc1/bot proxy: 45.152 мёртв → временно 38.154 (acc2 spare), VPS+local ✅
- FL proxy O110-B deployed, S4 green

Задача: scripts/preprod_stress_v2.py — один orchestrator Wave 2.

Deliverables:
1. scripts/preprod_stress_v2.py → data/preprod_stress_v2.json + .md
2. Тиры: anon · free JWT · trial · premium (preprod_mint_token.py)
3. Reuse preprod_load_feed.py (ramp → 50 VU), ux_journey.py J1–J11
4. Draft burst DRAFT_BURST_MAX=20 (optional preprod_draft_burst.py)
5. Timings: feed · expand · tools · L2 · L3 · TZ · total (ms table in md)
6. TZ: 3–5 lead_id с [TZ attachment — assert detail fetch
7. Parser snapshot из radar_site.log (exchange_health + health:*)
8. S1-b: preprod_ai_matrix.py --scenario skills_mismatch
9. Minimal tests (timing parser / tier matrix)
10. PREPROD_STRESS_RUN.md § Wave 2

Pass: p95 feed <2s @50 VU · draft 0% 5xx p95<90s · TZ ≥2/3 · J1–J11 0 critical · parsers not all red.

Не: mass regen, judge, Sonnet, новый VPS, правки .env/proxy.

Baseline W1: preprod_ux_audit_{anon,free,premium}.json 24/24 · load p95 1846ms · AI 96%.
```

**Запрос владельца 2026-06-07:** stress «максимально хороший» — все тиры подписки, поток пользователей, draft+tools+TZ, **тайминги** по этапам, UX, парсеры «сломан vs тишина».

**Mechanic сначала — нет.** Mechanic = инцидент «сломалось». Сначала **Wave 1** (готовые скрипты, owner) → **Wave 2** (этот §).

### Scope Coder

| # | Артеfact | DoD |
|---|----------|-----|
| 1 | `scripts/preprod_stress_v2.py` (orchestrator) | один entrypoint · JSON `data/preprod_stress_v2.json` + `.md` |
| 2 | **Тиры:** anon · free JWT · trial · premium JWT | mint через `preprod_mint_token.py` / env · matrix в отчёте |
| 3 | **Read load** | reuse k6 or `preprod_load_feed.py` · p50/p95/p99 |
| 4 | **Draft burst (controlled)** | N users × M leads · **cap** `DRAFT_BURST_MAX=20` · **не** 1000 OpenRouter |
| 5 | **Timings** | per phase ms: feed · expand · tools · shared L2 · L3 · TZ fetch · total; таблица в md |
| 6 | **TZ** | 3–5 lead_id с `[TZ attachment` в body · assert detail fetch ok · log size/chars |
| 7 | **Quality spot** | reuse validators O128 на burst sample (no judge) |
| 8 | **Parser snapshot** | pull `exchange_health:*` + last `health:*` lines from radar log → секция отчёта |
| 9 | **S3-pre** | ramp VU · fail if 502/`53300`; doc Neon pooler in report |
| 10 | **S1-b** | `preprod_ai_matrix.py --scenario skills_mismatch` (Node lead + yii2 user tags) |
| 11 | **S4-pre** | assert no runaway `cycle_sec` / cascade spam in parser snapshot |
| 12 | tests | smoke unit for timing parser / tier matrix (minimal) |

### Pass criteria (O129)

| Gate | PASS |
|------|------|
| Read p95 feed | < 2s @ 50 VU |
| Draft burst | 0% 5xx · p95 draft < 90s · 429 documented |
| TZ leads | ≥2/3 attachment text loaded |
| UX journey | J1–J11 0 critical (reuse `ux_journey.py`) |
| Parsers | см. runbook § Parser — не все red |

### Файлы

- `scripts/preprod_stress_v2.py` · optional `scripts/preprod_draft_burst.py`
- `docs/ops/PREPROD_STRESS_RUN.md` § Wave 1 + Wave 2
- **Не:** mass regen · judge · Sonnet env · новый VPS

### Deploy

Только restart API если меняется instrumentation; иначе scripts-only.

---

## § O128-L2-VOICE ✅ (2026-06-07)

**Coder:** `l3_human_style.py` (блок O128-B, uniquify A=план→шаги) · `ai_analyze.py` cliche/smell · tests **36/36** · deploy `deploy-l2-stack-vps.py` ✅

**Verify Lead:** VPS `O128-B` ×2 · audit 50 **96%** draft/tools · GOOD #8752 без «предпочтение по стеку»

---

## § O128-L2-VOICE spec (архив DoD)

**Боль:** L2 пишет «имею опыт / делал похожее» → заказчик просит кейсы. RawLead — **универсальный черновик**, не портфолио.

**Решение B (владелец):**
- ✅ **Можно:** «По ТЗ вижу…», «Для реализации [боль] выстрою: [шаги из ТЗ]», стек **из ТЗ** + 1 фраза «почему»
- ❌ **Нельзя:** «имею опыт», «я эксперт», «уже делал», «N проектов», «делал похожее», «предпочтение по стеку?», «какой язык выбрать?»
- **Вопросы:** 1 (редко 2) — только **бизнес-логика / edge case** из ТЗ: «В описании [X]. Как планируете [крайний случай]?»

**Не трогать:** `match_push.py` flow · env моделей · mass regen · `--judge` · `wordpress/`

### Файлы (только эти)

| Файл | Что |
|------|-----|
| `src/l3_human_style.py` | `build_shared_l2_system`, `build_uniquify_system`, `_HUMAN_GOOD_PATTERNS`, `_REPLY_AI_SMELL_RE`, GOOD/BAD примеры |
| `src/ai_analyze.py` | `_REPLY_DRAFT_CLICHE_RE`, `_FORBIDDEN_REPLY_GREETING_RE`, при необходимости `reply_draft_cliche_warn` |
| `tests/test_l3_human_style.py` | § `test_o128_*` (минимум 8 кейсов) |
| `tests/test_l3_human_style.py` или новый | smell/validator ловит BAD-фразы |

### DoD

| # | Критерий |
|---|----------|
| 1 | **L2 shared prompt:** блок «Позиция исполнителя» — план/шаги из ТЗ; запрет portfolio-claims; шаблон вопроса по edge case |
| 2 | Убрать/переписать: «Делал похожее…» в `_HUMAN_GOOD_PATTERNS`; GOOD **#8752** без «предпочтение по стеку» |
| 3 | **L3 uniquify:** каркас **(A)** был «опыт→план→вопрос» → **«план→шаги→вопрос»** (без кейса/опыта); retry suffix не предлагать «начни с опыта» |
| 4 | **Validator/smell:** retry при «имею опыт», «эксперт», «делал похож», «предпочтение по стеку», «какой стек/язык предпочитаете» |
| 5 | Сохранить: «Здравствуйте!», 4–6 предл., один «?», запрет Cursor/ИИ/промпт, O99 domain rules (creative/TG/attachments) |
| 6 | `pytest tests/test_l3_human_style.py -q` — все зелёные + новые o128 |
| 7 | Deploy: `python scripts/deploy-l2-stack-vps.py` |

### GOOD / BAD (вставить в промпт)

**BAD:** «Имею большой опыт интеграций AmoCRM. Готов обсудить.»  
**BAD:** «Делал похожие боты. Подскажите, какой стек предпочитаете?»  
**GOOD (B):** «Здравствуйте! По ТЗ — webhook AmoCRM: заявка с формы → сделка, тест на тестовом аккаунте. REST API Amo, как в описании. Подскажите, одна воронка или разные по источнику?»

### Проверка

```bat
python -m pytest tests/test_l3_human_style.py -q
python scripts/preprod_ai_prod_audit.py --profile site --limit 50
python scripts/deploy-l2-stack-vps.py
```

**Не делать:** Sonnet в `.env.site` · `backfill` reply_draft · правки `tools_catalog` (O125/O98 закрыты).

**Опц. P2 (если успеешь):** #9909 — «ИИ-бот» в title: не fail validator на слово «бот» когда в ТЗ явно AI-продукт.

---

## § L2-draft-tune ✅ (2026-06-07)

Audit 50: draft **96%** · tools **96%** · deploy `deploy-l2-stack-vps.py` ✅

---

## § O127-WP — Filter Bar v2 + Lead Card v3 ✅ (2026-06-07)

**Coder:** partials `feed-filter-bar.php` · `feed-card.php` · CSS §9 · JS `data-tier` · **1.18.19** · deploy VPS.

**Lead verify:** repo DoD ✅ · Local **1.18.19** + `rl-filter-btn--locked` ✅ · prod HTTP timeout из Lead env — owner Ctrl+Shift+R.

---

## § O127-WP spec (архив DoD)

**Design:** [`feed-cabinet-mvp.md`](../design/wp/feed-cabinet-mvp.md) **§9** · [`LEAD_DESIGN_PROMPT.md`](../team/design/LEAD_DESIGN_PROMPT.md) § O127-D ✅

**Суть:** один filter bar chrome (anon = locked кнопки, не скрывать) · одна карточка `data-tier` · один CTA · 48px mobile.

| # | DoD | Файл |
|---|-----|------|
| 1 | Unified filter bar: chips + `[Навыки▾]` + `[Сорт▾]` у **всех** тиров; anon `.rl-filter-btn--locked` + hint | `feed-filter-bar.php` / `page-lenta.php` · CSS §9.1 |
| 2 | `data-tier` anon\|free\|premium на карточке; rows auth-only / paid-only | `feed-card.php` · `rawlead-feed.js` |
| 3 | Lead Card v3 F-pattern · AC-1…AC-12 §9.2h | CSS §9.2g · JS |
| 4 | Free CTA: inline upsell (не редирект с 1-го клика) · Premium draft · Cabinet accordion | регресс **O124** |
| 5 | Убрать «Брать»/«Сомнительно» если остались | grep |
| 6 | Bump `RAWLEAD_CHILD_VERSION` · **не** merge с O124-w2 отдельно — включить anon polish в эту волну |

**Не трогать:** `src/` · `/ops/` · O126 API.

**Smoke:** Local BS `localhost:3009/lenta/` — anon locked hint · free/premium same chrome · card tiers · 390px.

**Deploy:** `deploy-wp-theme-vps.py` по команде owner.

---

## § O126-category-fix ✅ код (2026-06-07)

**Lead verify:** tests **7/7** · `_passes_category_filter` в `api_server.py` · `infer` default **`other`** · `scripts/backfill_lead_category.py`

| # | DoD | ✅ |
|---|-----|---|
| 1 | `lead_category.py` hints + other default | ✅ |
| 2 | API filter = resolved category | ✅ |
| 3 | backfill script | ✅ |
| 4 | ingest via `category_for_listing` / `lead_category` | ✅ shared module |
| 5 | `tests/test_o126_category.py` | ✅ **7/7** |

**Prod:** ✅ **2026-06-07** — API + backfill 1757 · smoke `category=dev` → **dev:20** · theme **1.18.20** dev icon `escapeHtml`

**Deploy owner:**
```bat
python scripts/backfill_lead_category.py --reconcile-visible --dry-run
# upload src/lead_category.py src/api_server.py → restart rawlead-api rawlead-radar
python scripts/backfill_lead_category.py --reconcile-visible
```
Smoke: `GET …/feed?limit=12&category=dev` → только `dev` в JSON.

---

## § O124-w2 — UI polish live-dev (**local ✅**, 2026-06-07)

**Режим:** владелец смотрит **BrowserSync** (`npm run dev` → `localhost:3009+`) · пишет правки в чат · Coder правит → BS reload.

**Setup (owner):** Local **radarzakaz** Start · junction OK · `RAWLEAD_API_URL=https://api.rawlead.ru` в wp-config.

| # | Правило |
|---|---------|
| 1 | **Только** `wordpress/rawlead-kadence-child/` — CSS/PHP/мелкий JS layout |
| 2 | **Не** трогать `src/` · парсеры · L2 · deploy без bump версии |
| 3 | После сессии: bump `RAWLEAD_CHILD_VERSION` · `deploy-wp-theme-vps.py` · Lead/owner |
| 4 | Регресс **O124**: accordion expand · flip только `--draft-flip` · free CTA 2-step · match-bar Premium |

**Файлы hot:** `assets/css/rawlead.css` · `assets/js/rawlead-feed.js` (осторожно) · `template-parts/` · `inc/marketing.php`

**Вход в чат:** владелец кидает список/скрины («кнопка ниже», «полоска как ЛК») — правишь пачкой, не переписываешь ленту.

**Статус:** ✅ **1.18.34 prod** (2026-06-07) · BrowserSync tail минимально закрыт

---

## § O124-feed-card ✅ (2026-06-07)

Лента: accordion expand · flip только отклик (`--draft-flip`) · `renderCompatMatchBar` Premium · free CTA 2-step · `rl-feed-shell--pending` + PHP cookie class · **1.18.18** VPS.

---

## § O121-w3-acc2 — acc2 join legacy filter ✅ (2026-06-05)

**Deploy:** `deploy-o121-w3-acc2-vps.py` · tests **6/6** local

| # | DoD | ✅ |
|---|-----|---|
| 1 | `_needs_join_bootstrap` · 0 listen + pending → join_loop | ✅ |
| 2 | `test_o121_w3_acc2.py` | ✅ 6/6 |
| 3 | Deploy VPS + `join-bootstrap acc2` в log | ⏳ owner |
| 4 | 6 pending → done в v2 CSV | ⏳ ~1.5–2 ч после deploy |

---

## § O121-w2b — /ops/ control timeout ✅ (код)

**Тикет:** [`2026-06-05-ops-failed-to-fetch.md`](../../problems/2026-06-05-ops-failed-to-fetch.md)

**Lead verify:** `rawlead-api.php` — `clear-bans` + restart → **90s** · `deploy-o121-w2b-vps.py` есть.

| # | DoD | ✅ |
|---|-----|---|
| 1 | timeout 90s в PHP | ✅ |
| 2 | deploy script | ✅ |
| 3 | **Owner smoke** `/ops/` clear-bans | ⏳ |
| 4 | delist 120s (O122) без регресса | ⏳ |

---

## § O121-w2 — прокси UX ✅ (2026-06-05)

**Deploy:** `deploy-o121-w2-vps.py` · VPS **active** · tests **9/9** local

| # | DoD | ✅ |
|---|-----|---|
| 1 | «Сбросить баны» TG + биржи | |
| 2 | Забанен → «Забанен — сначала сброс» | |
| 3 | Подписи групп · `status_label` human | |
| 4 | deploy VPS | |

---

## § O121-w3 — TG acc UI (**backlog**)

Join-таблица в `/ops/` · listen count · после w3-acc2.

---

## Сводка закрытого

O121-w0/w0b/w0c · O121-w1 · **O121-w2** · O122 · O120 · O107 · O123-w1 · O116 — [`STATUS.md`](../common/STATUS.md)

---

## § O105-w1-r3 (**⏸ по симптому**)

---

## § O125 — L2 только по «Написать отклик» ✅ (2026-06-07)

**Решение владельца:** не гонять tools-L2 на radar вхолостую · `TOOLS_BACKLOG_DRAIN=0`.

| # | DoD | ✅ |
|---|-----|---|
| 1 | `main.py` default `TOOLS_BACKLOG_DRAIN=0` | ✅ |
| 2 | `match_push`: `_ondemand_lead_tools` (tools-only) + `analyze_shared_reply_draft` на клик; **без** `analyze_premium` | ✅ |
| 3 | VPS `.env.site` `TOOLS_BACKLOG_DRAIN=0` · deploy `deploy-o125-l2-on-demand-vps.py` | ✅ |
| 4 | tests o37b + shared_draft + o98 | ✅ |

**Deploy:** `python scripts/deploy-o125-l2-on-demand-vps.py`

---

## § L2-tools-tune — consulting overuse ✅ (2026-06-07)

**Контекст:** O82-w2 ошибочно поставил Sonnet на prod L2; уже откатили env на `google/gemini-2.5-pro`. В Neon ~2630 visible с `tools_required` — **consulting 28%** slug (catch-all). Настраиваем **tools-only L2** (`analyze_lead_tools`), не shared draft / judge.

**Brief:** [`data/l2_tools_tune_brief.json`](../../../data/l2_tools_tune_brief.json) · audit [`data/preprod_ai_prod_audit_human.md`](../../../data/preprod_ai_prod_audit_human.md)

| # | DoD | ✅ |
|---|-----|---|
| 1 | `_TOOLS_ONLY_SYSTEM`: consulting guard · rhino guard · whitelist-only | ✅ |
| 2 | `tools_catalog`: alias html/css→javascript; reject cyrillic/unknown slugs; consulting post-filter | ✅ |
| 3 | `finalize_tools_for_lead`: min 2 после фильтра; TZ-hints fallback | ✅ |
| 4 | tests `test_tools_catalog_o98.py` (**11/11**) | ✅ |
| 5 | deploy VPS: `ai_analyze.py` + `tools_catalog.py` · restart `rawlead-radar` | ✅ Lead verify |

### Файлы (только эти)

- `src/ai_analyze.py` — `_TOOLS_ONLY_SYSTEM`, при необходимости docstring `analyze_lead_tools`
- `src/tools_catalog.py` — `_TOOL_ALIAS_MAP`, `normalize_tools_required` / `finalize_tools_for_lead`
- `tests/test_tools_catalog_o98.py` — кейсы consulting/rhino/cyrillic/html
- `scripts/deploy-fix-l2-models-vps.py` — **не трогать** (env уже ok) · deploy через `deploy_vps_ssh` upload + restart

### Правила промпта (обязательно в `_TOOLS_ONLY_SYSTEM`)

1. **`consulting`** — только если в title/body явно: консультация, аудит, сопровождение, «нужна консультация», без работ исполнителя. Иначе — предметные slug (seo, wordpress_dev, photoshop…).
2. **`rhino`** — только при 3D / Rhino / Grasshopper / CAD в тексте. **Не** для GAS, ботов, таблиц.
3. **Whitelist-only** — только slug из списка в промпте; html+css → javascript; google sheets → google_sheets_api.
4. Исправить строку «GAS/Rhino/google-таблица → … rhino» — она провоцирует false positive (lead #9907).

### Post-process (`tools_catalog`)

- Drop slug с кириллицей / не из KNOWN_TOOLS+canonical после alias.
- Если после normalize остался один `consulting` без «консульта»-маркеров в TZ — заменить hints из `tools_from_tz_text`.
- Alias: `html`, `css` → `javascript` (или `html_css` если уже в KNOWN_TOOLS).

### Как проверить

```bat
python -m pytest tests/test_tools_catalog_o98.py -q
python -m pytest tests/test_preprod_ai_prod_audit.py -q
```

Deploy (local):

```bat
python scripts/deploy_vps_ssh.py
```

или upload `src/ai_analyze.py` + `src/tools_catalog.py` → `/opt/rawlead/src/` · `systemctl restart rawlead-radar`.

**Не делать:** `--judge` · `backfill_tools_required.py` mass · `qa_prompt_loop --full` · смена env моделей.

**После deploy:** owner/Lead — `preprod_ai_prod_audit.py --profile site --limit 50` ($0) для сравнения consulting%.

---

_Lead · L2-tools-tune активно · w3-acc2/w2b deploy owner_
