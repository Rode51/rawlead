# Coder — hot queue (active)

**→ Now:** § **G6** (L3 judge uniquify)

**Index:** G0–G4 ✅ · G3-POLISH ✅ · draft_as_is-L2 ✅ · **G5** ✅ · **G6** ⏳

**Владелец:** посевы M1 **после** зелёного sign-off § PRE-ADS-GATE · runbook [`PREPROD_STRESS_RUN.md`](../../ops/PREPROD_STRESS_RUN.md)

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
