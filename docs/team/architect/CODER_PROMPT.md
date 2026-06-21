# Coder — hot queue (active)

**→ Now:** post-M1 backlog (CSP/HSTS nginx · pool/COUNT load)

**Index:** G0–G10 ✅ · MiMo ✅ · **PRE-M1 security** M1+M2 ✅ **2026-06-21**

---

## § PRE-M1-SECURITY — Lead ✅ 2026-06-21

**MiMo M1+M2:** `_resolve_user_id` Bearer-only · `RADAR_CORS_ORIGINS` на VPS.

| Проверка | Результат |
|----------|-----------|
| pytest G0 | **32 passed**, 1 skipped |
| `GET /v1/me/feed` без Bearer | **401** prod |
| `X-RawLead-User-Id` без Bearer | **401** (unit) |
| deploy | `_deploy_pre_m1_security_vps.py` |

**Post-M1:** CSP/HSTS · JWT httpOnly · rate-limit — MiMo backlog.

**Владелец:** посевы M1 **после** G-SEC + G8–G10 · runbook [`PREPROD_STRESS_RUN.md`](../../ops/PREPROD_STRESS_RUN.md)

---

## § G-SEC — безопасность

**Авто:** G0 pytest ✅ **2026-06-21** — `30 passed`, `1 skipped`.

**S-1 ✅ (2026-06-21 @coder, prod `api.rawlead.ru`):**
| Проверка | Код |
|----------|-----|
| JWT acc1 `GET /v1/me/replies` | **200** · inbox только user acc1 |
| JWT monica `GET /v1/me/replies` (изоляция) | **200** · overlap lead_id с acc1 = **0** |
| JWT acc1 `POST /v1/me/leads/999999991/draft` (нет в ленте) | **404** |

**S-2:** владелец 5 мин — `/ops/` под паролем · webhook без секрета → 401/403

**Не в scope G-SEC:** CSP/HSTS · JWT localStorage · rate-limit — post-M1 (MiMo backlog)

---

## § G7b + CABINET — Lead ✅ 2026-06-21

**Commits:** `3e12011` (L2 tools finalize) · `2af72a1` (stress PASS + InboxCard link).

**Артефакт:** `data/preprod_stress_v2.json` **09:52Z** · `pass_summary.pass: true` · l2 **100%** · draft p95 **~22s** · load p95 **1101ms**.

**Осталось:** ~~deploy~~ ✅ Lead 2026-06-21.

---

## § G7-SKILLS-VPS-USER (Lead ✅ 2026-06-21)

`preprod_ai_matrix` + `_ensure_preprod_test_user` · `data/preprod_skills_mismatch.json` PASS.

---

## § G7a-env (Lead ✅ 2026-06-21)

tunnel `:15432` · free acc2 mint · trial JWT · `--quick --skip-journey` → **tier_matrix ✅** · **tz 3/3 ✅** · load p95 **1651ms ✅** · `data/preprod_stress_v2.json`

**Overall FAIL** — не блокер G7a-env: `l2_auto` 60% · `draft_burst` p95 96s>90s · `skills_mismatch` FK (§ выше).

---

## § DEPLOY-WIN-NPM (Lead ✅ 2026-06-21)

`deploy-web-rawlead-vps.py` — `npm.cmd` + `shell=nt`.

---

**Артефакт:** `data/preprod_stress_v2.json` · commit `92060b7`

| Gate | Результат |
|------|-----------|
| load_p95_feed | ✅ **1139 ms** @50 VU |
| draft_burst | ✅ |
| parsers | ✅ |
| tier_matrix | ❌ free token → `plan=null` · trial token missing |
| tz_leads / l2 | ❌ без tunnel `DATABASE_URL` :15432 |

**DoD G7a (smoke):** load PASS — **✅**

**§ G7a-env (следующий шаг @coder):**
1. SSH tunnel VPS Postgres `:15432` · `.env.site` sync
2. Mint/refresh `RAWLEAD_PREPROD_FREE_TOKEN` · `RAWLEAD_PREPROD_TRIAL_TOKEN` (acc2/acc3)
3. Re-run: `.venv\Scripts\python.exe scripts\preprod_stress_v2.py --quick --skip-journey`
4. DoD: tier_matrix ✅ · tz ≥2/3

**После G7a-env PASS:** G7b full · G-SEC

---

## § G7a — load quick smoke (архив prompt)

## § G6 — L3 uniquify (Lead ✅ 2026-06-21)

`preprod_ai_prod_audit_judge.md` · **Accept L3: ✅ PASS** · 2026-06-20T18:24Z · 25/25 · uniq **3.04** · combined **4.19** · send **68%** · leak **0%** · L3 v4 `l3_opener_too_similar` · deploy API VPS.

---

## § YOUDO-T14878013 (Lead ✅ 2026-06-21)

Lead #8256 delist · `lead_pipeline` always fetch YouDo detail · pytest `test_youdo_long_listing_snippet_still_fetches_detail` · [`problems/2026-06-20-youdo-t14878013-mismatch.md`](../../problems/2026-06-20-youdo-t14878013-mismatch.md) · **deploy radar/API** если ещё не на prod.

---

## § FEED-MULTI-FILTER (Lead ✅ 2026-06-21 · **prod**)

`feed-filters.ts` · multi category/source · prod JS `page-50500e5c9078817b.js` · `lenta/index.html` 2026-06-21 06:40 UTC · owner smoke: dropdown «Фильтр» → биржи · чипы multi-toggle.

---

## § YOUDO-T14878013 — карточка ≠ биржа (архив)

**Симптом:** https://youdo.com/t14878013 — в ленте **полное несоответствие** (скрин: «Закрытый парсинг», до 400₽, web scraping/python) vs реальная страница YouDo.

**Гипотезы (проверить по факту):**
1. listing snippet попал в `title`/`body`, detail fetch fail → `detail:short` (см. [`problems/2026-06-16-youdo-antibot-browser.md`](../../problems/2026-06-16-youdo-antibot-browser.md))
2. неверный `url` / external id / чужая карточка в listing
3. устаревший body после редиректа/antibot HTML

| # | Действие | DoD |
|---|----------|-----|
| 1 | VPS/SQL: `SELECT id, source, title, body, url, budget_text, task_summary, created_at FROM leads WHERE url ILIKE '%14878013%'` | lead_id + поля в отчёт |
| 2 | Сравнить с live: detail fetch / curl / debug HTML `data/debug_listings/youdo_*` | таблица: поле в БД vs YouDo live |
| 3 | Root cause в `youdo_parser.py` / `exchange_browser_fetch.py` / `lead_pipeline.py` | фикс + pytest при возможности |
| 4 | Если лид мусор — delist/hide + **не** показывать в `/v1/feed` | owner smoke: карточка исчезла или совпадает |
| 5 | Кратко в `docs/problems/2026-06-20-youdo-t14878013-mismatch.md` | симптом · причина · фикс |

**Deploy:** API/radar если parser/pipeline · Next не трогать если только ingest.

---

## § FEED-MULTI-FILTER — несколько категорий и бирж (owner 2026-06-20)

**Запрос:** в ленте выбирать **несколько категорий** и **несколько бирж** сразу. Кнопка **«Все»** (категории) — сброс остальных, показать всё.

**API уже есть:**
- `GET /v1/feed?category=dev,design` · `parse_category_param` в `src/lead_category.py`
- `GET /v1/feed?source=fl,youdo,kwork` · `parse_feed_source_param` в `src/public_feed.py`

**Менять backend только если дыра в API.**

### Категории (чипы на desktop + sheet на mobile)

| Правило UX | Поведение |
|------------|-----------|
| **«Все»** | `categories=[]` → API без `category` · снять подсветку с dev/design/… |
| Клик **dev/design/…** | toggle в `Set` · **не** radio · можно 2+ активных |
| Клик «Все» при активных | сброс multi → показать все категории |
| Сняли последнюю категорию | = «Все» (пустой фильтр) |
| Pill / label | «Разработка · Дизайн» или «2 категории» |

### Биржи (dropdown / sheet)

| Правило | Поведение |
|---------|-----------|
| Чипы бирж | multi-toggle (как категории) |
| API | `source=fl,youdo` comma-join |
| Сброс | все биржи (пустой `source`) |

| # | Файлы | DoD |
|---|-------|-----|
| 1 | `FilterBar.tsx` — desktop category chips multi | dev+design одновременно · «Все» сбрасывает |
| 2 | `FilterSheet.tsx` — mobile categories + sources multi | то же |
| 3 | `FilterDropdown.tsx` — sources multi | |
| 4 | `app/lenta/page.tsx` · `lib/api.ts` — `categories: string[]` `sources: string[]` → `category=dev,design` `source=fl,youdo` | feed reload |
| 5 | E2E опц. | `next_e2e` J3 / `ux_journey` J3 не регресс |

**Не в scope:** WP theme · saved filters ЛК.

---

## § FEED-MULTI-SOURCE — (merged → § FEED-MULTI-FILTER выше)

_legacy index only — см. § FEED-MULTI-FILTER_

**Что такое L3 (канон, не путать):**
- **L2** = один shared `reply_draft` на лид (`leads.reply_draft`) — это G5 ✅.
- **L3** = `rephrase_reply_draft_per_user()` — **переписать L2** другим каркасом/тоном для пары `user_id + lead_id` (O89 anti-copypaste).
- **НЕ** подстановка навыков из ЛК в текст. `user_id` → seed вариации; стек **только из base (L2)**.
- Код: `src/ai_analyze.py` · `src/l3_human_style.py` · `match_push._build_personalized_reply`.

**Что НЕ делать в G6:** skills_mismatch / O128 / «разные навыки → разный стек» — **post-M1** (`--scenario skills_mismatch` в matrix).

**Прогон:**
```powershell
.venv\Scripts\python.exe scripts/preprod_ai_prod_audit.py --profile site --judge-l3 --judge-l3-limit 25
```
(флаги `--judge` / `--judge-l1` **не обязательны** для gate G6)

**Env:** `.env.site` — `DATABASE_URL` (**VPS Postgres**, не Neon) · OpenRouter · `AI_ENABLED=1`

**БД локально:** SSH-туннель → [`PREPROD_ACCOUNTS.md`](../../ops/PREPROD_ACCOUNTS.md) § 1b · `DATABASE_URL=...@127.0.0.1:15432/rawlead` · или mint/audit на VPS.

**Как скрипт собирает пары L3:**
1. Из БД: `user_lead_replies` vs `leads.reply_draft` (source=db), где personal ≠ shared.
2. Добор synthetic: `rephrase_reply_draft_per_user` на свежих лидах для 2 audit user_id (`…a101`, `…a102`).

**Judge:** LLM сравнивает **shared_reply** vs **personal_reply** → метрики uniquify.

| Метрика | PASS |
|---------|------|
| `accept_l3` | **true** |
| `avg_uniqueness` | ≥ **3.0**/5 |
| `avg_combined_3` | ≥ **3.8**/5 |
| `send_as_is_pct` | ≥ **50%** |
| `forbidden_leak_pct` | ≤ **10%** (нет Cursor/ИИ/ChatGPT в personal) |

**Артефакты:** `data/preprod_ai_prod_audit.json` · `data/preprod_ai_prod_audit_judge.md` (секция **L3 — per-user reply**) · `preprod_ai_prod_audit_human.md`

**Если FAIL:** правки **только L3** (`l3_human_style.build_uniquify_system`, `rephrase_reply_draft_per_user`, retry `l3_too_similar`) · deploy API если менял `src/` · **не** L2 shared prompt (G5/L2 уже ✅).

**После PASS:** Lead verify → G7a `preprod_stress_v2.py --quick`

**Lead verify 2026-06-20:** код L3 v2 + neon guard — OK · gate `preprod_ai_prod_audit_judge.md` **старый (2026-06-14, без L3)** → **FAIL** до прогона с VPS `DATABASE_URL`.

| # | Действие | DoD |
|---|----------|-----|
| 1 | **Локальный `.env.site`:** VPS Postgres tunnel `:15432` — ✅ owner 2026-06-20 (`scripts/_fix_local_env_vps_db.py`) | neon guard OK |
| 2 | Прогон `--judge-l3 --judge-l3-limit 25` | `Accept L3: ✅ PASS` в **gate** `preprod_ai_prod_audit_judge.md` |
| 3 | Commit: `l3_human_style.py` · `preprod_ai_prod_audit.py` · артефакты `data/preprod_ai_prod_audit*` | Lead verify |

---

## § NEON→VPS — канон БД (owner 2026-06-20)

**Факт:** prod `DATABASE_URL` = **Postgres на VPS** (`127.0.0.1:5432` на сервере) · [`PROD_FACTS.md`](../common/PROD_FACTS.md). Neon — **архив**, не preprod.

| Зона | Что сделать |
|------|-------------|
| **Локально** | `.env.site` — только VPS (tunnel `:15432` или mint на VPS) |
| **Hot docs** | `PREPROD_ACCOUNTS` · `PREPROD_STRESS_RUN` · `CODER_PROMPT` · `MIGRATE_NEON_TO_VPS_POSTGRES` — уже VPS |
| **`.env.example`** | комментарии «Neon» → «VPS Postgres» |
| **Скрипты preprod** | stderr/print «Neon» → «VPS Postgres» где про `DATABASE_URL` |
| **Не в этом шаге** | rename `neon_legacy_consumer.py` · архив `docs/problems/*neon*` · массовый refactor `neon_insert` в логах |

---

## § G5 — AI matrix (PRE-ADS-GATE) ✅

**Прогон:** `.venv\Scripts\python.exe scripts/preprod_ai_matrix.py --profile site`

**DoD:** `data/preprod_ai_report.json` · `s1_pass: true` · **12/12 L1+L2** · 0 errors · 401/429 нет

**Fix (2026-06-20):** `src/ai_analyze.py` — money auto-fill · tools min-2 после finalize + `analyze_lead_tools` fallback

---

## § G4-fix — UX journey (Lead ✅ 2026-06-20)

Desktop + mobile → `data/preprod_ux_journey.json` **11/11** · `j5_draft_ok: true` · 0 critical. Harness: `scripts/preprod_playwright/ux_journey.py`.

---

## § G3-POLISH — mobile + drafts (owner 2026-06-20 · до G4)

**Контекст:** G3 audit PASS 0 critical · LLM rating 3/5 · [`problems/2026-06-20-mimo-post-g1-e2e.md`](../../problems/2026-06-20-mimo-post-g1-e2e.md) не блокер. Владелец: закрыть polish **до G4**.

**Не трогать:** FAB поддержки (жёлтая кнопка) — overlap на карточке **оставляем**.

| # | Что | Файлы | DoD |
|---|-----|-------|-----|
| **1** | **Бегущая строка** на главной — **разделитель жёлтый→серый**, не внутри hero-контента. Вынести marquee из `Hero.tsx` между `<Hero />` и `<LivePreview />` (`page.tsx` или `SkillsMarquee.tsx`). Чёрная полоса + border = граница `#FACC15` / `#EEEDEA`. На мобилке не сжимать CTA. | `components/home/Hero.tsx` · `app/page.tsx` · опц. новый компонент | owner smoke 390px: строка **внизу жёлтого**, сразу над серым блоком «Живая лента» |
| **2** | **Tap target 44px** на mobile для «Написать отклик» и «Отклик ✓» (`h-9`→`min-h-11` @max-width 640 или `.rl-card-cta--replied-slot`) | `FeedCard.tsx` · `globals.css` | min-height **44px** touch area · desktop без регресса |
| **3** | **Лента 390px** — меньше тесноты: header stack (заголовок / кабинет), чуть больше gap/padding в карточке, не ломать 2-col md | `app/lenta/page.tsx` · `FeedCard.tsx` · `FilterBar.tsx` | Playwright viewport 390 — без horizontal scroll · читаемые отступы |
| **4** | **Черновики L2** — поднять `draft_as_is` (сейчас **3.67**). Тюнинг `_shared_reply_system` / `l3_human_style` / retry в `analyze_shared_reply_draft` — конкретнее по ТЗ, меньше шаблона, без воды. **Не** L3 uniquify (это G6). | `src/ai_analyze.py` · `src/l3_human_style.py` | Перегнать `ux_audit.py` U10b → **avg draft_as_is ≥ 4.0** · vendor-lock 0 |
| **5** | **O280 diff** из G3 (если ещё uncommitted): quota · Отклик ✓ badge · globals · Support FAB error — **включить в commit** | `rawlead-next/*` | один commit с §1–3 |

**Deploy:** Next `deploy-web-rawlead-vps.py` · API если §4 (`deploy-*-vps` api unit restart).

**DoD:** ~~см. таблицу~~ · **Lead verify 2026-06-20:** UI §1–3 ✅ · L2 retry §4 в коде · **FAIL:** `ux_audit` 3 critical · `draft_as_is` **3** (цель ≥4) · G1 **24/24** после deploy ✅

---

## § PRE-ADS-GATE — порядок (до M1 wave 1)

**Цель:** люди приходят в стабильное приложение. **Один шаг за раз** — PASS → следующий → Lead verify → галочка в [`TASKS.md`](../common/TASKS.md).

**Env:** `.env.site` · `RAWLEAD_PREPROD_ACCESS_TOKEN` (premium) · см. [`PREPROD_ACCOUNTS.md`](../../ops/PREPROD_ACCOUNTS.md)

**MiMo (бесплатно):** параллельно **M0–M4** · скиллы security/code-review · [`.mimocode/MIMO_RULES.md`](../../../.mimocode/MIMO_RULES.md) § PRE-ADS · отчёты → `docs/problems/` → Lead triage → фикс @coder.

| Шаг | Кто | Прогон | PASS | Артефакт |
|-----|-----|--------|------|----------|
| **G0** | @coder | `pytest tests/test_o280_next_e2e.py tests/test_o116_feed.py tests/test_pre_ads_mimo_wave1.py tests/test_yookassa_billing.py -q` | all green | stdout |
| **G1** | @coder | `scripts/preprod_playwright/next_e2e.py --base-url https://rawlead.ru --gate-all` | **24/24** | `data/preprod_next_e2e.json` |
| **G2** | @coder | `scripts/preprod_playwright/smoke.py --base-url https://rawlead.ru` | **5/5** `s2_pass` | `data/preprod_playwright_report.json` |
| **G3** | @coder | `scripts/preprod_playwright/ux_audit.py --base-url https://rawlead.ru` | **0 critical** | `data/preprod_ux_audit_human.md` |
| **G4** | @coder | `scripts/preprod_playwright/ux_journey.py --base-url https://rawlead.ru` | J1–J11 0 critical · J5 draft OK | `data/preprod_ux_journey.md` |
| **G5** | @coder | `scripts/preprod_ai_matrix.py --profile site` | `s1_pass: true` | `data/preprod_ai_report.json` |
| **G6** | @coder | `scripts/preprod_ai_prod_audit.py --profile site --judge-l3 --judge-l3-limit 25` | L3 uniq + send gate PASS | `data/preprod_ai_prod_audit_human.md` |
| **G7a** | @coder | `preprod_stress_v2.py --quick` | smoke load PASS | `data/preprod_stress_v2.json` |
| **G7b** | @coder | **full:** `preprod_stress_v2.py` без `--quick` (ramp **10→30→50 VU** · draft burst **×20** · journey · parsers) | p95 feed <2s @50 VU · draft 0% 5xx | same JSON |
| **G-SEC** | @coder | pytest + ручной S-1/S-2 (§ ниже) | нет P0 FAIL | STATUS |
| **M0–M4** | **MiMo audit** + owner | static + `data/preprod_*` · skills security-review | P0=0 в отчёте | `docs/problems/*-mimo-*.md` |
| **G8** | owner | VPS `radar_site.log` 2–4 цикла · `/ops/` прокси живы | нет cascade exhausted | STATUS § radar |
| **G9** | owner | S5–S6-b ручная ([`PREPROD_STRESS_RUN.md`](../../ops/PREPROD_STRESS_RUN.md)) | 15+10+5 мин | чат Lead «S5–S6 зелёные» |
| **G10** | owner | anon: квиз → TG login → % в ленте | воронка ок | FOR_YOU |

**Уже зелёное (не повторять без регресса):** O200 L2 judge owner bar 2026-06-18 · O280 feed UX owner 2026-06-20 · E2E gate 24/24 2026-06-20 (перегнать G1 после каждого Next deploy).

**MiMo M0 (2026-06-20):** [`problems/2026-06-20-mimo-gsec-delta.md`](../../problems/2026-06-20-mimo-gsec-delta.md) — Wave1 #7 #8 ✅ · **новых P0=0** · nginx CSP/HSTS **P1 post-M1**

**MiMo M1 (2026-06-20):** [`problems/2026-06-20-mimo-post-g1-e2e.md`](../../problems/2026-06-20-mimo-post-g1-e2e.md) — **P0=0** · harness≈PA-5b ✅ · draft 404 security ✅ · **P1:** CTA на km=0 → post-M1

**Не блокирует M1:** PA-4 O208-B K-hide (freeze) · **nginx CSP/HSTS** (MiMo S1/S2 — post-M1, reload only) · **FeedCard CTA при km=0** (MiMo G1) · full pentest / bug bounty · repo audit A10–A11.

### § G-SEC — безопасность (не «взлом», но обязательно до посевов)

**Что это:** регрессия известных дыр + IDOR/inbox + оплата. **Не** нанимаем пентестера и **не** DDoS-им prod.

| Уровень | Что | Статус |
|---------|-----|--------|
| **Авто** | G0 pytest: webhook `compare_digest` · draft feed-membership 404 · inbox IDOR SQL · billing idempotent | в G0 |
| **Ручной S-1** | Чужой JWT → `/v1/me/replies` только свои · чужой `lead_id` draft → 404 если нет в ленте | @coder curl |
| **Ручной S-2** | `/ops/` не открыт без пароля · webhook без секрета → 401/403 | owner 5 мин |
| **Известный backlog** | JWT localStorage (XSS) · rate-limit `/v1/me/*` · **nginx CSP+HSTS** (MiMo S1/S2) · API proxy headers (S3) · `/ops/` nginx auth (S4) · owner UUID fallback (#18) · webhook HMAC body (#21) · ops len leak (#20) · cross-user L3 dedup | **post-M1** или hotfix если G-SEC S-1 FAIL |

Источник находок: [`problems/2026-06-20-mimo-pre-ads-readiness.md`](../../problems/2026-06-20-mimo-pre-ads-readiness.md) · [`problems/2026-06-20-mimo-post-g1-e2e.md`](../../problems/2026-06-20-mimo-post-g1-e2e.md) · [`problems/2026-06-20-mimo-gsec-delta.md`](../../problems/2026-06-20-mimo-gsec-delta.md) · Wave 1 закрыл #7 #8 · pool bypass в основном `_db_conn` (не 28 bare connect).

**Красные флаги (стоп посевы):** G1–G7b FAIL · G-SEC S-1 FAIL · ingest 🔴 >24h · proxy cascade каждый цикл · 429/5xx массово.

**После G0–G10 PASS:** Lead обновляет STATUS/TASKS → владелец → [`M1_SEEDING_CHECKLIST.md`](../marketing/M1_SEEDING_CHECKLIST.md).

---

## Shipped index

**O280-FEED-UX-R1+R2** ✅ owner 2026-06-20 · **O116-SUPPORT** ✅ · **PRE-ADS-MIMO W1** ✅ · **M1-bot-START** ✅
