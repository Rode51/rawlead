# STATUS — архив (холодное хранилище)

**Не читать агентам по умолчанию.** Актуальный снимок: [STATUS.md](../common/STATUS.md).

Перенесено из hot STATUS **2026-05-30** (~1200 строк). Новые сдачи: одна строка в hot STATUS; детальный блок — сюда при необходимости.

---

## (архив) O37 load NO-GO (**2026-05-30**)

| Слой | Отчёт | Результат |
|------|-------|-----------|
| **S1** premium-lite matrix | `data/preprod_ai_report.json` (old) | **❌** L1 **12/12** · L2 **8/12** — **не путь сайта** |
| **S3** k6 (до SSL) | `data/preprod_k6_summary.json` (old) | **❌** fail **50%** — HTTPS wrong vhost |

Root cause закрыт в **O71** (nginx SSL api.rawlead.ru + shared draft path).

---

## ✅ S6 + O37c (**2026-05-30**)

| § | Результат |
|---|-----------|
| **S6** | владелец **ок** |
| **O37c** | **18/19** · U5 desktop ИИ flake · **U5 mobile ✅** |

---

## ✅ O70 cabinet + audit script (**Lead verify 2026-05-30**)

| Метрика | Было → Lead re-run |
|---------|---------------------|
| Pass | 11/19 → **17/19** |
| Critical | 8 → **2** (U5 desktop+mobile — ИИ flake, O67) |
| Mobile U1–U4,U7–U10 | **✅** |
| U7 | **✅** audit (prod **1.11.14** — cabinet JS **1.11.15** не на VPS) |
| Repo theme | **v1.11.15** · VPS **1.11.14** |

**→ Deploy** `deploy-wp-theme-vps.py` · S6 · manual U7 overlay после deploy.

---

## (архив) O37c прогон (**2026-05-30 · NO-GO S2**)

| Метрика | Значение |
|---------|----------|
| Pass | **11/19** |
| Critical | **8** |
| Desktop U2/U3 | **✅** (O69 подтверждён audit) |
| Mobile sheet U3/U8 | ❌ triage → **O70** ✅ |
| U7 cabinet modal | ❌ triage → **O70** ✅ |
| LLM | **1/5** · `data/preprod_ux_audit_human.md` |

**→ @coder** § O70 ✅ · re-run **18/19** · **→ S6**

---

## ✅ O69 filters/sort (**✅ Lead verify 2026-05-30 · prod v1.11.14 · владелец принял**)

| § | Проверка |
|---|----------|
| **Theme** | VPS `RAWLEAD_CHILD_VERSION` **1.11.14** ✅ |
| **t1–t2** | `feedCountSuffix()` → `state.sort` · `updateCount()` на смену sort ✅ prod JS |
| **t3–t4** | `row.category \|\| group.category` · «Популярные навыки» 2+ niche · desktop «Ещё навыки» ✅ |
| **Lenta** | `https://rawlead.ru/lenta/` **200** |

**→ Владелец:** S6 (390px + desktop) · re-run O37c U2/U8

---

## ✅ O64–O68 deploy prod (**Lead verify 2026-05-30**)

| § | VPS после deploy |
|---|------------------|
| **Theme** | **v1.11.14** (O69) · до O69 было **v1.11.13** |
| **Backend** | `delist_checker` · `l1_backlog_report` · `fetch_visible_unnotified_legacy` ✅ |
| **API** | `/health` → `draft_fail_per_hour:0` ✅ |
| **Legacy** | цикл **~2–3 мин** (16:07→16:10→16:12) · catch-up **8 в бот** |
| **Lenta** | `https://rawlead.ru/lenta/` **200** |
| **→ Владелец** | **S6** + **O37c audit** (O69 ✅ — глазами) |

---

## (архив) → O69 filters/sort (**2026-05-30**)

| Симптом | Статус |
|---------|--------|
| Count «пo датe» при sort match | **✅ v1.11.14** |
| «Ещё навыки» Tier B | **✅** |
| 2 ниши пустые навыки | **✅** |

---

## (архив) → O64–O68 код (**Coder 2026-05-30**)

| § | Суть | Файлы |
|---|------|-------|
| **O64** | `/status` L1 breakdown + ИИ строка | `radar_status.py` · `pg_storage.py` |
| **O65** | Delist batch | `delist_checker.py` · `sql/014_*` |
| **O66** | Legacy poll 60s | `neon_legacy_consumer.py` · `config.py` |
| **O67** | `/health` draft_fail_per_hour | `api_server.py` · `ai_analyze.py` |
| **O68** | «Отклик ✓» в CTA | `rawlead-feed.js` · **v1.11.13** |
| **Тесты** | `tests/test_o64_o67.py` **7/7** (Lead verify) | — |

---

## ✅ O37c-filters (**2026-05-30 · prod v1.11.13**)
| **Код** | `buildSheetContent` · `syncChipActiveStates` · `ensureSheetDelegation` · skills по category |
| **→ Владелец** | prod: Дизайн → Фильтры → chip highlight → S6 / re-run O37c |

---

## (архив) → O64–O67 (**владелец 2026-05-30**)

| § | Задача | Приоритет |
|---|--------|-----------|
| **O64** | L1 breakdown в `/status` + `clear_l1_backlog --by-age` | P0 |
| **O67** | ИИ draft fail (L1 OK, L2 intermittent) | P0 |
| **O66** | Legacy poll 1 мин + catch-up visible→@FLPARSINGBOT | P0 |
| **O65** | Delist: заказ снят с биржи → пропадает из ленты | P1 |

**Факт VPS:** L1 `visible=1` · draft 7578 fail / 7592 OK · legacy цикл **~10 мин**

---

## ✅ O37c-filters mobile bar (**Coder 2026-05-30 · theme v1.11.8 prod**)

| | |
|--|--|
| **Sheet build** | отдельные блоки: **Специализация** · **Навыки** (chips) · **Сортировка** — без clone `<details>` |
| **Fix** | навыки не показывались — hidden dropdown в bar |

---

## ✅ O37c-filters (**Coder 2026-05-30 · theme v1.11.5 prod**)

| | |
|--|--|
| **Scope** | навыки по специализации · `is-active` на chip · mobile sheet b1–b4 |
| **f1** | bar без изменений · skills по category · toggle draft · «Применить» |
| **f2** | openSheet: `readCategoriesFrom` + `renderSkillsCatalog` + `loadCatalog` · delegation без dup listeners · `.rl-cat-chip.is-active` в sheet |
| **CSS** | mobile sheet: skills/sort видны flat (не `display:none`) |
| **Файлы** | `rawlead-feed.js` · `rawlead.css` · `functions.php` · `style.css` |
| **Deploy** | **v1.11.5** · `deploy-wp-theme-vps.py` |
| **→ Lead/владелец** | re-run `ux_audit.py` U2 · U8 |

---

## ✅ WAVE-UX-MOBILE код (**Coder 2026-05-30 · theme v1.11.4**)

| | |
|--|--|
| **Scope** | M1–M5 · mobile `<768px` · desktop без регресса |
| **M1** | overflow-x hidden · карточки 100% · inbox padding |
| **M2** | burger + nav drawer · desktop nav скрыт на mobile |
| **M3/M5** | `[Фильтры ▾]` в filter bar · unified sheet · fix clone selector |
| **M4** | tap-outside collapse card · sheet overlay/close/Esc |
| **Файлы** | `header.php` · `page-lenta.php` · `rawlead-feed.js` · `rawlead.css` · `functions.php` |
| **→ Lead** | **✅ verify 2026-05-30** · **O37c-filters** → Coder **deploy сразу** → re-run O37c |
| **→ S6** | ⏸ после audit 0 critical mobile |

---

| | |
|--|--|
| **Скрипт** | `scripts/preprod_mint_token.py` — Telethon acc1 → Neon `agent` → `.env.site` |
| **Mint** | `tg_user_id=8233488286` · `user_id=895912a1-ffb6-46fb-be7e-4e051f2ff8c1` (≠ owner) |
| **Docs** | `PREPROD_ACCOUNTS.md` · `FOR_YOU.md` § mint + audit |
| **→ Тебе** | mint + audit ✅ · **→ Coder WAVE-UX-MOBILE** |

---

## ✅ D-O40 Design (**Lead verify 2026-05-30**)

| | |
|--|--|
| **Brief** | `DESIGNER_PROMPT.md` § WAVE-UX-MOBILE · `feed-cabinet-mvp.md` §7.6 |
| **Scope** | M1–M5 · приёмка m1–m11 · только `<768px` |
| **→ Дальше** | **@coder** WAVE-UX-MOBILE → deploy → re-run O37c |

---

## ✅ O37c код (**Lead verify 2026-05-30**)

| | |
|--|--|
| **Скрипт** | `scripts/preprod_playwright/ux_audit.py` — U1–U10 · desktop 1440 + mobile 390 |
| **Token** | exit 2 без `RAWLEAD_PREPROD_ACCESS_TOKEN` · запрет yandex-cdp без token |
| **LLM** | OpenRouter → `data/preprod_ux_audit_human.md` |
| **Docs** | `PREPROD_ACCOUNTS.md` · `PREPROD_STRESS_RUN.md` § O37c |

---

## ✅ O37c прогон (**2026-05-30** · **8 critical · LLM 1/5**)

| | |
|--|--|
| **Auth** | `chromium+token` · acc1 `895912a1-…` · **≠ owner** |
| **PASS** | **11/19** · mobile sheet/tap-outside — главные провалы |
| **U5 draft** | ✅ desktop + mobile (~19–21 с) |
| **→ Дальше** | **WAVE-UX-MOBILE** → re-run O37c |

---

## ✅ O37b Lead verify (2026-05-30)

| | |
|--|--|
| **b1** | **✅** tools v1.11.3 prod |
| **b3** | **⚠️** bot getMe OK · acc1 ❌ |
| **b4** | **❌ отклонён** — `ux_review.py` скрины-only · моб **5/5 ложно** → **O37c** |

---

## ✅ O37b Lead verify (2026-05-30)

| | |
|--|--|
| **b1** | On-demand L2 → `UPDATE leads.tools_required` · honest empty-state · theme **v1.11.3** |
| **b2** | `docs/ops/PREPROD_ACCOUNTS.md` · `ux_journey` **`cdp`/`dolphin-cdp`** · `.env.example` token/CDP |
| **b3** | `scripts/preprod_bot_smoke.py` → `data/preprod_bot_smoke.json` · **getMe OK** (@rawlead_bot) · Telethon acc1 ❌ (сессия/lock — ops) |
| **b4** | `data/preprod_ux_review.md` + скрины `data/preprod_ux_review/` · ПК 4/5 · моб 5/5 |
| **Playwright** | J5 **PASS** `browser: cdp` · draft 2/2 (7546, 7544) · CDP `127.0.0.1:9222` |
| **Тесты** | **14/14** unittest (+ `test_tools_persist_o37b`) |
| **→ Lead** | ~~deploy~~ **✅ v1.11.3** 2026-05-30 |
| **→ Дальше** | **O37 load** · bot acc1 ops · **S6** |

---

## ✅ O61 Lead verify + deploy (2026-05-30)

| | |
|--|--|
| **Theme** | **v1.11.2** prod |
| **API** | `no skill overlap` **удалён** · km=0 draft OK |
| **JS** | кнопка paid без km-gate |
| **Тесты** | **20/20** unittest |
| **→ Дальше** | **O37-UX** (обновить скрипт под O61) |

---

## ✅ O61 draft без km-порога (**Coder 2026-05-30**)

| | |
|--|--|
| **O61a** | API: убран `no skill overlap` · shared-cache при km=0 |
| **O61b** | feed JS: кнопка «Написать отклик» для paid без km>0 |
| **Theme** | **v1.11.2** · API `src/` |
| **Тесты** | `test_draft_skill_overlap_o61` 3/3 · draft suite **22/22** |
| **→ Lead** | ~~deploy~~ **✅** 2026-05-30 |
| **→ Дальше** | **O37-UX** |

---

## ✅ O60 Lead verify + deploy (2026-05-30)

| | |
|--|--|
| **Theme** | **v1.11.1** prod |
| **API/bot/radar** | **active** · `DRAFT_HOURLY_LIMIT=0` |
| **O60a** | anon feed `with_reply_draft=0` · badge только logged-in |
| **O60b** | лимит draft **выключен** (env=0) |
| **O60c/d** | `feedCountSuffix` + `initLivePreview()` на prod JS |
| **O60e** | цикл 12:42: `fl:id=5507331 visible=1` · FL page-1 иногда **FlListingError** (proxy) — ops |
| **Тесты** | **17/17** unittest локально |
| **→ Дальше** | **O37-UX** J1–J11 (J5 без 429) |

---

## ✅ O60 hotfix приёмки (**Coder + Lead 2026-05-30**)

| | |
|--|--|
| **O60a** | API: shared `reply_draft` не в `/v1/feed` · paid — только `user_lead_replies` · JS badge только logged-in |
| **O60b** | `DRAFT_HOURLY_LIMIT` env · default **0** = без лимита · UI 429 только если limit>0 |
| **O60c** | счётчик: «по дате» / «по совместимости» по sort+skills |
| **O60d** | главная live preview: `GET /wp-json/rawlead/v1/feed?limit=3` · fallback demo |
| **O60e** | FL partial pagination при сбое proxy page-2+ · `fetch_error` в логе |
| **Theme** | **v1.11.1** (bump) · API `src/` |
| **Тесты** | `test_feed_privacy_o60` 4/4 · draft 4/4 · `test_draft_async` 9/9 |
| **→ Lead** | ~~deploy~~ **✅** 2026-05-30 |
| **→ Дальше** | **O37-UX** (J5 auth, без 429) |

---

## ✅ O37-UX Lead verify (2026-05-30)

| | |
|--|--|
| **Gate** | **PASS** · 11/11 · 0 critical · J5 draft 2/2 |
| **Браузер** | `yandex-cdp` (CDP к Яндексу — **не** отдельное окно Chromium) |
| **Auth** | `has_auth: true` · cookies из профиля Яндекса |
| **→ Дальше** | **O37-AI + LOAD** · **S6** — 15 мин глазами владельца |

---

## ✅ O37-UX Playwright prod v1.11.2 (**Coder 2026-05-30**)

| | |
|--|--|
| **Скрипт** | `ux_journey.py` — O61: J5 без km>0 · CDP/has_auth fix |
| **Prod** | **J1–J11 PASS** (0 critical) · J5 draft **2/2** (leads 7566, 7554) |
| **Браузер** | `--browser yandex-cdp --headed` · auth из сессии Яндекс (CDP) |
| **Отчёты** | `data/preprod_ux_journey.json` · `.md` · скрины `data/preprod_ux_journey/` |
| **→ Lead** | UX green **с оговорками** → **O37b** |
| **→ Дальше** | **O37b** → load → **S6** |

---

## ✅ O59a draft stability (**Lead verify + deploy 2026-05-29**)

| | |
|--|--|
| **Theme** | **v1.11.0** prod |
| **API/bot** | **active** · `sanitize_draft_error_detail` · poll `failed`+`error` · 4× L2 retry |
| **Tests** | **14/14** unittest (draft_async + reliability + shared) |
| **→ Тебе** | Ctrl+F5 `/lenta/` · 2× «Написать отклик» · fail → причина + «Повторить» |
| **→ Дальше** | **O37-UX** green J5 → O37-LOAD |

---

## ✅ Wave-2 accept (**закрыта 2026-05-29**)

| Волна | Суть | Theme |
|-------|------|-------|
| O52–O54 | карточки · ₽ · ЛК · сосед · draft без цены | v1.10.5–6 |
| O55 | demo главная · collapse · TG | v1.10.7 |
| O56+O57 | async · shared draft · uniform cards | v1.10.8 |
| O58 | GET draft poll (WP) | **v1.10.9** |

**→ Дальше:** **O37-UX** → O37 load → S6.

---

## ✅ O38 Mechanic audit (**закрыт 2026-05-29**)

| | |
|--|--|
| **Verdict** | **NO-GO O37** |
| **P0 code** | flaky draft → **O59a** |
| **P0 docs** | TZ_API · NEON_SCHEMA · design canon |
| **Артефакт** | [`problems/2026-05-29-gemini-full-audit.md`](../../problems/2026-05-29-gemini-full-audit.md) § Решение |

---

## ✅ O58 (**Lead verify + deploy 2026-05-29**)

| | |
|--|--|
| **Theme** | **v1.10.9** prod |
| **Fix** | GET draft poll · `$draft_proxy` GET+POST · проброс **202/200** |
| **Smoke** | GET `/wp-json/.../draft` → **401** (route exists), не «No route…» |
| **→ Тебе** | Ctrl+F5 `/lenta/` · «Написать отклик» → spinner → черновик |

---

## ✅ O56+O57 (**Lead verify + deploy 2026-05-29**)

| | |
|--|--|
| **Theme** | **v1.10.8** prod |
| **API** | `draft_async.py` · migration `lead_draft_jobs` **OK** |
| **Model** | `OPENROUTER_MODEL_SHARED_DRAFT=google/gemini-2.5-pro` on VPS |
| **Services** | rawlead-api + rawlead-bot-poll **active** · feed **200** |
| **O56** | async poll · min-height 240px · event delegation |
| **O57** | shared draft cache · 1 L2/lead |
| **Tests** | 15/15 local |
| **→ Тебе** | Ctrl+F5 `/lenta/` · отклик ×2 на один lead · expand после collapse |

---

## 📌 O57 SHARED DRAFT (2026-05-29)

Один L2 на lead · `leads.reply_draft` = канон · 100 users = 1 AI call.

**Модель:** L1 = flash-lite · shared draft = **pro/sonnet** (`OPENROUTER_MODEL_SHARED_DRAFT`) — 1×/lead, качество важнее.

---

## ⚠️ Приёмка O55 → **O56+O57** (2026-05-29)

| Замечание | Корень | Задача |
|-----------|--------|--------|
| Draft flaky / «draft generation failed» | Sync L2 · OpenRouter | **O56a** async+poll |
| Свернутые карточки разной высоты | height:auto | **O56b** min-height |
| После отклика не разворачивается | Двойной click listener | **O56c** delegation |

---

| | |
|--|--|
| **Theme** | **v1.10.7** on prod |
| **API/bot-poll** | **active** · `ensure_bot_polling_mode` · `tg:draft:callback` logging |
| **O55a** | Home: 42% / **100% ✦** / 67% static demo · center scale |
| **O55b** | Feed `updateCardDraft` → collapse |
| **O55c** | webhook reset on bot-poll start · error logging |
| **Smoke** | home 200 · demo text on `/` · tests 6/6 |
| **→ Тебе** | Ctrl+F5 `/` `/lenta/` · **TG: нажми «Сгенерировать отклик»** на свежем push |

### Приёмка O54 → O55

| Замечание | Статус |
|-----------|--------|
| Главная demo | **✅ Lead verify** |
| Лента collapse | **✅ Lead verify code** |
| TG generate | **✅ deploy** · **→ ты** нажми кнопку |

---

## ⚠️ (архив) Приёмка O54 → O55 — до verify

| Замечание | Задача |
|-----------|--------|
| Главная: фикс. % + идеальная по центру | **O55a** |
| Лента: после отклика не сворачивается | **O55b** |
| TG generate — тишина | **O55c** |

**Lead diag (до O55):** bot-poll active · 0 `tg:draft:` в логе.

---
| **→ Тебе** | **Ctrl+F5** `/` demo · `/lenta/` отклик → collapse · TG push → «Сгенерировать» |

---

## ✅ WAVE-2-ACCEPT-FIX O54 (**Lead verify + deploy 2026-05-29**)

| | |
|--|--|
| **Theme** | **v1.10.6** |
| **API** | `reply_draft_strip.py` на prod · api **active** |
| **O54a** | grid `align-items: start` · cards `height: auto` |
| **O54b** | промпты без срока/цены · strip API/TG/БД · inline tail test **OK** |
| **Tests** | 12/12 local · prod strip «45 000» → **False** |
| **→ Тебе** | **Ctrl+F5** expand соседа · черновик без «срок/стоимость» |

### Приёмка O53 → O54 (2026-05-29)

| Замечание | Задача | Статус |
|-----------|--------|--------|
| Сосед «раскрывается» при expand | **O54a** | **✅ deploy** |
| В черновике срок и цена | **O54b** | **✅ deploy** |

---

## ✅ WAVE-2-ACCEPT-FIX O53 (**Lead verify + deploy 2026-05-29**)

| | |
|--|--|
| **Theme** | **v1.10.5** |
| **O53a** | Expand in-cell 420px — без `grid-column` на `.is-expanded` |
| **O53b** | `formatBudgetDisplay` · `decodeHtmlEntities` · strip `\r` |
| **O53c** | ЛК = markup ленты · без глаза · ✕ в head-meta |
| **Smoke** | prod: budget helpers · no views in cabinet render · lenta/cabinet 200 |
| **→ Тебе** | **Ctrl+F5** `/lenta/` + `/cabinet/` — раскрытие · ₽ · одинаковые карточки |

### Приёмка O52 → O53 (2026-05-29)

| Замечание | Задача | Статус |
|-----------|--------|--------|
| Раскрытая карточка на всю ширину — не то | **O53a** | **✅ Coder** |
| «Р» в бюджете · артефакты текста | **O53b** | **✅ Coder** |
| ЛК карточки ≠ лента (без глаза) | **O53c** | **✅ Coder** |

---

## ✅ WAVE-2-ACCEPT-FIX O52 (**Lead verify + deploy 2026-05-29**)

| | |
|--|--|
| **Theme** | **v1.10.4** |
| **O52a** | TG draft без цены/срока · `strip_tg_draft_price_deadline` |
| **O52b** | Badge «Отклик ✓» · expand после отклика |
| **O52d** | Уведомления — chip-row порог |
| **O52e** | Grid без `:has` — сосед не дёргается |
| **O52c** | ❌ отменено · F2 ≥2 тега для ✦ |
| **Tests** | **41/41** · radar **active** |

---

## ✅ PRE-STRESS-WAVE-2 deploy prod (**Lead verify 2026-05-29**)

| # | Суть | Статус |
|---|------|--------|
| **O47** | L1 CMS tags strict | **✅ deploy** · tests 38/38 |
| **O48** | Draft reliability | **✅ deploy** |
| **O49** | L2 premium v2 | **✅ deploy** |
| **O50** | TG full card + generate | **✅ deploy** |
| **O51** | ЛК 2 col grid | **✅ deploy** |
| **Radar** | `fix-vps-radar-crlf.py` restart | **active** |

**→ Владельцу:** **O52** ✅ Coder → deploy → потом O38

### Приёмка 2026-05-29 (→ O52)

| Замечание | O52 | Статус |
|-----------|-----|--------|
| TG L2: убрать срок/цену, вернуть привет | a | **✅ Coder** |
| Карточка: expand после отклика, badge вместо кнопки | b | **✅ Coder** |
| 100% без ИДЕАЛЬНО (1 тег) | **OK F2** · O52c ❌ | — |
| Соседняя карточка дёргается при collapse | e | **✅ Coder** |
| Уведомления — NEO UI | d | **✅ Coder** |

---

## ✅ O52 WAVE-2-ACCEPT-FIX (**Coder ✅ 2026-05-29**)

| | |
|--|--|
| **a** | TG draft: `strip_tg_draft_price_deadline` · L2 prompt/validate: привет «Здравствуйте» |
| **b** | Лента: badge «Отклик ✓» · expand после generate · `updateCardDraft` head+cta |
| **d** | `.rl-cabinet-notif` NEO card · chip-row порог % · toggle hint |
| **e** | CSS: убран `:has(.is-expanded)` на list · expand только на карточке |
| **Файлы** | `match_push.py` · `ai_analyze.py` · `rawlead-feed.js` · `rawlead-cabinet.js` · `rawlead.css` · `page-cabinet.php` |
| **Тесты** | `test_l2_premium_v2` 6/6 · `test_match_push_o50` 5/5 |
| **Smoke** | `/lenta/` 2 col expand/collapse · `/cabinet/` notif chips · TG callback без ₽/срок |

---

## 📋 PRE-STRESS-WAVE-2 — блокеры приёмки (владелец 2026-05-29)

| # | Суть | P | Статус |
|---|------|---|--------|
| **O47** | L1: Joomla ≠ WordPress tag | **P0** | **✅ Coder** |
| **O48** | Draft 503 + scale (retry, limit, log) | **P0** | **✅ Coder** |
| **O49** | L2 premium quality (no «Готов…») | P1 | **✅ Coder** |
| **O50** | TG: полная карточка + «Сгенерировать» → draft + ЛК | P1 | **✅ Coder** |
| **O51** | ЛК: 2 колонки как лента | P1 | **✅ Coder** |
| **O38** | Gemini + **вся AI-логика** | — | ⏸ после Wave-2 |
| **O37** | Stress **strong agent** | — | ⏸ после O38 |

ТЗ: [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md) § **PRE-STRESS-WAVE-2**

---

## ✅ O51 LK-GRID-2COL (**Coder ✅ 2026-05-29**)

| | |
|--|--|
| **g1** | `#rl-cabinet-list`: grid 2 col · max-width 880px как feed |
| **g2** | `<768px`: 1 col · expanded `grid-column: 1 / -1` |
| **Файлы** | `rawlead.css` |
| **Smoke** | desktop 2 col · 390px 1 col |

---

## ✅ O50 TG-PUSH-FULL-CARD (**Coder ✅ 2026-05-29**)

| | |
|--|--|
| **b1** | Push: source · budget · match% · summary · tag labels · tools |
| **b2–b3** | `callback_data` `draft:{id}` · handler → `generate_and_store_lead_draft` → TG + inbox |
| **b5** | Dedupe: сохранённый `user_lead_replies.reply_draft` |
| **b6** | Generate-кнопка только при paid `effective_access` |
| **Файлы** | `match_push.py` · `telegram_control.py` · `api_server.py` |
| **Тест** | `test_match_push_o50` — **4/4 OK** |

---

## ✅ O49 L2-PREMIUM-V2 (**Coder ✅ 2026-05-29**)

| | |
|--|--|
| **q1–q2** | L2 prompt: без «Готов…» · 2–3 шага · срок/цена |
| **q3** | `_validate_reply_draft_take`: reject `^готов\s` → retry LLM |
| **Файлы** | `ai_analyze.py` · `AI.md` § L2 |
| **Тест** | `test_l2_premium_v2` — **4/4 OK** |

---

## ✅ O48 DRAFT-RELIABILITY (**Coder ✅ 2026-05-29**)

| | |
|--|--|
| **Корень** | `analyze_premium` без `errors[]` → 503 без причины в логах; 2 retry flaky на OpenRouter |
| **r1** | `me_lead_draft`: `errors=[]` → `logger.warning` `lenta:draft:{id}:fail …` |
| **r2** | On-demand: `max_retries=3` (pipeline остаётся 2) |
| **r3** | 503 JSON `{detail, retry_after_sec}` · WP proxy · UI «Повторить» + detail |
| **r4** | Rate limit 10 draft/h per user → 429 |
| **r5** | `draft_ok` / `draft_fail` rolling 24h · `/health` + log |
| **Файлы** | `api_server.py` · `ai_analyze.py` · `rawlead-feed.js` · `rawlead-cabinet.js` · `rawlead-api.php` · `tests/test_draft_reliability.py` |
| **Тест** | `python -m unittest tests.test_draft_reliability -v` — **3/3 OK** |
| **Smoke** | `/lenta/` paid → «Написать отклик» ×2 · 503 → detail + «Повторить» · `curl /health` → draft_ok/draft_fail |

---

## ✅ O47 L1-TAGS-STRICT (**Coder ✅ 2026-05-29**)

| | |
|--|--|
| **Корень** | L1 ставил `wordpress_dev` на Joomla/BaForms → ложный 100% match |
| **Fix t1** | `_LITE_SYSTEM_HEAD`: жёсткие правила CMS (Joomla/Bitrix/OpenCart ≠ WP) |
| **Fix t2** | `sanitize_l1_cms_tags()` — post-validate по маркерам в title/snippet |
| **Файлы** | `ai_analyze.py` · `skills_catalog.py` · `tests/test_l1_tags_cms.py` |
| **Тест** | `python -m unittest tests.test_l1_tags_cms -v` — 5 golden + 3 edge **OK** |
| **Backfill** | не делали (v1 — только новые L1 после деплоя) |

---

## 📋 PRE-STRESS-PACK — deploy prod (**✅ 2026-05-29**)

| # | Суть | Кто | Статус |
|---|------|-----|--------|
| **O42** | Match: **F2** · cap 12 | **✅ deploy** | Lead verify ✅ |
| **O43** | Push + порог в ЛК | **✅ deploy** | Lead verify ✅ |
| **O44** | L2 draft «как сделаю» | **✅ deploy API** | новые L2 после radar |
| **O45** | `/ops/` admin (owner TG) | **✅ deploy** | nginx + API 200 |
| **—** | **Приёмка pack** | **→ ты** · замечания ниже | частично OK |
| **O38** | Gemini audit | @mechanic | **после приёмки** |
| **O37** | Stress | — | после O38 |

ТЗ: [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md) § **PRE-STRESS-PACK**

---

## ✅ PRE-STRESS-PACK deploy prod (**Lead verify 2026-05-29**)

| | |
|--|--|
| **API** | `deploy-o34-vps.py` · 355 files · `rawlead-api` + `rawlead-radar` **active** |
| **Theme** | **v1.10.3** · 33 files · F2 JS + O43 notif proxy |
| **nginx** | `/ops/` + `/v1/admin/` → :8000 · `https://rawlead.ru/ops/` **200** |
| **MATCH_PUSH** | `.env.site` **MATCH_PUSH=1** |
| **Тесты local** | `test_match_f2` + `test_match_push_o43` **15/15 OK** |
| **→ Тебе** | § smoke ниже → приёмка → **O38** audit |

**Smoke (Ctrl+F5):**

1. `/lenta/` — навыки → % вырос (F2) · **ИДЕАЛЬНО ✦** только ≥2 тега у лида  
2. `/cabinet/` — «Уведомления» (paid) · порог 30–100 · hint free + `/start` бота  
3. `/ops/` — после входа owner TG в `/cabinet/` · таблица users + визиты  
4. Inbox — новый L2 черновик с «как сделаю» (старые лиды — старый текст)

**Приёмка 2026-05-29 (замечания владельца):**

| Тема | Вердикт Lead |
|------|----------------|
| **100% + ИДЕАЛЬНО** | F2 **работает**: 2 lead_tags ∩ профиль = 100%. Логика match **не потеряна** |
| **L1 теги** | 7051 = **Joomla**, L1 поставил `wordpress_dev` → ложный 100% (**баг L1**, не F2) |
| **Инструменты** | `tools_required` = что нужно **заказу** (L2), не пересечение с твоими навыками — **by design** |
| **Черновик 7051** | По делу (BaForms, SmartCaptcha) · «Готов заменить» — шаблонно · **7/10** |
| **2-й черновик 503** | lead 7019 · flaky L2 · тикет [`problems/2026-05-29-lenta-draft-503-flaky.md`](../problems/2026-05-29-lenta-draft-503-flaky.md) |

---

## ✅ O43 MATCH-PUSH (**Coder ✅ 2026-05-29**)

| | |
|--|--|
| **Корень UI** | WP REST **`/me/notification-settings`** не был в `rawlead-api.php` → 404 |
| **Fix** | GET/PATCH proxy · ЛК: блок paid (`effective_access`) · hint free + `/start` |
| **Push** | `merge_chat_id_on_login` при TG login (private chat_id) · `beta` plan eligible |
| **Файлы** | `rawlead-api.php` · `rawlead-cabinet.js` · `page-cabinet.php` · `match_push.py` · `api_server.py` |
| **Prod checklist** | `.env.site` `MATCH_PUSH=1` · бот poll · `/start` @rawlead_bot · `users.tg_chat_id` · `push_enabled` · лог `push:match:` в radar |
| **Тест** | `tests/test_match_push_o43.py` |
| **→ Lead** | deploy theme + `src/` · smoke: порог 30/60 · km=45 → push только 30 |

---

## ✅ O44 L2-DRAFT (**Coder ✅ 2026-05-29**)

| | |
|--|--|
| **reply_draft** | 3–5 предл.: суть → **как сделаешь** (из approach) → срок/цена «от …» |
| **Запрет** | канцелярит / вода · **>6 предл.** → `warn:` в лог, не fail |
| **Файлы** | `src/ai_analyze.py` (`_PREMIUM_SPLIT_SYSTEM`, validate, warn) |

---

## ✅ O45 OWNER-ADMIN /ops/ (**Coder ✅ 2026-05-29**)

| | |
|--|--|
| **`GET /ops/`** | HTML dashboard · JWT owner из `localStorage` (`rawlead_access_token`) |
| **`GET /v1/admin/dashboard`** | users Neon + pageviews 7d · **403** не-owner |
| **`POST /v1/admin/pageview`** | beacon path (whitelist) |
| **SQL** | `sql/011_admin_pageviews.sql` (+ auto-create в коде) |
| **nginx** | `data/vps-staging/rawlead.ru.nginx` → proxy `/ops/` + `/v1/admin/` → :8000 |
| **Файлы** | `src/owner_admin.py` · `src/api_server.py` |
| **→ Lead ops** | nginx reload · `psql` 011 · `RAWLEAD_PUBLIC_API_URL` при другом origin API |

---

## ✅ O42 MATCH-SYSTEM F2 (**Coder ✅ 2026-05-29**)

| | |
|--|--|
| **F2** | `km = round(100 * matched / len(lead_tags))` · лишние user_tags **не штрафуют** |
| **ИДЕАЛЬНО ✦** | km=100 **и** ≥2 тега у лида (feed · cabinet · live preview) |
| **Cap** | user_tags **12** (`skills_catalog` · API · WP picker hint) |
| **L1** | lead_tags max **6** без изменений |
| **Тесты** | `test_match_f2` **10/10 OK** |
| **Файлы** | `rank.py` · `skills_catalog.py` · `rawlead-feed.js` · `rawlead-cabinet.js` · `rawlead-scroll.js` · `page-cabinet.php` · `NEON_SCHEMA.md` §3 |
| **→ Lead ops** | deploy `src/` + theme JS · restart API |

---

## ✅ WAVE-4-MICRO v1.10.3 — micro-6…7 (**Coder ✅ · Lead verify ✅ · deploy prod 2026-05-29**)

| | |
|--|--|
| **micro-6** | ЛК modal «+ навык»: `rl-skills-panel` убран с panel · CSS override · **center** desktop + 390px |
| **micro-7** | TG badge **TG** (не chat id) · preview title без `**` |
| **Theme** | **v1.10.3** · deploy **33 файла** |
| **Radar** | **active** после `fix-vps-radar-crlf.py` · цикл ~15 с |
| **→ Владельцу** | Ctrl+F5 `/cabinet/` «+ навык» · `/` TG в preview → **O37** |

---

## 📋 Process — design docs cleanup (**Lead Architect 2026-05-29**)

| Проблема | Fix |
|----------|-----|
| `.mdc` устарели (v1.8.1, REFERENCE v4, `/feed`) | Обновлены `lead-designer.mdc`, `designer.mdc`, `lead-product.mdc`, `README.md` |
| 3 «ПРИОРИТЕТ» § в промптах | Одна **→ Сейчас** в шапке · **⛔ АРХИВ** в `DESIGNER_PROMPT` |
| `DESIGN_BRIEF` путали с WP | Явно: **только пульт** · WP = `docs/design/wp/` |
| Designer читал `LEAD_DESIGN_PROMPT` + архив | Канон: [`LEAD_DESIGN.md`](../design/LEAD_DESIGN.md) § «Один активный план» |

## 🔧 INCIDENT 2026-05-29 — radar down ~42 мин (**✅ fixed Lead ops**)

| | |
|--|--|
| **Симптом** | последний заказ ~42 мин назад |
| **Корень** | `run-radar-site.sh` **CRLF** → `bash\r` exit **127** · restart counter **85** |
| **Fix** | `scripts/fix-vps-radar-crlf.py` · sed deploy/*.sh · restart |
| **После** | `rawlead-radar` **active** · цикл **15:50 UTC** · L1 FL visible в `radar_cycle.log` |
| **→ Coder backlog** | ~~CRLF sed в deploy-wp-theme-vps.py~~ **✅ v1.10.2** |

---

---

## ✅ WAVE-4-MICRO v1.10.2 — micro-1…5 + DEPLOY-CRLF (**Coder ✅ · Lead verify ✅ · deploy prod 2026-05-29**)

| | |
|--|--|
| **micro-1** | hero live-счётчик удалён — prod без «— заказов…» |
| **micro-2** | `rawlead-support.js` enqueued · FAB → модалка чата |
| **micro-3** | лента sort-skills → `localStorage` only · «Сбросить» не трогает `/me/tags` |
| **micro-4** | «Мои навыки» → `GET /me/tags` в draft |
| **micro-5** | modal ЛК — flex center · max-width 480px |
| **DEPLOY-CRLF** | `deploy-wp-theme-vps.py` sed `deploy/*.sh` · Lead + `fix-vps-radar-crlf.py` restart |
| **Theme** | **v1.10.2** · deploy **33 файла** |
| **Radar** | **active** после deploy · цикл ~15 с · FL 90 + Kwork 12 |
| **→ Владельцу** | Ctrl+F5 `/lenta/` `/cabinet/` — FAB · «Мои навыки» · modal center · UI OK → **O37** |

---

## ✅ WAVE-4-MICRO — копирайт + превью ленты + ЛК expand (**Coder ✅ · Lead verify ✅ · deploy prod 2026-05-29**)

| | |
|--|--|
| **Scope** | hero H1/sub · live preview API (3 карточки) · «Подбираем» только по «Ещё лиды» · ЛК клик=черновик · pricing/how канон · marquee ∞ |
| **Theme** | **v1.10.1** · `rawlead-scroll.js` live preview · `marketing.php` inner HTML |
| **Lead verify** | prod `/` — новый H1 · preview секция · `/pricing/` `/how/` copy · deploy **33 файла** |
| **→ superseded** | micro-1…5 → **v1.10.2** выше |

---

## 🔧 INCIDENT 2026-05-29 ~09:18 UTC — radar restart loop (**✅ fixed Lead ops**)

| | |
|--|--|
| **Симптом** | лента «давно не обновляется» · владелец после deploy |
| **Корень** | тот же **CRLF** в `deploy/*.sh` → `bash\r` exit **127** · unit перезапускался |
| **Fix** | `scripts/fix-vps-radar-crlf.py` · restart `rawlead-radar` |
| **После** | **active** · цикл **~15 с** · FL 90 + Kwork 12 · TG монитор acc1/acc3 ready |
| **Примечание** | `neon_insert: 0` на idle = dup_fast_skip, не «радар мёртв» · последний лид в API **#6929** ~08:57 UTC |
| **→ Coder backlog** | ~~CRLF sed в deploy-wp-theme-vps.py~~ **✅ v1.10.2** · deploy-o34 уже sed · restart radar — Lead ops при src-deploy |

---

## 🔧 INCIDENT 2026-05-29 — radar down ~42 мин (**✅ fixed Lead ops**)

| | |
|--|--|
| **Scope** | inbox full cards · load-more V2/V3 · nav on `/lenta/` · support FAB · copy V6 · skeleton V7 |
| **Спека** | `DESIGNER_PROMPT.md` § WAVE-4-UX-FIX |
| **Theme** | v1.9.0 · `rawlead-support.js` · WAVE-4 CSS block |
| **→ Владельцу** | Ctrl+F5 `/lenta/` `/cabinet/` · FAB «Поддержка» · карточки ЛК |

---

## ✅ O41-WAVE3 — Gumroad hero split (**Coder ✅ · Lead verify ✅ · deploy prod 2026-05-29**)

| | |
|--|--|
| **Scope** | hero split · live preview · secondary CTA · H1 «Лиды без шума» |
| **Theme** | **v1.9.0** · `live-preview.php` новый · 32 файла на VPS |
| **Prod check** | https://rawlead.ru/ — hero жёлтый · preview белая секция · «Тарифы ↓» |
| **Radar** | **active** (CRLF не затронут theme-deploy) |
| **→ Владельцу** | Ctrl+F5 `/` desktop + 390px · OK → stress O37 |

---

## ✅ O35 WAVE-2-CSS — Neo-Brutalist Wave 2 (**Coder ✅ · Lead verify ✅ 2026-05-29**)

| | |
|--|--|
| **Theme** | **v1.9.0** · `wordpress/rawlead-kadence-child/` |
| **A** | IO reveal `.rl-lead-card` / `.rl-inbox-card` · match-bar on `.is-visible` · perfect yellow `ИДЕАЛЬНО ✦` · «Загрузить ещё» |
| **B** | by Rode51 · mark SVG · hero geo · megaphon · hover 120ms / btn active 0.96 |
| **C** | announcement W15 · nav W16 · pricing table 300 ⭐ · `/how` 3 шага · contact без формы |
| **D** | `.rl-flow__sources` + cube CSS/JS удалены · без indigo perfect-match |
| **→ Lead ops** | **✅ deploy 2026-05-29** — theme v1.9.0 + landing content · Ctrl+F5 6 URL |
| **→ Сейчас** | **⏸** владелец UI check WAVE-4 · stress **после** OK |
| **→ После** | O37 stress (@coder) |

---

## ✅ BACKLOG-TAIL-CLEAR-O40 (**Coder ✅ · Lead verify ✅ 2026-05-29**)

| | |
|--|--|
| **Fix** | `count_leads_missing_l1_recent` · `clear_l1_backlog_tail(by_age)` · `/status`: «Без L1 (48 ч)» + «Хвост исторический» |
| **Script** | `--by-age --days-old 7` · dry-run: `older_than_Nd`, `protected_48h`, `to_clear` |
| **Lead verify** | regression **7/7** · VPS sync **346** · код на prod |
| **VPS dry-run** | `missing_before=153` · **`older_than_7d=0`** · `to_clear=0` — **весь хвост моложе 7 сут** (много &lt;48 ч) |
| **→ Владельцу** | `/status` — новый формат после restart ✅ · **apply сейчас нечего** — повторить `--days-old 1` через 24–48 ч или снизить `--hours-protect` (осторожно) |

---

## ✅ O39 PIPELINE-FAST-STABLE (**Coder ✅ · Lead verify local ✅ 2026-05-29**)

| | |
|--|--|
| **Fix** | `neon_synced_at/hash` в SQLite · dup **fast path** без `lead_exists` · `dup_fast_skip` в footer + `/status` |
| **Lead verify** | `test_dup_fast_path` **4/4** · 90 dupes **<90s** без Neon RTT · `.gitattributes` · deploy smoke |
| **VPS** | **✅ deploy 2026-05-29 ~14:27 UTC** · 1-й цикл **242.7 с** (прогрев) · 2-й **71.0 с** · `dup_fast_skip=86` |
| **→ Владельцу** | TG `/status` · в логе `dup_fast_skip` на idle-циклах |

---

## ✅ BOT-STATUS-V2 (O32) — `/status` v2 (**Coder ✅ · Lead verify local ✅**)

| | |
|--|--|
| **Fix** | Site `@rawlead_bot` · блоки FL/Kwork/TG/**Цикл**/лента/L1/acc · «Проблемы» только при сбоях |
| **Цикл** | `cycle_sec` + `neon_dup_skip` + rollup `L1/visible` за 10 мин |
| **Lead verify** | `test_radar_status_v2` **6/6 OK** · `test_l1_pipeline` **3/3 OK** · лимит **3490** симв |
| **Файлы** | `radar_status.py` · `radar_cycle_log.py` · `telegram_control.py` · `RADAR_LOG.md` |
| **→ Lead ops** | deploy `src/` + restart radar → владелец: TG «ℹ Статус» / `/status` · **✅ deploy 2026-05-29** |

---

## ✅ TG-AUTH-500-HOTFIX — вход TG (**Coder ✅ 2026-05-29**)

| | |
|--|--|
| **Корень** | `api_server.py` — не было import `verify_telegram_login`, `login_bot_token` |
| **Fix** | import из `telegram_login.py` · smoke `401 invalid telegram hash` |
| **Prod** | `rawlead-api` restart · `POST /v1/auth/telegram` fake hash → **401** (не 500) |
| **→ Владельцу** | повторить вход на https://rawlead.ru/cabinet/ |

---

## ✅ CABINET-PROD-LOGIN L1 — UI prod (**Lead verify ✅** · **auth ✅**)

| | |
|--|--|
| **Theme/UI** | v1.8.2 · loginUrl prod · widget грузится ✅ |
| **Auth API** | `POST /v1/auth/telegram` → **401** на fake hash · import fix ✅ |

---

## ✅ VPS — O34 radar **задеплоен** (Lead ops **2026-05-29 ~13:52 UTC**)

| | |
|--|--|
| **Deploy** | sync **336** файлов · `l1_pool.py` **170 строк** · `main.py` **29.05** · restart `rawlead-api` + `rawlead-radar` |
| **CRLF fix** | `deploy/*.sh` — radar падал **exit 127** до `sed` CRLF · сейчас **active** |
| **backlog** | `clear_l1_backlog --apply` — cleared **37** · `missing_after=152` (хвост без L1) |
| **O34 признак** | циклы **после** рестарта **без** `конвейер:backlog=` · footer «лenta после L1 — см. Neon is_visible» |
| **pipeline:L1** | в логе **0 строк** — норма при **0 новых** за цикл (лог только при `l1_done>0`) |
| **Парсер** | **жив:** FL 90/0 new · Kwork 12/0 new · TG пульс OK · цикл **~234 с** |
| **Лента API** | top `created_at` **2026-05-29T05:15:22Z** — **нет новых visible** (рынок тихий + L1 **МИМО**, не stall backlog) |
| **→ Владелцу** | `/status` в TG — **O32+O39** после Lead deploy |
| **Baseline** | цикл **~234 с** (1-й после deploy) → **≤90 с** idle со 2-го цикла (`dup_fast_skip`) |

---

## ✅ O39 PIPELINE-FAST-STABLE — dup fast path (**Coder ✅ 2026-05-29**)

| | |
|--|--|
| **Fix** | SQLite `neon_synced_hash` — dup без `pg.lead_exists()` каждый цикл · replay при смене hash |
| **Счётчики** | footer `dup_fast_skip=N` · `neon_dup_skip` для audit · `/status` блок «Цикл» |
| **Ops** | `.gitattributes` `*.sh eol=lf` · `deploy-o34-vps.py` post-deploy smoke |
| **Тесты** | `test_dup_fast_path` **4/4** · `test_l1_pipeline` **3/3** · 90 dupes **< 90 с** mock |
| **Файлы** | `storage.py` · `lead_pipeline.py` · `radar_cycle_log.py` · `radar_status.py` · `deploy-o34-vps.py` |
| **→ Lead ops** | deploy `src/` + restart radar → 2-й цикл: `dup_fast_skip≈102` · `cycle_sec ≤ 90` idle |

---

## ✅ PIPELINE-INSTANT-O34 — код + VPS

| | |
|--|--|
| **Hot path** | dedup → **filter → budget** → Neon → **L1 pool** (3 workers) → visible → feed |
| **Lead verify local** | `tests.test_l1_pipeline` **3/3 OK** |

---

## ✅ DESIGN-WAVE-1-E5 + E5b-COPY-GAP (**Coder ✅ 2026-05-29**)

| | |
|--|--|
| **✅ e5-1,3–8** | NEO CSS · TWO-SPEEDS strip · inbox `replied_at` · C1 mobile |
| **✅ e5-2 + E5b** | «ты»-форма · лендинг c4 · faq 300 ⭐ · marketing O23 · badge убран |
| **Theme** | **v1.8.1** · **✅ prod deploy** |
| **Landing plugin** | `rawlead-landing/content/*.html` · reactivate на VPS |
| **→ Lead** | verify Ctrl+F5 `/` `/faq/` `/cabinet/` desktop + 390px |

---

## ✅ DESIGN-WAVE-1 — Design + PM (**Lead verify ✅ 2026-05-29**)

| | |
|--|--|
| **Design** | NEO-BRUTALIST · inbox UI · C1 mobile · `REFERENCE` v4 · `feed-cabinet-mvp` v3 · `DESIGNER_PROMPT` |
| **PM** | c1–c4 · TWO-SPEEDS · «ты»-форма · Stars 300 ⭐ |
| **Lead правка** | c2 inbox empty states · H1 «Мои отклики» · счётчик без «7 дней» (A1) |
| **Код** | **✅** @coder § **DESIGN-WAVE-1-E5** + **E5b-COPY-GAP** · theme **v1.8.1** prod |

---

## ✅ SITE-ACCEPT-GATE O20 (**владелец ✅ 2026-05-28**)

| | |
|--|--|
| **Gate** | a1–a9 приняты на prod **v1.7.24** |
| **Free** | delay 15 мин · нет отклика · ЛК = inbox |
| **Paid/beta** | instant · отклик · inbox · уведомления |
| **Дальше** | **Design + PM** → Coder финал → PRE-PROD (O21) |

---

## ✅ MATCH-PUSH-V2 O30 + WP proxy (**Lead verify ✅ 2026-05-28**)

| | |
|--|--|
| **sql/010** | `push_min_match` DEFAULT 60 · `push_enabled` DEFAULT TRUE — **Neon ✅** |
| **match_push.py** | top-3 **убран** · всем paid при `km >= push_min_match` · `push_enabled` |
| **API** | `GET/PATCH /v1/me/notification-settings` (30–100) |
| **WP proxy** | `rawlead-api.php` GET/PATCH `/me/notification-settings` — **✅ prod 200** |
| **UI** | `/cabinet/` блок «Уведомления» — toggle + слайдер |
| **Theme** | **v1.7.24** · **✅ Lead ops prod** |

---

## ✅ HOTFIX UX wave — v1.7.23 (**Lead verify ✅ 2026-05-28**)

| | |
|--|--|
| **#20 DRAFT-403** | `barPct = keyword_match` · кнопка только `km > 0` · 403 → «Нет пересечения…» |
| **#21 CABINET-SKILLS** | `pickerNiche = null` · full catalog · все 4 группы в модалке |
| **#22 FEED-SORT-DD** | `mousedown` закрывает `.rl-filter-sort-dd` |
| **Theme** | **v1.7.23** |
| **Деплoy** | **✅ Lead ops** — prod rawlead.ru |

---

## ✅ TAGS-V0.3 + b3 + OWNER-BETA — (**Lead verify ✅ 2026-05-28**)

| | |
|--|--|
| **TAGS t3-1…t3-7** | 51 canonical · PUT/GET max 6 · merge v0.2→v0.3 · picker **«Ещё навыки»** · чипы 4+«+N» · L1 smoke warn |
| **t3-2b** | `openai`/`gpt` → `llm_integration` |
| **OWNER-BETA-GRANT** | `_grant_owner_beta_if_match` при TG-login |
| **b3-HOTFIX** | `status`: inactive/failed = ok · ▶ → `start` если ≠ active |
| **Lead verify** | py_compile ok · 51 tags · 7-й tag → 6 · theme **v1.7.19** |
| **Деплoy** | theme + API restart на VPS — **→ владелец/Lead ops** |

**Открыто:** SITE-ACCEPT-GATE a2 + a5–a6 (TG-login владельца с VPN).

---

## ✅ PRE-DESIGN-BLOCKERS O27–O29 (**Lead verify ✅ 2026-05-28**)

| | |
|--|--|
| **O27** | `POST …/draft` → `analyze_premium` · `tools_required` в Neon + ответ API · feed/cabinet «Инструменты» |
| **O28** | `/start` → `upsert_subscriber_chat_id` · `push_match_for_lead` после L1 · dedupe `match_push_log` · env `MATCH_PUSH=1` |
| **O29** | `sendInvoice` XTR · `pre_checkout_query` · `successful_payment` → `plan=agent` · `stars_available` в API · UI `/pay` + кабинет |
| **Lead verify** | py_compile ok · draft 403 free / tools в `renderExpandedBody` · push top-K=3 paid/owner · Stars `activate_subscription` |
| **Theme** | **v1.7.22** (O25b + blockers) |
| **Деплoy** | **✅ Lead ops 2026-05-28** — Neon `009` · env `MATCH_PUSH=1` `STARS_ENABLED=1` · theme + API/bot/radar restart · smoke 5/5 |

---

## ✅ FEED-CARD-UX O25–O26 + O25b (**Lead verify ✅ 2026-05-28**)

| | |
|--|--|
| **O25/O25b** | `feed_social.py`: fresh instant 1–3 · 15m/60m растут с age · delayed bonus · eye SVG + count (без «просмотров») |
| **O26** | perfect-match badge + green bar |
| **Smoke** | fresh 1 / delayed 2 · 15m 21/35 · 60m 29/41 (lead_id=42) |
| **Theme** | **v1.7.22** |

---

## ✅ CABINET-INBOX-O23 — лента vs inbox (**Lead verify ✅ 2026-05-28**)

| | |
|--|--|
| **Модель** | `/lenta/` — единственная lenta; anon + free TG → delay 15 мин, без «Написать отклик»; paid/beta → instant + кнопка |
| **Inbox** | `user_lead_replies` · `GET/DELETE /v1/me/replies` · `/cabinet/` = профиль + inbox |
| **L2** | `analyze_premium` on-demand через `POST …/draft` (O27) |
| **Lead verify** | o23-1…7 · API `feed_delayed:true` · theme **v1.7.15** на prod |
| **Деплoy VPS** | **✅ Lead** — `deploy-l3-vps.py` · Neon `008` · API restart |
| **Владельцу** | § **SITE-ACCEPT-GATE** a1–a9 |

**Открыто:** SITE-ACCEPT-GATE a1–a9.

---

## ✅ L1 + L2 — вход ЛК prod + страницы сайта (**✅ Lead verify 2026-05-28**)

| | |
|--|--|
| **L1** | `canMountTelegramWidget()` + allowlist rawlead.ru; hotfix **v1.7.8** — рекурсия `tg_login_bot_id`↔`fallback_url` → 500 на `/cabinet/` |
| **L2** | hero CTA лента+ЛК; pricing Stars; plugin `rawlead-landing` + `wp-vps-skeleton-pages.py` |
| **Lead verify** | `marketing.php`, `functions.php` v1.7.7, `page-cabinet.php`, `rawlead-cabinet.js` — без hard-block prod |
| **Деплой (владелец)** | `deploy-wp-theme-vps.py` + `wp-vps-skeleton-pages.py` · BotFather `/setdomain` → rawlead.ru |

---

## ✅ E-polish D1 — навыки + шапка (**Coder 2026-05-28**)

| | |
|--|--|
| **Сделано** | закрытие навыков по клику вне; sticky footer «Применить»; header: Лента+Тарифы; CTA «Вход в ЛК» / «Кабинет» |
| **Файлы** | `template-parts/rawlead/header.php`, `page-lenta.php`, `assets/css/rawlead.css`, `assets/js/rawlead-feed.js` |
| **Как проверить** | § LENTA-HEADER-UX приёмка 1–4; деплой theme **v1.7.6+** (`functions.php` bump + `scripts/deploy-wp-theme-vps.py`) |

---

## ✅ E-polish B1 — навыки per user_id (**✅ Lead + владелец 2026-05-28**)

| | |
|--|--|
| **Сделано** | гость → `localStorage`; JWT → Neon `user_tags`; REST без owner #1; theme **v1.7.5** на VPS |
| **Lead verify** | `rawlead-api.php`: GET tags без Bearer → `[]`; PUT → 401; `/me/feed` → 401; `rawlead-feed.js`: guest не шлёт PUT |
| **Файлы** | `inc/rawlead-api.php`, `assets/js/rawlead-feed.js`, `functions.php` |

---

## ✅ L3 — навыки picker + retention 7d + L3-FIX (**Lead verify ✅ 2026-05-28**)

| | |
|--|--|
| **L3-FIX** | API `?mode=full` → static L1 pool (Tier A+B); ЛК `?mode=full&limit=200`; modal **сверху**; theme **v1.7.10** |
| **TG login RU** | widget fail → redirect; VPN hint; popup timeout 8s; `#tgAuthResult` hash; `RAWLEAD_TG_BOT_ID` в install + DEPLOY_VPS |
| **Retention** | feed/me/feed 7d; `purge_old_leads.py` + systemd timer |
| **Lead verify** | `api_server.py` L518–581, `rawlead-cabinet.js` L156–219/1423, `rawlead.css` L2425–2456 — ок |
| **Деплoy VPS** | **✅ Coder 2026-05-28** — `deploy-l3-vps.py`: theme **v1.7.10**, API `mode=full`, `RAWLEAD_TG_BOT_ID=8989158953`, units **active** |
| **Владельцу** | BotFather `/setdomain` → `rawlead.ru` · приёмка 🛑/▶ в @rawlead_bot |

**⚠️ Вход TG из РФ:** без VPN redirect на `oauth.telegram.org` тоже не откроется — VPN обязателен.

---

## ✅ E-polish B3 — owner-only TG controls (**Coder 2026-05-28**)

| | |
|--|--|
| **Сделано** | `is_radar_admin()`; admin-клавиатура ⏸/▶/🛑/ℹ только владельцу; подписчикам welcome + `remove_keyboard`; `/stop-radar` + 🛑 → `systemctl stop` через `deploy/radar-ctl.sh`; ▶ поднимает unit если inactive |
| **Файлы** | `src/telegram_control.py`, `deploy/radar-ctl.sh`, `deploy/sudoers.d/rawlead-radar-ctl`, `docs/ops/DEPLOY_VPS.md` §9–10 |
| **Как проверить** | § BOT-OWNER-CONTROLS приёмка 1–4; **на VPS** — 🛑 → `systemctl is-active rawlead-radar` = inactive; ▶ → active |
| **Деплой VPS** | **✅** с L3 (`deploy-l3-vps.py`: `radar-ctl.sh`, sudoers, CRLF fix `deploy/*.sh`) |
| **Hotfix 2026-05-28** | `bot_poll.py` fcntl; offset до 🛑; **`rawlead-bot-poll.service`**; ack «✓ Принято»; статус — явная строка ingest (🛑/⏸/▶) |
| **b3-HOTFIX** | **✅ Coder** — см. блок **b3-HOTFIX** выше · Lead verify VPS pending |
| **Радар VPS** | **✅ active** (Lead restart 2026-05-28) · TG acc1+acc3 **ready** · acc2 skip (нет chat_ids) · `bot_start` entity — некритично |

---

## ✅ LK-UX-POLISH + A1 + 3f-A (**Lead verify ✅ 2026-05-28**)

| | |
|--|--|
| **LK-UX** | merge guest-навыков; avatar в шапке; user bar + «Выйти»; @rawlead_bot hint |
| **A1** | «N лидов · по совместимости» |
| **3f-A2** | expand + copy (**⚠️** L2 on-demand нет — только готовый `reply_draft` в Neon) |
| **Lead verify** | `mergeGuestSkillsAfterAuth`, `header.php`, `page-cabinet.php`, v**1.7.11** |
| **Деплой** | `deploy-wp-theme-vps.py` + restart API |

---

## ✅ 3f-B — тариф/статус подписки (**Lead verify ✅ 2026-05-28**)

| | |
|--|--|
| **Сделано** | `GET /v1/me/subscription` из Neon; `POST …/pause` (days/resume); блок «Подписка» в ЛК; `/pricing/` 590 ₽ + Stars soon; `sql/007_subscriptions_status.sql` |
| **Lead verify** | `api_server.py` L765–931 · `rawlead-api.php` REST proxy · `page-cabinet.php` + `rawlead-cabinet.js` subscription UI · `rawlead.css` · v**1.7.13** |
| **Stars** | live при `STARS_ENABLED=1` — см. блок **O27–O29** |
| **Beta owner** | `plan=owner` → status **beta**, `can_pause=false` ✅ |
| **Деплoy** | Neon: `007_subscriptions_status.sql` · `deploy-wp-theme-vps.py` · `systemctl restart rawlead-api` |
| **Не в 3f-B** | NEO-BRUTALIST CSS (MATCH_PUSH/Stars — **O27–O29 ✅**) |

---

## ✅ LK-FEED-FILTERS (O22) + SFW sfw-8 / sfw-3…7 (**Lead verify ✅ 2026-05-28**)

| | |
|--|--|
| **O22** | sort match\|time + sessionStorage; min_match 30–100; `_passes_min_match`; карточка `keyword_match` % |
| **sfw-8** | `POST /v1/me/leads/{id}/draft` + «Генерируем…» в ЛК |
| **sfw-3…7** | how/faq/contact/pricing; footer; FAQ `<details>`; contact stub |
| **Lead verify** | `api_server.py` · `page-cabinet.php` · `rawlead-cabinet.js` · v**1.7.14** |
| **⚠️** | `reply_draft` в `leads` — один на лид (полный P4b per-user позже) |
| **Деплoy** | theme + API на VPS · Lead ops |

---

## ⚠️ Pivot O23 (2026-05-28) — лента vs inbox

**Решение владельца:** `/cabinet/` **не** дублирует ленту. Inbox откликов + профиль. «Написать отkлик» на **`/lenta/`** (paid). ТЗ: § **CABINET-INBOX-O23**.

**Код v1.7.14** (match-лента в ЛК) — **legacy до O23**.

---

## Сейчас (2026-05-29)

**Design + PM ✅ → Coder E5.**

| Волна | Кто | Статус |
|-------|-----|--------|
| **DESIGN-WAVE-1** | @lead-designer + @lead-product | **✅** Lead verify |
| **E5 NEO + copy + C1** | @coder | **→** § **DESIGN-WAVE-1-E5** |
| **PRE-PROD-STRESS** | @coder → владелец | **O21** · после E5 |

**Владельцу:** Site/Legacy ■ на ПК — **не включать**; радар 24/7 только VPS systemd.

---

## ✅ P5-E2-VPS deploy (Lead ops 2026-05-28)

| | |
|--|--|
| **Сделано** | sync кода на `/opt/rawlead`; `.env` + `.env.site` + `.env.legacy`; Telethon-сессии acc1–3; `rawlead-radar` + `rawlead-radar-legacy` **active**; ПК `stop-radar-desktop-full.vbs` |
| **Скрипты** | `scripts/finish-vps-e2.py`, `scripts/check-vps-e2.py`, `prep-vps-env.ps1` (+ `.env.legacy`) |
| **Проверка** | `main.py` + `tg_main` на VPS; `/v1/feed` — свежий FL-лид `2026-05-28`; TG acc1/acc3 **ready**; `http://rawlead.ru/lenta/` → 200 (nginx :80) |
| **Заметки** | acc3 = `233333925_telethon.session` (не +66985780470); CRLF в `.sh` — `sed` в finish-e2; Legacy consumer ok |

---

## ✅ P5-E2-VPS (Coder 2026-05-28)

| | |
|--|--|
| **Сделано** | e2 legacy unit + runner; e4 пауза по профилю; e3/e5/e6 docs/импорт; `DEPLOY_VPS.md` E2b |
| **Файлы** | `deploy/run-radar-legacy.sh`, `deploy/systemd/rawlead-radar-legacy.service`, `src/storage.py`, `src/telegram_control.py`, `docs/ops/DEPLOY_VPS.md`, `.env.example` |

---

## ✅ Принято (код + Lead verify)

Сводка волны **2026-05-24 … 2026-05-28**. Детали — [`archive/TASKS_HISTORY.md`](../archive/TASKS_HISTORY.md).

| Блок | Суть |
|------|------|
| **Этап 0** | Радар ПК, legacy/site split, пульт, TG acc1–3 |
| **3b–3d** | Neon, API, WP `/lenta/` `/cabinet/` |
| **E0–E5** | PRE-LAUNCH A–D, REVOLUTION UI, copy c1–c4, canonical tags E2b |
| **3x** | Бадж «Горячий» — **✅** |
| **P5 E1** | API на VPS (`rawlead-api`, health ok) |
| **P5 E2** | код + **деплой VPS** — Site+Legacy systemd |
| **E-polish B1** | навыки per user_id (guest localStorage + JWT Neon) — **✅** |
| **SITE-POLISH волна** | BACKLOG-CLEAR, FEED-FRESHNESS, … NEON-AUDIT |
| **Dogfood** | LEGACY-REPLY-DRAFT, STOP-STATUS-SPAM, CABINET-LOGIN-FALLBACK |
| **PRE-PROD** | Скрипты S1–S6 — **прогон не начат** |

**Лента:** ingest на VPS, интервал Site **1 мин** (`.env.site`). Прокси acc1–3 на месте.

---

## ЛК и подписка (честный статус)

**Лестница (канон O6):** polish (D1–A1) → **§ 3f фаза A** ✅ → **фаза B** ✅ → **фаза C / касса** (590–990 ₽).

| Есть сейчас | Ещё нет (очередь) |
|-------------|-------------------|
| `/cabinet/`, вход TG + fallback | Gate «L2 только paid» |
| JWT, навыки per user (B1 ✅) | L2 персонально под профиль (P4b full) |
| `/v1/me/feed`, match %, sort, min_match, L2 on-demand | PRE-PROD stress S1–S6 |
| `/v1/me/subscription` — реальные поля Neon | ЮKassa / несколько тарифов |
| Push match TG (O28) · Stars оплата (O29) · `tools_required` (O27) | NEO-BRUTALIST CSS |
| Таблица `subscriptions` + `is_active` / `paused_until` | |
| Блок «Подписка» + `/pricing/` Stars live при `STARS_ENABLED=1` | |

**ТЗ:** [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md) § **3f-OWNER-BETA** (фазы A→B→C).

---

## Блокеры (актуальные)

| Блокер | Кто |
|--------|-----|
| Пульт: sticky-скролл логов | код ✅ · `rebuild-pult.bat` — владелец |
| SSL :443 на VPS (если нужен прямой HTTPS) | владелец · certbot |

Закрытые тикеты: [`docs/problems/`](../problems/) — не дублировать здесь.

---

## MVP acceptance (Plan B)

Сверка: [`LEAD_PRODUCT_PROMPT.md`](../product/LEAD_PRODUCT_PROMPT.md) § «Готово когда» — после **3f** и stress.

---

_Lead Architect · ревизия docs 2026-05-28_

### B1 verify (владелец, ~3 мин)

1. **Гость `/lenta/`:** инкognito → навыки → «Применить» → Network: **нет** `PUT …/me/tags`; перезагрузка — навыки на месте (localStorage).
2. **Два гостя:** другой браузер — **другие** навыки (не owner #1).
3. **ЛК:** `/cabinet/` → TG-вход → навыки → `PUT …/me/tags` **200** + `Authorization: Bearer`.
4. **Кросс-девайс:** тот же TG на телефоне и ПК → `/cabinet/` — **одинаковые** навыки после reload.
5. **Лента залогинен:** после входа в ЛК открыть `/lenta/` — подтянулись навыки из Neon (тот же JWT).

