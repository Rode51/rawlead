# PRE-PROD-STRESS — прогон перед трафиком

**Ворота:** [`docs/team/architect/PRE_PROD_GATE.md`](../team/architect/PRE_PROD_GATE.md) § S1–S6.

**Когда:** после § P5 (WP + API + Site на VPS), **и после** Design + PM copy + Coder финал (O21). DNS готов, рекламы нет.

---

## Слой 0 — UX-audit «как человек» (S2, **O37c**)

**Один прогон** перед stress — жесты U1–U10 desktop 1440 + mobile 390:

```powershell
# .env.site: RAWLEAD_PREPROD_ACCESS_TOKEN=… (paid JWT, обязательно)
.venv\Scripts\python.exe scripts\preprod_playwright\ux_audit.py --base-url https://rawlead.ru --browser chromium
```

Отчёты: `data/preprod_ux_audit.json` · `data/preprod_ux_audit.md` · **`preprod_ux_audit_human.md`** (LLM) · скрины `data/preprod_ux_audit/`

| Что делает | Детали |
|------------|--------|
| U1–U10 | header/footer · навыки · sort tap-outside · expand · draft+tools · FAB · ЛК · **mobile sheet U8** · marketing CTA · console/network |
| Auth | `RAWLEAD_PREPROD_ACCESS_TOKEN` — U5/U7/U8 draft и ЛК |
| LLM | OpenRouter vision — mobile скрины → human.md (Критично / Раздражает / Ок) |

| PASS S2 / O37c | 0 critical · test token · human.md · U8 mobile прогнан |

Debug: `--headed` · dev: `--skip-llm` · см. [`PREPROD_ACCOUNTS.md`](PREPROD_ACCOUNTS.md)

**Coder:** § PRE-PROD-UX-AUDIT в `CODER_PROMPT.md` (скрипт **→** после финала UI).

---

**Не гонять:** 1000+ premium OpenRouter. Нагрузка — **чтение** API/ленты.

### Переменные

| Переменная | Пример | Где |
|------------|--------|-----|
| `BASE_URL` | `https://rawlead.ru` | Playwright |
| `API_URL` | `https://api.rawlead.ru` | k6 / load |
| OpenRouter | `.env.site` на VPS или локально | матрица ИИ |

---

## Слой 1 — ИИ (S1)

**Локально или на VPS** (нужен ключ OpenRouter в `.env.site`):

```powershell
cd C:\Users\hramo\uisness
.venv\Scripts\python.exe scripts\preprod_ai_matrix.py --profile site --dry-run
.venv\Scripts\python.exe scripts\preprod_ai_matrix.py --profile site
```

Отчёт: `data/preprod_ai_report.json`

| Критерий S1 | PASS когда |
|-------------|------------|
| По каждой category (`dev`, `design`, `marketing`, `text`) | ≥3 фикстуры в отчёте |
| L1 | `task_summary` не пустой |
| L2 | `reply_draft` не пустой на «нормальном» лиде |
| Итог | `summary.s1_pass: true` |

Узкий прогон (экономия):

```powershell
.venv\Scripts\python.exe scripts\preprod_ai_matrix.py --profile site --category dev --limit 1
```

**Красные флаги:** массовые `errors` с `401`/`429`; пустой `reply_draft` на всех L2.

### S1-b — `skills_mismatch` (edge case, **→ Coder в matrix**)

**Боль:** в ЛК пользователь ставит **редкие** навыки (Yii2, FontLab), открывает заказ **другого домена** (Node.js) — L3 не должен **падать**, **зависать** или **вшивать** чужой стек из профиля; отклик = **нейтральный каркас по ТЗ** (O128-B).

| # | Проверка | Статус |
|---|----------|--------|
| 1 | Фикстура matrix: lead **Node.js** + user tags **`yii2`** (или `fontlab`) | ⏳ `preprod_ai_matrix.py --scenario skills_mismatch` |
| 2 | Ожидание: `reply_draft` **не пустой** · без 5xx · стек из **ТЗ**, не из профиля | |
| 3 | Нет галлюцинации «опыт на Yii2» на Node-заказе (O128) | |
| 4 | API: `POST …/draft` при km=0 — **200/202**, не hang (O62) | ручная S6-b |

**Пока скрипта нет:** ручная **S6-b** (ниже). После Coder — прогон в S1.

---

## Слой 2 — Сайт Playwright (S2, S5 частично)

**Только боевой/staging URL** (DNS готов):

```powershell
.venv\Scripts\python.exe scripts\preprod_playwright\smoke.py --base-url https://rawlead.ru
```

Отчёт: `data/preprod_playwright_report.json`

| Сценарий | Что проверяет |
|----------|----------------|
| `lenta_loads` | `/lenta/` без error banner |
| `multi_category` | chip «Дизайн» не ломает ленту |
| `skills_apply` | «Навыки ▾» → чип → «Применить» |
| `cabinet_login_stub` | `/cabinet/` — блок входа |
| `no_verdict_chips` | нет «Брать / Не брать / Сомнительно» на карточках |

| Критерий S2 | PASS когда |
|-------------|------------|
| Все 5 сценариев | `s2_pass: true` |

Debug с окном браузера: `--headed`

---

## Слой 3 — API нагрузка (S3)

### S3-pre — лимит соединений Postgres (edge case, **до** k6/load)

**Prod БД:** **Neon Postgres** (`DATABASE_URL`), не Supabase — но лимит **max connections** тот же класс проблем.

**Как сейчас в коде:** `NeonLeadStorage.connection()` → **`psycopg.connect()` на каждый запрос** без app-level pool (`src/pg_storage.py`). 50 воркеров = до **50 одновременных** сессий к Postgres.

| Симптом при перегрузе | Значение |
|-----------------------|----------|
| p95 **> 5000 ms**, рост 502 от nginx | connection starvation / DB reject |
| `too many connections` · `53300` · `42P05` | лимит Neon исчерпан |
| 5xx **> 1%** только под нагрузкой | не «медленный API», а **DB pool** |

**Перед запуском S3 (checklist):**

| # | Проверка |
|---|----------|
| 1 | **`DATABASE_URL`** на VPS — **pooler** Neon (host `*-pooler.*` или порт **6543**), не direct при 50 VU. См. Neon dashboard → Connection pooling. **Проверка:** `python scripts/check_neon_pooler.py` (локально/VPS env) · в логе `rawlead-api` startup: `db: pooler`. |
| 2 | Если только direct URL — **снизить** load: `--workers 15–20` или k6 `VUS=20`, не 50 с первого раза. |
| 3 | **Ramp-up:** 2 мин × 10 VU → 3 мин × 30 → 5 мин × 50 (k6 stages или два прогона `preprod_load_feed.py`). |
| 4 | Во время прогона: `journalctl -u rawlead-api -n 50` — нет лавины `psycopg` / `connection` / `53300`. |
| 5 | **→ Coder backlog (O129):** app-level pool или `psycopg_pool` + cap; до фикса — жёсткий ceiling VU в runbook. |

**PASS S3 с оговоркой:** p95 < 2s @ целевых VU **после** pooler/ramp. FAIL если 502/5xx коррелируют с ростом workers — сначала DB, потом nginx.

### Вариант A — k6 (если установлен)

```powershell
k6 run -e API_URL=https://api.rawlead.ru -e VUS=50 -e DURATION=5m scripts/preprod_k6_feed.js
```

Сводка: stdout + `data/preprod_k6_summary.json`

### Вариант B — Python (без k6)

```powershell
.venv\Scripts\python.exe scripts\preprod_load_feed.py --api-url https://api.rawlead.ru --workers 50 --duration 300
```

Отчёт: `data/preprod_load_summary.json`

| Критерий S3 | PASS когда |
|-------------|------------|
| `GET /v1/feed?limit=20` p95 | **< 2000 ms** |
| Ошибки 5xx | **< 1%** запросов |
| Итог | `s3_pass: true` |

Эндпоинты в прогоне: `/health`, `/v1/feed?limit=20`, `/v1/skills/catalog` — **без** L1/L2.

**Красные флаги:** CORS на WP; 502 от nginx; p95 > 5 с при 20 VU; **Postgres connections** (S3-pre).

---

## Слой 4 — Радар на VPS (S4)

**Владелец на VPS** (после E2 или Site ▶ на сервере):

1. `systemctl status rawlead-radar` — active
2. `tail -f /opt/rawlead/data/radar_site.log` — 2–4 цикла FL+Kwork
3. В футере цикла: `neon_insert` или `neon_replay` > 0 (или явная причина `0`)
4. Нет лавины `ai:http:401` / `429`

### S4-pre — ловушка «бесконечного ретрая прокси»

**Боль:** все слоты в бане → `exchange_get` крутит cascade (`max_attempts ≈ slots × strikes` в `exchange_proxy.py`) → **цикл радара растягивается**, кажется что «радар завис».

| Красный флаг в `radar_site.log` | Что значит |
|--------------------------------|------------|
| `proxy cascade exhausted` / `pool exhausted (0/N alive)` **каждый цикл** | ingest **заблокирован** прокси |
| Один `proxy=host:port` + 403/timeout **много строк подряд** | ретраи на мёртвый слот |
| `cycle_sec` **>>** нормы (напр. >180s при ~60s) | цикл съели fetch + Playwright retries |
| `health:fl kind=proxy` при живом kwork | per-source бан FL |

**Перед S4:** `/ops/` → ≥1 живой слот FL/Kwork · при exhausted → **«Сбросить баны»** · 3 цикла без spam `cascade exhausted`.

**PASS S4:** 2–4 цикла · нет runaway `cycle_sec` · kind≠proxy на primary (или явный fix).

Записать в [`STATUS.md`](../team/common/STATUS.md) § PRE-PROD-STRESS одну строку baseline, напр.:

`цикл FL+Kwork ~N мин │ ИИ L1=M │ neon_insert=K`

---

## Ручная приёмка владельца (S5, S6)

| # | Действие | ~время |
|---|----------|--------|
| S5 | 15 мин на `https://rawlead.ru/lenta/` — 10 карточек осмысленные, без вердикт-чипов | 15 мин |
| S6 | `/cabinet/`: смена навыков → другой `reply_draft` на том же лиде (L3 uniquify) | 10 мин |
| **S6-b** | **skills_mismatch:** в ЛК навыки **Yii2/FontLab** (нет в ленте) → отклик на **Node.js** лид → draft **≤30s**, текст **по ТЗ**, без Yii2/«опыт», без 5xx/hang | 5 мин |

**S6-b PASS:** «По ТЗ вижу…» + Node из описания · **не** «на Yii2 делал» · API не 502.

Подписать в чат Lead: «S1–S6 зелёные» → «едем на прод».

---

## Порядок прогона

```
1. DNS + certbot + WP theme (владелец)
2. preprod_ai_matrix.py          → S1 (+ S1-b когда Coder)
3. preprod_playwright/smoke.py   → S2
4. S3-pre: Neon pooler / ramp    → затем k6 или load
5. radar_site.log (S4-pre прокси) → S4
6. глазами S5–S6–S6-b            → владелец
```

---

## Опционально: P5-E2 радар на VPS

См. [`DEPLOY_VPS.md`](DEPLOY_VPS.md) § E2 — **после** E1 и DNS. Перед слоем 4: стоп Site на ПК, один `rawlead-radar` на VPS.

---

## Файлы скриптов

| Путь | Роль |
|------|------|
| `scripts/preprod_fixtures.py` | 12 фикстур × 4 category |
| `scripts/preprod_ai_matrix.py` | S1 |
| `scripts/preprod_k6_feed.js` | S3 (k6) |
| `scripts/preprod_load_feed.py` | S3 (Python) |
| `scripts/preprod_stress_v2.py` | O129 Wave 2 orchestrator |
| `scripts/preprod_draft_burst.py` | O129 draft burst (cap 20) |
| `scripts/preprod_playwright/ux_audit.py` | S2 / O37c (U1–U10 + LLM) |
| `scripts/preprod_playwright/smoke.py` | S2 smoke (legacy 5 сценариев) |

Отчёты пишутся в `data/preprod_*.json` (gitignore ок).

---

---

## Wave 1 — ✅ 2026-06-07 (owner)

**Цель:** прогнать **существующие** скрипты на prod · baseline + красные флаги до O129.

### Sign-off (факт)

| Gate | PASS | Значение |
|------|------|----------|
| UX anon | ✅ | 24/24 · `preprod_ux_audit_anon.json` |
| UX free | ✅ | 24/24 · `preprod_ux_audit_free.json` |
| UX premium | ✅ | 24/24 · `preprod_ux_audit_premium.json` |
| Smoke | ✅ | 5/5 · `preprod_playwright_report.json` |
| Load S3 | ✅ | p95 feed **1846ms** · 0% err · 3047 req |
| AI S5 | ✅ | **96%** draft+tools (50 sample) |
| Radar S4 | ✅ | FL **4/4** after ban clear + O110-B deploy |
| ux_journey | ⏸ | J1–J11 → **Wave 2 (O129)** |
| LLM human.md | ⏸ | optional · Wave 2 |
| load 50 VU | ⏸ | Wave 2 S3-pre ramp |

```powershell
cd C:\Users\hramo\uisness

# 1) UX полный (desktop) — U1–U10 + LLM
.venv\Scripts\python.exe scripts\preprod_playwright\ux_audit.py --base-url https://rawlead.ru

# 2) User journeys J1–J11 (draft ×2, mobile J10) — нужен RAWLEAD_PREPROD_ACCESS_TOKEN premium
.venv\Scripts\python.exe scripts\preprod_playwright\ux_journey.py --base-url https://rawlead.ru

# 3) Smoke 5 сценариев
.venv\Scripts\python.exe scripts\preprod_playwright\smoke.py --base-url https://rawlead.ru

# 4) API read load — S3-pre: pooler/ramp, затем workers (не 50 с ходу без pooler)
.venv\Scripts\python.exe scripts\preprod_load_feed.py --api-url https://api.rawlead.ru --workers 20 --duration 180
# если OK → повтор --workers 50 --duration 300

# 5) ИИ audit ($0 heuristics)
.venv\Scripts\python.exe scripts\preprod_ai_prod_audit.py --profile site --limit 50

# 6) VPS radar — 2–4 цикла в radar_site.log (SSH tail)
```

| # | PASS | Артеfact |
|---|------|----------|
| W1 | ux_audit 0 critical | `data/preprod_ux_audit_human.md` |
| W2 | ux_journey J5 draft OK | `data/preprod_ux_journey.md` |
| W3 | load p95 < 2s, 5xx < 1% | `data/preprod_load_summary.json` |
| W4 | S4 radar без лавины 403/proxy | log snippet |
| W5 | audit ≥95% draft | `preprod_ai_prod_audit_human.md` |

**Anon/free/premium:** Wave 1 покрывает **anon** (J7, smoke) + **premium** (J5/J8 с token). **Trial/free logged** — глазами 10 мин или ждём O129 matrix.

**Не гонять Wave 1:** 100+ concurrent draft (сжигает Gemini).

---

## Wave 2 — O129 (Coder)

**Pre-gate O131-PERF (owner, до полного rerun):** deploy § O131 в `CODER_PROMPT.md` · Neon **pooler** на VPS · затем Wave 2 gates ниже.

Полная симуляция: тиры × draft burst × TZ × **timings JSON** × parser snapshot. § **O129-STRESS-V2** в `CODER_PROMPT.md`.

```powershell
cd C:\Users\hramo\uisness

# Полный прогон (ramp 10→30→50 VU, draft×20, J1–J11, TZ, parsers)
.venv\Scripts\python.exe scripts\preprod_stress_v2.py `
  --base-url https://rawlead.ru `
  --api-url https://api.rawlead.ru `
  --vps-log

# Быстрый smoke orchestrator (короткий ramp, draft×5)
.venv\Scripts\python.exe scripts\preprod_stress_v2.py --quick --skip-journey

# Только draft burst
.venv\Scripts\python.exe scripts\preprod_draft_burst.py --api-url https://api.rawlead.ru

# S1-b отдельно
.venv\Scripts\python.exe scripts\preprod_ai_matrix.py --profile site --scenario skills_mismatch
```

| Артеfact | Путь |
|----------|------|
| Orchestrator JSON | `data/preprod_stress_v2.json` |
| Human md | `data/preprod_stress_v2.md` |
| Draft burst | `data/preprod_draft_burst.json` |
| skills_mismatch | `data/preprod_skills_mismatch.json` |
| Journey (stress) | `data/preprod_ux_journey_stress.json` |

| Gate | PASS |
|------|------|
| Load p95 feed | < 2s @ 50 VU (после S3-pre ramp) |
| Draft burst | 0% 5xx · p95 draft < 90s · 429 в отчёте |
| TZ | ≥2/3 `[TZ attachment — извлечено` в detail |
| UX J1–J11 | 0 critical |
| Parsers | не все red · cascade < 5 · cycle_sec ≤180s |
| S1-b | skills_mismatch pass |

**Env:** `RAWLEAD_PREPROD_ACCESS_TOKEN` (premium) · опц. `RAWLEAD_PREPROD_FREE_TOKEN` · `RAWLEAD_PREPROD_TRIAL_TOKEN` · `DATABASE_URL` для TZ/skills · `--no-mint` если токены уже в `.env.site`.

**Не гонять:** mass regen · judge · правки proxy/env.

---

## O218 — Quiz E2E (Playwright j1–j7)

**Gate pre-ads** · prod URL · изолированный browser context на persona.

```powershell
cd C:\Users\hramo\uisness

# Mint tokens (once)
.venv\Scripts\python.exe scripts\preprod_mint_token.py --account acc1 --write-env-site
.venv\Scripts\python.exe scripts\grant_premium_local.py --username RawLead --plan agent --days 30
# → RAWLEAD_MONICA_TOKEN in .env.site (see PREPROD_ACCOUNTS.md)

# Desktop j1–j7
.venv\Scripts\python.exe scripts\preprod_playwright\quiz_e2e.py --base-url https://rawlead.ru

# Mobile j1,j2,j5,j7 @ 390×844
.venv\Scripts\python.exe scripts\preprod_playwright\quiz_e2e.py --base-url https://rawlead.ru --viewport mobile

# Subset / debug
.venv\Scripts\python.exe scripts\preprod_playwright\quiz_e2e.py --ids j1,j2,j5 --headed --slow-mo 100

# pytest import smoke (full prod E2E: RAWLEAD_O218_E2E=1)
.venv\Scripts\python.exe -m pytest tests/test_o218_quiz_e2e.py -q
```

| Artifact | Path |
|----------|------|
| JSON | `data/preprod_quiz_e2e.json` |
| Screenshots (fail) | `data/preprod_quiz_e2e/` |

**Env:** `RAWLEAD_PREPROD_ACCESS_TOKEN` · `RAWLEAD_MONICA_TOKEN` · opt. `DATABASE_URL` (Neon j3)

---

## Parser: «сломан» vs «заказов нет»

**Где смотреть:** @FLPARSINGBOT `/status` · `/ops/` биржи · строка `health:fl` в `radar_site.log`.

| Симптом | Скорее всего | Действие |
|---------|--------------|----------|
| 🟢 **last_ok < 15 мин** · `downloaded > 0` · `new=0` | Парсер **жив**, фильтры L0/L1 или dup | OK для launch |
| 🟢 fetch ok · `downloaded=0` · kind=**ok** | Лента биржи **пустая** или вёрстка 0 карточек | Сверить сайт руками; если на FL есть заказы — тикет parse |
| 🔴 kind=**proxy** / **403** / pool exhausted | Прокси | `/ops/` → сброс баны · switch slot |
| 🔴 kind=**browser** / antibot | Playwright/YouDo | proxy/antibot runbook |
| 🟡 **15–45 мин** без ok | Secondary редкий опрос или тишина | Не паника; смотри `last_downloaded` |
| 🔴 **> 45 мин** без ok | Вероятно **не работает** | Mechanic или `/ops/` |

**Правило:** `downloaded ≥ 1` за цикл → ingest **не мёртв**. `new=0` ≠ «парсер сломан».

---

_Lead · Wave 1+2 · edge cases S3-pre/S4-pre/S1-b · 2026-06-07_
