# Coder — **→ Сейчас:** § **O72e-4** (QA-автомат regen→judge→LLM-патч)

**Порядок:** **O72e-3 ✅** (код+deploy · gate send/L1 ❌) · **O72e-4 P0** · owner запускает `--apply` · ads ⏸.

---

# § O72e-3 — Judge FAIL: L1 + L2 промпты (**→ @coder**, P0)

**Judge 2026-06-01** (`data/preprod_ai_prod_audit_judge.md`, `--judge-since 2026-06-01`):

| Слой | Метрика | Gate | Факт |
|------|---------|------|------|
| **L2** | combined | ≥4.0 | **3.56** ❌ |
| **L2** | send_as_is | ≥50% | **22.7%** ❌ |
| **L2** | specificity | — | **3.09** (узкое место) |
| **L1** | l1_usable | ≥70% | **25%** ❌ |
| **L1** | category_ok | — | **25%** ❌ |
| **tools** auto | ≥85% | **~57%** (backfill идёт) |

**Решение владельца 2026-06-01:** промпт «Senior Freelance Acquisition Agent» (ниже) — **канон духа L2**; в код адаптировать под RawLead.

### Адаптация промпта владельца (обязательно)

| Из промпта владельца | В `_SHARED_REPLY_SYSTEM` + `_CABINET_REPLY_SYSTEM` |
|----------------------|-----------------------------------------------------|
| Стек из ТЗ, не lead_tags (Rhino/GAS ≠ Python) | **§1** перед генерацией: среда из title+body+task_summary; **запрет** подставлять canonical_tag / tools_required, если противоречат тексту |
| 2–3 нишевые проблемы + методы (Elementor DOM, FontLab, API парсинг…) | **§2** чеклист по category (dev/design/marketing/text) — 2–3 термина из judge top-5 |
| 3 строки: задача → подход → CTA | **§3** 4–5 предложений: (1) деталь из ТЗ (2) 2–3 шага «Сначала…» (3) **один** уточняющий вопрос |
| Сроки + бюджет в отклике | **❌ не в reply_draft** (O57 strip TG) · срок/цена только в premium `money` / `time_for_client`, не shared draft |
| Запрет «большой опыт», «готов качественно» | уже есть — усилить; validator cliche |

**Не копировать** промпт целиком в `_PREMIUM_SPLIT_SYSTEM` (legacy bot) — только shared + cabinet + `_TOOLS_ONLY_SYSTEM`.

### Задачи

| # | Задача |
|---|--------|
| p1 | Переписать `_SHARED_REPLY_SYSTEM` по таблице выше + 5 паттернов из judge § L2 |
| p2 | `_CABINET_REPLY_SYSTEM` — те же правила + profile_excerpt |
| p3 | `_TOOLS_ONLY_SYSTEM` + `_PREMIUM_SPLIT` tools: **стек из ТЗ**; GAS/Rhino/Excel явно; map vendor→generic (O72e-2) |
| p4 | `_LITE_SYSTEM_HEAD`: dev vs design vs marketing (judge § L1 top-5); **не выдумывать бюджет**; email-рассылки → marketing + осторожный verdict |
| p5 | Post-validate L1: category vs lead_tags согласованы (опц. lightweight в `sanitize` / `partition`) |
| p6 | Unit: 3 fixture-лида из judge worst (#8776, #8925 GAS/Rhino, #8704 шрифт) — draft содержит ≥2 термина из fix-list |
| p7 | Deploy VPS `ai_analyze.py` |
| p7b | **QA regen** (владелец 2026-06-01 уточнение): `regen_shared_reply_drafts.py --profile site --apply --limit 50` — **переписать черновики на той же выборке**, чтобы **сразу** re-judge после смены промпта (не ждать радар) |
| p8 | Re-judge: `preprod_ai_prod_audit.py --profile site --judge --judge-l1 --judge-limit 40` → combined **≥4.0**, send **≥50%**, L1 usable **≥70%** |
| p9 | Prod-gate (ads): QA PASS **или** **20–30 лидов ingested после deploy** (`--judge-since <deploy-date>`) · owner 5× «отправил бы as-is» |

### L1 модель — эксперимент (владелец 2026-06-01: дёшево + качественно)

**Сейчас:** `OPENROUTER_MODEL_SUMMARY` → по умолчанию **`google/gemini-2.5-flash-lite`** (`config.py`). L1 = **каждый** лид после L0 · пачка до **`L1_BATCH_PER_CYCLE=40`**/цикл — **объём × цена**, не как L2 (1× Sonnet).

**Judge-сигнал:** `verdict_fair` **4.1/5**, `context` **3.5/5**, но **`category_ok` 25%**, **`l1_usable` 25%** — узкое место **классификация dev/design/marketing + галлюцинации бюджета**, не «модель тупая». **Порядок:** p4+p5 (промпт + post-validate) → **потом** A/B модели.

| # | Задача |
|---|--------|
| p10 | **A/B L1** на **тех же 20** lead_id из judge (offline replay, **не** mass Neon): flash-lite · **flash** · **deepseek/deepseek-chat** · опц. **claude-3.5-haiku** |
| p11 | Метрики: `l1_usable`, `category_ok`, `$`/`lead` (OpenRouter usage в логе или оценка tok) · **не** Sonnet/GPT-4 на L1 |
| p12 | Победитель → только `OPENROUTER_MODEL_SUMMARY` в `.env.site` · если flash-lite **≥70%** после p4 — **не** поднимать модель (экономия) |

**Кандидаты (дешевле → дороже, только L1):**

| Модель | Роль | Ориентир |
|--------|------|----------|
| `google/gemini-2.5-flash-lite` | baseline | ~5–15 ₽/день при 30–80 L1/день (`AI.md`) |
| `google/gemini-2.5-flash` | +рассуждение, ~2–3× tok | если lite не тянет category после промпта |
| `deepseek/deepseek-chat` | был в `INGEST_CATEGORY_STRATEGY` | дешёвый JSON, проверить RU+категории |
| `anthropic/claude-3.5-haiku` | запасной (`AI.md`) | если Gemini 429/качество |

**❌ Запрещено на L1:** `OPENROUTER_MODEL_PREMIUM` / Sonnet / pro — **убьёт бюджет** при batch 40.

**Бесплатный слой (до LLM):** `category` от парсера + keyword `lead_tags` (`INGEST_CATEGORY_STRATEGY`) — усилить, если A/B не даёт 70% без ×3 cost.

**Два смысла regen (не путать):**

| | QA (✅ нужно) | Полировка ленты (❌) |
|--|---------------|----------------------|
| **Зачем** | Проверить промпт **до/вместо** недели радара | «Чтобы старые карточки красиво смотрелись» |
| **Когда** | После каждого deploy `ai_analyze.py` | Никогда как цель |
| **Сколько** | 50–100 visible, `--limit` | Mass по всей Neon «на launch» |

**❌ Не цель:** переписывать всю ленту ради UX пользователя — старые заказы протухают; regen = **лаборатория**, не продукт.

**Accept:** p8 green · owner 5× «отправил бы as-is» · 0 vendor-lock tools · **не** трогать F2+ rank (O82-w2 ✅).

**Файлы:** `src/ai_analyze.py` · `tests/test_shared_draft.py` · `tests/test_preprod_ai_prod_audit.py` (fixtures) · `scripts/regen_shared_reply_drafts.py`

**Эталон (владелец, для смысла — не literal в JSON):** Senior Freelance Acquisition Agent · стек из ТЗ · 2–3 нишевые проблемы · сухой стиль · без воды.

---

# § O72e-4 — QA-автомат: regen → judge → **LLM-патч** промпта (**→ @coder**, сразу после p7 deploy)

**Решение владельца 2026-06-01:** после O72e-3 deploy — **запустить автомат**; владелец **следит** в терминале · gate, не 100% · **≤5** итераций.

### Цикл (одна команда)

```
qa_prompt_loop.py --profile site --apply --llm-edit-prompt
  loop (max QA_LOOP_MAX=5):
    regen 50
    judge L1+L2 (limit 40)
    PASS? → exit 0 · data/qa_prompt_loop_<ts>.json
    FAIL? → LLM-редактор: патч _LITE_SYSTEM_HEAD / _SHARED_REPLY_SYSTEM / _CABINET (не весь файл)
         → unittest fixtures (p6) + test_preprod_ai_prod_audit
         → deploy ai_analyze.py VPS (см. q7)
         → next iteration
  iteration=5 & FAIL → exit 1 + эскалация
```

| # | Задача |
|---|--------|
| q1 | **`scripts/qa_prompt_loop.py`** — оркестратор: regen → judge → метрики → JSON/md |
| q2 | Exit **0** iff L2 combined≥4 · send≥50% · L1 usable≥70% |
| q3 | **`QA_LOOP_MAX=5`** · **`--dry-run`** (regen+judge без apply patch) |
| q4 | Лог: `data/qa_prompt_loop_<date>.json` · патчи: `data/qa_prompt_patches/iter_N.md` |
| q5 | **`--llm-edit-prompt`**: вход = блок промпта + top-5 fix из judge · выход = замена блока (max +800 симв/итерация) |
| q6 | Guardrails: unit p6 · no price/deadline в shared draft · no Cursor/Gemini в reply · diff только `_LITE_*` / `_SHARED_*` / `_CABINET_*` / `_TOOLS_ONLY_*` |
| q7 | **`--deploy-vps`** каждую итерацию **или** один deploy после PASS — один режим, в шапке скрипта |
| q8 | Owner online при `--apply` · Ctrl+C = стоп |

**Модель LLM-редактора:** `gemini-2.5-flash` или `OPENROUTER_MODEL_JUDGE` — не Sonnet на L1 ingest.

**~$/итерация:** regen 50 + judge 40 + patch ≈ **$3–8** · cap **≤$40**.

**Accept:** `--dry-run` ok · `--apply` с owner · gate **≤5** итераций · patches в `data/qa_prompt_patches/`.

**Файлы:** `scripts/qa_prompt_loop.py` · `regen_shared_reply_drafts.py` · `preprod_ai_prod_audit.py` · `src/ai_analyze.py` · tests p6

---

# § O80 — ИИ UX + качество отклика/инструментов (**→ @coder**, P0)

**Решение владельца 2026-06-01:** замылился глаз — **Playwright + LLM** снова прогоняет UI и **оценивает** отклики/блок «Инструменты» (не только owner 5×).

| # | Задача |
|---|--------|
| u1 | Re-run `scripts/preprod_playwright/ux_audit.py` → `preprod_ux_audit*.json/md` + **human.md** |
| u2 | JWT: `preprod_mint_token.py --account acc1 --write-env-site` |
| u3 | Сценарий **U10b** (или расширить U4): «Написать отклик» × **5 карточек** · скрин блоков **Инструменты** + **Черновик** |
| u4 | LLM human.md: rating 1–5 · **отдельно** «tools слишком узкие?» (neon/telethon = fail) · «draft as-is?» 1–5 |
| u5 | Опц.: `--judge-since` на тех же lead_id · сводка в `data/preprod_ux_audit_human.md` |

**Accept:** robot **≥18/19** · human md с **оценкой draft+tools** · 0 critical «vendor lock» в tools на 5 карточках.

**Файлы:** `scripts/preprod_playwright/ux_audit.py` · `ux_journey.py` · `data/preprod_ux_audit*`

---

# § O72e-2 — Промпт + **tools generic** (**→ @coder**, P0)

**Judge 2026-06-01:** combined **3.56** · send **33%** · пример бага: **neon** в «Инструменты» — это **наш** стек, не ТЗ заказчика.

| # | Задача |
|---|--------|
| p1 | L2 отклик: инструменты/этапы из **ТЗ заказа**, не из RawLead stack |
| p2 | L1: dev vs design · все пункты ТЗ в summary |
| **t-tools** | **tools_required — обобщённо:** `postgresql` не `neon`/`supabase`; `telegram`/`telegram_bot` не `telethon`/`aiogram`; `python`/`php` — язык; **не** fastapi/neon/cursor в списке, если нет в тексте заказа. Промпт `_PREMIUM_SPLIT_SYSTEM`: убрать «Neon, Telethon…» как образец tools |
| t-map | `_normalize_tools_required`: map vendor→generic (`neon→postgresql`, `supabase→postgresql`, `telethon→telegram`, `aiogram→telegram`, …) · audit `KNOWN_TOOLS` sync |
| t-ui | Карточка `/lenta/`: показывать **после** map (или только ingest новых) |
| p3 | Deploy VPS · **не** regen старых |
| p4 | Accept: O80 human **0 vendor-lock** · judge **≥15** L2 combined **≥4** **или** LLM draft avg **≥4/5** на 5 карточках |

---

# § O72e — Промпт L1+L2: стабильно ≥4 combined (**→ @coder**, P0)

**Решение владельца 2026-06-01:** combined **≥4.0/5** (не 3.5) · **L1 и L2** · **без regen** старых `reply_draft` в Neon.

| # | Задача |
|---|--------|
| e1 | Итерация `_LITE_SYSTEM` / L1 user-template: контекст ТЗ, вердикт, теги — **не пустой L1**, usable ≥70% на judge |
| e2 | Итерация `_SHARED_REPLY_SYSTEM`: **2–3 шага из ТЗ**, инструменты/стек по тексту заказа, **без** «готов взять» / generic MVP |
| e3 | Judge только **свежие** лиды: флаг `--judge-since YYYY-MM-DD` или `ingested_at` после O72d deploy · **не** `--judge` по всему Neon |
| e4 | Accept: **40 L2 + 35 L1** свежих · avg combined **≥4.0** · send_as_is **≥50%** (owner цель — «как в FL отправил бы») |
| e5 | Owner loop: 5× «Написать отклик» на **новых** карточках → если ≥4/5 OK — gate soft ads |

**Не в задаче:** `regen_shared_reply_drafts.py --apply` на старых · mass replay L1.

**Файлы:** `src/ai_analyze.py` · `scripts/preprod_ai_prod_audit.py` · `tests/test_preprod_ai_prod_audit.py` · deploy VPS `ai_analyze.py`

**После ✅:** soft ads · UX P1 (O76 human md) · backlog O63/O74.

---

# § O79 — FL/Kwork: proxy pool при 1 мин цикле (**→ @coder**, P0 ops)

**Контекст:** Site VPS `POLL_INTERVAL_MINUTES=1` · сейчас FL/Kwork часто **direct** (DC IP → 403/0). Round-robin **уже** в `exchange_proxy.py` — **env на VPS пустой**.

| # | Задача |
|---|--------|
| p1 | **Карта 5 IP** (OWNER 2026-06-01): acc1/bot **45.152** · acc2 **38.154** · acc3 **168.90** · FL/Kwork pool **212.102, 185.147, 38.154, 168.90** (без 45.152) · см. `DEPLOY_VPS.md` § карта |
| p2 | Лог: `fetch:fl proxy=host:port` · **один** proxy на весь fetch (fix double `_pick_url`) |
| p3 | Failover: 403/429/timeout → **следующий** URL в списке (до исчерпания пула), не падать весь цикл |
| p4 | Accept: 10 циклов VPS · ≥2 разных host в логе · FL `скачано` >0 |

**Файлы:** `src/exchange_proxy.py` · `src/fl_parser.py` · `src/kwork_parser.py` · `docs/ops/DEPLOY_VPS.md` (§ proxy)

---

# § O72d — (**✅ deploy · ❌ regen отменён**)

**Lead verify 2026-06-01:** VPS `ai_analyze.py` 1241 lines = local · API/radar **active** · health OK · regen 80 **не** (владелец) · гейт = **новые** лиды.

---

# § O72d-archive — Regenerate shared drafts + re-judge (reference)

**Почему:** O72c judge = **15% send_as_is** на **старом кэше** Neon. Промпты O72c уже в `ai_analyze.py` — нужен **regen** + повтор judge.

| # | Задача |
|---|--------|
| r1 | Deploy `ai_analyze.py` VPS/API |
| r2 | Скрипт regen `reply_draft` visible leads (50–100, `gemini-2.5-pro`) |
| r3 | Re-judge → **send_as_is ≥70%** · combined **≥3.5** |
| r4 | Опц.: cliche → fail ingest |

**Accept:** judge L2 PASS · owner 5× draft на **свежих** карточках.

**После:** O76 → soft ads.

---

# § O72c — (**✅ реализация · ❌ product gate L2**)

**Сдача кода:** Sonnet judge L1+L2 · `config.ai_model_judge` · отчёт `preprod_ai_prod_audit_judge.md` · промпты L1/L2 обновлены · cliche warn · **12/12** tests.

**Judge prod (40 L2 + 35 L1):**

| Метрика | Результат | Accept |
|---------|-----------|--------|
| L2 relevance | **4.2**/5 | ✅ |
| L2 specificity | **2.6**/5 | ❌ вода |
| L2 universal_helpful | **2.98**/5 | ❌ |
| L2 combined | **3.26**/5 | ❌ &lt;3.5 |
| **send_as_is** | **15%** | ❌ &lt;70% |
| L1 context | **3.2**/5 · usable **34%** | ⚠️ |
| Auto draft (форм.) | **98%** | ✅ |

**Вывод:** формально отклики ок, **по смыслу — слишком generic** («готов взять», без шагов из ТЗ). Judge читал **старый кэш** `reply_draft` в Neon — промпты сами по себе его не перепишут.

**→ O72d** · **реклама ⏸**

_Критерии judge / запуск — см. `preprod_ai_prod_audit.py` docstring · отчёт `data/preprod_ai_prod_audit_judge.md`._

---

# § O72b — (**✅ Lead verify 2026-05-31**)

**Сдача:** `draft_only_pass` **97.8%** (45/46) · tools bucket **89.1%** · combined **87%** · canonical **51** без изменений · 8/8 unittest OK.

**Остаток (не блокер O72b):** 1× `L2:reply_draft` (#7051 «Готов…») · 5× `tools:empty_but_desc_hints` · 25 L1 empty — отдельно.

---

# § O72 — (**✅ фаза 1 · Lead verify 2026-05-31**)

**Контекст:** Owner **9/10** draft OK · 1 завис · 1 «разбор недоступен» → O72 **+ L1** + top fail cases для правки промпта.

**План:** [`PRE_LAUNCH_MARKETING.md`](../../ops/PRE_LAUNCH_MARKETING.md) § O72

## o72-1 — Скрипт выборки + auto-metrics (**P1**)

| # | Задача |
|---|--------|
| s1 | Новый `scripts/preprod_ai_prod_audit.py` (или флаг `--prod-sample` у matrix) — читает Neon, **не** дергает OpenRouter на фазе 1 |
| s2 | Выборка: **N=100–200** лидов · stratify category + source · **+** лиды с пустым L1/`task_summary` |
| s3 | **L2:** validators `reply_draft` · **L1:** пустой разбор при visible lead · tools vs catalog |
| s4 | **tools_required:** пустой массив · slug не из `/v1/skills/catalog` · дубликаты · эвристика «в описании есть Figma/Python/…, а tools пуст» |
| s5 | JSON → `data/preprod_ai_prod_audit.json` · markdown → `data/preprod_ai_prod_audit_human.md` |

## o72-2 — LLM judge (опционально, **P2**)

| # | Задача |
|---|--------|
| j1 | Флаг `--judge --limit 30` — второй проход OpenRouter на подвыборке |
| j2 | Промпт: релевантность 1–5 · конкретность 1–5 · tools match да/нет/частично · «отправил бы as-is» да/нет |
| j3 | В отчёт: avg scores · **top-10 worst** · **рекомендации правок промпта** (1 абзац на паттерн) |
| j4 | Если owner дал lead_id проблемных карточек — **root cause** в отчёте |

## o72-3 — Accept O72

| # | Критерий |
|---|----------|
| a1 | Скрипт отрабатывает на prod Neon без ручных правок |
| a2 | Отчёт JSON + human md в `data/` |
| a3 | **≥85%** auto-pass (нет fail validators + tools ok) |
| a4 | Если `--judge`: avg **≥3.5/5** по релевантности и конкретности |
| a5 | STATUS блок + ссылка на отчёт |

**Не в задаче:** дашборд в WP · CI cron (только ручной запуск Lead/владелец).

**Файлы (ожидаемо):** `scripts/preprod_ai_prod_audit.py` · `data/preprod_ai_prod_audit.json` · опц. тест smoke на mock rows.

---

# § O63-w1 — парсеры YouDo + Freelance.ru (**✅ Lead verify 2026-06-01**)

**Сдача:** `youdo_parser.py` · `freelance_ru_parser.py` · VPS deploy · `PUBLIC_FEED_SOURCES=…,youdo,freelance_ru` · **4/4** tests.

---

# § O63-w2 — FreelanceJob + Пчёл.нет (**✅ Lead verify 2026-06-01**)

**URL владельца 2026-06-01:**

| source_id | UI | Listing URL |
|-----------|-----|-------------|
| `freelancejob` | FreelanceJob | https://www.freelancejob.ru/projects/ |
| `pchyol` | Пчёл.нет | https://pchel.net/jobs/ |

**Решение владельца:** **только новые** — **не** подтягивать архив/старые страницы при первом включении.

| # | Задача |
|---|--------|
| w1 | `freelancejob_parser.py` · listing `/projects/` · sort **новые первые** (если есть в URL/HTML) |
| w2 | `pchyol_parser.py` · listing `/jobs/` · **пропускать** карточки «Закрыт» / «В работе» на листинге · sort «Вначале новые» |
| w3 | **`LISTING_MAX_PAGES=1`** по умолчанию (env `FREELANCEJOB_LISTING_MAX_PAGES` · `PCHYOL_LISTING_MAX_PAGES`) — как `freelance_ru` · **без** backfill deep pages |
| w4 | Ingest только через `process_new_listing` (dup `external_id` + `content_hash`) — **не** replay/seed старых id |
| w5 | `main.py` + `PUBLIC_FEED_SOURCES=…,freelancejob,pchyol` · proxy env · WP filter/badge |
| w6 | Fixture HTML: smoke parse · `tests/test_o63_parsers.py` +2 · reference scrape → `tests/fixtures/o63_pchyol_listing.html` (опц.) |
| w7 | VPS deploy + log `fetch:freelancejob` / `fetch:pchyol` · ≥1 **новый** visible/источник |

**Accept w2:** радар 10 циклов · новые лиды только с **page 1** · в ленте фильтр FreelanceJob / Пчёл.нет · **нет** массового импорта архива (2340 стр. Pchel — **не** ходить).

**Не в задаче:** пагинация >1 без отдельного OK владельца · regen L1 на старых.

**Файлы:** `src/freelancejob_parser.py` · `src/pchyol_parser.py` · `src/listing.py` · `main.py` · `page-lenta.php` · `rawlead-feed.js` source map · `.env.example`

---

# § O81-w1 — Flow-анимация лендинга (**✅ Lead verify + deploy 2026-06-01**)

**Спека:** [`LEAD_DESIGN_PROMPT.md`](../design/LEAD_DESIGN_PROMPT.md) § **O81-w1**

| # | Задача |
|---|--------|
| f1 | `flow.php` → `.rl-flow-anim` (chips → logo → 3 cards) |
| f2 | `rawlead-flow.js` + CSS · enqueue `functions.php` |
| f3 | IntersectionObserver 0.35 · один запуск · reduced-motion → финал |
| f4 | Demo-карточки: **«Совместимость N%»** · **без** «Брать/Сомнительно» |
| f5 | **Mobile 390px:** карточки **fly-out из логотипа** (не fade/slide-up) |
| f6 | Deploy theme · `/` без console.error |

**Accept:** desktop + mobile · chips in → charge → cards out · mobile = стрельба из лого

**Файлы:** `template-parts/rawlead/flow.php` · `assets/js/rawlead-flow.js` · `assets/css/rawlead.css` · `functions.php`

---

# § O82 — Match UX v2: прозрачность + «живой» % (**→ @coder**, P0 · **до рекламы**)

**Решение владельца 2026-06-01:** F2 даёт **33/50/67/100** пачками · `ai_score` = 3 корзины (85/55/15) · UI «Совместимость» без breakdown — **не moat**, «как у всех». Цель: **переиграть рынок** — понятная персональная оценка, не фейковый dating-%.

**Канон:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) §5 breakdown · [`NEON_SCHEMA.md`](NEON_SCHEMA.md) §3–4 · **O46 F2** остаёт до w2 (не ломать push/min_match).

### O82-w1 — UI правда (P1 · первый PR)

| # | Задача |
|---|--------|
| u1 | Карточка: **breakdown** под полоской — «Совпадение навыков N%» · «Качество заказа M» (`ai_score`) · опц. «Итог K» (`final_rank`) — как vision §5 |
| u2 | **Без навыков** (anon/guest): **не** стена «0%» — copy «Выбери навыки — покажем совместимость» **или** только «Качество заказа M» |
| u3 | Tooltip/мелкий текст: совместимость ≠ «хороший заказ» (copy из `SKILLS_TOOLS_CATALOG`) |
| u4 | Playwright **U11** (или U5+): breakdown виден · anon без skills ≠ ложный 0% на всех |
| u5 | Спека Design **✅:** [`DESIGNER_PROMPT.md`](../design/DESIGNER_PROMPT.md) § **O82-w1** (w1-1…w1-7) · `REFERENCE.md` §4 |

**Accept w1:** U11 pass · владелец 3 карточки глазами «понятно, не обман» · **не** менять формулу F2.

### O82-w1b — Match v2: стек, не «качество» (**✅ Lead verify + deploy 2026-06-01**)

**Решение владельца 2026-06-01:** w1 **не принят** визуально · убрать «Брать/Сомнительно» с карточки · **не** «Качество заказа» — только **совместимость стека**.

| # | Задача |
|---|--------|
| r1 | **Убрать** `renderVerdictChip` («Брать ✓» / «Сомнительно») из match row на `/lenta/` |
| r2 | Полоска + label **только «Совместимость N%»** = `keyword_match` (не `ai_score` / не `final_rank` на UI) |
| r3 | Breakdown: **совпадение навыков** (Design § D-O82b) — **не** строка «Качество заказа: …» |
| r4 | CTA «Добавь навыки…» **только** если `!isLoggedIn() && !hasUserSkills()` · при `hasUserSkills()` — **никогда** |
| r5 | Залогинен без навыков в ЛК — **не** anon-CTA; нейтрально «Укажи навыки в кабинете» или скрыть match (Design) |
| r6 | `ИДЕАЛЬНО ✦` оставить при km=100 + ≥2 тега лида (O26) · **без** замены на verdict chip |
| r7 | U11/U12 обновить под новую логику |

**Accept w1b:** owner 3 карточки · anon без навыков → CTA · anon/фильтр с навыками → % без CTA · **нет** «Брать»/«Качество заказа» на карточке.

**Файлы:** `rawlead-feed.js` · `rawlead.css` · `rawlead-cabinet.js` (если тот же match) · `ux_audit.py` U11

---

### O82-w2 — Движок v2 (P0 · moat)

| # | Задача |
|---|--------|
| e1 | **`keyword_match` + synonyms:** map RU/EN/варианты → `canonical_tag` (`yandex_direct`, `wordpress_dev`, …) · таблица в `skills_catalog.py` или `rank.py` |
| e2 | **Granular `ai_score`:** L1 JSON поле `ai_score` 0–100 **или** scoring из verdict+budget+tag confidence · **не** только 85/55/15 · fallback на корзины · **backend only** (w1b) |
| e3 | **F2+ формула** (Lead+Product выбор **одного** варианта до кода): **F2a** weighted tags (Tier A=1.0, B=0.7) · **F2b** bonus за «главный» тег ниши · **F2c** soft-cap знаменателя `min(len(lead_tags), 5)` · документировать в `NEON_SCHEMA` §3 |
| e4 | UI bar = **`keyword_match` only** (см. w1b) · breakdown = совпадение навыков, **не** «Качество × Навыки» |
| e5 | Unit-tests: 20 кейсов · на фикс. профиле **≥12 уникальных** % среди 30 лидов (не все 67/100) |
| e6 | Push `min_match` / sort=match — те же числа, что на карточке |

**Accept w2:** e5 green · owner: «не одно и то же на каждой карточке» · push порог 60% осмыслен · deploy VPS API+theme.

### O82-w3 — backlog (не блокер ads)

| # | Задача |
|---|--------|
| b1 | Embeddings task_summary ↔ user profile (vision «позже») |
| b2 | Per-user веса навыков в ЛК |

**Не в задаче:** скрывать ленту при km=0 (O62) · regen L1 на старых лидах.

**Старт O82:** **после ✅ O63-w1** · w1 можно до w2 · **оба w1+w2 до soft ads** (владелец 2026-06-01).

---

# § O83 — «Инструменты» только для авторизованных (**→ @coder**, P0 · с O82-w1)

**Решение владельца 2026-06-01:** на `/lenta/` **anon/free без JWT** — блок **«Инструменты»** в раскрытой карточке **не показывать** (premium hint; не светить L2 сторонним).

| # | Задача |
|---|--------|
| t1 | `rawlead-feed.js` `renderExpandedBody`: секция tools **только** если `isLoggedIn()` |
| t2 | `/v1/feed` для anon: **не** отдавать `tools_required` в JSON (или `[]`) — не только UI |
| t3 | Paid JWT / `/cabinet/` — **без изменений** (tools видны) |
| t4 | Playwright: anon expand card — **нет** h4 «Инструменты»; logged-in — есть |

**Accept:** anon `/lenta/` expand ×3 — 0 блоков «Инструменты» · paid mint token — tools на месте.

**Файлы:** `rawlead-feed.js` · `api_server.py` `_row_to_item` / feed handler · опц. `ux_audit.py` U12.

---

# § O63 — парсеры (полный scope · reference)

**Gate:** ✅ O37-UX · **Owner 2026-06-01:** все 4 источника.

| source_id | UI | URL старт |
|-----------|-----|-----------|
| `youdo` | YouDo | https://youdo.com/ |
| `freelance_ru` | Freelance.ru | https://freelance.ru/project/ |
| `freelancejob` | FreelanceJob | https://www.freelancejob.ru/projects/ |
| `pchyol` | Пчёл.нет | https://pchel.net/jobs/ |

| # | Задача |
|---|--------|
| p1 | Парсеры listing (как `fl_parser.py`) ×4 |
| p2 | `main.py` + лог цикла |
| p3 | Neon + `PUBLIC_FEED_SOURCES` |
| p4 | Proxy env per source |
| p5 | WP фильтр/badge источника |
| p6 | VPS smoke ≥1 visible/биржу |

**Accept:** 4 source в env → радар → `/lenta/` с фильтром по source.

---

# § O74 — TG: прямая ссылка на заказ (**📋 backlog · владелец 2026-05-30**)

**Суть:** в push @rawlead_bot / @FLPARSINGBOT — **кликабельная ссылка** на заказ на бирже (или первоисточник), не только текст карточки.

| # | Задача |
|---|--------|
| t1 | Кнопка URL / inline link · `project.url` или canonical source URL |
| t2 | Site push + Legacy consumer · единый формат |
| t3 | Accept: push на TG-лид → ссылка открывает биржу |

**Gate:** после O72 · параллельно O63 ok.

---

# § O75 — (**✅ Lead verify 2026-05-31**)

**Сдача:** `feed_visibility_where_sql` (7d + is_visible) · `/v1/feed` + `/v1/me/feed` + match_push · batch `feed_retention` в site main (~1h) · `hide_feed_older_than` (не DELETE) · `verify_o75_feed_prod.py` · 4/4 tests.

**Prod smoke:** `api.rawlead.ru/v1/feed` limit=50 · **over_7d=0** ✅

**Deploy:** VPS site main + API — после merge; batch дочистит stale visible в Neon.

---

# § O76 — (**✅ Lead verify 2026-06-01**)

**Сдача:** `preprod_ux_audit.json` **19/19** · **0 critical** · 2026-06-01 · token acc1 · скрины `data/preprod_ux_audit/`.

**LLM human** (`preprod_ux_audit_human.md`): rating **2/5** — контакты (дубль TG, нет формы) · «Сбросить фильтр» · не P0 robot. **→ @designer/@coder** по желанию владельца после soft ads.

**Bot smoke:** `preprod_bot_smoke.json` — bot ok · `/status` acc1 **fail** (не gate).

---

# § O76-archive — Pre-launch UX re-audit (reference)

**Контекст:** O37c был **18/19** (2026-05-30) · после O69–O75 · theme **v1.11.15** · владелец **не** логинится в TG acc руками — **Coder/Playwright через Cursor** (сессии в `.env`).

| # | Задача |
|---|--------|
| u1 | Re-run `scripts/preprod_playwright/ux_audit.py` на **https://rawlead.ru** · mobile + desktop · U1–U10 |
| u2 | **JWT:** `preprod_mint_token.py --account acc1 --write-env-site` → `RAWLEAD_PREPROD_ACCESS_TOKEN` (не owner uuid) |
| u3 | Сценарии: `/lenta/` · `/cabinet/` · фильтры · **«Написать отклик»** · overlay · 7d лента (нет древних) |
| u4 | **TG acc1:** mint + bot smoke `preprod_bot_smoke.py` — без телефона владельца |
| u5 | Опц. LLM-обзор journey: `preprod_ux_journey` + human md «как пользователь» |
| u6 | Отчёты → `data/preprod_ux_audit*.json/md` · скрины `data/preprod_ux_audit/` |

**Accept:** **≥18/19** pass (как O37c) · **0 critical** · owner читает `preprod_ux_audit_human.md` за 15 мин · **блокер soft ads** если &lt;17/19 или critical.

**MCP:** Playwright из [`MCP_POOL.md`](../common/MCP_POOL.md) · CDP Dolphin — только если token-путь не проходит.

**Не в scope:** новый дизайн · правки без тикета.

---

# § O77 — Просмотры: медленный старт на «горячих» (**📋 backlog · владелец 2026-05-31**)

**Продукт:** на **новом** заказе — «я первый / среди первых». O25 сейчас ~20 views к 15 мин — слишком быстро.

| Возраст | Поведение |
|---------|-----------|
| **0–15 мин** (hot) | **1–4** views, медленный рост |
| **>1 ч** | заметно больше |

**Файлы:** `src/feed_social.py` · **Gate:** после O76, не мешать O72d.

---

# § O78 — Admin-кабинет владельца (**📋 backlog · владелец 2026-05-31**)

Web admin: users · leads hide/delist · radar pause. Заготовка `/ops/` — мало. **Gate:** после soft ads, не прерывать O72d.

---

## O63 — cross-source dedup

**Риск:** одно задание на FL + YouDo + Freelance.ru → **дубли в ленте**.

**Уже есть (не ломать):**

| Слой | Как |
|------|-----|
| **Neon** | `content_hash` = SHA-256 **нормализованного** title+snippet · **UNIQUE глобально** (не per-source) · `ON CONFLICT DO NOTHING` |
| **SQLite** | только `(source, external_id)` — **не** cross-source |

→ **Одинаковый текст** с двух бирж → **одна** карточка в `/lenta/` (вторая отсекается на ingest).

**Дырки (закрыть в O63):**

| # | Задача |
|---|--------|
| d1 | **Нормализация:** единый `listing_content_hash` для всех новых парсеров · title+body без URL/₽/«FL.ru»/«YouDo» в шуме |
| d2 | **Счётчик в логе:** `cross_source_dup` / `neon_dup_hash` — когда insert отбит hash'ем, лог **какой source выиграл** (первый в Neon) |
| d3 | **Accept:** один и тот же текст с FL и `youdo` → **1** lead в feed · smoke-тест |
| d4 | **Backlog O63b (если мало):** fuzzy / эмбеддинги для «пересказанных» дублей — **не блокер** первой волны |

**Не делать:** отдельный dedup per-source · снимать UNIQUE `content_hash`.

---

## Закрыто (индекс)

Детали § → [`archive/CODER_PROMPT_ARCHIVE.md`](../archive/CODER_PROMPT_ARCHIVE.md). **Grep** по номеру задачи.

| Задача | Статус | Где |
|--------|--------|-----|
| O80 — Playwright U10b + LLM draft/tools audit | ✅ | STATUS 2026-06-01 |
| O72e-2 — tools generic + VPS map | ✅ | STATUS 2026-06-01 |
| O71 — API HTTPS + shared draft gate | ✅ | archive |
| O70 — O37c triage | ✅ | archive |
| O69 — Лента: сортировка в счётчике + навыки «Ещё» / 2 ниши | ✅ | archive |
| O65 — Снятие с ленты: заказ закрыт | ✅ | archive |
| O37c-filters — навыки по специализации + highlight | ✅ | archive |
| WAVE-UX-MOBILE — пересборка mobile feed + ЛК | ✅ | archive |
| O61 — draft без порога km | ✅ | archive |
| O60 — hotfix приёмки владельца | ✅ | archive |
| O58 — | ✅ | archive |
| O56+O57 — | ✅ | archive |
| WAVE-2-ACCEPT-FIX O55 — | ✅ | archive |
| WAVE-2-ACCEPT-FIX O54 — | ✅ | archive |
| WAVE-2-ACCEPT-FIX O53 — | ✅ | archive |
| WAVE-2-ACCEPT-FIX — O52 | ✅ | archive |
| PRE-STRESS-WAVE-2 — | ✅ | archive |
| PRE-STRESS-PACK — | ✅ | archive |
| WAVE-4-MICRO — микроправки UI | ✅ | archive |
| DEPLOY-CRLF — radar не должен падать после deploy | ✅ | archive |
| WAVE-2-CSS — Neo-Brutalist Wave 2 | ✅ | archive |
| BACKLOG-TAIL-CLEAR-O40 — хвост без L1 старше N дней | ✅ | archive |

| … | | полный список в архиве |
| **P-PORTFOLIO** | **📋 после O76** | личное портфолио на VPS — см. backlog ниже |

---

# § P-PORTFOLIO — backlog (**📋 не стартовать до O76**)

**Владелец 2026-05-31:** тот же хост rawlead.ru · интерактивное портфолио для FL · параллельно рекламе RawLead.

| # | Задача |
|---|--------|
| p1 | URL: `/portfolio/` или отдельный WP-шаблон — **не** смешивать с child theme ленты без TZ Design |
| p2 | Статика/анимации по макету `@designer` (scroll, карточки, CTA) |
| p3 | Кейсы: RawLead · **Crystal Debt** `C:\Users\hramo\crystal-debt-core` (TG Mini App fin) · **Михалыч** `C:\Users\hramo\Miha` (групповой ИИ-бот) · чат-бот WIP — скрины/тексты от владельца |
| p4 | Lighthouse mobile ≥85 · без секретов в git |
| p5 | **ИИ v4:** UI **scrub до/после** + **pain-chips → схема** (CSS/JS, без LLM на старте) · опц. `POST /portfolio/ai-plan` после чипов · **запрет** МИМО/БРАТЬ · rate limit · ключ `.env` only |
| p5b | Motion: scroll-snap кейсы · perf budget mobile · база URL **`labs.rawlead.ru`** макет владельца |
| p6 | **CD-блок:** fake JSON транзакций в static JS · UI по макету Design · **не** деплой `crystal-debt-core` |

**Accept:** одна URL для вставки в FL · владелец «готов слать заказчикам».

**Не делать:** OpenRouter/Supabase keys в frontend · поднятие полного Crystal Debt на VPS ради витрины.

Дизайн: `LEAD_DESIGN_PROMPT` § **D-P-PORTFOLIO** · [`FOR_YOU.md`](../../FOR_YOU.md) § «После гейтов».

---

## Правило hot-файла

| | |
|--|--|
| **Лимит** | **≤ ~120 строк** в CODER_PROMPT.md |
| **Активное** | одна § в шапке + backlog (O63) |
| **После ✅** | § → архив · в hot — строка в индекс · в TASKS — ✅ |
| **Lead** | раз в 1–2 недели или при >150 строк — ревизия архива |

