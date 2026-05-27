# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.10** (4 категории Digital · §0i) · [`ROADMAP.md`](../architect/ROADMAP.md)

---

## Сейчас (2026-05-27) — подготовка к прод

**PM ✅** · **E0/E1** ✅ · **E2** SKILLS-TOOLS ✅ Lead verify 2026-05-27 · **→ E3** Design · **E2b** @coder (canonical tags).  
**Роли:** Coder = `CODER_PROMPT` · Mechanic = `docs/problems/` + **Gemini 2.5 (2M)** · канон [`LEAD.md`](../architect/LEAD.md) § «Coder vs Mechanic».

### STOP-STATUS-SPAM (§ P0, 2026-05-27) — **✅ принято владельцем**

| | |
|--|--|
| **Симптом** | После стопа 100+ «📊 Статус радара» в @FLPARSINGBOT |
| **Фикс** | consumer в kill; offset per bot; poll lock по token |
| **Приёмка** | владелец 2026-05-27 — **спама нет** |

### LEGACY-REPLY-DRAFT (§ P0, 2026-05-27) — **✅ принято владельцем 2026-05-27**

| | |
|--|--|
| **Симптом** | @FLPARSINGBOT: разбор есть, «Черновик отклика» **пустой** при **Сомнительно** |
| **Решение** | **B:** Брать 4–8 предл. · Сомнительно **2–4 предл.** · МИМО без карточки; `/lenta/` не трогали |
| **Lead verify** | см. выше · **LEGACY-DRAFT-LEN-SOFTEN** ✅ принято владельцем 2026-05-27 |
| **Сразу** | `stop-radar-desktop-full.vbs` → Legacy ▶ **один раз** (иначе старый consumer) |
| **Тикет** | [`2026-05-27-legacy-bot-empty-reply-draft.md`](../problems/2026-05-27-legacy-bot-empty-reply-draft.md) — код ✅ |

**Как проверить (владелец, ~5 мин):**

1. `scripts\stop-radar-desktop-full.vbs` → ярлык **RawLead Legacy** → ▶.
2. Дождаться лида **Сомнительно** в @FLPARSINGBOT — в «Черновик отклика» **2–4 предложения** (не пусто).
3. Лид **Брать** — черновик **4–8 предл.** с «Здравствуйте. Готов реализовать…».
4. **МИМО** / пустой draft — **нет** карточки; в `data\radar_legacy.log`: `neon:skip … skip:ai:no_reply_draft verdict=…` или `skip:ai:МИМО`.
5. `/lenta/` — без регрессии (только match % / L1, без черновика в UI).

**Файлы:** `src/ai_analyze.py`, `src/telegram_notify.py`, `src/lead_pipeline.py`, `docs/FOR_YOU.md`, `docs/team/architect/AI.md` (канон уже был)

### LEGACY-DRAFT-LEN-SOFTEN (§ P0, 2026-05-27) — **✅ принято владельцем 2026-05-27**

| | |
|--|--|
| **Симптом** | Заказ терялся: ИИ вернул 1 или 5 предложений → `AiAnalyzeError` → `skip:ai_unavailable_no_draft` |
| **Фикс** | Длина 4–8 / 2–4 — **цель промпта**, не hard fail; skip только пустой draft / стоп-слова / МИМО |
| **Лог** | Вне диапазона: `warn:reply_draft_sentences=N verdict=…` в `radar_legacy.log` (не `skip`) |

**Как проверить (владелец):**

1. `stop-radar-desktop-full.vbs` → Legacy ▶ (один consumer).
2. Дождаться **Сомнительно** с коротким черновиком (1 предл.) — карточка **приходит**, в логе `warn:reply_draft_sentences=1` (опц.).
3. **Брать** с 3 или 9 предл. — карточка **приходит**, не `skip:ai_unavailable`.
4. Пустой draft / **МИМО** — по-прежнему **нет** карточки (`skip:ai:no_reply_draft` / `skip:ai:МИМО`).

**Файлы:** `src/ai_analyze.py`, `docs/team/architect/AI.md`

### § PRE-LAUNCH D2 d2-10 (Coder 2026-05-27) — **✅ принято владельцем 2026-05-27**

| # | Что | Файлы |
|---|-----|-------|
| **d2-10** | Сетка row-major `1 2 / 3 4` на `/lenta/` и `/cabinet/` | `rawlead.css` — `display: grid; grid-template-columns: repeat(2, minmax(0, 1fr))`; mobile 1 col; убраны `column-count` / `break-inside` |
| **d2-1** | Title: tooltip при hover; при `.is-expanded` — без ellipsis, полная строка + блок «Полное название» в body | `rawlead.css`, JS уже с `title=` |
| **d2-7** | Чек-лист ниже | — |

**Как проверить (владелец, ~5 мин):**

1. `python scripts/wp_install_rawlead_theme.py` → Ctrl+F5 `http://radarzakaz.local/lenta/`
2. **Сетка:** desktop — карточки **1, 2** в первой строке, **3, 4** во второй (не 1 над 5). Mobile ≤767px — одна колонка.
3. **Title:** наведи на обрезанный заголовок — tooltip; клик раскрыть — заголовок читается целиком.
4. **Фильтры:** DevTools → Network → клик category «Дизайн» → `GET /v1/feed?category=design` **200**, список карточек меняется; 2 category → `category=dev,design`; навыки → «Применить» → `skills=` + `sort=match`.
5. **Кабинет:** вход (widget или fallback) → та же 2-col сетка; раскрыть карточку — «Инструменты» / «Черновик отклика» (placeholder если L2 пуст).

**Deploy:** `python scripts/wp_install_rawlead_theme.py`

### § PRE-LAUNCH A→D + D2 — **✅ E0/E1 принято владельцем 2026-05-27**

| § | Статус |
|---|--------|
| **A–D, C4/C5, d2-10, d2-1, d2-7** | ✅ принято |
| **C6** fallback login | ✅ принято |
| **Оговорка** | `/cabinet/` — фильтр `min_score` 50/70% остался (не блокер legacy) |

**Neon:** `sql/005_premium_subscriber.sql` — **✅ применено**.

**Остаётся (не E0):**

| # | Пункт |
|---|--------|
| **c7 / d2-9** | L2 `reply_draft` под `user_tags` → **§ P4b** |

**→ Сейчас:** **E3** @lead-designer (PRE-LAUNCH-UX v2 + DESIGN-DIRECTION) · **E2b** @coder (CANONICAL-TAGS) параллельно → E4 copy → E5 WP → P5/stress

**Артефакт E2:** [`SKILLS_TOOLS_CATALOG.md`](../product/SKILLS_TOOLS_CATALOG.md) v0.2 · решения владельца: анон = сортировка; кросс-нише = дубли; L1 = пул + pending_tags.

**Тикет login:** [`2026-05-27-cabinet-telegram-widget-login-fails.md`](../problems/2026-05-27-cabinet-telegram-widget-login-fails.md) — ✅ принято 2026-05-27.

### E2 SKILLS-TOOLS-RESEARCH (2026-05-27) — **✅ Lead verify Product**

| r# | Статус |
|----|--------|
| r1–r3 | ✅ 4 ниши, Tier A/B, tools, синонимы, 25 лидов Neon |
| r4 | ✅ по артефакту (владелец 2026-05-27) |
| r5 | ✅ handoff Design |

**Замечания (не блокер E3):** в tools-таблице есть `related_skills` вне пула (git_workflow…) — поправить при E5; блок «вопросы §8» частично дублирует финальные решения владельца.

### → Сейчас: Design (E3) + Coder E2b параллельно → E4 → E5 → P5/stress

**Дорожная карта этапов:** [`TASKS.md`](TASKS.md) § «Поэтапно до трафика».  
**UX-бриф владельца (фильтры, контакты, feedback, mobile):** [`LEAD_DESIGN_PROMPT.md`](../design/LEAD_DESIGN_PROMPT.md) § PRE-LAUNCH-UX v2 — **после** research, **спор с владельцем до идеала**.

### ЛК и подписка — честный статус (2026-05-27)

| Готово в коде/БД | Ещё не «прод для каждого подписчика» |
|------------------|--------------------------------------|
| Схема `users`, `user_tags`, `subscriptions`; JWT + `/v1/me/*` | Вход `/cabinet/` — **fallback** ✅ принято 2026-05-27 (`FOR_YOU.md` § fallback) |
| `GET /v1/me/feed` — match % по **тегам пользователя** | `/v1/me/subscription` — **заглушка** `free` (биллинга нет) |
| L2 поля в Neon: `tools_required`, `reply_draft`; UI в раскрытии кабинета | Нет gate «только paid видит L2» на API |
| L1 `task_summary` на ленте | Каталог навыков ≈ top-теги из лидов, не полный research-список |
| | Push ИИ-агента в TG **на пользователя** — фаза 3f, не сейчас |

**Вывод:** скелет ЛК и персональный **match по навыкам** — да; **полный продукт «каждый платный получает свой ИИ-разбор под навыки»** — после login + каталог + подписка + приёмка L2.

### → Дальше: E2–E5 PRE-LAUNCH-UX · P4b · P5 · **PRE-PROD-STRESS** · трафик

**Ворота трафика:** [`PRE_PROD_GATE.md`](../architect/PRE_PROD_GATE.md) — после P5 на хосте § **PRE-PROD-STRESS** (S1–S5), затем «едем на прод».

### PULT-MIN hotfix (Lead 2026-05-27) — **✅ verify**

| | |
|--|--|
| **Корень** | `kill_non_venv` при ▶ убивал **venv** `radar_control` (API) → пульт «error /start», воркеры не стартовали |
| **Фикс** | `/start` → `scripts/radar_spawn_workers.py`; pre-kill только `main`/`tg_main`; bat: lock + `/MIN`; убран post_spawn |
| **Verify** | `POST /start` → `200 {"ok":true}`; `/health` жив; `running=true` |
| **Владелец** | `stop-radar-desktop-full.vbs` → `start-radar-desktop-site.vbs` → ▶ → `radar_site.log` свежие строки |

### SQLite → Neon (§ SQLITE-NEON-SYNC, 2026-05-27)

| | |
|--|--|
| **Симптом** | dry-run: **1475** id в SQLite без Neon (**98** на живой ленте); в Neon с 26.05 почти нет новых |
| **Причина** | SQLite-dup → ранний выход; `content_hash` конфликт без строки по `external_id`; `skip:dup_content` до resync |
| **Фикс s7–s12** | `lead_exists` → insert (retry без hash) + `neon_resync_*` в лог; footer `neon_sqlite_resync`; replay UTF-8 |
| **Как проверить** | Stop → ▶ Site; в `radar_site.log`: `neon_resync_check` / `neon_resync_insert`, footer `neon_sqlite_resync` > 0 или `neon_insert` > 0; `.venv\Scripts\python.exe scripts\replay_neon_lite_site.py --profile site --backfill-missing --dry-run` |
| **Владелец** | Stop → ▶ Site (один раз); ключ OpenRouter в `.env.site` = `.env` (`…178`); не дублировать ▶ |

### SITE-BAT-VENV (§ b4–b10, 2026-05-27)

| | |
|--|--|
| **Симптом** | Два python: `.venv` + `Python311\python.exe` на `main`/`tg_main`/`radar_control` |
| **Фикс** | b4–b6: kill/spawn venv; b7–b10: полный стоп VBS, legacy `kill_non_venv` при втором ярлыке, ✕ → `/shutdown`, ярлыки только на `.vbs` |
| **Как проверить** | `stop-radar-desktop-full.vbs` → VBS Site → ▶; нет `Python311\...\main.py --profile site`; ✕ Site — нет `radar_control` на :18775; лампа «Биржи» зелёная ≥1 цикл |

| Трек | Статус |
|------|--------|
| **→ Coder** | **LOG-NOTIFY-DETAIL** (l6) · **POST-RESTART-CHECK** (c1–c7) |
| **→ Владелец** | `/lenta/` живая · OpenRouter в `.env.site` · ярлыки на `.vbs` |

### BOT-NOTIFY-SPLIT (владелец 2026-05-27) — **✅ Lead verify 2026-05-27 ~17:16**

| | |
|--|--|
| **Симптом** | @rawlead_bot шлёт карточки бирж, которые ждутся от @FLPARSINGBOT |
| **Факт** | `radar_site.log` 16:37 — **8 в бот** (до фикса); 17:12+ — **в бот 0** на биржах; Legacy 17:02 — **в бот 2**, `neon:skip` по id |
| **Причина** | Site `main` слал в `TELEGRAM_CHAT_ID` через rawlead; Legacy молчал на sqlite-dup |
| **Фикс (код)** | Биржи Site: без notify-плана + `skip:site_exchange_no_owner_bot`; `SITE_NOTIFY_OWNER=0` для TG; Legacy: `skip:legacy_sqlite_dup` |
| **Lead verify** | Site footer **17:16** `Итого в бот: 0`; Legacy **17:02** `в бот 2` (владелец подтвердил); процессы только `.venv` |

### Lead verify (2026-05-27 ~16:14, устарело)

| Проверка | Site | Legacy |
|----------|------|--------|
| Старт | ✅ 16:13:13 `радар:старт`, цикл 16:13:15 | ✅ 16:14:15 `neon:старт` |
| Цикл бирж / footer | ⏳ **ещё нет** (только TG ready 16:13:40) | — |
| Neon consumer | — | ✅ `выборка 8` (первый раз не 0 за день), **`новых 0` в бот** |
| `neon_resync_*` / `neon_sqlite_resync` | ❌ в логе **нет** | — |
| Процессы | ❌ **дубли** venv + `Python311` на `main`/`tg_main`/`radar_control` | ❌ дубли на `neon_legacy_consumer` |

**Вывод:** перезапуск живой; Legacy **видит** 8 строк в Neon, но в flparsig **0 новых**. Site цикл бирж **не завершён** — ждать footer или чинить дубли процессов (@coder b4–b6).

### Сделано (Coder § SITE-BAT-VENV b4–b10 + § SQLITE-NEON-SYNC s7–s12, 2026-05-27)

| § | Что |
|---|-----|
| b4 | `kill_all_radar_control` — radar_control + main/tg/join профиля, любой python |
| b5 | spawn без изменений: только `.venv\Scripts\python.exe` / `pythonw` в bat |
| b7 | `stop-radar-desktop-full.bat` + `.vbs` — kill site + legacy; канон в FOR_YOU / DESKTOP_LAUNCH |
| b8 | Legacy bat `:desktop_only` → `kill_non_venv_radar_workers(profile=legacy)` |
| b9 | ✕ пульт → POST `/shutdown` (stop + `kill_all_radar_control` своего профиля) |
| b10 | `rebuild-pult.bat` + DESKTOP_LAUNCH: ярлыки **только** на `start-radar-desktop-*-.vbs` |
| s7–s9 | Биржи: `neon_resync_check` / `insert` / `skip:*`; retry INSERT без `content_hash`; не `dup_content` до resync |
| s10 | `replay_neon_lite_site.py` — UTF-8 stdout/stderr, ASCII `\|` в сводке |
| s11 | `pg_storage.connection()` — `with psycopg.connect`, без shared `_conn` |

**Файлы:** `src/process_guard.py`, `src/lead_pipeline.py`, `src/pg_storage.py`, `scripts/radar_control.py`, `scripts/stop-radar-desktop-full.bat`, `scripts/stop-radar-desktop-full.vbs`, `scripts/start-radar-desktop.bat`, `scripts/start-radar-desktop-site.bat`, `scripts/rebuild-pult.bat`, `desktop/src/main.ts`, `docs/FOR_YOU.md`, `docs/ops/DESKTOP_LAUNCH.md`
| **Vision v0.10** | ✅ |
| **P1 · D1 · P4 · F-LOCAL** | ✅ код |
| **S-SPLIT** · **NEON-DATA** · **F-SITE-FILTERS-0i** | ✅ код · приёмка ⏳ |
| **§ P5 деплой** | ⏸ после приёмки Neon + «едем на прод» |
| **Lead Design** | ⏸ в конце |

**Диагностика Neon (Lead):** ~3260 строк; последний `created_at` **2026-05-26 ~09:00 UTC**; `design` ~260, `is_visible=true` ~1; dup по **тексту**, не по категории.

**Coder:** [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md) § P5 (только после ворот)  
**Ворота:** [`PRE_PROD_GATE.md`](../architect/PRE_PROD_GATE.md) § блокер N/O

### Сделано (Coder § NEON-DEDUP-REPLAY + LOG-NEON-CYCLE + P5-PREP, 2026-05-27)

| § | Что |
|---|-----|
| r1 | `plan_new_listing`: dup Neon без L1 → FILTERS_SITE → L1 → `update_after_lite`; SQLite-dup тоже догоняет L1 |
| r2 | Dup + L1 есть → `neon_dup_skip`, без повторного L1 |
| r3 | `scripts/replay_neon_lite_site.py` — `--dry-run` / `--limit N`, только site + PUBLIC_FEED_SOURCES |
| f1 | `api_server`: feed/me-feed используют `is_visible = TRUE` (без `notified_at` gate) |
| a1 | SITE fallback: `SITE_NOTIFY_ON_AI_UNAVAILABLE=0` по умолчанию → при падении L1 в TG не шлём; opt-in через env |
| a2 | Лог цикла: `skip:ai_unavailable` отдельным счётчиком в строке источника |
| l1 | Футер цикла: `neon_insert` / `neon_replay` / `neon_dup_skip` (отдельно от `dup` SQLite) |
| l2 | Убрана подпись «на сайт = в бот» → «лента после L1 — см. Neon is_visible» |
| h1 | `RADAR_CORS_ORIGINS` в `.env` — без `*` если задан список |
| h2 | Воркеры main/tg → `data/radar_{profile}_{exchanges|tg}.log`, ротация ~5MB |
| h5 | Tauri HTTP: + `:18766` (API) к :18765/:18775 |

**Файлы:** `src/lead_pipeline.py`, `src/pg_storage.py`, `src/radar_cycle_log.py`, `src/main.py`, `scripts/replay_neon_lite_site.py`, `scripts/radar_control.py`, `desktop/src-tauri/capabilities/default.json`, `.env.example`, `docs/ops/RADAR_LOG.md`

**Как проверить:**
1. Site ▶ 30 мин → в `radar_site.log` футер с `neon_insert` / `neon_replay`; Neon-счётчики отдельно от `dup`
2. `.venv\Scripts\python.exe scripts\replay_neon_lite_site.py --profile site --dry-run` → список без L1
3. `--limit 10` → `ai_verdict` / `task_summary` у старых design в Neon
4. `/lenta/` — карточки с «Суть задания»
5. `RADAR_CORS_ORIGINS=http://radarzakaz.local` → пульт не отдаёт `*`
6. `data/radar_site_exchanges.log`, `data/radar_site_tg.log` после Site ▶

---

### Сделано (Coder § F-SITE-FILTERS-0i + пульт p1–p3, 2026-05-27)

| § | Что |
|---|-----|
| f0 | `FILTERS_SITE.md` — убраны из стопа: `figma`, `фигма`, `видеомонтаж`, `смонтировать`, `монтаж рилс`, `motion design`, `иллюстратор`, `фотошоп`, `photoshop`, `логотип`, `баннер`, `дизайн макета`, `отрисовать`, `таргетолог`, `настройка таргет`, `ведение инстаграм` |
| f1 | «Берём» Site — 4 ниши §0i уже были в `FILTERS_SITE.md` ✅ |
| f2 | `neon_ingest_wide` уже в `config.py` ✅ |
| f3 | `pg_storage.py`: `_MIN_AI_SCORE_VISIBLE_NONTECH = 50`; `_is_visible_lite(lite, category)` — dev=40, design/marketing/text=50 |
| p1 | `radar_control.py`: лампа Legacy «Neon» (consumer) — не «Биржи disabled»; исправлен `status_payload` (только `not neon_consumer_enabled()` → disabled) |
| p2 | `FOR_YOU.md`: «лампа **Neon** = consumer, не биржи» в разделе «оба ▶» |
| p3 | `start-radar-desktop-site.bat` убивает старый API при старте ✅ (было) |

**Файлы:** `docs/ops/FILTERS_SITE.md`, `src/pg_storage.py`, `scripts/radar_control.py`, `docs/FOR_YOU.md`

**Как проверить:**
1. Site ▶ → лид с «figma» в title → проходит фильтр → `is_visible` при L1-вердикте «Брать»/«Сомнительно»; Legacy → тот же лид может не идти (стоп в FILTERS_LEGACY)
2. Legacy ▶ → пульт → лампа подписана **«Neon»**, статус «работает» (не «выкл»)
3. `ai_score=55` + category=design → `is_visible=true`; `ai_score=45` + category=design → `is_visible=false`; `ai_score=45` + category=dev → `is_visible=true`
4. Site ▶ → rebuilt `desktop.exe` (после `rebuild-pult.bat`)

---

### Сделано (Coder § S-SPLIT-NEON-DATA, 2026-05-27)

| § | Что |
|---|-----|
| n1 | Legacy: `RADAR_EXCHANGES_ENABLED=0`, spawn `neon_legacy_consumer.py`, не `main.py` |
| n2 | Site: `RADAR_EXCHANGES_ENABLED=1`, spawn `main` + `tg_main`; defaults в `config.py` |
| n3 | Site ingest: `record_new_lead` **до** `FILTERS_SITE` (`cfg.neon_ingest_wide`) |
| n4 | Legacy consumer: SELECT Neon → `FILTERS_LEGACY` → `analyze_project` → TG; SQLite дедуп |
| n5 | Legacy `DATABASE_URL` — только read (без `record_new_lead` в consumer) |

**Файлы:** `src/config.py`, `src/lead_pipeline.py`, `src/pg_storage.py`, `src/neon_legacy_consumer.py`, `src/main.py`, `scripts/radar_control.py`, `src/process_guard.py`, `.env.example`, `.env.site`, `.env.legacy`

**Как проверить:**

1. Site ▶ 24/7 → в `radar_site.log` циклы бирж; Neon `leads` растёт; `/lenta/` живая.
2. Legacy ▶ → процесс `neon_legacy_consumer.py --profile legacy`, **нет** `main.py`; в `radar_legacy.log` строки `neon:цикл`.
3. Legacy бот — заказы по `FILTERS_LEGACY.md` без второго парсера бирж.
4. `data/legacy_neon_cursor.json` — курсор; при первом старте = `MAX(id)` (без бэклога).

### Сделано (Coder § S-SPLIT-DUAL + F-PROMPT p3, 2026-05-27)

| § | Что |
|---|-----|
| d1 | `RADAR_EXCHANGES_ENABLED` (site=0); site ▶ без spawn `main.py` |
| d3 | Лампа **Биржи** idle «выкл» на site; TG живая |
| d5 | `kill_non_venv` pre/post_spawn + `keep_pids` + фильтр `--profile` |
| p3 | `analyze_premium(lite=…)` — L2 из `AI.md`, блок «Уже от L1» в user |

**Файлы:** `src/config.py`, `src/process_guard.py`, `scripts/radar_control.py`, `src/ai_analyze.py`, `src/lead_pipeline.py`, `docs/team/architect/AI.md`, `.env.example`, `docs/FOR_YOU.md`

**Как проверить:**

1. Legacy ▶ → `main.py --profile legacy`, лампа TG «выкл», биржи ok.
2. Site ▶ → только `tg_main --profile site`, лампа биржи «выкл», TG ok.
3. Оба ▶ → legacy `main` + site `tg_main`; в `radar_site.log` нет цикла бирж.
4. Site «Брать» → L2 user с `Уже от L1` (см. лог/отладку промпта).

### Сделано (Coder § S-SPLIT-TG + PULT-THEME, 2026-05-27)

| § | Что |
|---|-----|
| g1 | `radar_tg_enabled()` в `config.py`; legacy `RADAR_TG_ENABLED=0` → без spawn `tg_main`, лампа TG «выкл» |
| g2 | site default `RADAR_TG_ENABLED=1` — tg_main (биржи → § S-SPLIT-DUAL) |
| g3 | `kill_duplicate` / `count_radar_workers` по `--profile` — два пульта ▶ без пересечения воркеров |
| t1 | `data-profile` на `<html>`; тема legacy в `tokens.css` (янтарь) |
| t2 | Бейдж **LEGACY** / **SITE** в заголовке |
| t3 | API site: `VITE_RADAR_API` в bat + query `?profile=` / `?port=` + Tauri `RADAR_CONTROL_PORT` из env |

**Файлы:** `src/config.py`, `scripts/radar_control.py`, `desktop/src/main.ts`, `desktop/index.html`, `desktop/src/styles/tokens.css`, `desktop/src/styles/pult.css`, `desktop/src-tauri/src/lib.rs`, `.env.example`

**Как проверить:**

1. Legacy VBS → ▶ → в процессах только `main.py --profile legacy`, **нет** `tg_main`; лампа TG серая, подпись «выкл»; пульт янтарный, бейдж LEGACY.
2. Site VBS → ▶ → только `tg_main` `--profile site` (биржи выкл); лампа TG живая; API `http://127.0.0.1:18775/health`.
3. Оба пульта ▶ одновременно — без `database is locked` на acc (только site держит tg_main).

### Сделано (Coder § P1.2b / f6 TG, 2026-05-27)

| § | Что |
|---|-----|
| m1 | Listen **только** `TG_PUBLIC_FEED_ALLOWLIST.txt` ∩ join queue `done` — без `INGEST_SOURCES_SNG_25.json` TG-A и без droplist |
| m2 | `docs/ops/TG_JOIN_QUEUE_v2.csv` — 30 Tier A (11 done, 19 pending, волны ~3/нед); site: `TG_JOIN_QUEUE_CSV` в `.env.site` + default профиля |
| — | `join_queue_csv_path()` в `tg_join_lib` — очередь из env, не хардкод v1 |

**Файлы:** `src/public_feed.py`, `src/tg_join_lib.py`, `src/config.py`, `docs/ops/TG_JOIN_QUEUE_v2.csv`, `scripts/build_tg_join_queue_v2.py`, `.env.site`, `.env.example`

**Как проверить:**

1. Site радар ▶ → в `data/radar_site.log` нет `тг:…` из MVP-чатов (`ipomogator`, `workk_on`, …).
2. `TG_JOIN_QUEUE_v2.csv` — pending theyseeku, remoteit, …; join по `tg_join_queue.py` / авто в `tg_main`.
3. После join строка `done` + `chat_id` → listen подхватит без рестарта (если id в `telethon_chat_ids_accN.txt` или seed из CSV).
4. `python scripts/build_tg_join_queue_v2.py` — пересборка v2 после правки allowlist.

### Сделано (Coder § S-SPLIT, 2026-05-27)

| § | Что |
|---|-----|
| s1 | `RADAR_PROFILE` + `--profile`; `.env.legacy` / `.env.site` (+ fallback `.env`); defaults в `config.py` |
| s2 | `docs/ops/FILTERS_LEGACY.md` — копия `FILTERS.md`, помечен «не править при SITE» |
| s3 | `docs/ops/FILTERS_SITE.md`; `filters.py` → файл по профилю |
| s4 | `data/radar_legacy.log` / `data/radar_site.log`; locks `._{role}_{profile}.lock` |
| s5 | Site API :18775; `start-radar-desktop-site.vbs` / `-legacy.vbs` |
| s6 | Ключи из `.env.site` (отдельный файл; владелец копирует и подставляет бот+OpenRouter) |
| s7 | LEGACY: `AI_MODE=legacy` → один `analyze_project`, без L1/L2 |
| s8 | SITE: `AI_MODE=split` → L1 Neon + L2 в бот |
| s9 | `.env.example` § S-SPLIT; `FOR_YOU.md` — два ярлыка |

**Как проверить (владелец):**

1. Скопировать `.env` → `.env.legacy` (как есть) и `.env.site` (новый `TELEGRAM_BOT_TOKEN` + ключ OpenRouter).
2. Ярлык **Радар Legacy** → `scripts\start-radar-desktop-legacy.vbs` → лог `data/radar_legacy.log`, бот @FLPARSINGBOT.
3. Ярлык **Радар Site** → `scripts\start-radar-desktop-site.vbs` → лог `data/radar_site.log`, API :18775.
4. LEGACY 24 ч: поведение как до split (один разбор в TG). SITE: L1 в Neon/`/lenta/`, L2 при «Брать».

### Решение владельца (2026-05-27): 2 контура, без смешивания

| Контур | Зачем | Бот |
|--------|--------|-----|
| **LEGACY** | Твой рабочий поток — **не трогать** | Текущий @FLPARSINGBOT |
| **SITE** | Сайт + подписчики + L1/L2 | **Новый** бот (создашь) |

Канон: [`PROJECT_MAP.md`](PROJECT_MAP.md) § «Два контура» · Coder § **S-SPLIT**

### Продукт (владелец 2026-05-26, F-LOCAL)

| Поверхность | ИИ |
|-------------|-----|
| **Telegram-бот (ты)** | Полный разбор + уведомление — **как подписка**, без изменений по смыслу |
| **`/lenta/` публичка** | Карточка заказа **без** «разбора от бота» (не дублировать TG-простыню) |
| **Дедуп** | ✅ `listing_dedup` — уже в пайплайне |
| **TG скоро** | Автоджойн + стоп рекламы в [`FILTERS.md`](../../ops/FILTERS.md) § TG |
| **ИИ 2 уровня** | L1: score + **`task_summary`** (2 предл.) для карточки; L2 → бот при «Брать» · полный текст — ссылка на источник · [`CODER_PROMPT`](../architect/CODER_PROMPT.md) § F-LOCAL |

### Решение владельца (лентa, 2026-05-26)

- Публичка: **только фриланс-биржи** — `fl`, `kwork`, `freelancehunt`
- **Отложить** (код парсеров не удалять): `vc_ru`, `habr_career` (вакансии / job-ленты)
- `.env`: `PUBLIC_FEED_SOURCES=fl,kwork,freelancehunt`

### Принято владельцем (§ F-LOCAL + F-RESEARCH, 2026-05-26)

**С оговорками:** L2 пока **не** получает блок L1 в промпт (см. доработку ниже); 20 тестов §6 research — не в STATUS.

### Проверка Lead (авто, 2026-05-26)

| Критерий | Результат |
|----------|-----------|
| `.env` `PUBLIC_FEED_SOURCES` | ✅ `fl,kwork,freelancehunt` |
| `filters.py` smoke (стоп/берём) | ✅ |
| L1 `analyze_lite` + `task_summary` → Neon/API/JS | ✅ `sql/004_task_summary.sql`, `rawlead-feed.js` «Суть задания» |
| L2 только при «Брать» в `send_listing_notification` | ✅ |
| Счётчик `ИИ L1=… L2=…` в футере цикла | ✅ |
| `FILTERS.md` + v0.10 + § TG | ✅ |
| L2 user с контекстом L1 (`analyze_premium(lite=…)`) | ✅ § F-PROMPT p3 |
| F-RESEARCH r4 — 20 тестов pass/fail | ⚠️ не сдано |
| `stop_tg` отдельно | ⏸ опционально |
| Git | ⚠️ не закоммичено (после 445c603) |

### Сделано (Coder § F-LOCAL, 2026-05-26)

| § | Что |
|---|-----|
| f1 | V10.1 + TG-стопы: `filters.py` ← [`FILTERS.md`](../../ops/FILTERS.md) |
| f2–ai3 | L1 `analyze_lite` / L2 `analyze_premium`; env `OPENROUTER_MODEL_*`; счётчик L1/L2 в `radar.log` |
| f4 | `/lenta/`: `task_summary` в API + JS; бот — только «Брать» + полный L2 |
| f5 | Ниже — как крутить фильтры и лог |

**Файлы:** `src/ai_analyze.py`, `src/lead_pipeline.py`, `src/pg_storage.py`, `src/filters.py`, `src/config.py`, `src/api_server.py`, `sql/004_task_summary.sql`, `wordpress/.../rawlead-feed.js`, `.env.example`

**Как проверить:**
1. Neon: `sql/004_task_summary.sql`
2. `.env`: `AI_ENABLED=1`, `OPENROUTER_MODEL_SUMMARY=deepseek/deepseek-chat` (опц.), перезапуск радара
3. `data/radar.log`: строки `filter` / `МИМО` / `dup`; в футере `ИИ L1=… L2=…` (L2 ≪ L1)
4. `/lenta/`: в карточке «Суть задания», не простыня body; в бот — полный разбор только на «Брать»

**FILTERS + лог (владелец):** правки списков → [`docs/ops/FILTERS.md`](../../ops/FILTERS.md) → перезапуск радара; `FILTER_WIDE=1` — в ИИ всё кроме стопа, `0` — ещё нужно «берём». В логе смотри `filter` (Python), `МИМО` (L1), `dup`, футер `L1` vs `L2`.

### Сделано (Coder § P4, 2026-05-26)

| § | Что |
|---|-----|
| a1 | `POST /v1/auth/telegram` — проверка hash Login Widget |
| a2 | Upsert `users` по `tg_user_id`, JWT 7d |
| a3 | `/v1/me/*` — `Authorization: Bearer` (любой UUID); owner header — fallback |
| a4 | `/cabinet/` — экран входа + виджет TG, `localStorage` token |
| a5 | `.env.example` — `TELEGRAM_LOGIN_BOT_TOKEN`, `RAWLEAD_JWT_SECRET`, `RAWLEAD_TG_BOT_USERNAME` в wp-config |

**Файлы:** `src/telegram_login.py`, `src/jwt_auth.py`, `src/api_server.py`, `sql/003_users_telegram.sql`, `wordpress/.../rawlead-api.php`, `page-cabinet.php`, `rawlead-cabinet.js`, `requirements.txt`

**Как проверить:**
1. Neon: `sql/003_users_telegram.sql`
2. `pip install -r requirements.txt` · перезапуск API `:18766`
3. `wp-config.php`: `define('RAWLEAD_TG_BOT_USERNAME', 'имя_бота');` (без @)
4. `python scripts/wp_install_rawlead_theme.py` → `/cabinet/` → Login → теги/лента
5. DevTools: запросы с `Authorization: Bearer …`

### Принято владельцем (§ P1.3d + § D1 + § P4, 2026-05-26)

- **P1.3d:** код — только источники из `PUBLIC_FEED_SOURCES`; парсеры вакансий не удалены
- **D1:** чипы «Категория» на `/lenta/` и `/cabinet/` (код в теме WP)
- **P4:** вход через Telegram Login + JWT + `/v1/me/*`

**Проверка Lead (авто, не замена твоего клика):**

| Проверка | Результат |
|----------|-----------|
| Код `public_feed` дефолт 3 биржи | ✅ |
| Чипы `filter-category-*` в `page-lenta.php` | ✅ |
| `POST /v1/auth/telegram` в `api_server.py` | ✅ |
| **`.env` `PUBLIC_FEED_SOURCES`** | ⚠️ проверить: **одна** строка `PUBLIC_FEED_SOURCES=fl,kwork,freelancehunt` (без `PUBLIC_FEED_SOURCES=` внутри значения) |
| API `:18766` | ⚠️ не отвечал (таймаут) — `pip install` + старт API |
| `radar.log` последний цикл | ⚠️ 20:17 — видны FL+Kwork, цикл оборван TG-ошибками; пульт `last_cycle` со старыми 5 источниками до рестарта |

### Сделано (Coder § P1.3d, 2026-05-26)

| § | Что |
|---|-----|
| b1 | Дефолт env: `fl,kwork,freelancehunt` — `src/public_feed.py`, `.env.example` |
| b2 | `run_cycle` + P1.4 лог — **3** строки бирж (только из `PUBLIC_FEED_SOURCES`); vc_ru/habr_career не вызываются и не логируются |
| b3 | Канон [`PUBLIC_FEED_WEB_SOURCES.txt`](../../ops/PUBLIC_FEED_WEB_SOURCES.txt) — без изменений |
| b4 | Парсеры `vc_ru` / `habr_career` в `src/` — на месте |

**Файлы:** `src/public_feed.py`, `src/main.py`, `src/radar_cycle_log.py`, `.env.example`

**Как проверить:**
1. `.env`: `PUBLIC_FEED_SOURCES=fl,kwork,freelancehunt`
2. Перезапуск радара → `data/radar.log`: `── Цикл ──` + **3** строки (FL, Kwork, Freelancehunt) + `Итого`
3. Нет строк VC.ru / Habr Career в логе и пульте «Последний цикл»

### Сделано (Coder § D1, 2026-05-26)

| § | Что |
|---|-----|
| d1 | Sidebar + mobile sheet: блок **Категория** (5 chips) после «Источник» |
| d2 | `GET /v1/feed?category=dev|design|marketing|text`; смена → `offset=0`, лента с нуля |
| d3 | Desktop: Код/Дизайн/Маркетинг/Тексты; mobile: SMM для marketing |
| d4 | «Сбросить фильтры» снимает category; `/cabinet` — те же чипы + `?category=` в me/feed |

**Файлы:** `page-lenta.php`, `page-cabinet.php`, `assets/js/rawlead-feed.js`, `assets/js/rawlead-cabinet.js`, `assets/css/rawlead.css`

**Как проверить:**
1. `python scripts/wp_install_rawlead_theme.py` → Ctrl+F5 `/lenta/`
2. Чип «Дизайн» → Network `GET …/feed?category=design&offset=0`
3. «Сбросить фильтры» → без `category` в query
4. `/cabinet/` — те же чипы, фильтр в персональной ленте

### Принято владельцем (§ P1.H, 2026-05-26)

- Пульт: **Биржи ok**, `count_radar_workers() == (1, 1)`
- `data/radar.log`: цикл **18:38:11** — один `── Цикл ──`, 5 бирж + `Итого в бот`
- `GET /status` → `last_cycle.ts` совпадает с логом
- Доп. фикс: `main.py` `_echo` — `UnicodeEncodeError` под cp1251 (spawn с пульта), иначе main падал сразу после заголовка цикла
- Оговорка: иногда остаются **system Python** дубли main/tg — снять **Стоп → ▶** с пульта; не критерий отказа

### Сделано (Coder § P1.H, 2026-05-26)

| § | Что |
|---|-----|
| R1 | `src/main.py` — `data/.main.lock`, второй экземпляр exit 1 + строка в `radar.log` |
| R2 | **Не** `kill_duplicate` в `main`/`tg_main` при старте (убивал дочерний system Python, exit 15/0). Очистка — `radar_control` `pre_spawn` + lock |
| R2b | `kill_duplicate_radar_workers` — `keep_pids` / дерево `expand_spawn_keep_pids` (не резать child PID) |
| R3 | После ▶: только `pre_spawn` (без `post_spawn`/`trim`); `count==(1,1)`; при наличии `.venv` воркера — 1 логический main/tg |
| R3b | `kill_non_venv`: не трогать **только** `.venv\\Scripts\\python(.exe)`; system+путь проекта — убить |
| R3d | `count_radar_workers` — shim+child = 1 логический воркер |
| R4 | `data/.radar_ops.lock` — межпроцессный lock `/start`/`/stop` (гонка 2× radar_control) |
| R5 | `stop-radar.bat` — main/tg/join (`python`+`pythonw`), **без** `radar_control` / API |
| R6 | `tg_main` — lock до `_log_start`; fail-closed; `radar_control` lock — fail-closed |
| — | `start-radar-desktop.bat` — если `/health` ok, не kill API (двойной ярлык) |

**Источник 2× main:** гонка двух `radar_control` на `/start` (каждый spawn main+tg) + system/Cursor воркеры; не bat spawn.

**Файлы:** `src/main.py`, `scripts/tg_main.py`, `src/process_guard.py`, `scripts/radar_control.py`, `scripts/stop-radar.bat`, `scripts/start-radar-desktop.bat`

**Как проверить:**
0. После правок **перезапустить API пульта** (закрыть Tauri / убить `radar_control.py`, снова `start-radar-desktop.bat`) — иначе старый код в памяти
1. Пульт уже открыт (API жив) → `scripts\stop-radar.bat` → API **не** падает (`http://127.0.0.1:18765/health` ok)
2. Пульт ▶ → `count_radar_workers()` → `(1, 1)`, **5+ мин** живы (exe может быть `.venv` или system+путь проекта)
3. `data/radar.log` — **нет** `радар:дубль` с `radar_control:post_spawn` / `:trim` сразу после ▶; один `── Цикл ──`, 5 строк FL…Habr + `Итого`, лампа **Биржи ok**
4. Второй ручной `start-radar-all.bat` при работающем пульте — lock, дубль не остаётся

Тикет: [`2026-05-26-duplicate-workers-regression.md`](../../problems/2026-05-26-duplicate-workers-regression.md)

### Сделано (Coder § P1.4, 2026-05-26)

| § | Что |
|---|-----|
| P1.4.1 | `data/radar.log` — `── Цикл … ──`, строка на **5** источников (fl/kwork/vc_ru/freelancehunt/habr_career), `Итого в бот │ на сайт` |
| P1.4.1 | `SourceCycleStats` — filter / МИМО / dup / budget без раздувания `errors[]` |
| P1.4.2 | `radar_control` tail **800** строк; вкладка **Статус** — «Последний цикл» из SQLite |
| P1.4.2 | `GET /status` → `last_cycle` JSON (опц.) |

**Файлы:** `src/radar_cycle_log.py`, `src/main.py`, `src/lead_pipeline.py`, `src/radar_status.py`, `scripts/radar_control.py`, `desktop/src/main.ts`, `docs/ops/RUN.md`, `docs/ops/RADAR_LOG.md`

**Как проверить:**
1. Перезапуск радара (`start-radar.bat`)
2. `data/radar.log` — после цикла 5 строк источников + итого (не `карточки_fl=…`)
3. Пульт → вкладка **Статус** — те же строки в блоке «Последний цикл»
4. [`RADAR_LOG.md`](../../ops/RADAR_LOG.md) — расшифровка колонок

### Сделано (Coder § P1, 2026-05-26)

| § | Что |
|---|-----|
| P1.1 | `PUBLIC_FEED_SOURCES` — фильтр `GET /v1/feed` и `/v1/skills/catalog` (по умолчанию `fl,kwork`) |
| P1.1 | Ingest: `is_visible` только для source из whitelist |
| P1.2 | TG listen: только **allowlist** + `TG_JOIN_QUEUE_v2` (`done`); MVP/TG-A/droplist не слушаются |
| P1.3 | Парсеры: `vc_ru`, `freelancehunt`, `habr_career` — цикл радара после Kwork |
| P1.3c | **vc_ru** — API `api.vc.ru/v2.8/timeline?subsitesIds=jobs` (~12 постов/цикл); **habr_freelance** убран (410); **freelancehunt** — API v2 по `FREELANCEHUNT_API_TOKEN` или HTML/Playwright |

**Файлы:** `src/vc_ru_parser.py`, `src/freelancehunt_parser.py`, `src/html_fetch.py`, `src/main.py`, `src/public_feed.py`, `.env.example`, `requirements.txt`

**Как проверить:**
1. `.env`: `PUBLIC_FEED_SOURCES=fl,kwork,vc_ru,freelancehunt,habr_career` + `FREELANCEHUNT_API_TOKEN=…` (https://freelancehunt.com/my/api)
2. `pip install -r requirements.txt` → `playwright install chromium` (fallback HTML)
3. Перезапуск `uvicorn src.api_server:app --port 18766` + радар (`start-radar.bat`)
4. `data/radar.log` — в `ош=` префиксы `vc_ru:id=…`, `habr_career:id=…`; без токена FH — `freelancehunt:fetch:…API_TOKEN…`
5. `GET /v1/feed?limit=5` — source из env
6. TG — отдельно [`2026-05-26-p1-tg-migration-gaps.md`](../../problems/2026-05-26-p1-tg-migration-gaps.md)

### Сделано (Coder § V10.5 + P7, 2026-05-26)

| § | Что |
|---|-----|
| V10.5 | `_skills_sql`: пересечение через `jsonb_array_elements_text` + `ANY(text[])` — нет `jsonb && jsonb` |
| P7 c1 | Neon `leads.category` + `sql/002_leads_category.sql` (миграция применена) |
| P7 c2 | FL slug / Kwork `c=` + want → `listing_category` → `pg_storage` |
| P7 c3 | `GET /v1/feed?category=design,text` · ingest `category` |
| P7 backfill | `scripts/backfill_lead_category.py` — 3229 строк `infer_lead_category(title, body, lead_tags)`; NULL → 0 |
| — | Dogfood PROFILE / `ai_analyze` **не трогали** |

**Файлы:** `src/api_server.py`, `src/lead_category.py`, `src/pg_storage.py`, `src/fl_parser.py`, `src/kwork_parser.py`, `src/listing.py`, `sql/002_leads_category.sql`, `sql/001_neon_schema.sql`, `scripts/backfill_lead_category.py`

**Как проверить:**
1. Перезапуск `uvicorn src.api_server:app --port 18766`
2. `/lenta/` — выбрать навыки → «Применить» → 200, `sort=match`, без 500 в логе
3. `GET /v1/feed?skills=python&sort=match` → 200
4. `GET /v1/feed?category=design` → только design (фильтр по колонке, не infer на read)
5. Neon: `SELECT COUNT(*) FROM leads WHERE category IS NULL` → **0**
6. Новый лид с радара — в Neon `leads.category` заполнен при ingest

### Сделано (Coder § V10, 2026-05-26)

| § | Что |
|---|-----|
| V10.1 | `FILTERS.md` — стоп VA/диктор/озвучка, дропы §0i, «Берём» design/marketing/text |
| V10.2 | `/v1/feed` + чипы: design/marketing/text — порог «Брать» **55** при фильтре ≥70; dogfood (`pg_storage`, `ai_analyze`) **без изменений** |
| V10.3 | `/v1/skills/catalog` → `groups` (4 ниши) + `skills`; UI `/lenta/` — секции с заголовками |
| V10.4 | `audience.php` — 4 карточки; CSS 2×2 desktop; `home.md` канон |

**Файлы:** `src/lead_category.py`, `src/api_server.py`, `docs/ops/FILTERS.md`, `audience.php`, `rawlead-feed.js`, `rawlead.css`, `page-lenta.php`

**Как проверить:**
1. `python -c "from src.filters import default_listing_filter; f=default_listing_filter(); assert f.rejects('диктор')"`
2. Перезапуск `uvicorn src.api_server:app --port 18766` → `GET /v1/skills/catalog` — поле `groups`
3. `python scripts/wp_install_rawlead_theme.py` → главная 4 карточки 2×2; `/lenta/` — навыки по группам, фильтр «Брать (≥70 / digital ≥55)»
4. Бот: вердикт МИМО/3500 ₽ — как раньше (PROFILE не трогали)

| Neon | ✅ владелец |
| Allowlist TG | ✅ listen + join v2 (`TG_JOIN_QUEUE_v2.csv`) |
| **Product v0.9.2** | ✅ §0h v2: агрегаторы + большая база; TG raw не в ленту |
| **Docs / ROADMAP** | ✅ синхронизированы под ставку B |
| **TG dogfood** | ✅ /start acc авто при подключении · acc шлют в бот (владелец 2026-05-25) · дубли python — Mechanic |
| **Lead Design** | ✅ концепция + спека · [`feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) |
| **Designer** | ✅ § W в коде (Lead 2026-05-25) — лендинг + пульт CSS |
| **Coder** | ✅ § W · 3d · **3e** — **принято владельцем 2026-05-25** |
| **MVP скелет WP** | ✅ `/lenta/` + `/cabinet/` + меню «Кабинет» |
| **Coder § 3g** | ✅ commit `54ba7d5` |
| **WP `/lenta/`** | ✅ грузится |
| **Волна 2** Product | ✅ канон в `LEAD_PRODUCT_PROMPT` + `wp-skeleton` |
| **Coder § P3a** | ✅ U1–U6 — приёмка владельца |
| **Coder § P1 сайты** | ✅ код 2026-05-26 |
| **§ W2 принято** | ⏳ повторный прогон `/lenta/` |
| **Coder § 3h** | ✅ чипы как главная |
| **Coder § 3i** | ✅ |
| **Coder § 3j** | ✅ |
| **WP `/cabinet` demo JSON** | ❌ снято (3e — живой API) |

### Сделано (Coder § P3a, 2026-05-25)

| § | Что |
|---|-----|
| u1 | Раскрытие карточки: `grid-template-rows` 0fr→1fr + opacity; `prefers-reduced-motion` — без transition |
| u2 | Сетка 2×: `align-items: start`, карточка `align-self: start` — сосед не тянется |
| u3 | Одна `.is-expanded`; клик другой карточки закрывает предыдущую |
| u4 | «Применить» снаружи `<details>`, видна только при `[open]` (CSS sibling) |
| u5 | Бейдж навыков только при `appliedTags.length > 0`, `title="Применено навыков: N"` |
| u6 | Раскрытие: «Задача» из `body` (snippet как бот), «Разбор» из `ai_reasons`; API отдаёт `body` |

**Файлы:** `page-lenta.php`, `rawlead-feed.js`, `rawlead-cabinet.js`, `rawlead.css`, `src/api_server.py`

**Как проверить:**
1. `python scripts/wp_install_rawlead_theme.py` + Ctrl+F5 `http://radarzakaz.local/lenta/`
2. `uvicorn src.api_server:app --port 18766` — перезапуск после правки API
3. Desktop 2 колонки: раскрыть карточку — плавно; сосед не растягивается; другая карточка закрывает первую
4. «Навыки» → «Применить» только при открытом блоке; бейдж с tooltip после «Применить»
5. В раскрытии — «Задача» (текст заказа), при наличии — «Разбор»

### Сделано (Coder § 3j, 2026-05-25)

| § | Что |
|---|-----|
| 3j1 | `/lenta/`: `#rl-feed-list` — grid 2×420px, центр, max ~880px; &lt;768px — 1 колонка; empty/end на всю ширину |
| 3j2 | `bindWheelScroll`: `scrollTop += deltaY`; `bindSkillsPanels` — desktop + mobile sheet после открытия |
| 3j3 | Пульт вкладка «Статус»: строки `/status-text` → `.status-line` key/value; `lamp-pulse` без изменений |

**Файлы:** `rawlead.css`, `rawlead-feed.js`, `desktop/src/main.ts`, `desktop/src/styles/pult.css`

**Как проверить:**
1. ~~`wp_install_rawlead_theme.py`~~ ✅ Lead 2026-05-25
2. `uvicorn src.api_server:app --port 18766` + Ctrl+F5 `http://radarzakaz.local/lenta/` — desktop 2 карточки в ряд
3. Раскрыть «Навыки», колесо над списком — скролл внутри панели (mobile sheet — то же)
4. Пульт: `npm run tauri dev` в `desktop/` — running → pulse лампы; вкладка «Статус» — строки с ключом слева

### Сделано (Coder § 3i, 2026-05-25)

| § | Что |
|---|-----|
| 3i1 | `.rl-feed-list` — колонка по центру; карточки/skeleton `max-width: 420px` как flow.php |
| 3i2 | `draftTags` / `appliedTags`; клик — только черновик; «Применить» → `PUT /v1/me/tags` → `sort=match` → перезагрузка ленты; badge = applied |
| 3i3 | Панель навыков: wheel-scroll + тонкий scrollbar при hover |

**Файлы:** `wordpress/rawlead-kadence-child/page-lenta.php`, `assets/js/rawlead-feed.js`, `assets/css/rawlead.css`

**Как проверить:**
1. ~~`wp_install_rawlead_theme.py`~~ ✅ Lead 2026-05-25
2. `uvicorn src.api_server:app --port 18766`
3. `http://radarzakaz.local/lenta/` — Ctrl+F5: карточки узкие по центру (~420px)
4. Выбрать 2–3 навыка без перезагрузки → «Применить» → лента «Совместимость», порядок меняется
5. Навести на список навыков, колесо — скролл внутри блока

### Сделано (Coder § 3h, 2026-05-25)

| § | Что |
|---|-----|
| 3h1 | `/lenta/` + `/cabinet/`: карточки `.rl-lead-card` как на главной (flow.php); `.rl-match` 10px; `.rl-chips` — вердикт + до 4 тегов + «+N» |
| 3h2 | CSS: чипы `flex: 0 0 auto`, без растягивания; лента/кабинет — полная ширина карточки с жирной рамкой |

**Файлы:** `wordpress/rawlead-kadence-child/assets/js/rawlead-feed.js`, `rawlead-cabinet.js`, `assets/css/rawlead.css`

**Как проверить:**
1. ~~`wp_install_rawlead_theme.py`~~ ✅ Lead 2026-05-25
2. `uvicorn src.api_server:app --port 18766`
3. `http://radarzakaz.local/lenta/` — Ctrl+F5: карточки как блок лида на главной; теги — маленькие pills в ряд, не на всю ширину
4. 2–3 навыка в sidebar → подпись «Совместимость», % и порядок меняются
5. `http://radarzakaz.local/cabinet/` — те же чипы на карточках

### Сделано (Coder § W2, 2026-05-25)

| § | Что |
|---|-----|
| W2.1 | Nav без «Главная»; hero: лента + `#pricing-preview`; CTA «Попробовать» → `/lenta/` |
| W2.2 | flow/manifest/features/audience — канон Product (все ниши, не IT-only) |
| W2.3 | `#pricing-preview`: ИИ-агент, 5 пунктов, «Узнать первым →» |
| W2.4 | Inner HTML how/faq/contact/pricing из `docs/archive/wp-skeleton/`; `wp_skeleton_setup.py` путь |
| W2.5 | inner hero leads в `marketing.php` |

**Файлы:** `wordpress/rawlead-kadence-child/template-parts/rawlead/` (header, hero, flow, manifest, features, audience, pricing-preview), `inc/marketing.php`, `assets/css/rawlead.css`, `wordpress/rawlead-landing/content/*.html`, `scripts/wp_skeleton_setup.py`

**Как проверить:**
1. `http://radarzakaz.local/` — nav: Лента…Кабинет, без «Главная»; hero «Смотреть ленту» + «Смотреть тарифы ↓» → скролл к тарифу
2. Манифест, 01–03, «Для кого» — новые тексты; тариф «ИИ-агент», «Узнать первым →»
3. `/how/`, `/faq/`, `/contact/` — навыки, облако, нетехнические ниши (если старый контент — деактивировать/активировать плагин RawLead Landing или `python scripts/wp_skeleton_setup.py`)
4. `scripts/wp_install_rawlead_theme.py` или refresh темы — child на месте

### Сделано (Coder § 3g, 2026-05-25)

| § | Что |
|---|-----|
| 3g1 | `record_new_lead` → `is_visible=false`; `update_on_notify` → `lead_tags` из ИИ; feed/me только `notified_at` |
| 3g2 | `GET /v1/skills/catalog`, `/v1/feed?skills&sort`, `/v1/me/feed?skills&sort`; `min_score` по sort |
| 3g3 | `/lenta/`: чипы навыков → `PUT /v1/me/tags`, сортировка Новые/Совместимость, подпись полоски |
| 3g4 | `lead_tags` в `AI.md` + `ai_analyze.py` |

**Файлы:** `src/pg_storage.py`, `src/ai_analyze.py`, `src/api_server.py`, `src/rank.py`, `wordpress/rawlead-kadence-child/`, `docs/team/architect/TZ_API.md`, `docs/team/architect/AI.md`, `docs/ops/RUN.md`

**Как проверить:**
1. Радар + бот → 1–2 карточки в TG
2. `uvicorn src.api_server:app --port 18766`
3. Neon (разово): `UPDATE leads SET is_visible=false WHERE notified_at IS NULL;`
4. `http://radarzakaz.local/lenta/` — только bot-лиды; навыки из каталога; sort; теги = кабинет
5. `GET /v1/skills/catalog`, `GET /v1/feed?sort=match&skills=python`

### Сделано (Coder § 3e, 2026-05-25)

| § | Что |
|---|-----|
| 3e1 | `GET/PUT /v1/me/tags`, `GET /v1/me/feed` (rank NEON §3), `GET /v1/me/subscription` stub, auth `X-RawLead-User-Id` |
| 3e2 | `page-cabinet.php` + `rawlead-cabinet.js` + REST `me/feed`, `me/tags`; совместимость = `final_rank`; кнопки AI disabled |
| 3e3 | Проверка: `PUT /v1/me/tags` + лиды с `lead_tags` в Neon |

**Файлы:** `src/api_server.py`, `src/rank.py`, `wordpress/rawlead-kadence-child/` (inc/rawlead-api.php, page-cabinet.php, assets/js/rawlead-cabinet.js, css), `docs/team/architect/TZ_API.md`, `docs/ops/RUN.md`

**Как проверить:**
1. `uvicorn src.api_server:app --port 18766`
2. `PUT /v1/me/tags` с заголовком owner UUID (см. `RUN.md` §5)
3. `http://radarzakaz.local/cabinet/` — теги редактируются, лента с «Совместимость» %
4. `http://radarzakaz.local/lenta/` — без изменений (открытая лента по `ai_score`)

### Сделано (Coder § W + 3d, 2026-05-25)

| § | Что |
|---|-----|
| W1–W6 | FL/TG цвета, motion, scroll IO для кубиков, match-bar, один тариф, header «Лента» + CTA, lamp-pulse в пульте |
| 3d1 | `page-lenta.php` — `/lenta/` (не `/feed` — RSS) · REST → `GET /v1/feed` |
| 3d2 | Карточки закрытая/раскрытая, infinite scroll, фильтры источник + min_score |
| 3d3 | `page-cabinet.php` — каркас (далее § 3e) |
| 3d4 | `inc/rawlead-api.php` (`RAWLEAD_API_URL`) · `RUN.md` §5 WP |

**Файлы:** `wordpress/rawlead-kadence-child/` (css, js, page-feed, page-cabinet, inc/rawlead-api.php, header, scroll, pricing, flow), `desktop/src/styles/pult.css`, `docs/ops/RUN.md`

**Как проверить:**
1. `uvicorn` :18766 + `http://radarzakaz.local/lenta/` и `/cabinet/`
2. Главная: FL зелёный, TG синий, «Лента» в меню, CTA «Попробовать →», анимации scroll
3. `/feed`: карточки из API; фильтры; раскрытие карточки
4. Пульт ▶: зелёная лампа пульсирует

### Сделано (Coder 3c, 2026-05-25)

| § | Что |
|---|-----|
| 3c1 | `GET /health` → `{"status":"ok","version":"0.3c"}` |
| 3c2 | `GET /v1/feed?limit&offset&min_score` — только `is_visible=true`, sort `ai_score` DESC |
| 3c3 | `GET /v1/leads/{id}` — одна карточка |
| 3c4 | `POST /v1/internal/leads` — ingest с `X-API-Key`; ON CONFLICT DO NOTHING |
| 3c5 | `TZ_API.md` v0.2 синхронизирован; `RUN.md` §5 — как запустить |

**Файлы:** `src/api_server.py`, `requirements.txt` (+fastapi, uvicorn), `docs/team/architect/TZ_API.md`, `docs/ops/RUN.md`

**Как проверить:**
1. `uvicorn src.api_server:app --port 18766`
2. `GET /health` → 200 `{"status":"ok","version":"0.3c"}`
3. `GET /v1/feed?limit=5` → JSON `items[]`, только `is_visible=true`
4. `POST /v1/internal/leads` с заголовком `X-API-Key` → `{"id":N,"inserted":true}`; повтор → `{"inserted":false,"reason":"duplicate"}`

---

### Сделано (Coder 3b, 2026-05-25)

| § | Что |
|---|-----|
| 3b1 | `users`, `user_tags`, `subscriptions` + эволюция `leads` |
| 3b2 | `is_visible` (bool); **`contour` нет** |
| 3b3 | `user_id` в user-scoped таблицах; seed owner UUID `#1` |
| 3b4 | `content_hash` UNIQUE + ON CONFLICT ingest |
| 3b5 | `sql/001_neon_schema.sql` ↔ `NEON_SCHEMA.md` |
| 3b6 | `pg_storage`: `is_visible`, `ai_score`, `lead_tags` (заглушки до 3f) |

**Файлы:** `sql/001_neon_schema.sql`, `docs/team/architect/NEON_SCHEMA.md`, `src/pg_storage.py`, `src/lead_pipeline.py`

**Как проверить:** Neon Console → SQL из `sql/001_neon_schema.sql`; ingest лида → колонки `is_visible`, `ai_score`, `lead_tags`; нет `contour`

**Проверено Coder 2026-05-25:** миграция применена к Neon (`parser`); таблицы `users`/`user_tags`/`subscriptions`/`leads`; owner UUID `#1`; ingest `coder_verify` → `is_visible=true`, `ai_score=85`, `lead_tags=[]`

### Сделано (Coder § P, 2026-05-25)

| § | Что |
|---|-----|
| P1 | ▶ без логов; стрелка открывает/сворачивает панель |
| P2 | Лампа TG: warn до ready+пульс; сброс ready при `/start`; fallback «статус…» |
| P3 | Вкладка Статус: роль acc, ready, /start бота, msgs=0 подсказки, phase/join |
| ✕ | `/stop` + destroy; бот «до связи» при стопе радара |

**Файлы:** `desktop/src/main.ts`, `scripts/radar_control.py`, `src/radar_status.py`, `src/tg_monitor.py`, `src/tg_join_runner.py`, `desktop/src-tauri/capabilities/default.json`

**Как проверить:** см. [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md) § «Как проверить § P»

### Сдано недавно (кратко)

Пульт ✕/логи · TG бюджет+ссылка · dedup Neon hash · лампа TG warn/ok · HTML-ссылки · `/start` acc · WP Kadence лендинг ✅

Детали сессий — [`archive/TASKS_HISTORY.md`](archive/TASKS_HISTORY.md), не дублировать сюда простынями.

---

## Блокеры

| Блокер | Кто |
|--------|-----|
| **FEED-DECOUPLE + SITE-AI-FALLBACK** | ✅ код · owner-проверка: `/v1/feed` при `notified_at IS NULL` и отсутствие TG-спама при `ai_unavailable` |
| **Neon dup без L1 → лента пустая** | ✅ код · владелец: replay + Site ▶ 30 мин |
| **Site-бот `chat not found`** | владелец · `.env.site` `TELEGRAM_CHAT_ID` |
| **`/cabinet/` сетка / login** | ✅ принято 2026-05-27 · [`2026-05-27-cabinet-telegram-widget-login-fails.md`](../problems/2026-05-27-cabinet-telegram-widget-login-fails.md) |
| Пульт «Нет связи с API» | Mechanic · [`2026-05-24-pult-no-api-connection.md`](../problems/2026-05-24-pult-no-api-connection.md) |
| 2× `main.py` | Mechanic · [`2026-05-24-duplicate-python-processes.md`](../problems/2026-05-24-duplicate-python-processes.md) |
| TG relay+card (если снова сломается) | prompt-test · [`2026-05-24-tg-forward-not-via-bot.md`](../problems/2026-05-24-tg-forward-not-via-bot.md) |

---

## MVP acceptance (ставка B)

Сверка с [`LEAD_PRODUCT_PROMPT.md`](../product/LEAD_PRODUCT_PROMPT.md) § «Готово когда» #1–#7 — обновлять после каждой фазы 3b–3f.

---

_Lead Architect · 2026-05-24_
