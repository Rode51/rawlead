# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.11** · [`ROADMAP.md`](../architect/ROADMAP.md)

**Очередь:** [`TASKS.md`](TASKS.md) · решения: [`OWNER_INTENT.md`](../architect/OWNER_INTENT.md) · **архив:** [`archive/STATUS_ARCHIVE.md`](../archive/STATUS_ARCHIVE.md)

> **Правило (~80 строк):** только «Сейчас» + активные задачи + сводка принятого. Детали сдачи → архив, не дублировать `CODER_PROMPT`.

---

## Сейчас (2026-06-01)

| | |
|--|--|
| **Theme prod** | **v1.11.17** ✅ deploy Lead 2026-06-01 |
| **O81-w1** | **✅** flow anim |
| **O82-w1b** | **✅** совместимость · без «Брать» |
| **API** | https://api.rawlead.ru **✅** · k6 fail **0%** · p95 ~1.7 s |
| **Draft** | `gemini-2.5-pro` · O72d prompts **на VPS** |
| **UX gate** | **O76 ✅ 19/19** · human md 2/5 — polish P1 |
| **O72e-2** | **✅ deploy** · tools map на VPS |
| **O80** | **✅ 20/20 robot · human 4/5 · draft avg 4.2** |
| **O72e-3** | **✅ код+deploy VPS** (1486 строк) · gate **⚠️** send **31.8%** · L1 **31.8%** → **O72e-4** |
| **O63-w1** | **✅** · **O63-w2** **✅** |
| **D-O81** | **✅ Design** · **O81-w1 ✅** код |
| **O83** | **✅ tools только auth** |
| **Реклама** | **⏸ после O63 deploy + O82** |

**Отчёты:** `data/preprod_ux_audit.json` · `preprod_ux_audit_human.md` · `preprod_ai_prod_audit_judge.md`

**Lead verify 2026-06-01 (4):** O79 **✅** (186 строк VPS · `fetch:fl/kwork proxy=` 212/185/38 · FL 90) · O72e deploy **✅** · judge since 2026-06-01 **3 L2** → combined **3.56** send **33%** → gate **❌** · **→ O72e-2** промпт или owner 5× глазами

**O72e-3→4:** deploy → **`qa_prompt_loop --apply`** (owner смотрит) · gate PASS → 5× draft → ads.

**Как проверить O79:** VPS `.env` → `FL_PROXY_URLS`/`KWORK_PROXY_URLS` (4 IP, без 45.152) · `systemctl restart rawlead-radar` · 10 циклов `radar_site.log`: `fetch:fl proxy=…` ≥2 host · FL `скачано` >0

**Как проверить O72e-2:** deploy VPS `ai_analyze.py` + `api_server.py` · `/lenta/` tools без neon/telethon · `unittest tests.test_preprod_ai_prod_audit` **16/16**

**Как проверить O80:** mint token → `scripts\preprod_playwright\ux_audit.py --base-url https://rawlead.ru` · **20/20** robot · `preprod_ux_audit_human.md` draft/tools

**Как проверить O72e-3:** deploy VPS `ai_analyze.py` · `regen_shared_reply_drafts.py --apply --limit 50 --since 2026-06-01` · judge `--judge --judge-l1 --judge-since 2026-06-01` · combined ≥4.0, send ≥50%, L1 usable ≥70%

**Как проверить O72e:** deploy `ai_analyze.py` VPS · новые лиды → `--judge --judge-l1 --judge-since 2026-06-01` · owner 5× draft

**O82 (match moat):** § `CODER_PROMPT` · w1 breakdown UI · w2 F2+ + synonyms + granular ai_score · **gate ads**

**Lead verify 2026-06-01 (7):** **O82-w1 ✅** · **O83 ✅** · **O63-w1 ⚠️** parsers+fetch на VPS · **`PUBLIC_FEED_SOURCES` без youdo/freelance_ru** → в ленте не видны · UX audit **U11/U12 не перегнан** (json 20 сцен.) · **O82-w2** не начат

**Lead verify 2026-06-01 (6):** **O82-w1 ✅** `.rl-match-breakdown` · zero state bar · **O83 ✅** anon API+UI strip tools · theme **v1.11.16**

**O63-w1 (2026-06-01):** `youdo_parser.py` · `freelance_ru_parser.py` · `main.py` · proxy env · WP filter/badge · dedup noise · **4/4** tests · **deploy VPS ✅** (`deploy-o63w1-o82-o83-vps.py`)

**Как проверить O81-w1:** `/` → scroll до «Один поток…» · chips in → charge → 3 cards fly-out · mobile 390px fly from logo · `prefers-reduced-motion` = финал сразу · DevTools 0 console.error

**Как проверить O82-w1b:** anon `/lenta/` → CTA «Добавь навыки…» без % · фильтр навыков → «Совместимость N%» + «Совпало X из Y» · нет «Брать»/«Качество заказа» · `ux_audit.py` **U11**

**Как проверить O82-w1:** _(superseded by w1b)_ · см. O82-w1b

**Как проверить O83:** anon expand ×3 — 0 «Инструменты» · mint token — tools на месте · `ux_audit.py` **U12** · `unittest tests.test_feed_privacy_o60`

**Как проверить O63-w1:** VPS log `fetch:youdo` / `fetch:freelance_ru` · `/lenta/` фильтр YouDo/Freelance.ru · `unittest tests.test_o63_parsers`

**O63-w2 (2026-06-01):** **✅ Lead verify** · **6/6** tests · VPS parsers+env · БД **13** fj / **10** pchyol · log `fetch:*` · **⚠️ deploy:** перезапуск **`rawlead-api`** (Lead ops) — без него новые source не в ленте

**Как проверить O63-w2:** `unittest tests.test_o63_parsers` **6/6** · VPS log `fetch:freelancejob` / `fetch:pchyol` · env `PUBLIC_FEED_SOURCES=fl,kwork,youdo,freelance_ru,freelancejob,pchyol` · `/lenta/` фильтр FreelanceJob / Пчёл.нет

---

## Активно

### O72 — AI draft quality audit

| | |
|--|--|
| **Цель** | качество `reply_draft` + `tools_required` на **реальных** лидах |
| **Фаза 1** | auto-metrics · tools vs catalog · JSON + human md |
| **Фаза 2** | LLM judge 20–30 samples (`--judge`) |
| **Accept** | ≥85% auto-pass · judge **combined ≥4.0** L1+L2 (свежие лиды) |
| **Coder** | [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md) § **O72** |
| **Статус** | **✅ O72b** auto · **O72c** judge отчёт · draft-only **98%** после cliche-validator |
| **Отчёт** | `preprod_ai_prod_audit.json` · `…_human.md` · **`preprod_ai_prod_audit_judge.md`** |

**O72c 2026-05-31:** `--judge`+`--judge-l1` · Sonnet 4 · `OPENROUTER_MODEL_JUDGE` в `config.py` · top-3 паттерны → `_LITE_SYSTEM` / `_SHARED_REPLY_SYSTEM` · cliche fail в validator.

**Как проверить:** `.venv\Scripts\python.exe scripts\preprod_ai_prod_audit.py --profile site` · judge: `--judge --judge-limit 40 --judge-l1 --judge-l1-limit 35` · `unittest tests.test_preprod_ai_prod_audit`

---

## Prod gates (кратко)

| Gate | Статус |
|------|--------|
| O71 HTTPS + k6 + shared draft | **✅** |
| O70 cabinet overlay v1.11.15 | **✅** |
| O69 filters/sort v1.11.14 | **✅** |
| O64–O68 delist · legacy poll · status | **✅** |
| O75 feed 7d hide + delist recheck | **✅** |
| **O76 UX re-audit** | **✅ 19/19** |
| O38 Mechanic audit | **✅ NO-GO** → закрыто O59–O71 |
| PRE-PROD stress S1–S3 | **✅** |

---

## Принято (сводка)

| Период | Блоки |
|--------|-------|
| **2026-05-30** | O64–O71 · mobile UX · filters · pre-launch infra |
| **2026-05-29** | Wave-2 O52–O58 · PRE-STRESS O42–O51 · O38 · pipeline O39 · O32 status |
| **2026-05-28** | E0–E5 · P5 E2 VPS · 3f A/B · site polish · match push |

Детали по задачам → [`archive/STATUS_ARCHIVE.md`](../archive/STATUS_ARCHIVE.md) · волны → [`archive/TASKS_HISTORY.md`](../archive/TASKS_HISTORY.md)

---

## ЛК / подписка

| Есть | Ещё нет |
|------|---------|
| `/cabinet/` TG + fallback · JWT · навыки | L2 per-user (P4b) |
| `/lenta/` paid draft · shared cache | ЮKassa |
| Push TG · Stars · `tools_required` | Heatmap (O73) |
| `/v1/me/subscription` · pause | |

---

## Блокеры

| Блокер | Кто |
|--------|-----|
| Пульт: sticky-скролл логов | `rebuild-pult.bat` — владелец |

Тикеты: [`docs/problems/`](../../problems/) — не дублировать здесь.

---

_Lead Architect · hot snapshot · 2026-06-01_
