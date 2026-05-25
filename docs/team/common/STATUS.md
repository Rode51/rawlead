# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.9.3** (все фрилансеры, не только IT) · [`ROADMAP.md`](../architect/ROADMAP.md)

---

## Сейчас (2026-05-25)

| Трек | Статус |
|------|--------|
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
| **Coder § W2** | ✅ в репо · **приёмка владельцем** ⏳ (~5 мин) |
| **Coder § 3h** | ✅ чипы как главная |
| **Coder § 3i** | ✅ |
| **Coder § 3j** | ✅ |
| **WP `/cabinet` demo JSON** | ❌ снято (3e — живой API) |

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
