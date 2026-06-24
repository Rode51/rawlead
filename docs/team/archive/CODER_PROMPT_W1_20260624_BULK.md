# CODER_PROMPT — bulk из hot pre-W1 (2026-06-24)
Полные §, снятые RULES-AUDIT-W1. Актуальный hot: [CODER_PROMPT.md](../architect/CODER_PROMPT.md).

> **Источник:** StrReplace ops из agent transcript `9f180369-…` + git HEAD (CABINET/PRE-M1) + Lead verify 2026-06-23 (NEXT-UI / NEXT-DRAFT — полное тело § не сохранилось в transcript после rotation hot).

---

## § NEXT-UI-HOTFIX — P1 · owner 2026-06-23 · wave 1

**Цель:** мелкий UI-fix Next (`rawlead.ru`) — **без** смены API/backend.

**Контекст (owner):** Hero CTA «мигает» при загрузке (quiz vs lenta) · FeedCard — лишняя «Свернуть» · устаревший копирайт на главной.

**Маршрут:** **MiMo `coder`** · deploy `deploy-web-rawlead-vps.py`

### Файлы (≤3)

| Path | Зачем |
|------|--------|
| `rawlead-next/components/feed/FeedCard.tsx` | убрать «Свернуть» · кнопка «Копировать» · collapse draft по клику на карточку |
| `rawlead-next/components/home/Hero.tsx` | lazy `quizDone` · placeholder `h-12` при `auth.status==='pending'` (anti-flicker) |
| `rawlead-next/components/home/*` (copy) | «Все биржи» · trial-плашка · CTA `hero-cta-lenta` / `hero-cta-quiz` |

**Playwright helper (не hot, но DoD):** `scripts/preprod_playwright/next_ui.py` — `collapse_draft_panel(card)` вместо кнопки «Свернуть».

### Задачи

1. **FeedCard:** нет «Свернуть», есть «Копировать текст».
2. **Collapse:** клик по карточке сворачивает панель черновика (`collapse_draft_panel`).
3. **Hero anti-flicker:** `quizDone` — lazy init (`hasAnonQuizCompleted` / profile) · пока `auth.pending` — placeholder той же высоты, что CTA.
4. **Копирайт:** «Все биржи» (не перечисление FL/Kwork/…) · trial-плашка · логика CTA: quiz done → `/lenta/`, иначе quiz.

### DoD

| # | Критерий |
|---|----------|
| 1 | `pytest tests/test_o280_next_e2e.py` — **2 passed** (4 skipped без Playwright) |
| 2 | Prod smoke: Ctrl+F5 `/` — нет моргания CTA · `/lenta/` — нет «Свернуть» |
| 3 | Deploy web bundle (`deploy-web-rawlead-vps.py`) |

**Verify 2026-06-23:** ✅ принято · мёртвая константа `FEED_DRAFT_COLLAPSE` в `next_ui.py` — не блокер.

---

## § NEXT-DRAFT-PLATFORM — P1 · owner 2026-06-23 · wave 2

**Цель:** L2/L3 черновик **под биржу** (Kwork t3203318) + ссылка «Открыть на {биржа} ↗» в FeedCard.

**Старт:** после ✅ NEXT-UI-HOTFIX · **без** смены quiz/UI ленты.

**Маршрут:** **MiMo `coder`** · deploy backend `deploy-g6-l3-vps.py` + web (FeedCard)

### Файлы

| Path | Зачем |
|------|--------|
| `src/ai_analyze.py` | `resolve_reply_platform(source, url)` · строка `Биржа: Kwork` (и FL/YouDo) в L2 user prompt |
| `src/l3_human_style.py` | platform playbooks в bundle deploy |
| `src/match_push.py` | `source` + `url` в push/draft контексте |
| `rawlead-next/components/feed/FeedCard.tsx` | `Открыть на {SOURCE_LABEL} ↗` → `item.url` |

### DoD

| # | Критерий |
|---|----------|
| 1 | `resolve_reply_platform` + `Биржа: Kwork` в user prompt — `test_shared_reply_user_includes_kwork_platform` |
| 2 | FeedCard external link с label биржи |
| 3 | `pytest tests/test_o135_draft.py tests/test_o220_match_code.py` — **28 passed** |
| 4 | Deploy: backend L2 + Next web · smoke Kwork-карточка в `/lenta/` |

**Verify 2026-06-23:** ✅ принято · deploy web + `ai_analyze.py` / `l3_human_style.py` / `match_push.py`.

---

## § YOUDO-IMAP-ONLY — P0 · owner 2026-06-23 · **модель B**

**Цель:** новые YouDo из mail.ru → Postgres → `/lenta/` без listing/antibot.

**Архитектура (B):** каждые ~90 с IMAP → **последние N** писем YouDo → для каждого `t{id}`: **если уже в PG — skip**, иначе ingest. **Нет** `youdo_imap_last_uid` · **нет** bootstrap cursor.

**Симптомы prod:** письма в `INBOX/Newsletters` · ids **нет в PG** · старый курсор съел UID · browser antibot ~3 мин/заказ.

**Маршрут:** **MiMo `coder`** — **2 волны** · Cursor `@coder` — только если MiMo стопнулся.

### Wave 1 — IMAP + poller + tests

| Path | Зачем |
|------|--------|
| `src/youdo_imap.py` | `fetch_last_youdo_emails(N)` · **удалить** cursor/`_IMAP_SEEN_KEY`/bootstrap_skip |
| `scripts/youdo_imap_poller.py` | PG dedup перед ingest · `default_listing_filter()` · log `new_id=` / `skip_exists=` |
| `tests/test_youdo_imap.py` | last-N · dedup skip (mock PG) · **нет** cursor tests |

**DoD wave 1:** pytest `test_youdo_imap` 0 failed · test last-N · test PG skip · test **нет** `youdo_imap_last_uid`.

### Wave 2 — listing off + pipeline (после ✅ wave 1)

| Path | Зачем |
|------|--------|
| `src/youdo_parser.py` | `YOUDO_LISTING_FETCH=0` → skip listing |
| `src/lead_pipeline.py` | email body/cache → `detail_ok=True` без browser |
| `.env.example` | `YOUDO_IMAP_FETCH_LAST` и listing flags |

**DoD wave 2 (полный §):**

1. pytest `test_youdo_imap` + `test_o269` + `test_o281` — 0 failed.
2. IMAP ingest **без** `youdo:trace stage=browser`.
3. Нет `fetch:youdo` listing при `YOUDO_LISTING_FETCH=0`.
4. Lead: deploy → `FETCH_LAST=50` + `poller --once` → smoke ids в PG.

### Env (после wave 2 + deploy)

| Var | Default |
|-----|---------|
| `YOUDO_IMAP_FETCH_LAST` | `30` |
| `YOUDO_LISTING_FETCH` | `0` |
| `YOUDO_CLICK_DETAIL` | `0` |
| `YOUDO_DETAIL_FETCH` | `0` |
| `YOUDO_IMAP_DETAIL_FROM_EMAIL` | `1` |

**Verify 2026-06-23:** ✅ deploy · backup `pre_youdo_imap_b_20260623-065533` · listing/browser **off**.

---

## § YOUDO-IMAP-DISCOVERY — P0 · owner 2026-06-22

**Решение владельца:** вариант A — двухконтурный YouDo.

| Контур | Роль | Частота |
|--------|------|---------|
| **IMAP (mail.ru)** | discovery: `project_id` + url + snippet из письма | poll 60–120s |
| **Браузер** | **только** detail по одному id (goto `/t{id}`), fallback если IMAP молчит | по событию + редкий listing backup |
| **Текущий listing-радар** | backup 2–3 дня, не выключать | `YOUDO_FETCH_EVERY_N_CYCLES=4` (можно ↑ до 8 после IMAP ok) |

**Почему лента пустая сейчас:** source-gate `detail_ok` · ingest идёт snippet/no_detail → `is_visible=False` · `click_ok=0` на listing. IMAP **сам по себе** не чинит ленту без detail-fetch по id из письма (или временного gate для email-snippet — **не делать** без owner).

### Mail.ru — да, напрямую

| Параметр | Значение |
|----------|----------|
| Host | `imap.mail.ru` |
| Port | `993` |
| TLS | SSL (IMAP4_SSL) |
| Login | полный email `user@mail.ru` (или `@inbox.ru` / `@bk.ru` — тот же IMAP) |
| Password | **не** основной пароль · «Пароль для внешнего приложения» в настройках Mail.ru |
| Папка | `INBOX` (или фильтр Gmail-style label — v1 INBOX) |
| Фильтр | `FROM` содержит `youdo` · опционально `SUBJECT` (уточнить по 1–2 реальным письмам owner) |

**Секреты:** только `/opt/rawlead/.env.site` на VPS · не в git · ops doc в `FOR_YOU.md` § YouDo IMAP.

### Сделать (@coder)

| # | Компонент | Где |
|---|-----------|-----|
| 1 | `youdo_imap_poller.py` — IMAP poll, mark `UID`/`Message-ID` seen в SQLite settings `youdo_imap_last_uid` | `scripts/` или `src/` |
| 2 | Парсер письма: regex `youdo\.com/t(\d+)` · title/snippet из text/html (BeautifulSoup) | `src/youdo_imap.py` |
| 3 | Ingest hook: `ListingProject` из письма → существующий pipeline (`lead_pipeline` / `try_record_new`) | reuse `youdo_parser` types |
| 4 | После ingest id: **detail-only** `fetch_task_detail(ext_id)` — один browser goto, **не** full listing | `youdo_parser.py` + `exchange_browser_fetch.py` |
| 5 | systemd: `rawlead-youdo-imap.timer` **или** thread в radar (предпочтение: **отдельный timer** — не блокирует TG) | `deploy/systemd/` |
| 6 | Env: `YOUDO_IMAP_ENABLED=1` · `YOUDO_IMAP_HOST` · `YOUDO_IMAP_USER` · `YOUDO_IMAP_PASSWORD` · `YOUDO_IMAP_POLL_SEC=90` | `.env.example` + `.env.site` |
| 7 | Trace: `youdo:imap new_id=…` · `detail_fetch ok/fail` | radar log |
| 8 | pytest: fixture письма YouDo (html/text) → id + snippet | `tests/test_youdo_imap.py` |

### Не в scope v1

- OAuth Mail.ru (достаточно app-password) · multi-user IMAP · FL/Kwork email (отдельный § позже).

### DoD

1. Owner включает рассылку YouDo на mail.ru · кладёт app-password в `.env.site`.
2. 1 реальное письмо → id в SQLite → detail fetch → `is_visible=True` в VPS Postgres `leads`.
3. Listing-радар **не отключён** · при `YOUDO_IMAP_ENABLED=1` listing можно реже (env `YOUDO_FETCH_EVERY_N_CYCLES=8` — ops, не код).
4. pytest green · deploy: imap unit + `youdo_parser` detail path · restart `rawlead-youdo-imap` + radar.

**Параллельно:** § YOUDO-CLICK-PROXY — нужен для detail из listing-backup; для IMAP-path приоритет **goto `/t{id}`** без click-through listing.

**Маршрут:** owner → mail.ru app-password · @coder implement · Lead deploy + verify лента.

---

---

## § YOUDO-CLICK-PROXY — P0 · owner 2026-06-22

**Симптом prod (post CLICK-RETRY deploy):** `click_summary new=48 ok=0` · **ноль** строк `click_detail` · `click_ok=0` при `parsed=50` и sticky листинг ~300KB.

**Гипотеза (подтверждена кодом + логами):** `youdo_click_through_details()` **молча** `return {}` если `_YOUDO_STICKY_PROXY != proxy_url` (или proc dead / IPC fail). В `fetch_listing_projects` proxy для клика = `exchange_primary_proxy_url("youdo") or hint`, где `hint` = **строка лога** `proxy_log_hint` (не URL). Листинг мог поднять sticky на **другом DC-слоте** карусели, чем `exchange_primary_proxy_url` на момент клика.

### Сделать

| # | Fix | Где |
|---|-----|-----|
| 1 | `youdo_sticky_active_proxy_url() -> str` (read `_YOUDO_STICKY_PROXY`) | `exchange_browser_fetch.py` |
| 2 | Click batch: `proxy = sticky_active or exchange_primary_proxy_url("youdo")` — **никогда** `or hint` | `youdo_parser.py` |
| 3 | Trace `stage=click_ipc_skip reason=proxy_mismatch|proc_dead|ipc_error|disabled` перед `{}` | `exchange_browser_fetch.py` |
| 4 | pytest: listing sticky proxy ≠ primary → click всё равно шлёт IPC на sticky proxy | `tests/test_o269_youdo_click_detail.py` |

**DoD:** prod 1 fetch: `click_detail` строки есть · `click_ok>0` или явный `click_ipc_skip` в trace · purge smoke: удалённые id → `youdo:ingest new>0`.

**Маршрут:** @coder → Lead deploy `youdo_parser.py` + `exchange_browser_fetch.py` · restart radar only.

---

---

## § YOUDO-CLICK-RETRY — owner 2026-06-22 · P0

**Проблема:** клик только при **первом** id в SQLite. Клик падает (SP) → snippet в базе → следующие циклы `new_projects` пусто → **повторного клика нет** → лента пустая (source-gate).

**Цель:** пока нет `detail_ok`, **повторять click-through** для id, которые **снова на листинге** (до успеха или лимита).

### Сделать

| # | Fix | Где |
|---|-----|-----|
| 1 | Флаг **pending detail**: `storage` setting `youdo_detail_pending:{project_id}=1` при `no_detail` / failed click (`detail_ok≠True`) | `lead_pipeline.py` + helper в `storage.py` или `youdo_parser.py` |
| 2 | Снять флаг при `detail_ok=True` (click cache / `_resolve_ingest_body`) | `lead_pipeline.py` |
| 3 | **Click targets** = `(not in seen_ids)` **OR** `(pending AND on current listing)`; приоритет **новые** → потом retry; cap `YOUDO_CLICK_DETAIL_MAX` | `youdo_parser.py` `fetch_listing_projects` |
| 4 | Trace: `stage=click_retry ext=…` · `click_summary` pending=N retry=M ok=K | `youdo_parser.py` |
| 5 | pytest: id в sqlite+pending+на листинге → попадает в click batch; после ok → pending снят | `tests/test_o269_youdo_click_detail.py` |

**Не в scope:** snippet в ленту без detail · backfill 4219 · god-file split.

**DoD:** pytest `test_o269`+`test_youdo_human`+`test_o281` 0 failed · deploy с § SP-STABLE (worker+src) · 24h: на `no_detail` id через 1–2 цикла есть `click_detail` (не только первый ingest).

**Маршрут:** @coder (можно одним PR со SP-STABLE deploy) · Lead deploy после ✅

---

---

## § YOUDO-SP-STABLE — owner 2026-06-22 · P0

**Цель:** чаще получать **detail HTML** в той же sticky-сессии, где листинг уже `parsed=50`. Сейчас: листинг ~300KB → ServicePipe 1701 → `sticky_teardown` → ephemeral `html_len=0` → `click_ok=0`.

**Не в scope:** source-gate · backfill 4219 snippets · split `exchange_browser_fetch` god-file · OCR.

**Канон:** [`2026-06-22-youdo-parser-audit.md`](../../problems/2026-06-22-youdo-parser-audit.md) §3 human-like · §6 log gaps · [`2026-06-16-youdo-antibot-browser.md`](../../problems/2026-06-16-youdo-antibot-browser.md)

### Симптом prod (2026-06-22)

| Лог | Смысл |
|-----|--------|
| `html_len=303627` + `parsed=50` | sticky листинг **ОК** |
| `html_len=1701` + `antibot_hit=1` | ServicePipe на **следующем** goto/клике |
| `sticky_teardown` → `ephemeral=1` | сессия убита — click-through теряется |
| `HtmlFetchError html_len=0` | ephemeral пустой ответ |
| `click_ok=0` · `new=0` | detail не в ingest |

### Сделать (приоритет)

| # | Fix | Где |
|---|-----|-----|
| 1 | **Human-like click:** `hover()` перед click · jitter **1.5–4s** между карточками (не rapid-fire) | `scripts/youdo_sticky_worker.py` |
| 2 | **Не рвать sticky** после успешного листинга из‑за SP на **первом** click/reload — retry `page.go_back()` / reload listing в **том же** tab до teardown (max 2) | `youdo_sticky_worker.py` + **≤40 строк** `exchange_browser_fetch.py` если нужно |
| 3 | **Trace:** `stage=click_detail` с `outcome` · `stage=click_summary click_ok=N` · selector_miss → debug HTML path · click_cache hit/miss в `lead_pipeline` | worker + `youdo_parser.py` **или** `lead_pipeline.py` (один из двух) |
| 4 | **Misleading log:** `new_ids=` в trace → `click_ok=` (audit P1-4) | `youdo_parser.py` |
| 5 | pytest: jitter между clicks (mock) · click IPC round-trip (audit P0-2) | `tests/test_o269_youdo_click_detail.py` |

### Лимиты

≤3 файла · ≤120 строк diff · `exchange_browser_fetch.py` **≤40** строк · **не** новые env без согласования owner

### DoD

| # | Критерий |
|---|----------|
| 1 | `pytest tests/test_o269_youdo_click_detail.py tests/test_youdo_human.py` — 0 failed |
| 2 | Deploy: `youdo_sticky_worker.py` + затронутые `src/*` · **restart `rawlead-radar` only** (worker subprocess) |
| 3 | **24h watch:** при `youdo:ingest new>0` — хотя бы 1× `stage=click_detail outcome=ok` **или** документированный blocker в `docs/problems/` |
| 4 | Не ухудшить: `fetch:youdo outcome=ok parsed=50` стабильность (нет роста `parsed=0` циклов) |

**Откат:** redeploy из `pre_source_gate_20260622-114840.tar.gz` только затронутые файлы · [`2026-06-22-youdo-source-gate-rollback.md`](../../problems/2026-06-22-youdo-source-gate-rollback.md)

**Маршрут:** MiMo coder (≤3 файла) · deploy Lead после verify ✅

---

---

## § YOUDO-SOURCE-GATE — owner 2026-06-22 (rev 2)

**Продукт:** в публичной ленте **нет** карточек «только с листинга» — ломает UX (нет черновика, половинчатый контент). YouDo в ленте = **только** когда есть текст с **detail-страницы** (click / goto / cache). Короткое, но настоящее ТЗ с detail — **ок** (не режем по символам).

| Источник | `detail_ok` | Лента (`is_visible`) | L1 / L2 / L3 |
|----------|-------------|----------------------|--------------|
| detail (click / goto / cache) | `True` | **да** | да |
| listing / snippet / title only | `False` | **нет** (`delist` или не insert visible) | нет |

**Код сейчас (поправить):** floor 300 символов при `detail_ok=True` — **убрать**. При `detail_ok≠True` — **delist** (как сейчас), но reason `youdo_no_detail` (не `detail:short` по длине).

**Сделать:**
1. `_youdo_detail_short_skips_l1` → переименовать/переписать: skip L1+L2+L3 когда `detail_ok is not True`; **всегда** `pg.delist_lead` для публички.
2. При `detail_ok is True` — **не** проверять length floor 300; `YOUDO_DETAIL_MIN_CHARS` не блокирует detail-path.
3. Physical pre-L1 — до gate; если physical → delist как сейчас.
4. **Post-deploy:** one-shot — скрыть уже видимые YouDo без detail (backfill или `restore` не поднимать snippets); согласовать с owner перед `--apply`.

**Лимиты:** ≤3 файла · ≤120 строк · `lead_pipeline.py` + тесты

**DoD:** `pytest test_o281` + `test_o223` — `detail_ok=False` → delist, no L3 · `detail_ok=True` + body 80 chars → L1 runs · **нет** кейса «preview visible».

**Deploy:** после § YOUDO-AUDIT-P0 · ожидание: YouDo в ленте **реже**, пока click-through не стабилен — это ок по owner.

---

## § YOUDO-AUDIT-P0 — Lead verify 2026-06-22

**Источник:** [`2026-06-22-youdo-parser-audit.md`](../../problems/2026-06-22-youdo-parser-audit.md) · аудит ✅ · **код P0 — нет**

**Лимиты:** ≤3 файла · ≤80 строк diff · **не** трогать `exchange_browser_fetch.py` / split god-files

| # | Fix | Файлы |
|---|-----|-------|
| 1 | **P0-1 dedup:** `list_seen_ids` не существует → `storage.list_project_ids(["youdo"])` или `has_seen` per id | `src/youdo_parser.py` |
| 2 | **pytest:** `test_youdo_human` setUp `YOUDO_DETAIL_FETCH=1` (утечка из `test_o281`) | `tests/test_youdo_human.py` |
| 3 | **pytest:** `test_o281` tearDown / `finally` — сброс `YOUDO_DETAIL_FETCH` | `tests/test_o281_youdo_full_tz_gate.py` |

**DoD:** `pytest tests/test_o269_youdo_click_detail.py tests/test_o281_youdo_full_tz_gate.py tests/test_youdo_human.py` — **0 failed** · click-through dedup покрыт тестом (mock storage с ids).

**Не в scope:** feed hygiene (`public_feed`/`vacancy_filter`/`backfill_*`) — ждёт решения owner · O281 `MIN_CHARS=0` — отдельный § после product call.

---

---

## § QUIZ-REDESIGN — P1 · owner 2026-06-23 · **Claude Code**

**Старт:** после **✅** YOUDO-IMAP-ONLY prod (уже).

**Задача (owner):** квиз технически правильный. Логику не трогаем. Только переписать тексты карточек — сейчас они слишком технические (ТЗ-стиль), пугают пользователей.

**Файлы для правки (только они):**
- `data/quiz_cards_v1.json` — 46 карточек (dev)
- `data/quiz_cards_v2.json` — 140 карточек (dev/design/marketing/text)

**Правила переформулировки:**

| Поле | Что делать |
|------|-----------|
| `title` | Переписать как **вопрос от пользователя** или **простую задачу клиента** · без tech-жаргона в заголовке · макс 70 символов |
| `task_summary` | Сократить до **1–2 предложений** · фокус на **что хочет клиент**, не на стек · макс 130 символов |
| `skills_on_like` | **НЕ ТРОГАТЬ** |
| `niche`, `signal`, `id`, `complexity`, `card_type` | **НЕ ТРОГАТЬ** |

**Примеры (было → стало):**

`"FastAPI-сервис: вебхуки Stripe → запись в PostgreSQL"` → `"Настроить приём оплаты на сайте и сохранять данные о покупках"`

`"amoCRM ↔ Google Sheets: двусторонняя авто-синхронизация сделок"` → `"Связать CRM клиента с таблицами Google — чтобы всё синхронизировалось само"`

`"Ретаргетинговые кампании в Яндекс Директ: look-alike + смарт-баннеры"` → `"Вернуть посетителей сайта через рекламу в Яндексе"`

`"UX-аудит + редизайн карточки товара: 3 варианта в Figma"` → `"Улучшить страницу товара: найти проблемы и нарисовать 3 варианта в Figma"`

**Не меняем:** логику квиза (`src/quiz_adaptive.py`) · UI (`QuizOverlay.tsx`) · тэги/сигналы/ниши · общее количество карточек.

**DoD:** оба JSON-файла обновлены · `skills_on_like` у всех 186 карточек идентичны оригиналу · тесты `test_o197_quiz_adaptive` проходят.

**Маршрут исполнения:** **Claude Code** (owner отдаёт напрямую) · копипаст § ниже.

---

## § FEED-HYGIENE — owner A 2026-06-22

**Цель:** убрать из публичной ленты физуслуги и `ai_verdict=МИМО` (код уже в diff — **verify + довести**).

**Файлы (diff есть):** `src/public_feed.py` · `src/vacancy_filter.py` · `scripts/backfill_feed_hygiene_vps.py` · `scripts/restore_youdo_visible_vps.py` · `tests/test_o75_feed_retention.py`

**DoD:** pytest `test_o75` · `backfill_feed_hygiene_vps.py --dry-run` на VPS · `--apply` по OK owner · deploy API.

**Не в scope:** YouDo source-gate · split parsers.

---

---

## § CABINET-PARITY — Lead ✅ 2026-06-21

| # | DoD |
|---|-----|
| Push `🔔 Match` без % | VPS `match_push.py` ✅ |
| ЛК уведомления без % | кнопки порога ✅ |
| Retake квиза | `#rl-cabinet-quiz-retake` напротив «Мои отклики» · **без** показа навыков (quiz-first) |

pytest: `test_match_push_o50` · `test_match_push_o250` · deploy API+Next.

---

## § PRE-M1-SECURITY — Lead ✅ 2026-06-21

Commit `786aede` · Bearer-only `/v1/me/*`.

Архив § → [`CODER_PROMPT_ARCHIVE`](../archive/CODER_PROMPT_ARCHIVE.md).
