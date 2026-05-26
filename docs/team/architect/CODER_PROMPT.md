# Coder — **§ P1 → D1 → P4 → P5** · V10/P7 ✅

**Ворота прод:** [`PRE_PROD_GATE.md`](PRE_PROD_GATE.md) — портфолио = продукт для людей, не только лендинг.

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.10** §0i.

**Порядок (жёстко):** **P1** → **D1** (после Design) → **P4** → **P5** только после «едем на прод».  
**⏸ P5** пока ворота не закрыты. **⏸** 25 источников / §3f без ТЗ.

---

# § P1 — Чистая публичная лента (**→ старт**)

---

# § V10.5 — Hotfix (архив): `GET /v1/feed` с `skills=` (500)

Тикет: [`docs/problems/2026-05-26-feed-skills-jsonb-500.md`](../../problems/2026-05-26-feed-skills-jsonb-500.md)

| # | Готово когда |
|---|----------------|
| h1 | «Применить» в `/lenta/` — 200, лента с `sort=match` |
| h2 | Нет `jsonb && jsonb` в логе |

---

# § V10 — Vision v0.10 (✅ принято 2026-05-26, архив)

Канон Product: [`LEAD_PRODUCT_PROMPT.md`](../product/LEAD_PRODUCT_PROMPT.md) § «Vision v0.10».

| § | Что | Файлы |
|---|-----|--------|
| **V10.1** | Стоп/белые списки §0i в коде | `src/filters.py`, [`FILTERS.md`](../../ops/FILTERS.md) § v0.10 |
| **V10.2** | Пороги `ai_score` 50–55 для design/marketing/text | [`PROFILE.md`](../../ops/PROFILE.md), ingest/API |
| **V10.3** | Skills catalog в `/lenta/` — **4 группы** (заголовки категорий) | `api_server` `/v1/skills/catalog` + `rawlead-feed.js` |
| **V10.4** | Лендинг «Для кого» — **4 карточки** (канон строк ниже) | `audience.php`, `docs/archive/wp-skeleton/home.md` |

### V10.1 — FILTERS

| # | Готово когда |
|---|----------------|
| f1 | Дроп-токены §0i по категориям в `filters.py` (или общий стоп + category на ingest) |
| f2 | Расширен «Берём» — design/marketing/text токены из FILTERS.md v0.10 |
| f3 | VA, диктор, озвучка — всегда стоп |

### V10.2 — PROFILE / ai_score

| # | Готово когда |
|---|----------------|
| p1 | При `category in (design, marketing, text)` — сниженный порог для «Брать» в ленте (50–55) или отдельные подписи чипа |
| p2 | Dogfood-бот — **без** ослабления owner PROFILE |

### V10.3 — Skills catalog

| # | Готово когда |
|---|----------------|
| s1 | API: `skills` с полем `category` (`dev`/`design`/`marketing`/`text`) или 4 массива в ответе |
| s2 | UI: в панели «Навыки» — 4 секции с заголовками как в vision §0i |
| s3 | Маппинг тег→категория: статический JSON в теме или эвристика по префиксу (Coder — минимальный v1) |

### V10.4 — Копирайт «Для кого» (4 карточки)

| # | Заголовок | Подтекст | Теги |
|---|-----------|----------|------|
| 1 | **Разработка & Код** | Боты, парсеры, FastAPI, веб — один поток вместо десятка вкладок. | Python · бот · парсер · автоматизация |
| 2 | **Дизайн & Видео** | UI/UX, Reels, монтаж, motion — заказы точно по вашим навыкам, без шума. | Figma · UI · монтаж · анимация |
| 3 | **Маркетинг & SMM** | Таргет, SEO, SMM, воронки — ИИ убирает нерелевантное до того, как вы открыли ленту. | таргет · SEO · SMM · контекст |
| 4 | **Тексты & Переводы** | Копирайтинг, локализация, редактура — только заказы под ваш профиль. | копирайт · перевод · редактура · субтитры |

CSS: сетка 4 карточки desktop (2×2), mobile 1 col — согласовать с `REFERENCE.md` §3.6.

### V10.5 — STATUS

Обновить [`STATUS.md`](../common/STATUS.md) — § V10.

---

## Вводные (ждёт владельца)

| Файл | Кто |
|------|-----|
| [`docs/ops/PUBLIC_FEED_WEB_SOURCES.txt`](../../ops/PUBLIC_FEED_WEB_SOURCES.txt) | **канон сайтов** — 4×P1 + fl,kwork |
| `docs/ops/TG_PUBLIC_FEED_ALLOWLIST.txt` | **Tier A PDF** — заполнен Lead 2026-05-26 |
| `docs/ops/TG_MIGRATION_2026-05-26.md` | снос старых + droplist · join после «отписался» |
| Старые чаты **не** в ленте | см. [`INGEST_SOURCES_PLAN.md`](INGEST_SOURCES_PLAN.md) |

Пока allowlist пуст — **в API** whitelist минимум `fl`, `kwork` только.

**Порядок до прода:** **P1** → **D1** → **P4** → **P5** ([`PRE_PROD_GATE.md`](PRE_PROD_GATE.md)). P1.3 сайты — опционально внутри P1.

## P1.1 — Фильтр `GET /v1/feed`

| # | Готово когда |
|---|----------------|
| f1 | Env `PUBLIC_FEED_SOURCES` = строка из [`PUBLIC_FEED_WEB_SOURCES.txt`](../../ops/PUBLIC_FEED_WEB_SOURCES.txt) (+ TG из allowlist позже) |
| f2 | То же для `/v1/skills/catalog` (теги только из видимых источников) |
| f3 | Док: как добавить `telegram_*` source после join allowlist |

**Файлы:** `src/api_server.py`, `.env.example`

## P1.2 — Радар не кормит мусор

| # | Готово когда |
|---|----------------|
| r1 | Слушать TG только чаты из allowlist + `TG_JOIN_QUEUE` tier A (не старые MVP-чаты) |
| r2 | Ingest с `source` вне whitelist → `is_visible=false` **или** не писать в Neon для публички (dogfood бот может остаться отдельным контуром — согласовать с Lead: owner-only notify) |

## P1.2b — TG migration (⏳ доработка)

**Отписка:** ❌ не делаем — владелец: пусть подписаны, **не слушаем** (`filter_listen_chat_ids`).

Тикет: [`docs/problems/2026-05-26-p1-tg-migration-gaps.md`](../../problems/2026-05-26-p1-tg-migration-gaps.md)

| # | Готово когда |
|---|----------------|
| m1 | Listen: **только** [`TG_PUBLIC_FEED_ALLOWLIST.txt`](../../ops/TG_PUBLIC_FEED_ALLOWLIST.txt) — убрать старый TG-A из listen |
| m2 | `TG_JOIN_QUEUE_v2.csv` — Tier A PDF; join 2–3/нед |
| m3 | Опционально: явный deny droplist chat_id (если пересечение с allowlist) |

## P1.3 — Парсеры сайтов P1 (**все 4**, владелец: «сначала сайты из списка»)

Канон URL и `source_id`: [`PUBLIC_FEED_WEB_SOURCES.txt`](../../ops/PUBLIC_FEED_WEB_SOURCES.txt)

| source | Как |
|--------|-----|
| `vc_ru` | VC.ru `/jobs` API JSON |
| `freelancehunt` | HTML projects |
| `habr_freelance` | freelance.habr.com/tasks |
| `habr_career` | career.habr.com/vacancies |

Очередь: VC.ru → Freelancehunt → Habr Career · тот же pipeline + AI.

## P1.3c — Довести парсеры до лида в Neon (**→ сейчас**, владелец)

| source | Проблема | Готово когда |
|--------|----------|----------------|
| `habr_career` | ✅ в логе `habr_career:id=…` после `PUBLIC_FEED_SOURCES` | оставить |
| `vc_ru` | 403 / пустая выдача | ≥1 лид/цикл в Neon или явный fallback URL в логе |
| `freelancehunt` | HTTP 403 антибот | Playwright или прокси домашний IP; ≥1 лид/цикл |
| `habr_freelance` | HTTP **410** сайт закрыт | **убрать** из `PUBLIC_FEED_WEB_SOURCES.txt` + не вызывать в `main.py` до нового URL |

**Владелец `.env` (строка одна):**  
`PUBLIC_FEED_SOURCES=fl,kwork,vc_ru,freelancehunt,habr_career`  
(без `habr_freelance` пока 410)

**Лог:** после цикла в `radar.log` в `ош=` должны быть префиксы `vc_ru:`, `freelancehunt:`, `habr_career:` — не только fl/kwork.

---

# § P1.4 — Читаемые логи + пульт (**→ после P1.3c**, владелец)

**Зачем:** понять **появляются ли вакансии** и **где режет фильтр/ИИ**, без разбора `ош=habr_career:id=… skip:dup_content`.

Канон для владельца: [`docs/ops/RADAR_LOG.md`](../../ops/RADAR_LOG.md)

## P1.4.1 — `data/radar.log` (человекочитаемо)

| # | Готово когда |
|---|----------------|
| l1 | После **каждого источника** в `run_cycle` — одна строка: `FL.ru │ скачано N │ новых │ в бот │ filter │ МИМО │ dup │ budget` (русские подписи) |
| l2 | Источники: `fl`, `kwork`, `vc_ru`, `freelancehunt`, `habr_career` — **всегда** строка (даже 0 скачано или `fetch:ошибка`) |
| l3 | Начало цикла: `── Цикл {ts} ──` · конец: `Итого в бот: X │ на сайт: X` (`notified_at`) |
| l4 | Счётчики: класс `SourceCycleStats` в `lead_pipeline` / `main` — не раздувать `errors[]` только для статистики |
| l5 | Старый формат `карточки_fl=…` — убрать или одна строка «legacy» внизу (предпочтительно **заменить**) |

**Файлы:** `src/main.py`, `src/lead_pipeline.py` (опц. `src/radar_cycle_log.py`)

## P1.4.2 — Пульт (desktop + radar_control)

| # | Готово когда |
|---|----------------|
| p1 | `scripts/radar_control.py`: `_TAIL_LINES` **800** (или 1000) для `/logs/radar.log` |
| p2 | Вкладка **Статус**: блок **«Последний цикл»** — те же 5 источников + итого (из SQLite `storage` settings, пишет `record_fl_kwork_cycle` / новый `record_cycle_summary`) |
| p3 | API `/status` JSON (если пульт на JSON): поле `last_cycle` для ламп/баннера — опционально |
| p4 | `docs/ops/RUN.md` — как читать лог |

**Файлы:** `scripts/radar_control.py`, `src/radar_status.py`, `desktop/src/main.ts` (рендер Статус), `desktop/index.html` при необходимости

## Не в P1.4

- Менять FILTERS/PROFILE (отдельно, после смотрения воронки)
- Показывать на `/lenta/` всё без `notified_at` (отдельное ТЗ, согласовать с Lead)

---

# § P2 — Опрос 2 мин + ротация прокси (FL/Kwork)

| # | Готово когда |
|---|----------------|
| t1 | `POLL_INTERVAL_MINUTES=2` работает; в `config.py` минимум **2** (не 10) |
| t2 | `FL_PROXY_URLS` / `KWORK_PROXY_URLS` — список через запятую; round-robin на каждый цикл или при 429/timeout — следующий |
| t3 | Лог: какой proxy использован; не логировать пароль |
| t4 | `.env.example` + строка в `docs/ops/RUN.md` |

**Не трогать** без задачи: лимиты Telethon join.

---

# § P3a — Приёмка W2 (владелец 2026-05-25) — **до хостинга**

Тикет: [`docs/problems/2026-05-25-portfolio-w2-acceptance.md`](../../problems/2026-05-25-portfolio-w2-acceptance.md)

| # | Готово когда |
|---|----------------|
| u1 | Раскрытие карточки: transition height/max-height + opacity; `prefers-reduced-motion: reduce` → без анимации |
| u2 | Accordion: **одна** `.is-expanded`; в grid 2× сосед **не** меняет высоту/контент |
| u3 | Клик другой карточки → предыдущая закрывается (проверить с u2) |
| u4 | «Применить» — **снаружи** `<details>`, под summary «Навыки», `hidden` пока details closed |
| u5 | Бейдж на «Навыки»: **владелец OK** — `title="Применено навыков: N"`; только если `appliedTags.length > 0` |
| u6 | Раскрытие: заголовок **«Задача»** + текст из `body` (логика как `telegram_notify._task_block`); `ai_reasons` — отдельным блоком «Разбор» если есть |

**Файлы:** `page-lenta.php`, `rawlead-feed.js`, `rawlead.css`, `rawlead-cabinet.js` (те же u6)

---

# § P3 — UI/UX прочее (после P3a)

| # | Готово когда |
|---|----------------|
| u7 | Empty state ленты: «Пока нет заказов» |
| u8 | Прогон 375px |

---

# § P7 — Категория из биржи (0 ₽)

Канон: [`INGEST_CATEGORY_STRATEGY.md`](INGEST_CATEGORY_STRATEGY.md)

| # | Готово когда |
|---|----------------|
| c1 | `leads.category` в Neon + ingest |
| c2 | FL/Kwork маппинг рубрики → category |
| c3 | `GET /v1/feed?category=` |

**API готово:** `GET /v1/feed?category=` ✅ · UI чипов — **§ D1**.

---

# § D1 — Чипы категорий в `/lenta/` (**после Design**)

**Design:** Lead Design → `feed-cabinet-mvp.md` §2.2 дополнение · 4 чипа: Код / Дизайн / Маркетинг / Тексты (+ «Все»).

| # | Готово когда |
|---|----------------|
| d1 | Sidebar + mobile sheet: `fieldset` «Категория» — radio/chips `dev|design|marketing|text` + пусто = все |
| d2 | JS: `GET /v1/feed?category=…` при смене; сброс offset |
| d3 | Подписи = `CATEGORY_TITLES` из vision (короткие на mobile) |
| d4 | «Сбросить фильтры» учитывает category |

**Не в D1:** регистрация (P4).

---

# § P8 — Дешёвая LLM (summary only)

| # | Готово когда |
|---|----------------|
| m1 | `OPENROUTER_MODEL_SUMMARY` в config |
| m2 | Промпт только title+snippet body |
| m3 | Вердикт: правила или короткий JSON; не GPT-4o на каждый лид |


---

# § P4 — Кабинет: регистрация через Telegram

| # | Готово когда |
|---|----------------|
| a1 | `POST /v1/auth/telegram` — body от Login Widget, проверка `hash` ([Telegram docs](https://core.telegram.org/widgets/login#checking-authorization)) |
| a2 | Upsert `users` (tg_id, username, …), JWT `access_token` TTL 7d |
| a3 | `/v1/me/*` — Bearer JWT; убрать 403 для не-owner UUID |
| a4 | WP: кнопка «Войти через Telegram» на `/cabinet/` или отдельная страница; после входа — `localStorage` token → заголовки fetch |
| a5 | `TELEGRAM_LOGIN_BOT_TOKEN` или тот же бот — в `.env.example` |

**Схема:** [`TZ_API.md`](TZ_API.md) · Neon `users` — [`NEON_SCHEMA.md`](NEON_SCHEMA.md)

---

# § P5 — Деплой бюджет 24/7 (WP shared + VPS API+радар)

**Канон:** [`docs/ops/DEPLOY_BUDGET.md`](../../ops/DEPLOY_BUDGET.md) · владелец: **без ПК**, минимум денег.

| # | Готово когда |
|---|----------------|
| d1 | `deploy/systemd/` — `rawlead-api.service`, `rawlead-radar.service` |
| d2 | `deploy/Caddyfile` (или nginx) — `api.домен` → :18766, TLS |
| d3 | `docs/ops/DEPLOY_VPS.md` — clone, venv, `.env`, enable systemd, перенос `data/*telethon*` |
| d4 | WP на shared: theme install + `rawlead_api_base_url` |
| d5 | CORS: origin = URL WP |
| d6 | **E1:** API на VPS, радар пока на ПК — лента живая |
| d7 | **E2:** радар на VPS, инструкция «остановить радар на ПК» — нет дублей TG |
| d8 | Приёмка: ПК выключен → `/lenta/` + бот через 30 мин |

**Не делать:** второй VPS, Docker Swarm, туннель с ПК как прод.

---

# § P6 — Публичный GitHub без следов ИИ

| # | Готово когда |
|---|----------------|
| g1 | Ветка `portfolio-public` **или** инструкция export в `rawlead-portfolio` |
| g2 | Исключить: `.cursor/`, `docs/team/`, `docs/problems/`, `*CODER*`, `*LEAD*`, agent transcripts |
| g3 | README: кейс человека (проблема → решение → стек → скрины), без Cursor/vibe/AI |
| g4 | `scripts/export_portfolio_repo.sh` или `.ps1` — копирует whitelist путей |
| g5 | Перед push: `rg -i "cursor|vibe.?cod|openrouter|lead architect" README` — 0 в публичном дереве |

**Важно:** основной `uisness` может оставаться приватным; публичный — отдельный репо.

---

# § 3j — Лента 2 колонки + wheel навыков + пульт (архив)

## § 3j1 — Две карточки в ряд (`/lenta/`)

| # | Готово когда |
|---|----------------|
| g1 | `.rl-feed-list` — **`display: grid`**, `grid-template-columns: repeat(2, minmax(0, 420px))`, `justify-content: center`, `gap: 1rem`, `max-width: ~880px`, `margin: 0 auto` |
| g2 | Карточка: `max-width: 420px`, `width: 100%` в ячейке |
| g3 | **&lt; 768px** (или &lt; 900px) — **1 колонка** по центру (как сейчас) |
| g4 | Skeleton / empty — в той же сетке |

**Не** `/cabinet/` — там одна колонка можно оставить.

---

## § 3j2 — Wheel в **раскрытом** блоке «Навыки»

Сейчас `bindWheelScroll` только `preventDefault` — **скролла нет**. Исправить:

```js
el.addEventListener("wheel", function (e) {
  if (el.scrollHeight <= el.clientHeight) return;
  e.preventDefault();
  el.scrollTop += e.deltaY;
}, { passive: false });
```

| # | Готово когда |
|---|----------------|
| w1 | `#rl-feed-skills-panel` (`.rl-feed-skills-dd__panel`) — wheel при наведении крутит **внутри панели** |
| w2 | То же в **mobile sheet** (клон sidebar в `#rl-feed-sheet-body`) — после открытия sheet перебиндить panel |
| w3 | `overflow-y: auto`, `max-height` достаточный (12–14rem), scrollbar при hover |

---

## § 3j3 — Пульт (Design §6, `feed-cabinet-mvp.md`)

**Проверка:** `desktop/src/styles/pult.css` — **`lamp-pulse`** на `.lamp__dot--ok` уже есть → не ломать.

| # | Готово когда |
|---|----------------|
| p1 | **§ 6.2 Статус:** вкладка «Статус» — не сырой `textContent` в одну кучу. Вариант A: строки из `/status-text` → `<div class="status-line">` на каждую строку (сохранить эмодзи/текст). Вариант B: краткий блок из `/status` JSON (лампы + running) + ниже monospace хвост из status-text |
| p2 | CSS `.status-line` / `.log-view--status`: ключ слева, значение справа где уместно; `font-size: 11–12px`, читаемо |
| p3 | `prefers-reduced-motion` — pulse лампы off (уже есть) |

Спека: [`feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) §6.1–6.2 · [`DESIGN_BRIEF.md`](../design/DESIGN_BRIEF.md) §7.

**Файлы пульт:** `desktop/src/main.ts`, `desktop/src/styles/pult.css`

---

## § 3j4 — Деплой

```powershell
python scripts/wp_install_rawlead_theme.py
```

Пульт: пересобрать/перезапустить Tauri (`npm run tauri dev` или ярлык) — Lead не собирает exe.

---

## § 3j5 — Приёмка

1. `/lenta/` desktop — **2 карточки в ряд**, узкие.
2. Раскрыть «Навыки», навести, колесо — список крутится.
3. Пульт running — лампа пульсирует; вкладка Статус — структурированно, не простыня без разбивки.

`STATUS.md` — § 3j.

---

## Файлы

| Путь |
|------|
| `wordpress/.../rawlead-feed.js`, `rawlead.css`, `page-lenta.php` |
| `desktop/src/main.ts`, `desktop/src/styles/pult.css` |

---

# § 3i — Лента: компактные карточки + навыки «Применить» (закрыто)

## Проблема (приёмка 3h)

- Карточки **на всю ширину** колонки — «бесконечная полоса». Нужны **небольшие блоки** как на главной (скрин flow).
- Навыки: **не** применять фильтр по каждому клику; **выбрать несколько → «Применить»** → тогда лента по совместимости.
- Блок навыков: при **наведении** — прокрутка **колёсиком мыши** (вертикальный wheel → scroll внутри списка навыков).

---

## § 3i1 — Компактные карточки

| # | Готово когда |
|---|----------------|
| c1 | `.rl-feed-list` — колонка карточек **по центру** (`align-items: center` или grid 1 col) |
| c2 | `.rl-feed-list .rl-lead-card` — **`max-width: 420px`**, `width: 100%`, жирная рамка 2px как на главной; **не** `width: 100%` на весь feed-main без лимита |
| c3 | На широком экране опционально **2 колонки** карточек max 420px — только если не ломает читаемость; иначе одна колонка по центру |
| c4 | Skeleton/end state — той же ширины |

**CSS ориентир:** скопировать ограничения из `.rl-lead-card` в flow (~792: `max-width: 420px`), убрать override `max-width: none; width: 100%` на ленте если мешает.

---

## § 3i2 — Навыки: черновик + «Применить»

| # | Готово когда |
|---|----------------|
| s1 | Состояние **`draftTags`** (клики по чипам) ≠ **`appliedTags`** (уходит в API / `GET /feed?skills=`) |
| s2 | Клик по навыку — только toggle **draft** (подсветка `is-active`), **без** `PUT` и **без** перезагрузки ленты |
| s3 | Кнопка **`Применить`** под списком навыков (desktop sidebar + mobile sheet): `PUT /v1/me/tags` с `draftTags` → `appliedTags` → `sort=match` → `resetAndLoad()` |
| s4 | Подсказка, пока draft ≠ applied: *«Выберите навыки и нажмите Применить»* |
| s5 | Badge на «Навыки» — число **applied** (не draft) |
| s6 | «Сбросить фильтры» сбрасывает и draft, и applied (tags `[]`, sort time) |

**Не ломать:** источник, min_score, infinite scroll.

---

## § 3i3 — Скролл навыков колёсиком

| # | Готово когда |
|---|----------------|
| w1 | Контейнер `.rl-feed-skills` или `.rl-feed-skills-dd__panel`: `max-height`, `overflow-y: auto` |
| w2 | На **`mouseenter`** + `wheel` на панели навыков: `preventDefault` и прокрутка `scrollTop` (чтобы колесо крутило список, а не всю страницу) |
| w3 | Визуально тонкий scrollbar при hover (как sidebar) |

---

## § 3i4 — Файлы

| Путь |
|------|
| `page-lenta.php` — кнопка «Применить» в блоке навыков |
| `assets/js/rawlead-feed.js` |
| `assets/css/rawlead.css` |

## § 3i5 — Деплой + приёмка

```powershell
python scripts/wp_install_rawlead_theme.py
```

1. Карточки **узкие**, по центру, как на главной.
2. Выбрал 3 навыка **без** перезагрузки → «Применить» → лента пересортировалась, подпись «Совместимость».
3. Навёл на список навыков, покрутил колесо — скролл внутри блока.

`STATUS.md` — блок § 3i.

---

# § W2 — Волна 2: лендинг (закрыто)

## Цель

1. **UX волны 2** — nav, hero CTA, якорь тарифов (REFERENCE).
2. **Канон текстов** — главная (partials) + inner pages how/faq/contact/pricing (plugin content).
3. После W2 — **§ 3h** (карточки `/lenta/`) в этом же чате или новом по желанию владельца.

---

## § W2.1 — Header + Hero (REFERENCE §3.1–3.2)

| # | Файл | Готово когда |
|---|------|----------------|
| w1 | `template-parts/rawlead/header.php` | Убран пункт **«Главная»** из `$nav`; brand **RawLead** → `/`; пункты: Лента · Как работает · Тарифы · FAQ · Контакты · Кабинет (если был); CTA pill **«Попробовать»** → `/lenta/` |
| w2 | `template-parts/rawlead/hero.php` | H1 **«Лиды без шума»** (без изменений). Подзаголовок **две строки** из канона (см. ниже). Primary **«Смотреть ленту»** → `rawlead_page_url('lenta')`. Secondary **«Смотреть тарифы ↓»** → `#pricing-preview` (не `/pricing`, не «Как работает») |
| w3 | `template-parts/rawlead/pricing-preview.php` | `id="pricing-preview"` на `<section>` (якорь hero). Тексты тарифа — § W2.4 |

**Подзаголовок hero (канон):**

```
Биржи, агрегаторы, Telegram-каналы — в одном потоке.
ИИ выбирает только то, что подходит вашим навыкам.
```

---

## § W2.2 — Главная: блоки partials

| Файл | Поле | Канон (вставить в `esc_html_e` / массив) |
|------|------|------------------------------------------|
| `flow.php` | `rl-flow__caption` | `Биржи и чаты — в одном потоке.` (home.md) |
| `manifest.php` | quote | `Перестаньте мониторить. Начните откликаться.` |
| `features.php` | 3 items | см. таблицу ниже |
| `audience.php` | 3 cards | **заголовок + текст** на карточку (сейчас один `<p>` — расширить разметку: `<h3>` + `<p>` или два поля в массиве) |

**features.php:**

| # | title | text |
|---|-------|------|
| 01 | Один поток | Биржи, агрегаторы, Telegram-каналы — всё в одной ленте. Не нужно переключаться между вкладками и чатами. |
| 02 | ИИ-разбор | Каждый заказ оценивается до того, как вы его видите. Шлак, спам, реферальные схемы — не доходят до ленты. |
| 03 | Вы решаете | Подходящий заказ — пуш в Telegram. Откликаетесь сами. Мы не пишем заказчикам за вас. |

**audience.php (3 карточки):**

| title | text | tags (мелко, optional) |
|-------|------|------------------------|
| Дизайн и визуал | Логотипы, UI/UX, иллюстрации, видеомонтаж — заказы точно по вашим навыкам, без шума дизайн-чатов. | дизайн · UI · иллюстрация · видео |
| Тексты и маркетинг | Копирайт, SMM, таргет, переводы, SEO — ИИ убирает нерелевантное ещё до того, как вы открыли ленту. | копирайт · SMM · таргет · SEO |
| Разработка и автоматизация | Сайты, боты, скрипты, интеграции — один поток вместо десятка вкладок. | разработка · бот · автоматизация |

---

## § W2.3 — Тариф `#pricing-preview`

| Поле | Канон |
|------|-------|
| name | ИИ-агент |
| price | от 300 ₽/мес |
| subtitle | *Для любой ниши — дизайн, тексты, код, маркетинг. ИИ знает ваши теги.* — отдельный `<p class="rl-price-card__lead">` если нет |
| list | Персональная лента по вашим навыкам · ИИ-оценка каждого заказа · Черновик отклика за одну кнопку · Рыночная цена заказа · Push в Telegram при новом матче |
| CTA | Ранний доступ → `/contact` |
| badge | Скоро |
| под карточкой | *Точная цена фиксируется на старте. Участники раннего доступа получают специальные условия.* |
| ссылка | **Узнать первым →** → `/contact` (не «Связаться →») |

---

## § W2.4 — Inner pages (plugin content)

**Источник:** `docs/archive/wp-skeleton/how.md`, `faq.md`, `contact.md`, `pricing.md`  
**Куда:** `wordpress/rawlead-landing/content/how.html`, `faq.html`, `contact.html`, `pricing.html` — HTML как сейчас (h2 + p/ul), **полный текст из MD**.

**После правки HTML** — обновить страницы в WP одним из способов:
- деактивировать/активировать плагин **RawLead Landing**, или
- поправить `scripts/wp_skeleton_setup.py`: `SKELETON` → `docs/archive/wp-skeleton` (сейчас битый путь `docs/ops/wp-skeleton`) и прогнать скрипт на Local, или
- вручную вставить в админке.

**`inc/marketing.php`** — inner hero lead (опционально, если уместно):

| slug | lead |
|------|------|
| how | Пять шагов: от навыков до вашего отклика |
| faq | Коротко о RawLead для любой ниши фриланса |
| contact | Ранний доступ — Telegram или форма |

---

## § W2.5 — Приёмка (владелец)

1. Главная: hero — две кнопки (лента + тарифы ↓), скролл к `#pricing-preview`.
2. Nav без «Главная», логотип на home.
3. Манифест, 01–03, «Для кого» — новые тексты, не IT-only.
4. Тариф — один ИИ-агент, подпись и «Узнать первым →».
5. `/how/`, `/faq/`, `/contact/` — контент из скелета (навыки, облако, нетехнические ниши).
6. `scripts/wp_install_rawlead_theme.py` или обычный refresh — тема на месте.

---

## Файлы (W2)

| Путь |
|------|
| `wordpress/rawlead-kadence-child/template-parts/rawlead/header.php` |
| `wordpress/rawlead-kadence-child/template-parts/rawlead/hero.php` |
| `wordpress/rawlead-kadence-child/template-parts/rawlead/flow.php` |
| `wordpress/rawlead-kadence-child/template-parts/rawlead/manifest.php` |
| `wordpress/rawlead-kadence-child/template-parts/rawlead/features.php` |
| `wordpress/rawlead-kadence-child/template-parts/rawlead/audience.php` |
| `wordpress/rawlead-kadence-child/template-parts/rawlead/pricing-preview.php` |
| `wordpress/rawlead-kadence-child/inc/marketing.php` |
| `wordpress/rawlead-landing/content/how.html` |
| `wordpress/rawlead-landing/content/faq.html` |
| `wordpress/rawlead-landing/content/contact.html` |
| `wordpress/rawlead-landing/content/pricing.html` |
| `scripts/wp_skeleton_setup.py` (путь SKELETON — по необходимости) |
| `docs/team/common/STATUS.md` |

## Не трогать (W2)

- `src/`
- § 3g API
- `/lenta/` JS (кроме если мелочь в CSS лендинга)

---

# § 3h — Лента: карточки = главная (flow.php), теги компактные

**Спека:** [`feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) §3  
**Эталон (главная):** `template-parts/rawlead/flow.php` → `.rl-lead-card` + `.rl-match` + `.rl-chips`  
**Баг от владельца:** на `/lenta/` длинная строка растянутых `#тегов` на всю ширину — **так нельзя**. Нужно как на втором скрине: компактная карточка, маленькие чипы.

---

## Цель

1. **Визуал закрытой карточки** = блок «лид» на главной (жирная рамка 2px, Unbounded title, match-bar **10px**, чипы «Брать» / вердикт ИИ).
2. **Теги навыков** — только **компактные pill** (`width: fit-content`, **без** `flex: 1` / растягивания на всю строку). Максимум **4** тега + «+N» если больше.
3. Multi-навыки в sidebar — без регрессии (§ 3h2).

---

## § 3h1 — Разметка и классы (rawlead-feed.js)

Переделать `renderCard()`:

| Было | Стало |
|------|--------|
| `.rl-feed-card` отдельный стиль | Использовать **`.rl-lead-card`** на `<article>` (или дублировать те же BEM-классы) |
| match в одну строку с `flex:1` bar | Блок **`.rl-match`**: `.rl-match__label` (Совместимость / Оценка ИИ + **NN%**), затем `.rl-match__bar` 10px на **всю ширину карточки** |
| `.rl-feed-card__tags` на всю ширину | **`.rl-chips`**: сначала чип вердикта (`rl-chip--take` / maybe), потом до 4× `.rl-chip` для `lead_tags` (без `#` или с `#` — как на макете, но **маленькие**) |
| Источник + время в шапке | Оставить source pill сверху (FL/Kwork/TG цвета) — мелко, как сейчас |

**Структура закрытой карточки (как flow.php):**

```
[source · time]
H3 title
budget
.rl-match (label + bar 10px)
.rl-chips (Брать + теги compact)
[body раскрытие — как сейчас]
```

**CSS обязательно:**

```css
.rl-lead-card .rl-chips .rl-chip,
.rl-feed-card .rl-chips .rl-chip {
  flex: 0 0 auto;
  width: auto;
  max-width: 100%;
}
/* убрать любое flex:1 / justify-content: stretch на тегах */
```

Переиспользовать стили `.rl-lead-card` из `rawlead.css` (~792+), не дублировать «плоский» feed-only вид.

---

## § 3h2 — Навыки (sidebar)

| # | Готово когда |
|---|----------------|
| s1 | Подзаголовок «Отметьте, что умеете — лента подстроится» |
| s2 | Multi-select чипов, `PUT /v1/me/tags`, перезагрузка с `skills=` |
| s3 | Подпись полоски: без тегов «Оценка ИИ», с тегами «Совместимость» |

API не менять.

---

## § 3h3 — Кабинет (опционально в этом же PR)

`rawlead-cabinet.js` — те же классы карточки, те же правила чипов (не растягивать).

---

## § 3h4 — Деплой Local

После правок:

```powershell
python scripts/wp_install_rawlead_theme.py
```

Ctrl+F5 на `http://radarzakaz.local/lenta/` (uvicorn :18766).

---

## Приёмка (владелец)

1. Карточка **визуально как** блок лида на главной (скрин рядом).
2. Теги **не** тянутся на всю ширину — только маленькие pills в ряд с переносом.
3. 2–3 навыка в sidebar → % и порядок меняются.

---

## Файлы (3h)

| Путь |
|------|
| `wordpress/rawlead-kadence-child/assets/js/rawlead-feed.js` |
| `wordpress/rawlead-kadence-child/assets/js/rawlead-cabinet.js` |
| `wordpress/rawlead-kadence-child/assets/css/rawlead.css` |
| `wordpress/rawlead-kadence-child/page-lenta.php` |
| `docs/team/common/STATUS.md` |

## Не трогать

- `src/api_server.py`
- § 3f

---

## Закрыто

§ P · 3b · 3c · W · 3d · 3e · **3g**

---

_Lead Architect · 2026-05-25 · W2 разблокирован_
