# Полный аудит + AI-логика — MiMo Auto (O280 post-cutover)

**Статус:** **🟡 triaged Lead 2026-06-19** · P0 → `CODER_PROMPT` § **O283-MIMO** + **O280-R2**  
**Дата:** 2026-06-19 · pilot owner · MiMo Auto  
**Приоритет:** findings → post-cutover fixes → повтор go/no-go → O37 stress  

## Запрос владельца

1. Плотный построчный аудит всего проекта  
2. **Отдельно — вся ИИ-логика:** L1 tags, L2 draft, validation, false 100% match  
3. Findings → input для **stress-теста** (O37)  
4. **Docs drift (2026-06-19):** перепроверить документацию — расхождения с кодом/prod, устаревшие статусы, противоречия между канонами  
5. **Product drift (2026-06-19):** `PRODUCT_VISION` **v0.12** vs **реальный MVP на prod**  
6. **rawlead-next/ post-O280 cutover** — deploy/nginx риски  
7. **Parser stability:** FL, Kwork, YouDo camoufox, TG

## Scope @mechanic

### A — Код + ИИ

| Область | Что искать |
|---------|------------|
| **`src/ai_analyze.py`** | L1/L2 prompts · validation · false match · draft paths · thread-safety · retry |
| **`src/rank.py` + L1 tags** | false positive 100% · Joomla/WP cases |
| **`src/draft_async.py` + `match_push.py`** | shared draft cache · lock · poll · TG path |
| **`src/lead_pipeline.py`** | когда L2 skip · no_reply_draft |
| **`api_server.py`** | draft GET/POST · 202 pending · 503 paths |
| **Parsers** | FL restart loop · Kwork fragile JSON · YouDo browser-only · TG notification retry |

### B — Документация (отчёт drift)

| # | Проверить | Искать |
|---|-----------|--------|
| d1 | **STATUS ↔ TASKS ↔ ROADMAP ↔ OWNER_INTENT** | устаревшие статусы O280 · противоречия |
| d2 | **CODER_PROMPT** | § «→ Следующее» vs реальный prod |
| d3 | **Код ↔ docs** | env keys · API routes · schema (TZ_API, NEON_SCHEMA) |
| d4 | **ИИ-канон** | prompts в коде vs docs |
| d5 | **PROD_FACTS** | Theme version · deploy snapshot vs реальность |
| d6 | **rawlead-next/** | O280 cutover · nginx · CORS · security headers |
| d7 | **problems/** | открытые тикеты vs закрытые фиксы |
| d8 | **Product drift** | PRODUCT_VISION v0.12 §0d acceptance vs prod |

### d8 — Product drift (чеклист)

Сверить `PRODUCT_VISION.md` **v0.12** с кодом + prod (Next.js cutover, VPS API/bot):

| § vision | Вопрос |
|----------|--------|
| **§0d #1-5** | Каждый пункт acceptance — **done / partial / missing** + evidence |
| **§0c Direction B** | `/feed` anon · ≥50 лидов/день · ИИ-модерация · шлак <30% |
| **§0c Direction C** | `/cabinet` inbox · регистрация · multi-user-ready |
| **§0c Direction D** | draft · рыночная цена · push TG · подписка vs «после MVP» |
| **§0a SaaS-ready** | `user_id` везде · нет хардкода владельца |

---

## Решение (MiMo · 2026-06-19)

### 1. AI P0/P1

| Pri | Проблема | Evidence | Fix |
|-----|----------|----------|-----|
| **P0** | Thread-safety bug: `_reply_validate_lead_ctx` — module-level mutable tuple, concurrent writes from `set_reply_validate_lead_context()` (line 525) race in multi-threaded FastAPI | `ai_analyze.py:116` — no lock, global mutable state | **O283-MIMO-AI** — contextvars · test concurrent draft |
| **P0** | Draft polling broken in cabinet post-O280 cutover — owner smoke confirmed «отклики не работают (нет draft poll)» | O280-POST-CUTOVER task · `rawlead-next/app/cabinet/page.tsx` no draft poll implementation | **O280-R2-6** + **O283-MIMO-CABINET** — poll pending in cabinet |
| P1 | L1 false 100% match: Joomla→wordpress_dev, generic CMS signals misclassify | `ai_analyze.py` L1 prompts `_LITE_SYSTEM_HEAD` lines 1369-1475 · few-shot examples `_LITE_FEWSHOT_BLOCK` (17 examples, static) | O59 backlog · stress matrix · add negative examples |
| P1 | `_ai_error_kind()` operator precedence: `"openrouter" in msg and "формат" not in msg` — `or` with `isinstance` check causes HTTP errors from non-RequestException to return "http" | `ai_analyze.py:919` | P2 — works but fragile · add parens for clarity |
| P1 | L3 uniqueness hack: trivial space injected after "Здравствуйте!" when drafts identical | `ai_analyze.py:2541-2542` | Refactor: generate meaningfully different opener |
| P1 | 2673-line God-file: ai_analyze.py bundles L1, L2, L3, validation, parsing, prompts, stats, concurrency | `ai_analyze.py` · acknowledged in ARCHITECTURE.md line 146 | P2 — refactor into modules (validation, prompts, flows) |
| P2 | `_LITE_FEWSHOT_BLOCK` — 17 few-shot examples as static string, maintenance burden if categories change | `ai_analyze.py:1348-1366` | Move to external file or dynamic generation |

---

### 2. Parser stability P0/P1

| Pri | Парсер | Проблема | Impact | Fix |
|-----|--------|----------|--------|-----|
| **P0** | **FL** | Restart loop: `fl_hard_reset` sets `restart_source_fl=1` → context close every ~3 cycles → no-op with `FL_LISTING_SUBPROCESS=1` → infinite recovery loop without actual recovery | Dead FL source at night · operator unaware | **O283-MIMO-FL** — audit all `fl_hard_reset` call sites · O257 tests green |
| **P0** | **FL** | httpx fallback disabled by default: `FL_HTTPX_AUTO_FALLBACK=1` exists but confusing dual-flag with `FL_HTTPX_FALLBACK` (O210 conflict) | Browser failure = dead parser without explicit flag | **O283-MIMO-FL-DOC** — document default · single-flag design |
| **P0** | **YouDo** | Browser-only (zero httpx fallback): `YOUDO_BROWSER_ONLY=1` default · Camoufox failure = source completely dead | YouDo down → no recovery path | Acceptable risk · document · ensure Camoufox health monitoring |
| P1 | **FL/Kwork** | Browser errors invisible to operator: logged to journal only, not `radar_site.log` | Night failures undetected until morning | Add journal→site.log forwarding for browser errors |
| P1 | **Kwork** | Silent parsed=0: no recovery mechanism, returns `[]` silently | Kwork source silently dies | Add parsed-zero streak recovery like FL |
| P1 | **Kwork** | Fragile JSON extraction: manual bracket-depth counting in `_extract_wants_array()` | HTML structure change = silent break | Refactor to proper HTML parser |
| P1 | **YouDo** | Camoufox+Playwright version pinning: `playwright<1.60` required or camoufox#617 crashes | Dependency update = breakage | Pin in requirements.txt · CI check |
| P1 | **TG** | No retry in `telegram_notify.py`: single attempt per send | Network blip = lost notification | Add retry with backoff (1-2-4s) |
| P1 | **All** | Orphan processes after SIGKILL: camoufox/chromium orphans accumulate eating RAM | VPS memory leak | Add orphan cleanup in radar startup |
| P2 | **YouDo** | 11+ storage keys for state management, no state machine | Easy inconsistent state | Document state machine · add consistency checks |
| P2 | **Secondary** | FreelanceJob, Freelance.ru, Pchyol: no anti-bot detection, no browser fallback | Silent break on bot protection change | Acceptable for low-traffic sources |
| P2 | **VC.ru, Habr** | Zero test coverage | Unknown regressions | Add basic integration tests |

---

### 3. Docs drift P0/P1/P2

| Pri | Файл | Написано | Prod/код | Кто |
|-----|------|----------|----------|-----|
| **P0** | `TZ_API.md` v0.3g | 10 эндпоинтов | **20+** в `api_server.py` (draft GET/POST, auth, replies, admin, ops, rephrase, tools, premium) | **Lead O39-docs** |
| **P0** | `NEON_SCHEMA.md` v0.3 | 4 таблицы | +`user_lead_replies`, `draft_jobs`, `lead_draft_jobs`, `match_push_log`, `admin_pageviews`, +cols `reply_draft`, `tools_required`… | **Lead O39-docs** |
| P1 | `PROD_FACTS.md` AUTO:VPS_PROBE | Theme `ver` = `1.5.0` | Repo theme = `1.19.20` — different metrics conflated (probe `ver` ≠ WP theme ver) | Lead — clarify metric |
| P1 | `O280_AS_BUILT.md` verify checklist | `/pricing/` = 404 | `/pricing/` exists and builds in `rawlead-next/app/pricing/page.tsx` | Lead — update stale checklist |
| P1 | `TASKS.md` GTM gate | O280 cutover = "⏳" | O280 cutover = **done** (PROD_FACTS + nginx confirm) | Lead — mark done |
| P1 | `docs/README.md` | References `docs-guard.mdc` Cursor rule | Unknown if exists | Lead — verify or remove |
| P1 | `WP_TO_NEXT_HANDOFF.md` | References `web/` package | Actual folder = `rawlead-next/` | Lead — update legacy refs |
| P2 | `PRODUCT README` (docs/team/common) | PRODUCT_VISION = v0.9 | PRODUCT_VISION = **v0.12** | Lead — update version |
| P2 | `PROJECT_MAP.md` line 51 | `contour` owner/saas marked cancelled | Still referenced in older context | Lead — add note |
| P2 | `PROJECT_MAP.md` line 146 | `api_server.py` labeled "God-file" warning "не читать целиком" | May hide bugs from AI agents | Coder — consider modular split |

---

### 4. Product drift P0/P1/P2

| Pri | § vision | Обещано | Prod/код | Статус | Evidence |
|-----|----------|---------|----------|--------|----------|
| **P0** | §0d #3 | Draft + push TG | Draft **flaky post-O280** · push OK | **partial** | O280-POST-CUTOVER: no draft poll in cabinet |
| **P0** | §0d #1 | `/feed` ≥50/день · модерация | Feed live on Next.js · метрики шлака не замерены | **partial** | No monitoring of % spam after AI moderation |
| P1 | §0d #5 | Docs → 2-й user за 1-2 дня | TZ_API/schema drift мешает | **partial** | O39-docs not confirmed complete |
| P1 | §0c Direction D | draft · рыночная цена · push TG · подписка | L2 draft works (pre-O280) · 790₽ fixed · push OK · billing partial | **partial** | Stars live · YooKassa pending |
| P1 | §0a SaaS-ready | `user_id` везде · нет хардкода | `user_id` in schema + API · `_OWNER_USER_ID` hardcode in some paths | **partial** | Known since v0.9 audit |
| P2 | §0d #4 | multi-user-ready | `user_id` in API · single-user in practice | **partial** | TG Login pending (phase 3g) |

---

### 5. rawlead-next/ and O280 nginx/deploy risks

| # | Risk | Severity | Detail |
|---|------|----------|--------|
| 1 | **No security headers** | **HIGH** | No `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Content-Security-Policy`, `Strict-Transport-Security`, `Referrer-Policy` on `rawlead.ru` — production serving financial/payment flows (790 RUB subscription) |
| 2 | **No rate limiting on admin endpoints** | **HIGH** | `/ops/` and `/v1/admin/` proxied to FastAPI with zero nginx-level throttle — brute-force/DDoS hits backend directly |
| 3 | **`/v1/admin/` publicly reachable** | **HIGH** | No IP allowlist or Basic Auth at nginx level — security depends entirely on FastAPI backend auth |
| 4 | **MOCK_LEADS fallback masks prod errors** | **HIGH** | `lenta/page.tsx` lines 96-106: silently falls back to MOCK_LEADS on any API/CORS error — real prod failures invisible to users and operator |
| 5 | **No gzip/brotli compression** | **MEDIUM** | Static HTML/JS/CSS served uncompressed — increased page load times |
| 6 | **No www→bare redirect** | **LOW** | `www.rawlead.ru` serves same content — duplicate content for SEO |
| 7 | **No automated rollback** | **MEDIUM** | Rollback relies on manual nginx reconfiguration + rsync — no script |
| 8 | **Draft polling not implemented** | **P0** | Cabinet UI has no draft poll — core MVP feature broken post-cutover |
| 9 | **No Metrika on Next** | **LOW** | Was on WP theme — analytics gap |

---

### 6. Топ-10 P0/P1 (сводка)

| # | Pri | Находка | Категория |
|---|-----|---------|-----------|
| 1 | **P0** | Draft polling broken post-O280 cutover | code (frontend) |
| 2 | **P0** | Thread-safety bug in `_reply_validate_lead_ctx` | code (AI) |
| 3 | **P0** | FL restart loop — infinite recovery without actual recovery | code (parser) |
| 4 | **P0** | TZ_API.md critically outdated (10 vs 20+ endpoints) | docs |
| 5 | **P0** | NEON_SCHEMA.md critically outdated (4 tables vs many) | docs |
| 6 | **P0** | MOCK_LEADS fallback masks real prod failures | code (frontend) |
| 7 | **P0** | No security headers on production | deploy (nginx) |
| 8 | **P1** | No rate limiting on admin endpoints | deploy (nginx) |
| 9 | **P1** | YouDo browser-only, zero fallback | code (parser) |
| 10 | **P1** | L1 false 100% Joomla→wordpress_dev still open | AI |

---

### 7. Stress scenarios (10 · не прогонялись)

| # | Сценарий | Фокус | Ожидаемый результат |
|---|----------|-------|---------------------|
| 1 | **50x concurrent draft generation** | OpenRouter rate limit · `_draft_or_concurrency()` semaphore · timeout cascade | Graceful degradation, 429 handling, no 503 |
| 2 | **100x concurrent feed requests** | API `/v1/feed` · Neon connection pool · caching | <500ms p95 · no DB exhaustion |
| 3 | **100 users x 1 lead shared draft** | Shared draft cache · lock contention · `analyze_shared_reply_draft()` thread-safety | No race conditions · `_reply_validate_lead_ctx` bug must be fixed first |
| 4 | **Ingest flood 1000+ leads** | L1 batch · OpenRouter concurrency · Neon batch insert | No OOM · L1 <30s per lead · no duplicate inserts |
| 5 | **TG bot command spam** | `telegram_control.py` getUpdates · offset management · rate limit | No re-processing · no offset corruption |
| 6 | **API key rotation mid-cycle** | OpenRouter key swap · in-flight requests | Graceful failover · no partial states |
| 7 | **DB pool exhaustion** | Neon/local Postgres · connection leak · max_connections | Timeout · auto-recovery · no deadlock |
| 8 | **Camoufox crash during YouDo fetch** | Browser-only · no fallback · orphan cleanup | YouDo marked failed · no zombie processes · radar continues |
| 9 | **FL browser ban + restart loop** | O283-MIMO-FL fix must be in place · `fl_hard_reset` guard | FL recovers or degrades · no infinite loop |
| 10 | **Mixed load: 20 feed + 10 draft + 5 ingest** | All subsystems concurrent · resource contention | No deadlocks · fair scheduling · monitoring accurate |

→ input для **O37** после P0 fixes.

---

### 8. Go/no-go

**CONDITIONAL NO-GO.** P0 blockers remain:

| Блокер | Почему |
|--------|--------|
| Draft polling post-O280 | Core MVP feature (§0d #3) broken — users cannot see replies in cabinet |
| Thread-safety bug | `_reply_validate_lead_ctx` race — will fail under concurrent L2 calls |
| FL restart loop | Infinite recovery without recovery — FL source unreliable at night |
| TZ_API / NEON_SCHEMA | Critically outdated — risk of wrong stress scenarios and new developer confusion |
| No security headers | Production serving payments without CSP/HSTS/X-Frame-Options |
| MOCK_LEADS fallback | Masks real prod errors — false confidence in system health |

**После P0 fixes** — Lead повторяет go/no-go → O37.

---

## Lead triage (2026-06-19)

**Verify Lead (read-only):**

| Finding | Lead verdict |
|---------|--------------|
| Cabinet «no draft poll» | **Частично верно:** `FeedCard` poll есть · cabinet только `mergePendingDrafts` из localStorage без API poll для pending → **O283-MIMO-CABINET** |
| FL restart loop | **Частично:** O257 fix + `test_o257_restart_source_no_loop.py` есть · нужен audit **всех** call sites `fl_hard_reset` |
| `_reply_validate_lead_ctx` race | **Подтверждено** — global tuple `ai_analyze.py:116` |
| MOCK_LEADS on prod | **Подтверждено** — `lenta/page.tsx:96-106` silent fallback |
| TZ_API / NEON_SCHEMA drift | **Подтверждено** — Lead **O39-docs** |
| Security headers nginx | **Вероятно** — отдельный § **O283-MIMO-NGINX** после R2 |

**Маршрутизация:** см. [`CODER_PROMPT.md`](../team/architect/CODER_PROMPT.md) § **O283-MIMO** · docs → Lead · stress → O37 после green.

---

## Артефакт

§ **Решение** + **Lead triage** выше · P0 code → `CODER_PROMPT` § **O283-MIMO** · docs → Lead **O39-docs**
