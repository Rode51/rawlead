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
| **Ворота прод** | ⏳ P1 ✅ → D1 → P4 → [`PRE_PROD_GATE.md`](../architect/PRE_PROD_GATE.md) |
| **Coder § P1** | ✅ P1.3c парсеры (smoke 12+10+25) · приёмка лога после рестарта · TG ⏳ P1.2b |
| **§ P5 деплой** | ⏸ после ворот + «едем на прод» |
| **Ingest «всё для всех»** | ❌ отменено |
| **Dogfood** | ✅ бот без ослабления фильтров |
| **Хостинг** | ⏳ после V10 |

**Coder:** [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md) § **P1** (след. **D1** — Design)

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
