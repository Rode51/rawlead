# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.10** (4 категории Digital · §0i) · [`ROADMAP.md`](../architect/ROADMAP.md)

---

## Сейчас (2026-05-26) — Vision v0.10

**PM ✅** · канон §0i · план Product § «Vision v0.10».

| Трек | Статус |
|------|--------|
| **Vision v0.10** | ✅ Product + владелец |
| **Coder § V10** | ✅ **принято владельцем 2026-05-26** |
| **Coder § P3a / W2** | ✅ **принято владельцем 2026-05-26** |
| **§ V10.5** | ✅ **принято владельцем 2026-05-26** |
| **§ P7 category** | ✅ **принято владельцем 2026-05-26** |
| **Ворота прод** | ✅ P1 · D1 · P4 код → **P5** деплой после «едем на прод» |
| **Design D1** | ✅ спека + UI |
| **Coder § P1.3d / D1 / P4** | ✅ **принято владельцем 2026-05-26** |
| **Coder § P1** | ✅ P1.3c · ✅ **P1.4** · ✅ **P1.H** · TG ⏳ P1.2b |
| **§ P5 деплой** | ⏸ после ворот + «едем на прод» |
| **Ingest «всё для всех»** | ❌ отменено |
| **Dogfood** | ✅ бот без ослабления фильтров |
| **Хостинг** | ⏳ после V10 |

**Coder:** § **P5** деплой ([`PRE_PROD_GATE.md`](../architect/PRE_PROD_GATE.md)) — только по фразе «едем на прод»  
**Lead:** проверка 2026-05-26 — см. ниже · коммит в git

### Решение владельца (лентa, 2026-05-26)

- Публичка: **только фриланс-биржи** — `fl`, `kwork`, `freelancehunt`
- **Отложить** (код парсеров не удалять): `vc_ru`, `habr_career` (вакансии / job-ленты)
- `.env`: `PUBLIC_FEED_SOURCES=fl,kwork,freelancehunt`

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
| **`.env` строка 70** | ⚠️ ещё **5** источников (`vc_ru`, `habr_career`) — **поменять** на 3 и **перезапуск радара** |
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
| P1.2 | TG listen: только allowlist + tier **TG-A** (`INGEST_SOURCES_SNG_25.json` + `TG_JOIN_QUEUE.csv`); MVP-чаты отфильтрованы |
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
| Allowlist TG | ⏳ `docs/ops/TG_PUBLIC_FEED_ALLOWLIST.txt` |
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
| Пульт «Нет связи с API» | Mechanic · [`2026-05-24-pult-no-api-connection.md`](../problems/2026-05-24-pult-no-api-connection.md) |
| 2× `main.py` | Mechanic · [`2026-05-24-duplicate-python-processes.md`](../problems/2026-05-24-duplicate-python-processes.md) |
| TG relay+card (если снова сломается) | prompt-test · [`2026-05-24-tg-forward-not-via-bot.md`](../problems/2026-05-24-tg-forward-not-via-bot.md) |

---

## MVP acceptance (ставка B)

Сверка с [`LEAD_PRODUCT_PROMPT.md`](../product/LEAD_PRODUCT_PROMPT.md) § «Готово когда» #1–#7 — обновлять после каждой фазы 3b–3f.

---

_Lead Architect · 2026-05-24_
