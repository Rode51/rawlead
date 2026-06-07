# Coder — горячий контур (активное)

**→ Сейчас:** **O129-STRESS-V2** (Coder) · Wave 1 ✅ **2026-06-07** — [`PREPROD_STRESS_RUN.md`](../../ops/PREPROD_STRESS_RUN.md)

---

## § O129-W1 ✅ (2026-06-07)

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
