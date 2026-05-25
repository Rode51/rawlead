# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.9** (ставка B) · roadmap: [`ROADMAP.md`](../architect/ROADMAP.md) · владелец: [`../FOR_YOU.md`](../FOR_YOU.md)

---

## Сейчас (2026-05-25)

| Трек | Статус |
|------|--------|
| **Product v0.9** | ✅ принято Lead Architect |
| **Docs / ROADMAP** | ✅ синхронизированы под ставку B |
| **TG dogfood** | ✅ /start acc авто при подключении · acc шлют в бот (владелец 2026-05-25) · дубли python — Mechanic |
| **Lead Design** | ✅ концепция + спека · [`feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) |
| **Designer** | ✅ § W в коде (Lead 2026-05-25) — лендинг + пульт CSS |
| **Coder** | ✅ § W · 3d · **3e** — **принято владельцем 2026-05-25** |
| **MVP скелет WP** | ✅ `/lenta/` + `/cabinet/` + меню «Кабинет» |
| **Coder § 3g** | ✅ Lead 2026-05-25 · лента = бот-only + навыки + sort · **→ приёмка владельца** |
| **WP `/cabinet` demo JSON** | ❌ снято (3e — живой API) |

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
