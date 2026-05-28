# Coder — **→ E-polish (B1)** · после § P5-E2-VPS ✅

**Ворота прод:** [`PRE_PROD_GATE.md`](PRE_PROD_GATE.md) · бюджет: [`docs/ops/DEPLOY_BUDGET.md`](../../ops/DEPLOY_BUDGET.md).

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.11**.

**Порядок (владелец 2026-05-28):** **E-polish** (B1 → A1 → C1) → **§ 3f-OWNER-BETA** → **§ PRE-PROD-STRESS**.

**→ Сейчас @coder:** **E-polish B1** ([`OWNER_INTENT.md`](OWNER_INTENT.md)) · VPS E2 — **владелец** (`DEPLOY_VPS.md` § E2/E2b).

**✅ Архив (не трогать без § в шапке):** SITE-POLISH, FEED-FRESHNESS, 3x-HOT-BADGE, BACKLOG-CLEAR, LEGACY-SELF-STOP, HOTFIX-POST-PULT и др. — см. [`STATUS.md`](../common/STATUS.md).

# § LEGACY-SELF-STOP — ▶ гасится через ~15 с (**владелец 2026-05-28**)

**Симптом:** Legacy ▶ → лампа «Neon» зелёная секунды → снова **■**; `radar_legacy.log` — пачка `neon:старт`, мало `neon:цикл`.

| # | Задача |
|---|--------|
| ls1 | `radar_control.start`: если `popen` жив, **не** вызывать `_stop_unlocked` только из‑за `count_radar_workers==0` (Windows lag) — **Lead 2026-05-28** черновик в `scripts/radar_control.py`, verify |
| ls2 | `neon_legacy_consumer._sleep_with_tg_poll`: не `time.sleep(negative)`; при `sleep_sec==0` — min 0.05 с — **Lead 2026-05-28** |
| **ls0** | **Корень 2026-05-28:** `NameError: process_legacy_neon_listing` / `short_err` не импортированы в `neon_legacy_consumer.py` → consumer падает на 1-м цикле → пульт ■ — **✅ import** `lead_pipeline` |
| ls3 | Ошибки воркера → красный баннер пульта (`errors` из `/start`) + хвост `data/radar_legacy_exchanges.log` |
| ls4 | Приёмка: ▶ 2 мин — `neon:цикл` в логе, ■ не сам; `rebuild-pult.bat` после правок desktop |

**Проверка:** `data\radar_legacy_exchanges.log` — нет Traceback; ▶ 120 с — пульт **■** не сам.

# § PULT-LOG-SCROLL-STICK — логи/статус не прыгают (**владелец 2026-05-28**)

**Симптом:** читаешь лог или вкладку «Статус» наверху — при автообновлении уезжает вниз.

| # | Задача |
|---|--------|
| ps1 | `logFollowBottom` только если ползунок **у низа** (порог ~32px) — уже есть; **не** сбрасывать в `true` при смене вкладки — **Lead 2026-05-28** `desktop/src/main.ts` |
| ps2 | При обновлении «Статус» (innerHTML) восстанавливать **gap от низа**, не `scrollTop` |
| ps3 | `scripts\rebuild-pult.bat` — владелец после сдачи |

# § P5-E2-VPS — Site + Legacy dogfood на VPS (**владелец 2026-05-28**)

**Решение:** парсер + TG listen + **dogfood** на **одном VPS**; владелец управляет **@FLPARSINGBOT** (/status, /pause, кнопки — уже в `telegram_control` + `neon_legacy_consumer`). Пульт на ПК **не** 24/7.

**До деплоя:** если ▶ Legacy на ПК — не должен сам гаситься (§ LEGACY-SELF-STOP). Канон: [`OWNER_INTENT.md`](OWNER_INTENT.md).

| # | Задача |
|---|--------|
| e1 | `deploy/run-radar-site.sh` + `rawlead-radar.service` — уже есть; приёмка E2 |
| e2 | **Новый** `deploy/run-radar-legacy.sh` + `deploy/systemd/rawlead-radar-legacy.service` → `neon_legacy_consumer.py --profile legacy` |
| e3 | `DEPLOY_VPS.md` § E2b — `.env.legacy` на VPS, scp **не** нужны Telethon для legacy |
| e4 | **Пауза раздельно:** `SQLITE_PATH` в `.env.legacy` ≠ site **или** `radar_paused_site` / `radar_paused_legacy` — чтобы /pause в FLPARSING **не** гасил Site ingest |
| e5 | После деплоя: на ПК `stop-radar-desktop-full` — проверка **нет** дублей TG listen |
| e6 | @rawlead_bot: hotfix `load_site_rollup_line` import — статус Site-бота |

**Не делать:** второй VPS; Freelancehunt на VPS.

**Приёмка владельца:**

1. ПК: оба пульта **■**, скрипт stop full.
2. VPS: `rawlead-radar` + `rawlead-radar-legacy` active.
3. `/lenta/` обновляется без ПК.
4. @FLPARSINGBOT: `/status`, `/pause` → `/старт` — карточки dogfood; **Site** на паузе только если e4 сделан (иначе общая пауза — предупредить в статусе).

**✅ Coder 2026-05-28:** e2–e6 · Lead verify · деплoy на VPS — владелец.

# § BACKLOG-CLEAR — сброс хвоста L1 без OpenRouter (**✅ 2026-05-28**)

**Запрос:** очистить очередь ~1253 без L1; **новые** заказы в ленту; **не грузить** OpenRouter всем хвостом.

**Факт Neon (2026-05-28):** без L1 **1253**; из них **~55 за 24 ч** — остальное **старый хвост** (конвейер + wide ingest + replay TG).

| # | Задача |
|---|--------|
| b1 | Скрипт `scripts/clear_l1_backlog.py` (или флаг replay): `--dry-run` / `--apply` |
| b2 | **По умолчанию:** пометить хвост **без вызова ИИ**: `created_at < NOW() - INTERVAL '48 hours'` (или `id < max_id - 100`) → `ai_verdict='Пропущено'`, `ai_score=0`, `is_visible=false`, `ai_reasons=['backlog_cleared']` |
| b3 | **Не трогать** последние 48 ч / top 100 id DESC — их L1 как сейчас (DESC батч) |
| b4 | Лог: сколько строк cleared vs сколько осталось без L1 |
| b5 | После apply: `count_leads_missing_l1` < 100; Site ▶ — новые fl/kwork с L1 в приоритете |

**Владелец:** Stop не нужен; после apply — Site ▶, смотреть `/lenta/` (верх < 15 мин).

**Не делать:** DELETE FROM leads; L1 на все 1253 подряд.

---

# § NEON-AUDIT-FILTERS — выборка отказов ИИ (**→ после b2**)

**Факт (Neon, fl/kwork с L1):** МИМО ~261 · Сомнительно ~186 · Брать ~77 · `is_visible=true` ~256 · false ~230.

**Топ `ai_reasons` у МИМО:** «не относится к разработке, дизайну, маркетингу или текстам» · «общий/физический труд» — **похоже на задуманный scope §0i**, не баг фильтра.

| # | Задача |
|---|--------|
| a1 | SQL/скрипт отчёт: 20 случайных **Брать** + 20 **МИМО** за 7 дней — title + reasons + score → `docs/team/common/` или вывод в STATUS § NEON-AUDIT |
| a2 | Сверка: сколько отсечено **до L1** (`skip:filter` в логе) vs **на L1** — если filter режет «Брать» кандидатов, примеры в тикет |
| a3 | Опционально: 5 спорных карточек владельцу в чат (без автоправки FILTERS без Product) |

**→ Сейчас @coder:** **§ BACKLOG-CLEAR** · **§ HOTFIX-POST-PULT**.

# § HOTFIX-POST-PULT — приёмка владельца 2026-05-28 (**→ сейчас**)

| # | Симптом | Фикс |
|---|---------|------|
| h1 | **@rawlead_bot** не отвечает на «Статус» | `radar_site.log`: `тг:бот:NameError:name 'load_site_rollup_line' is not defined` → **import** в `radar_status.py` из `radar_cycle_log` |
| h2 | **Legacy-пульт** сам гасится, **@FLPARSINGBOT** шлёт привет | `radar_legacy.log`: куча `neon:старт` без стабильного цикла — consumer падает/рестарт; **Stop** не убивает orphan `neon_legacy_consumer` / `pythonw` → `stop-radar-desktop-full.vbs` + `kill_duplicate_radar_workers(profile=legacy)`; при **Stop** в `radar_control` гарантировать kill consumer |
| h3 | Очередь L1 огромная — откуда | см. ниже § «Почему backlog» — не баг «одной ночи», накопление wide ingest + конвейер |

**Проверка h1:** `/status` в @rawlead_bot → текст без Traceback; пульт Site вкладка «Статус» 200.

**Проверка h2:** Legacy ■ → 30 с тишина в @FLPARSINGBOT на новые карточки; `neon:старт` не сыпется без ▶.

**Почему backlog 1000+ (для STATUS):** Site `neon_ingest_wide` пишет fl/kwork/tg в Neon **до L1**; при `RADAR_CONVEYOR=1` L1 только батчем; раньше `ORDER BY id ASC` гонял **старые** id — свежие не попадали в ленту; replay TG + долгие прогоны без L1 (401/падения) → тысячи строк `ai_verdict IS NULL`. После фикса DESC очередь **уходит**, но полное обнуление = часы или one-shot replay.

**→ Сейчас @coder (было):** **§ DROP-FREELANCEHUNT** · **§ PULT-STATUS-LOGS** · **§ FEED-FRESHNESS** · **§ SITE-POLISH** (stress не трогать).

**✅ 2026-05-28 FILTERS L2:** `FILTERS_SITE` + sync `FILTERS.md` / `FILTERS_LEGACY` + `filters.py` marketing — cloudflare/капча → только L4; убраны `есть заказ`/`пиши`; агрегатор — длинные маркеры.

**✅ 2026-05-28 env:** `PUBLIC_FEED_SOURCES` — `fl,kwork` + **21× `tg:-100…`** (без freelancehunt — решение владельца). (peer id, не CSV `chat_id` без префикса). Пересборка: `python scripts/build_public_feed_sources.py`.

---

# § SITE-POLISH — довести прод до stress (**→ сейчас**, владелец 2026-05-28)

**Цель:** [rawlead.ru](https://rawlead.ru) не «голый деплой», а **нормальный продукт**: лента свежая, ЛК, вход, UX, тексты. **PRE-PROD-STRESS — после приёмки этого блока.**

| # | Трек | Готово когда |
|---|------|----------------|
| **p1** | **§ FEED-FRESHNESS** — свежие FL/Kwork в `/lenta/` (не 40+ мин при работающем Site ▶) | владелец: верх ленты &lt; 15 мин в часы активности бирж |
| **p2** | **§ feed-source-filter** — `GET /v1/feed?source=tg|fl|kwork` + WP фильтр «Telegram» не пустой | см. ниже |
| **p3** | **ЛК `/cabinet/`** — навыки, match, L2 «Написать отклик», пустые состояния, mobile | § 3f-OWNER-BETA фаза A |
| **p4** | **Регистрация** — TG Login Widget на prod + fallback; `user_id` в Neon; ошибки понятные | `CABINET-LOGIN-FALLBACK` довести на `https://rawlead.ru` |
| **p5** | **UX** — E5/REVOLUTION хвосты на прод-URL, «Горячий» §3x, permalink `/lenta/` | @designer макет → Coder CSS |
| **p6** | **Тексты** — Product c1–c4 на WP prod (не «ранний доступ») | сверка с `LEAD_PRODUCT_PROMPT` |

**Не в polish:** биллинг 3h (после 3f-A), stress k6, acc2 join (ops).

**Сдача:** `STATUS.md` § SITE-POLISH · владелец чеклист в `FOR_YOU.md`.

---

# § DROP-FREELANCEHUNT — убрать FH из продукта (**→ сейчас**, владелец 2026-05-28)

**Решение:** от **Freelancehunt** отказались; в `.env` / `.env.site` уже без `freelancehunt` в `PUBLIC_FEED_SOURCES`.

| # | Готово когда |
|---|----------------|
| fh1 | **Не вызывать** в цикле Site: убрать из `_P1_WEB_SOURCES` / `enabled_sources` по умолчанию — только `fl`, `kwork` (+ tg из env) |
| fh2 | Дефолты: `public_feed.py`, `build_public_feed_sources.py`, `.env.example` → `fl,kwork` (без fh). **`build_public_feed_sources`:** пропускать строки с `⏸` / `отложен` / `отключён` / `❌` (сейчас «отключён» без ⏸ — FH снова в выводе) |
| fh3 | Доки: `PUBLIC_FEED_WEB_SOURCES.txt` ✅, `RADAR_LOG.md`, `KAK_ETO`, `STATUS` § TG — без fh в примерах |
| fh4 | `radar_cycle_log.py` — не печатать строку Freelancehunt; порядок источников FL + Kwork |
| fh5 | Парсер `freelancehunt_parser.py` — **оставить в repo**, не импортировать из `main` (⏸ отложен, как vc_ru) |
| fh6 | WP/feed: подпись источника fh не нужна в MVP; preprod fixtures — ок оставить |

**Владелец:** удалить `FREELANCEHUNT_API_TOKEN` из `.env.site` (не обязателен).

**Проверка:** Site ▶ 15 мин → в `radar_site.log` **нет** строки `Freelancehunt │`; `python scripts/build_public_feed_sources.py` — в строке нет `freelancehunt`.

---

# § PULT-STATUS-LOGS — подробные логи и статусы пультов + оба бота (**→ сейчас**)

**Запрос владельца:** нормальные **подробные** вкладки «Статус» / лампы Legacy + Site; понятный статус **двух ботов** (@rawlead_bot Site, @FLPARSINGBOT Legacy).

**Сейчас:** один `format_status_message` без профиля; Site rollup в payload, но текст статуса бедный; боты — только «Бот /start: да/нет» per acc, без имени бота.

| # | Задача |
|---|--------|
| pl1 | **`format_status_message`:** шапка `Профиль: SITE|LEGACY` · бот **`@rawlead_bot`** (site) / **`@FLPARSINGBOT`** (legacy) · `TELEGRAM_CHAT_ID` · конвейер вкл/выкл · пауза |
| pl2 | **Site:** блок «Лента / Neon» — `site:сводка` 10 мин (из SQLite), последний цикл (FL/Kwork: скачано/новых/neon_insert/is_visible), **время последней visible** в Neon (1 SQL) |
| pl3 | **Legacy:** блок «Dogfood» — карточек в бот за сессию / последний neon consumer (если есть счётчик в логе или SQLite) |
| pl4 | **TG acc:** без изменения логики listen; ясные подписи acc1/acc2/acc3 + join pending |
| pl5 | **`/status` JSON (пульт):** поля `bot_label`, `bot_start_ok`, `conveyor`, `poll_min`, `profile`, `site_rollup_10m`, `last_visible_at` — desktop может рисовать карточки |
| pl6 | **Desktop `main.ts`:** вкладка «Статус» — рендер JSON-блоков (не только plain text), ошибка config с подсказкой `RADAR_CONVEYOR=1` |
| pl7 | **Два пульта:** Legacy `:18765` + `radar_legacy.log` · Site `:18775` + `radar_site.log` — в статусе **имя лог-файла** |
| pl8 | **Кнопка «Статус» в TG-боте** (`telegram_control.py`): тот же текст, что `/status-text` пульта **для этого профиля** (site-бот не путать с legacy) |
| pl9 | `docs/ops/RADAR_LOG.md` § «Статус пульта» — расшифровка полей |

**Не делать:** stress k6; новые фичи ленты.

**Приёмка владельца:**

1. Site-пульт → «Статус» — видно @rawlead_bot, FL+Kwork, сводка 10 мин, нет Freelancehunt.
2. Legacy-пульт → «Статус» — @FLPARSINGBOT, Neon consumer, TG выкл или отдельно.
3. `/status` в @rawlead_bot и в @FLPARSINGBOT — осмысленные разные тексты (не один шаблон без профиля).

**Сдача:** `STATUS.md` § PULT-STATUS-LOGS · `FOR_YOU.md` одна строка.

---

# § PULT-POLL-STATUS — «POLL_INTERVAL минимум 10, получено: 1» (**шаг 0, владелец**)

**Симптом:** Site-пульт, вкладка «Статус»: `Не удалось загрузить статус: POLL_INTERVAL_MINUTES: минимум 10 мин, получено: 1`.

**Причина:** в `config.py` интервал **1 мин** разрешён только при `RADAR_PROFILE=site` **и** `RADAR_CONVEYOR=1` в `.env.site`. Иначе `load_config()` падает на `/status-text` (радар при этом может работать).

**Владелец:** `.env.site` — обе строки → `stop-radar-desktop-full.vbs` → ярлык **RawLead Site** → проверка:

```powershell
.venv\Scripts\python.exe -c "import sys; sys.argv=['','--profile','site']; from config import load_config; c=load_config(); print(c.radar_profile, c.poll_interval_minutes, c.radar_conveyor)"
```

Ожидание: `site 1 True`.

**Coder (если не помогло):** понятная ошибка + `RUN.md` про конвейер.

---

# § FEED-FRESHNESS — «последний заказ 40 мин назад» (**после шага 0**)

**Симптом:** на [ленте](https://rawlead.ru/?page_id=5) верхняя карточка **~40 мин** и старее; владелец ожидает поток FL/Kwork.

**Что видно в `radar_site.log` (Lead 2026-05-28 ~16:00):**

| Факт | Вывод |
|------|--------|
| TG listen жив (`тг:пульс`, `тг:сообщ`) | TG не причина «тишины» на биржах |
| FL «новых 2», Kwork «новых 4», FH «новых 10» | Парсер **качает**, но мало **новых id** (dup) |
| Полный footer цикла / `site:сводка` / `конвейер:L1=` **редко в логе** | Подозрение: `main` **долго в цикле** или L1 backlog не догоняет |
| `в бот 0` на Site | Норма — в ленту только `is_visible` после L1 |

**Диагностика Lead 2026-05-28 (Neon, факт):**

| Метрика | Значение |
|---------|----------|
| Последняя **видимая** в ленте (`is_visible`) | **~57 мин** назад |
| Новые fl/kwork в Neon (insert) | **6–11 мин** назад, но `is_visible=false`, **L1 нет** |
| Очередь **без L1** (fl/kwork) | **1252** строки |
| `fetch_leads_missing_l1` | **`ORDER BY id ASC`** — батч 40/цикл жрёт **старые**, свежие ждут часы |

**Корень:** конвейер (`defer_l1`) + L1 backlog **сначала старьё** → лента не «мгновенная», даже при живом парсере.

**Лог:** после `── Цикл … ──` часто **нет** footer FL/Kwork — цикл `main` не завершается или L1 batch не логируется (отдельно от `тг:пульс`).

| # | Задача |
|---|--------|
| f1 | **`drain_l1_backlog` / `fetch_leads_missing_l1`:** приоритет **свежих** — `ORDER BY id DESC` или два прохода (N новых DESC + M старых ASC) |
| f2 | Порог: backlog &gt; 100 → лог `конвейер:backlog=1252` + в пульте «Статус» |
| f3 | Опция: для fl/kwork **L1 сразу** на ingest (конвейер только для догона старых) — продукт «мгновенно в ленту» |
| f4 | One-shot: догнать L1 для последних 200 id DESC (скрипт или флаг replay) |
| f5 | Footer цикла + `site:сводка` каждые 10 мин |
| f6 | Prod API — тот же Neon; не блокер если f1–f3 ок |

**Приёмка:** Site ▶ 30 мин в дневное время → верх `https://rawlead.ru` ленты — FL/Kwork **&lt; 15 мин** (если биржа даёт заказы).

---

# § feed-source-filter — фильтр источника в API (**внутри SITE-POLISH**)

**Симптом:** фильтр «Telegram» на `/lenta/` пустой — клиент режет 20 карточек без `tg:`.

| # | Готово когда |
|---|----------------|
| s1 | `GET /v1/feed?source=tg` (и `fl`, `kwork`) — фильтр **в SQL**, не в JS |
| s2 | `rawlead-feed.js` — передаёт `source` в REST-прокси |
| s3 | Replay TG только по 21 peer из `build_public_feed_sources.py` (опц. флаг `--whitelist-only`) |

---

# § REPLAY-TG-FIX — replay `--tg-replay` падает (**✅ код 2026-05-28**)

**Симптом:** `replay_neon_lite_site.py --profile site --tg-replay --limit 200` печатает `TG replay: 200`, затем **Traceback** — в Neon/`/lenta/` ничего не меняется.

**Причина:** `default_listing_filter(cfg)` — в `filters.py` сигнатура **без аргументов** (`default_listing_filter()`). То же в строке ~485 того же скрипта.

**Фикс:** заменить на `default_listing_filter()` (2 места в `scripts/replay_neon_lite_site.py`).

**Проверка владельца после фикса:**
```text
.venv\Scripts\python.exe scripts\replay_neon_lite_site.py --profile site --tg-replay --limit 200
```
Ожидание: строки `L1 tg:… → Брать|Сомнительно|МИМО`, в конце `Готово: L1=N` (N > 0). Затем `/lenta/` — фильтр «Все» или источник TG; не все 200 станут видимыми (МИМО/filter — норма).

**Не блокер если уже есть:** `PUBLIC_FEED_SOURCES` с `tg:-100…` в `.env.site` (строка ~96) — у владельца есть.

---

# § 3f-OWNER-BETA — ты = первый платный подписчик (тест без реальных денег сначала)

**Запрос владельца (2026-05-28):** нормальный `/cabinet/`, L2-бот с черновиком отклика, потом платежи; **владелец** гоняет сценарий до внешних юзеров.

**Канон продукта:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) Direction D · §0d acceptance #5 · цена **590–990 ₽/мес** (3h).

**Уже есть в коде (не переделывать):** `/cabinet/`, TG Login fallback, `/v1/me/feed`, `reply_draft` в `rawlead-cabinet.js`, `subscriptions` в Neon, @rawlead_bot.

| Фаза | # | Готово когда |
|------|---|----------------|
| **A. Обкатка без оплаты** | a1 | Владелец: `/start` @rawlead_bot → вход в `/cabinet/` (widget или fallback) → `user_id` в Neon |
| | a2 | `/cabinet/`: лента только match по `user_tags`; кнопка **«Написать отклик»** → L2 → `reply_draft` виден и копируется |
| | a3 | **§ P4b:** два набора `user_tags` у одного лида → **разные** черновики (smoke в `preprod_ai_matrix` расширить) |
| | a4 | Опционально: push в TG владельцу при новом match (`telegram_chat_id` в профиле) — флаг env |
| **B. Кабинет UX** | b1 | Lead Design: § в `DESIGNER_PROMPT` — кабинет «подписка», тариф, пауза (макет) |
| | b2 | Coder: страницы тариф/статус подписки в child theme; `subs.is_active` / `paused_until` в API |
| **C. Оплата (3h)** | c1 | ЮKassa / Robokassa / T-Bank — **один** провайдер, один тариф «ИИ-агент», webhook → `subscriptions` |
| | c2 | После оплаты: `is_active=true`, L2 без ручного «включения» |
| | c3 | Пауза подписки (`subs.paused_until`) — UI + крон (vision 3p, можно вместе с c1) |

**Не в этой задаче:** multi-user маркетинг, freemium 3q, несколько тарифов, оферта/ИП (владелец).

**Проверка владельца (A):** Site ▶ + API ▶ → зайти на `/cabinet/` → выбрать навыки → увидеть match → «Написать отклик» → черновик ≠ пустой.

**Сдача:** `STATUS.md` § 3f-OWNER-BETA · Product сверяет copy тарифа.

---

# § EXCHANGE-CONVEYOR — fetch 1 мин + прокси + L1 батч (**база в коде 2026-05-28**)

**Запрос владельца:** парсить биржи **каждую минуту**, не ждать 10 мин; FL/Kwork через **ротацию прокси**; не блокировать fetch долгим L1.

**Сделано (база):**

| Компонент | Файл |
|-----------|------|
| `RADAR_CONVEYOR=1` — ingest без L1 в hot path, L1 в конце цикла батчем | `lead_pipeline.py`, `main.py` |
| `POLL_INTERVAL_MINUTES=1` (min 1 при conveyor+site) | `config.py` |
| `FL_PROXY_URLS` / `KWORK_PROXY_URLS` round-robin | `exchange_proxy.py`, `fl_parser.py`, `kwork_parser.py` |
| `L1_BATCH_PER_CYCLE=40` | `config.py`, `.env.site` |

| # | Доработка / приёмка |
|---|---------------------|
| e1 | Лог цикла: `конвейер:вкл` при старте; `fetch:fl proxy=host:port` (без пароля) |
| e2 | При 429/timeout FL/Kwork — **следующий** прокси из списка в том же цикле (retry 1×) |
| e3 | TG **не** в conveyor defer — `process_new_listing_from_tg` L1 inline как сейчас |
| e4 | `docs/ops/RUN.md` — схема конвейера (fetch → Neon → L1 batch) |
| e5 | Замер: цикл fetch ≤2 мин при conveyor; L1 догоняет backlog, не копится бесконечно |

**Риски (не скрывать):** FL может банить частый crawl даже с прокси; OpenRouter $ при `L1_BATCH=40` каждую минуту.

**Проверка:** `.env.site`: `RADAR_CONVEYOR=1`, `POLL_INTERVAL_MINUTES=1`, прокси заданы → Site ▶ → в логе каждые ~1 мин заголовок цикла + `конвейер:L1=N`; FL/Kwork `скачано` без паузы 10 мин.

**Сдача:** `STATUS.md` § EXCHANGE-CONVEYOR

---

# § TG-FEED-SOURCES — TG в `/lenta/` и legacy consumer (**✅ код 2026-05-28**)

**Симптом:** Site `tg_main` слушает v2-чаты, но **TG нет** в `/lenta/` и в @FLPARSINGBOT — только FL/Kwork.

**Причина:** `is_visible` и `GET /v1/feed` требуют `source ∈ PUBLIC_FEED_SOURCES`. Ключ в Neon: **`tg:{peer_id}`** (напр. `tg:-1001199102856`), не `tg:1199102856` из CSV.

**Владелец / Lead:** `.env` уже обновлён (21 каналов done ∩ allowlist). После сдачи Coder — **перезапуск Site ▶** (и legacy consumer, если нужен TG в FLPARSING).

| # | Готово когда |
|---|----------------|
| t1 | `scripts/build_public_feed_sources.py` — печатает строку для `.env` (биржи из `PUBLIC_FEED_WEB_SOURCES.txt` + tg peers) |
| t2 | Док [`docs/ops/RADAR_LOG.md`](../../ops/RADAR_LOG.md) или `FOR_YOU.md` — одна строка: «после join done → `python scripts/build_public_feed_sources.py` → вставить в `.env` → рестарт Site» |
| t3 | **One-shot:** `scripts/replay_neon_lite_site.py --limit 200` — пересчитать L1 + `is_visible` для строк `source LIKE 'tg:%'` уже в Neon (без re-ingest) |
| t4 | **acc2:** в `radar_site.log` не `0 из 25 чатов` — join pending из `TG_JOIN_QUEUE_v2` (perezvonyu, webfrl, …) |
| t5 | Проверка: Neon `SELECT source, COUNT(*) FROM leads WHERE source LIKE 'tg:%' GROUP BY 1`; `/v1/feed` — есть `source` с префиксом `tg:`; legacy consumer — опц. карточки TG в FLPARSING (тот же whitelist) |

**Файлы:** `scripts/build_public_feed_sources.py`, `scripts/replay_neon_lite_site.py`, `docs/ops/RADAR_LOG.md` или `FOR_YOU.md`

**Не трогать:** split Legacy/Site, `FILTERS_*` содержимое

**Проверка:** Site ▶ 30 мин → новый пост в @distantsiya или replay → `/lenta/` фильтр «Все» — карточка с источником TG; `radar_site.log` — `is_visible` > 0 в `site:сводка` при годном L1

**Сдача:** `STATUS.md` § TG-FEED-SOURCES · не коммитить

---

# § SITE-LOG-ROLLUP — сводка Site за 10 мин

**Запрос владельца:** понятные логи **Site-контура** (парсер → L1 → Neon → лента), не путать с @FLPARSINGBOT.

**Канон:** парсит **`main.py --profile site`** + `tg_main`; пишет **`data/radar_site.log`**. @rawlead_bot — уведомления подписчикам (биржи владельцу по умолчанию **не** шлёт, `SITE_NOTIFY_OWNER=0`).

| # | Готово когда |
|---|----------------|
| r1 | Каждые **10 мин** (или в футере каждого цикла + отдельная строка раз в 10 мин) в `radar_site.log`: |
| | `site:сводка │ 10мин │ скачано N │ новых_sqlite M │ neon_insert K │ neon_replay R │ l1 L1 │ l2 L2 │ is_visible V │ filter F │ мимо X` |
| r2 | Счётчики **скользящее окно 10 мин** (не только последний цикл ~15 мин) — ring buffer в памяти процесса `main` или агрегация по timestamp строк |
| r3 | В пульте Site вкладка **radar** / **Статус** — та же сводка (если уже tail log — достаточно явной строки `site:сводка`) |
| r4 | [`docs/ops/RADAR_LOG.md`](../../ops/RADAR_LOG.md) — таблица расшифровки новой строки |
| r5 | Не ломать существующие футеры `Итого в бот` / `neon_insert` per cycle |

**Файлы (можно трогать):** `src/radar_cycle_log.py`, `src/main.py`, `src/lead_pipeline.py` (только note_* hooks если нужно), `scripts/radar_control.py` (опц. status), `docs/ops/RADAR_LOG.md`

**Не трогать:** `neon_legacy_consumer.py`, `FILTERS_LEGACY.md`, legacy AI_MODE

**Проверка:** Site ▶ 20 мин → в `radar_site.log` ≥2 строк `site:сводка │ 10мин` с ненулевым `скачано` или явным `0` + причина в том же цикле

**Сдача:** `STATUS.md` § SITE-LOG-ROLLUP · не коммитить

---

**Архив (3x ✅):** § 3x-HOT-BADGE ниже · P5 после rollup

**Архив задач ниже** — STOP-STATUS-SPAM, PRE-LAUNCH, S-SPLIT и т.д. (**не трогать** без нового § в шапке).

---

# § 3x-HOT-BADGE — Бадж «Горячий» (**✅ 2026-05-28**)

**Канон:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) §4 фаза 3x · [`LEAD_PRODUCT_PROMPT.md`](../product/LEAD_PRODUCT_PROMPT.md) § MARKET-INTEL-B.

**Суть:** если заказ появился **< 5 минут** назад — красный/оранжевый badge «Горячий» на карточке в `/lenta/` и `/cabinet/`.

| # | Готово когда |
|---|----------------|
| h1 | `GET /v1/feed` и `/v1/me/feed`: поле `is_hot: bool` **или** отдавать `created_at` ISO и считать на фронте (< 300 с) |
| h2 | `rawlead-feed.js` / `rawlead-cabinet.js` — рендер badge при hot |
| h3 | `rawlead.css` — `.rl-badge-hot` (один стиль, REVOLUTION-токены) |
| h4 | Mobile: badge не ломает filter-bar / карточку |

## Файлы (можно трогать)

- `src/api_server.py` — `is_hot` в items (если на бэкенде)
- `wordpress/rawlead-kadence-child/assets/js/rawlead-feed.js`
- `wordpress/rawlead-kadence-child/assets/js/rawlead-cabinet.js`
- `wordpress/rawlead-kadence-child/assets/css/rawlead.css`

## Файлы (не трогать)

- `src/ai_analyze.py`, `lead_pipeline.py`, legacy consumer
- `docs/ops/FILTERS_LEGACY.md`

**Проверка:** `wp_install_rawlead_theme.py` → Ctrl+F5 `/lenta/` → свежий лид (или подставить `created_at` в API) → badge виден; старый лид (>5 мин) — без badge.

**Сдача:** `STATUS.md` § 3x · не коммитить.

---

**→ Ранее @coder (порядок до выхода, архив):**

**✅ § STOP-STATUS-SPAM** — принято владельцем 2026-05-27

**🟠 § PRE-LAUNCH** — **A → B → C → D** (владелец 2026-05-27, до хостинга)

**⏸ § PRE-LAUNCH-UX** — **после** функционала § PRE-LAUNCH → **@lead-designer** → @coder (см. § внизу)

**🔴 § STOP-STATUS-SPAM (детали)** — после `stop-radar-desktop-full` в TG 100+ «📊 Статус радара». **Причина:** `kill_all_radar_control` / `_ALL_MATCH` **не** убивают `neon_legacy_consumer.py`; 2× consumer + опрос getUpdates ~каждые 2 с. Тикет: [`docs/problems/2026-05-27-status-spam-after-stop.md`](../problems/2026-05-27-status-spam-after-stop.md).

**✅ § PULT-MIN** — Lead hotfix 2026-05-27, владелец OK. Канон: `docs/ops/DESKTOP_LAUNCH.md` § антирегресс · `docs/problems/2026-05-27-pult-start-killed-api.md`. **Не ломать** `radar_spawn_workers.py` / `/start` без ▶-теста.

0a. § **BOT-NOTIFY-SPLIT** — **P0 продукт:** Site **не** шлёт биржи владельцу в @rawlead_bot; биржи → только Legacy → @FLPARSINGBOT (**блокер**, владелец 2026-05-27)
0. § **SITE-BAT-VENV** — **довести:** один `radar_control` + воркеры только из `.venv` (**блокер**, Lead verify ❌ 2026-05-27 ~16:00)
0b. § **SQLITE-NEON-SYNC** — **довести:** resync SQLite→Neon на биржах в рантайме (**блокер**, Lead verify ❌ 2026-05-27 ~16:00)
1. § **NEON-DEDUP-REPLAY** — зомби в Neon + dup без L1 (**блокер ленты**)
2. § **LOG-NEON-CYCLE** — счётчики в `radar_site.log` (не путать dup с «нет заказов»)
3. § **FEED-DECOUPLE** — лента не зависит от TG (`notified_at`) (**P0 продукта**)
4. § **SITE-AI-FALLBACK** — при сбое ИИ не слать “всё подряд” (только управляемо флагом)
3. § **P5-PREP** — только пункты под выбранный хостинг (после п.1–2)
4. § **P5** — **только** после ворот + «едем на прод» от владельца

LEGACY pipeline (один ИИ) не трогать без задачи владельца. § F-SITE-FILTERS-0i · S-SPLIT-* — **код ✅**, приёмка владельцем после п.1.

**Диагностика (Lead 2026-05-27):** Neon ~3260 строк, **0 insert с 26.05 ~09:00 UTC**; `category=design` ~260, `is_visible=true` ~1; figma-лиды с `ai_verdict IS NULL` — wide ingest + старый стоп **до** L1, затем `dup` без replay.

---

# § BOT-NOTIFY-SPLIT — Два бота, два смысла (**→ сейчас**, владелец 2026-05-27)

**Симптом:** в ЛС приходят карточки заказов с бирж от **@rawlead_bot**, хотя это поток **@FLPARSINGBOT** (личный парсер владельца).

**Канон (владелец, не спорить):**

| Контур | Бот | ИИ | Кому шлёт TG |
|--------|-----|-----|----------------|
| **LEGACY** | @FLPARSINGBOT | `AI_MODE=legacy`, `FILTERS_LEGACY`, один `analyze_project` | **Владелец** (`TELEGRAM_CHAT_ID` в `.env.legacy`) — «брать заказы» |
| **SITE** | @rawlead_bot | `AI_MODE=split`, L1→лента, L2→бот | **Подписчики** по навыкам из `/cabinet/` (Neon `users` + tags). **Не** дублировать legacy-поток бирж владельцу |

**Факт в логе (Lead verify):** `radar_site.log` **14:13** — `FL.ru … в бот 7`, `Kwork … в бот 1`, `Итого в бот: 8`, `tg:цепь … bot=8989158953` (@rawlead). `radar_legacy.log` **16:14** — `выборка 8` / `32`, **`новых 0 │ в бот 0`**.

**Причина (код):** `main.py --profile site` → `process_new_listing` → `send_listing_notification` → `TELEGRAM_BOT_TOKEN` site + **`TELEGRAM_CHAT_ID` владельца** — тот же путь, что dogfood, без разделения «биржи = только legacy».

## Задачи

| # | Готово когда |
|---|----------------|
| n0 | **Site + `PUBLIC_FEED_SOURCES` (fl, kwork, freelancehunt):** после L1/L2 **не** вызывать `send_listing_notification` в `TELEGRAM_CHAT_ID` владельца. Только Neon (`is_visible`) + `/lenta/`. |
| n1 | **Legacy consumer:** биржи из Neon → `FILTERS_LEGACY` → legacy ИИ → **только** `.env.legacy` бот → владелец. В логе `новых N │ в бот N` при живых заказах (если 0 — логировать `skip:*` по каждому id). |
| n2 | **Site TG** (`tg:*`): уведомления в rawlead — **не** на legacy-чат владельца для бирж; для TG — отдельное правило (см. n3). |
| n3 | **Подписчики (MVP v1):** если нет multi-user push — флаг `.env.site` `SITE_NOTIFY_OWNER=0` (default): site **вообще** не шлёт владельцу; dogfood бирж **только** Legacy ▶. Опц. `SITE_NOTIFY_OWNER=1` — только для отладки L1/L2 в rawlead. |
| n4 | **L2 / навыки:** когда будет push подписчикам — отдельная ветка (JWT `/me`, tags), **не** `TELEGRAM_CHAT_ID` из `.env.site` для fl/kwork/fh. |
| n5 | `FOR_YOU.md` + `STATUS`: таблица «куда что приходит». |
| n6 | Приёмка: Site ▶ + Legacy ▶; новый заказ FL «Брать» по legacy-фильтру → **только** FLPARSING; в rawlead **нет** карточек fl/kwork/fh владельцу; `/lenta/` живая. |

## Файлы

| Путь |
|------|
| `src/lead_pipeline.py` |
| `src/main.py` |
| `src/neon_legacy_consumer.py` |
| `src/config.py` |
| `.env.example` |
| `docs/FOR_YOU.md` |
| `docs/team/common/STATUS.md` |

**Не делать:** менять `FILTERS_LEGACY.md`; убирать Site ingest в Neon; слать биржи в rawlead «для теста» без флага.

---

# § SITE-BAT-VENV — Фикс запуска воркеров с пульта (**→ сейчас**, 2026-05-27)

**Симптом:** лампа «Биржи» в пульте красная. В `radar_site_exchanges.log` ошибка `Unable to create process using '"C:\Users\hramo\AppData\Local\Programs\Python\Python311\python.exe" -u ...\src\main.py --profile site'`.

**Причина:** при разделении на профили в `start-radar-desktop-site.bat` (и `start-radar-desktop.bat`) остался старый код, который вытаскивает `RADAR_PYHOME` из `pyvenv.cfg` и запускает `radar_control.py` через **системный** `pythonw.exe`. Из-за этого `radar_control` наследует кривое окружение, и когда он пытается сделать `subprocess.Popen` для дочернего воркера через `.venv\Scripts\python.exe`, Windows блокирует создание процесса.

## Задачи

| # | Готово когда |
|---|----------------|
| b1 | В `scripts/start-radar-desktop-site.bat` удалить блок парсинга `pyvenv.cfg` (`findstr /b "home" ...`). Запускать `radar_control.py` напрямую через `"%RADAR_ROOT%\.venv\Scripts\pythonw.exe"`. |
| b2 | Сделать то же самое в `scripts/start-radar-desktop.bat` (legacy). |
| b3 | Приёмка: после запуска пульта через VBS и нажатия ▶ лампа «Биржи» становится зелёной, в `radar_site_exchanges.log` нет ошибки `Unable to create process`, воркер `main.py` нормально стартует. |

### Lead verify (2026-05-27 ~16:00) — **частично**

| Факт | Значение |
|------|----------|
| bat b1–b2 | ✅ в репо: запуск через `.venv\Scripts\pythonw.exe` |
| Цикл бирж | ✅ в `radar_site.log` есть строки FL/Kwork/FH (~16:00) |
| Дубли процессов | ❌ одновременно venv **и** `Python311\python.exe` для `main.py` / `tg_main.py` / `radar_control.py` |
| `Unable to create process` | ⏳ ушла после bat, но при ▶ с пульта снова появляются system-воркеры |

| # | Готово когда |
|---|----------------|
| b4 | `process_guard.kill_all_radar_control(profile=site)` (и legacy) завершает **все** `radar_control`/`main`/`tg_main` с **любым** python (не только venv) |
| b5 | `radar_control.py` spawn воркеров: **только** `_ROOT/.venv/Scripts/python.exe`; родитель `radar_control` — только venv `pythonw` (проверить, что desktop/VBS не поднимает system `pythonw` вторым API) |
| b6 | Приёмка: после одного VBS + ▶ — в списке процессов **нет** `...\Python311\python.exe` с `main.py`/`tg_main.py`/`radar_control.py` для site; лампа «Биржи» зелёная ≥1 цикл |

### Владелец: откуда дубли (Lead 2026-05-27, не баг «кликает не так»)

| Источник | Механизм |
|----------|----------|
| ✕ закрытие пульта | `main.ts` → POST `/stop` — гасит **воркеры**, **`radar_control` остаётся** |
| `stop-radar.bat` | Убивает main/tg/join, **не** `radar_control` — в FOR_YU было неверно |
| Legacy bat `:desktop_only` | Если `/health` ок — **не** вызывает `kill_all_radar_control` → второй `desktop.exe`, старый system API жив |
| Ярлык только на `desktop.exe` | Bat с kill **не запускается** → зомби system `pythonw` + новый venv из другого ярлыка |
| Два профиля Site+Legacy | 2 API — норма; **4+** `main.py` — баг |

| # | Готово когда |
|---|----------------|
| b7 | `scripts/stop-radar-desktop-full.bat` (+ `.vbs` без окна): `kill_all_radar_control` для **site** и **legacy**; в `FOR_YOU.md` / `DESKTOP_LAUNCH.md` — канон вместо «только stop-radar.bat» |
| b8 | Legacy bat: при `goto desktop_only` всё равно `kill_non_venv_radar_workers(profile=legacy)` (или не пропускать kill API при втором ярлыке) |
| b9 | Опция (продуктово): ✕ на пульте → `/stop` + `kill_all_radar_control` **только своего** профиля; или явная кнопка «Выход и остановить API» |
| b10 | `rebuild-pult.bat` / инструкция: ярлыки на стол **только** на `start-radar-desktop-*-.vbs`, не на exe |

## Файлы

| Путь |
|------|
| `scripts/start-radar-desktop-site.bat` |
| `scripts/start-radar-desktop.bat` |
| `scripts/stop-radar-desktop-full.bat` (новый) |
| `scripts/radar_control.py` |
| `src/process_guard.py` |
| `desktop/src/main.ts` (закрытие окна) |
| `docs/FOR_YOU.md` · `docs/ops/DESKTOP_LAUNCH.md` |

---

# § SQLITE-NEON-SYNC — SQLite «видел», Neon нет (**→ сейчас**, Lead verify ❌ 2026-05-27 ~16:00)

**Симптом (факты Lead, не гипотеза):** сверка живых лент FL/Kwork/FH (парсеры Site) с Neon `leads`:

| Биржа | На ленте | В Neon по `external_id` | В SQLite `projects` | В SQLite, но **нет** в Neon |
|--------|----------|------------------------|----------------------|-----------------------------|
| FL | 90 | 8 | 85 | **~77** |
| Kwork | 12 | 2 | 12 | **10** |
| FH | 10 | 0 | 9 | **9** |

В `radar_site.log` при этом: `FL … новых 8` ≈ только те 8 ID, что **уже** в Neon; `neon_insert: 0`, `neon_dup_skip` в основном **TG**. Это **не** «99% дублей на бирже».

**Причина (код):** `lead_pipeline.process_new_listing` → `storage.try_record_new` → при `False` ранний `return`, **без** `pg.record_new_lead`, если нет `neon_replay`. Локальная SQLite накопила ID с прошлых прогонов (wide ingest / сбой L1 / старый профиль), Neon — нет.

**Параллельно у владельца:** OpenRouter 401 на Site, пока в `.env.site` ключ **не** тот же, что в `.env` (суффикс `178`). Site грузит `.env.site` с `override=True`, потом `.env` с `override=False` — **переменные из `.env.site` не перезаписываются** общим `.env`. После фикса env — **Stop → ▶ Site** (процесс должен перечитать env).

## Задачи

| # | Готово когда |
|---|----------------|
| s1 | Если `neon_ingest_wide` и `pg.enabled`: при `try_record_new` → `False` проверить Neon по `(source, external_id)`. **Нет строки** → выполнить `record_new_lead` + дальше фильтр/L1 (как для нового), **не** выходить молча |
| s2 | Если строка в Neon есть, но `ai_verdict` NULL — путь **neon_replay** (см. § NEON-DEDUP-REPLAY), не считать «полным dup» |
| s3 | Счётчик/лог: `neon_sqlite_resync` (или явный skip-reason) — когда SQLite был «старый», Neon догнали |
| s4 | **One-shot:** `scripts/replay_neon_lite_site.py` (или новый) — опция `--backfill-missing`: live listing ∪ SQLite-only → INSERT в Neon для `PUBLIC_FEED_SOURCES`, затем L1; `--dry-run` печатает N «sqlite без neon» (Внимание: скрипт сейчас падает с `UnicodeEncodeError` на символе `│` при выводе в консоль Windows, нужно добавить `sys.stdout.reconfigure(encoding='utf-8')`) |
| s5 | Приёмка: после Site ▶ 30 мин — в Neon есть `external_id` с **сегодняшней** ленты FL (пример: ID > `5506729`); в логе `neon_insert` > 0 **или** `neon_replay` с успешным L1; **нет** массового `ai:http:…401` (ключ — зона владельца) |
| s6 | `STATUS.md`: 5 строк — симптом, причина, фикс, как проверить |

### Lead verify (2026-05-27 ~16:00) — **не принято**

| Факт | Значение |
|------|----------|
| Footer цикла | `neon_insert: 0` · `neon_replay: 2` · `neon_dup_skip: 110` · **`neon_sqlite_resync` в логе нет** |
| Биржи | FL скачано 90, **новых 2**; Kwork новых 8; FH новых 7 — массового догона ~77 FL **нет** |
| dry-run | `replay_neon_lite_site.py --backfill-missing --dry-run` → **sqlite без Neon: 1475** (на живой ленте **98**) |
| Гипотезы | (1) `lead_exists` true, хотя по `external_id` нет; (2) ранний `neon_dup_skip` / `skip:dup_content` до resync; (3) ветка `in_neon` + нет L1 replay + `not inserted` → return без AI; (4) дубль system+venv воркер — гонка/старый код |

| # | Готово когда |
|---|----------------|
| s7 | В `process_new_listing` (только `PUBLIC_FEED_SOURCES` / биржи): при `try_record_new`→False **сначала** `lead_exists(source, external_id)`; если False — **обязательно** `record_new_lead` + L1, не `_neon_dup_skip_return` |
| s8 | Debug-лог (1 строка на лид, rate-limit ok): `neon_resync_check` / `neon_resync_insert` / `neon_resync_skip:<reason>` — чтобы в `radar_site.log` было видно, почему не догнали |
| s9 | Счётчик `neon_sqlite_resync` в footer цикла (уже в ТЗ) — **появляется** при реальном догоне |
| s10 | `replay_neon_lite_site.py`: UTF-8 stdout (Windows); `--backfill-missing --dry-run` без падения; `--limit 50` (без dry-run) — в Neon появляются строки с сегодняшних FL id |
| s11 | Проверить/откатить посторонний патч `pg_storage.py` (если есть `connection()` context manager от Lead — привести к одному стилю psycopg, без поломки `with psycopg.connect`) |
| s12 | Приёмка: 1 цикл Site после фикса → footer `neon_insert` > 0 **или** `neon_sqlite_resync` > 0; для FL id с ленты (пример `5506883+`) — строка в Neon; **нет** `ai:http:401` (ключ — владелец, Stop→▶) |

## Файлы

| Путь |
|------|
| `src/lead_pipeline.py` |
| `src/pg_storage.py` |
| `src/storage.py` (только если нужен helper «exists in sqlite») |
| `scripts/replay_neon_lite_site.py` |
| `src/radar_cycle_log.py` |
| `docs/team/common/STATUS.md` |

**Не делать:** чистить SQLite вслепую без логики; ломать legacy consumer; снимать UNIQUE `content_hash`.

---

# § STOP-STATUS-SPAM — стоп не гасит consumer (**→ P0**, 2026-05-27)

**Симптом:** 100+ «📊 Статус радара» в @FLPARSINGBOT после стопа пульта / VBS.

**Причина (код):** `neon_legacy_consumer.py` остаётся жить; опрос `getUpdates` + ответ на «ℹ Статус»; дубли venv+system усиливают эффект.

**Тикет:** [`docs/problems/2026-05-27-status-spam-after-stop.md`](../problems/2026-05-27-status-spam-after-stop.md)

| # | Готово когда |
|---|----------------|
| s1 | Полный стоп убивает `neon_legacy_consumer` (см. тикет) |
| s2 | После VBS 30 с — 0 процессов uisness radar; в TG нет автоспама без кнопки |

---

# § PRE-LAUNCH — до хостинга (**→ @coder**, владелец 2026-05-27)

**Решение владельца:** лента = **совместимость %** по навыкам пользователя; **без** фильтра «Брать / Сомнительно» и **без** отдельной «оценки лида» в UI. Платный ИИ = инструменты + короткий человечный отклик. **UI/тексты** — § **PRE-LAUNCH-UX** (Design **перед** выкладкой).

## A — Лента: только match % (без вердиктов)

| # | Готово когда |
|---|----------------|
| a1 | `/lenta/` + `/cabinet/`: убрать чипы/фильтры **Брать · Не брать · Сомнительно** и пороги `min_score` по вердикту |
| a2 | Главная метрика карточки: **«Совместимость N%»** = `final_rank` / match по **выбранным навыкам** (`PUT /v1/me/tags`, `sort=match`); без подписи «Оценка ИИ» как основной |
| a3 | API: не требовать `ai_verdict` для отображения ленты; `is_visible` + skills match достаточно (сверка с § FEED-DECOUPLE) |
| a4 | Убрать с карточки отдельную **оценку лида** (score как «вердикт заказа») — только % совпадения + теги/источник |

**Файлы:** `rawlead-feed.js`, `rawlead-cabinet.js`, `rawlead.css`, `page-lenta.php`, `page-cabinet.php`, `src/api_server.py`, `src/pg_storage.py` (read path)

## B — Специализации: чипы работают + мульти + навыки

| # | Готово когда |
|---|----------------|
| b1 | Чипы **Категория/специализация** на `/lenta/` и `/cabinet/` реально фильтруют: `GET /v1/feed?category=…` / `me/feed` — Network 200, лента меняется |
| b2 | **Несколько специализаций** одновременно (OR): UI multi-select + API `?category=dev,design` или повторяемый param — согласовать с `TZ_API.md` |
| b3 | Навыки в панели **зависят от выбранных специализаций**: каталог `/v1/skills/catalog` — секции `groups` только для активных category; смена category → сброс/фильтр skill-чипов |
| b4 | «Применить» → `offset=0`, лента пересчитана; пустой результат — понятный empty state (не молчаливый баг) |

**Файлы:** `page-lenta.php`, `page-cabinet.php`, `rawlead-feed.js`, `rawlead-cabinet.js`, `src/api_server.py`, `src/lead_category.py`, `docs/team/architect/TZ_API.md` (если меняется контракт — одна строка в § API)

**Проверка:** Ctrl+F5 `/lenta/` → 2 специализации → список навыков сузился → 3 навыка → «Применить» → порядок и % изменились.

## C — ИИ для платных подписчиков (L2 premium)

| # | Готово когда |
|---|----------------|
| c1 | [`AI.md`](AI.md) § L2 premium (подписчик): **краткое описание задачи**, **методы/инструменты** для выполнения, **короткий отклик** — разговорный, без воды и лишней вежливости, «как ты решишь» |
| c2 | `analyze_premium` / JSON: поля `tools_required[]` (или в `approach`), `reply_draft` — обязательные; не дублировать L1 `task_summary` |
| c2b | **Neon:** выполнить [`sql/005_premium_subscriber.sql`](../../sql/005_premium_subscriber.sql) — иначе `GET /v1/feed` **500** `tools_required does not exist`; в `RUN.md` / сдаче — одна строка владельцу |
| c3 | Выдача в кабинете/TG подписчику (когда JWT/me): блоки «Инструменты» + «Черновик отклика»; legacy @FLPARSINGBOT pipeline **не** ломать |
| c4 | **Legacy @FLPARSINGBOT:** не слать карточку без `reply_draft`. Если ИИ недоступен/пустой черновик — `skip:ai_unavailable_no_draft` в лог и `в бот 0` (лучше пропуск, чем «сырой» MVP без отклика) |
| c5 | Лог причины для владельца: `neon:skip ... skip:ai_unavailable_no_draft` / `skip:ai:no_reply_draft` (чтобы видно было, почему не пришло) |
| c6 | **/cabinet/ login fallback:** если Telegram Widget не загрузился/битый iframe — альтернативный вход без widget (одноразовый код через бота или deep-link). Тикет: [`docs/problems/2026-05-27-cabinet-telegram-widget-login-fails.md`](../../problems/2026-05-27-cabinet-telegram-widget-login-fails.md) |
| c7 | **Персонализация L2 до P5:** при генерации `reply_draft` учитывать профиль пользователя (его `user_tags`/ниша) как минимум для владельца (`user_id=#1`) и зафиксировать это в `AI.md`; в сдаче показать 3 примера «один лид → разные профили = разные черновики» |

**Согласование текста промпта:** владелец + **@lead-product** (короткий § в `AI.md`) → потом Coder в код.

**Файлы:** `docs/team/architect/AI.md`, `src/ai_analyze.py`, `src/lead_pipeline.py`, `src/telegram_notify.py`, `wordpress/.../rawlead-cabinet.js` (раскрытие карточки)

## D — Быстрее парсинг

| # | Готово когда |
|---|----------------|
| d1 | Замер: один цикл FL+Kwork в `radar_site.log` — время от `── Цикл ──` до `Итого` (baseline в STATUS) |
| d2 | Безопасные ускорения: меньше лишних fetch/retry; параллель только если не ломает SQLite lock; не резать L1 без флага |
| d3 | Опц. env `POLL_INTERVAL_MINUTES` / лимиты источников — документ в `.env.example`; цель: цикл бирж **≤ ~N мин** (N согласовать с владельцем после замера) |

**Файлы:** `src/main.py`, `src/fl_parser.py`, `src/kwork_parser.py`, `src/public_feed.py`, `.env.example`

## D2 — Добив по приёмке владельца (2026-05-27, обязательно до P5)

**Факт:** PRE-LAUNCH A/B/C частично в коде, но приёмка владельца **не пройдена**.

| # | Готово когда |
|---|----------------|
| d2-1 | Заголовок карточки: при hover есть полный title (tooltip/атрибут), при раскрытии карточки title читается полностью (не обрезан) |
| d2-2 | Категории реально переключают выдачу: клик по category меняет карточки (`/v1/feed`/`/v1/me/feed`), не косметика |
| d2-3 | Навыки зависят от category и есть явная кнопка **«Сбросить всё»** у навыков |
| d2-4 | Убрать пустые «дырки» в сетке ленты (стабильный layout, без лишнего пустого блока) |
| d2-5 | Раскрытие карточек: одновременно открыта только **одна** карточка; соседние не раскрываются каскадом |
| d2-6 | `/cabinet/` доступен и понятен сценарий L2: вход работает, в раскрытии видны `tools_required` + `reply_draft` (если данных нет — понятный placeholder, не «пусто») |
| d2-7 | В сдаче: короткий чек-лист «как владелец проверяет за 5 минут» + где смотреть Network (`/v1/feed`, `category`, `skills`) |
| d2-8 | При пустом Telegram Widget в `/cabinet/`: fallback вход работает и не блокирует приёмку (см. тикет `2026-05-27-cabinet-telegram-widget-login-fails.md`) |
| d2-9 | Проверка персонализации: при смене навыков владельца в ЛК (`PUT /v1/me/tags`) и повторной генерации L2 текст `reply_draft` меняется под профиль (не только сортировка ленты) |
| d2-10 | Сетка карточек в `/lenta/` и `/cabinet/` рендерится **построчно** (row-major): `1 2 / 3 4 / 5 6`, без «колоночного добора» вида `1 5 / 2 6`. Нужен обычный grid/flex layout, не masonry/columns |

**Lead verify 2026-05-27:** d2-10 **❌ не сдано** — в `rawlead.css` осталось `column-count: 2` на `#rl-feed-list`. Убрать columns/masonry; `display: grid; grid-template-columns: repeat(2, minmax(0, 1fr))` (mobile: 1 col). **→ сейчас только этот пункт** (+ опц. d2-1 title без ellipsis при `.is-expanded`, d2-7 чек-лист в STATUS).

**✅ § LEGACY-REPLY-DRAFT** — Lead verify 2026-05-27 (приёмка ⏳). Тикет [`2026-05-27-legacy-bot-empty-reply-draft.md`](../problems/2026-05-27-legacy-bot-empty-reply-draft.md).

**✅ § LEGACY-DRAFT-LEN-SOFTEN** — Lead verify 2026-05-27 (приёмка ⏳). Не терять заказ из‑за счётчика предложений.

**✅ § CANONICAL-TAGS-E2b** — Lead verify 2026-05-28 (миграция Neon ⏳). L1 + API под [`SKILLS_TOOLS_CATALOG.md`](../product/SKILLS_TOOLS_CATALOG.md).

| # | Готово когда |
|---|--------------|
| e2b-1 | `AI.md` + L1: теги **только** из canonical_tag пула каталога; границы category (text ≠ 3D, dev ≠ нейминг) |
| e2b-2 | Neon `pending_tags` + после L1: unknown → pending, known → `lead_tags` |
| e2b-3 | `GET /v1/skills/catalog` — из каталога (не агрегация `lead_tags`) |
| e2b-4 | Анон `/lenta/`: `skills=` — **сортировка** (все заказы в выдаче, match выше), не OR-фильтр |
| e2b-5 | Приёмка: `yandex_direct` не `яндекс.директ`; tilda вне пула → `pending_tags`; каталог в API |

**Файлы:** `docs/team/architect/AI.md`, `src/ai_analyze.py`, `src/pg_storage.py`, `src/api_server.py`, `src/rank.py`, `sql/` (миграция `pending_tags`), опц. `src/keyword_match.py`

| # | Готово когда |
|---|----------------|
| s1 | `_validate_reply_draft_take` / `_maybe`: **не** `raise` по `n < 4` / `n > 8` / `n < 2` — только пустой draft + `_validate_reply_draft_base` (стоп-слова) |
| s2 | Если `n` вне целевого диапазона — **всё равно** слать в TG; в `errors[]` / `neon:skip` **не** skip; опц. `warn:reply_draft_sentences=N verdict=…` в лог (не блокер) |
| s3 | Промпт `_LEGACY_SYSTEM` — «стремись к N предложениям», не «иначе пусто» |
| s4 | `AI.md` § dogfood — как выше (Lead уже правит канон) |

**Не менять:** skip при пустом draft, МИМО, `ai_unavailable`. `/lenta/` не трогать.

**Файлы:** `src/ai_analyze.py`, `src/lead_pipeline.py` (только warn в errors), `docs/team/architect/AI.md`

**Файлы:** `wordpress/rawlead-kadence-child/assets/js/rawlead-feed.js`, `wordpress/rawlead-kadence-child/assets/js/rawlead-cabinet.js`, `wordpress/rawlead-kadence-child/assets/css/rawlead.css`, `wordpress/rawlead-kadence-child/page-lenta.php`, `wordpress/rawlead-kadence-child/page-cabinet.php`, `src/api_server.py`, `docs/team/common/STATUS.md`

## E — Не в этом спринте (→ Design/Product)

| Тема | Кто | Когда |
|------|-----|--------|
| UI/UX панели фильтров, mobile, визуал % | **@lead-designer** → @coder | § **PRE-LAUNCH-UX**, **перед** P5 |
| Копирайт кнопок, подсказки | **@lead-product** | вместе с Design |

**Не делать в § PRE-LAUNCH:** полный биллинг; 25 источников; редизайн лендинга.

---

# § PRE-LAUNCH-UX — UI перед хостингом (**✅ E5 код Lead 2026-05-28 · приёмка ⏳**)

**Порядок (владелец 2026-05-27):** E0 Coder A–D → E1 ЛК → **E2 SKILLS-TOOLS-RESEARCH** (Product) → **E3 Design** (спор до идеала) → **E4 Product copy** → **E5 Coder вёрстка** → P5/stress.

**Не начинать u2 до:** `LEAD_PRODUCT_PROMPT` § SKILLS-TOOLS-RESEARCH r1–r5 + согласованный макет `LEAD_DESIGN_PROMPT` § PRE-LAUNCH-UX v2.

| # | Готово когда |
|---|----------------|
| u0 | ✅ Product § SKILLS-TOOLS-RESEARCH — `SKILLS_TOOLS_CATALOG.md` v0.2 |
| u1 | ✅ Design REVOLUTION — `REFERENCE.md` v3, `feed-cabinet-mvp.md` v2, `DESIGNER_PROMPT.md` |
| u2 | ✅ Product copy c1–c4 — [`LEAD_PRODUCT_PROMPT.md`](../product/LEAD_PRODUCT_PROMPT.md) § «Канон строк PRE-LAUNCH-UX copy» |
| u3 | ✅ REVOLUTION `rawlead.css` + c1–c4 в PHP/JS |
| u4 | UI modal ✅ · **POST endpoint** — отдельная задача (не блокер приёмки E5) |
| u5 | ✅ `loadCatalog()` → `/v1/skills/catalog` |

**Промпт Design:** [`LEAD_DESIGN_PROMPT.md`](../design/LEAD_DESIGN_PROMPT.md) § PRE-LAUNCH-UX v2.

---

# § OWNER-UX-POLISH — правки владельца (2026-05-28, **→ @coder**, после E5)

**Контекст:** приёмка E5 — визуальные доработки лендинга + `/lenta/` + `/how/`. Без новых фич.

| # | Задача | Файлы | Готово когда |
|---|--------|-------|--------------|
| o1 | **«Для кого» + «Тариф»** — меньше пустоты сверху: уменьшить `padding-top` / `margin-top` у секций (заголовок «Для кого» ближе к карточкам) | `rawlead.css` — `.rl-audience`, `#pricing-preview.rl-section` | визуально плотнее, без лишнего зазора |
| o2 | **«Как устроено»** — убрать горизонтальный скролл-ленту; статичная **grid** 1 col mobile / 3 col desktop; убрать строку «Свайп влево — следующий шаг» | `features.php`, `rawlead.css` — `.rl-features-scroll`, `.rl-features-track` | всё видно без свайпа, листаешь вниз |
| o3 | **«Как устроено»** — убрать крупные «призрачные» цифры 01–03 (`.rl-feature__ghost`); текст разбора **меньше** (`font-size` ~0.9–0.95rem) | `features.php` (опц. убрать span ghost), `rawlead.css` | нет дублей/чёрных огромных цифр |
| o4 | **Кубики FL / Kwork / TG** — при скролле **собираются** (уже есть в `rawlead-scroll.js` + CSS); при **hover** на куб — лёгкое **покачивание** (wiggle, 2–3°) | `rawlead.css` — `.rl-source-cube:hover` | анимация только hover, не ломать reduced-motion |
| o5 | **Карточка лида** в блоке flow (`.rl-lead-card` рядом с кубиками) — **поднимается** при появлении в viewport (как reveal: `translateY` + тень), не только `:hover` | `rawlead.css`, опц. `rawlead-scroll.js` observe `.rl-lead-card` | карточка «въезжает» при скролле |
| o6 | **«Для кого»** — если есть горизонтальный скролл — заменить на **grid 2×2** (уже grid в CSS; проверить, нет overflow-x) | `audience.php`, `rawlead.css` | без горизонтального скролла |
| o7 | **`/lenta/`** — панели **«Навыки»** и **«Сортировка»** раскрываются **поверх** карточек (не обрезаются). Причина: `overflow` на `.rl-filter-bar__inner` / stacking. `z-index` панелей ≥ 500, `overflow: visible` на bar при `[open]` | `rawlead.css`, опц. `page-lenta.php` | dropdown полностью виден |
| o8 | **`/how/`** — **двойная нумерация**: в `how.html` уже «1. …», CSS добавляет `::before` counter — **убрать** `body.page-how .rl-block-card > h2::before` (или counter в CSS) | `rawlead.css`, опц. `how.html` | один номер шага, без чёрных/дублирующих цифр |
| o9 | **Бонус:** `rawlead-landing/content/home.html` — убрать «Ранний доступ» (см. E4 c4) | `home.html` | — |

**Не делать:** новый горизонтальный скролл; сложные скрипты свайпа; менять API/радар.

**Приёмка владельца:** `wp_install_rawlead_theme.py` → главная + `/lenta/` + `/how/` Ctrl+F5.

---

# § POST-RESTART-CHECK + WP/TG/PROXY (**→ @coder**, часть в § PRE-LAUNCH)

**Контекст владельца:** после перезапуска Site проверить живые логи/уведомления и донастроить продуктовую подачу.

## Задачи

| # | Готово когда |
|---|----------------|
| c1 | Проверка `radar_site.log` после перезапуска: есть циклы бирж, нет критических ошибок, отдельно отчёт по TG (`join/listen/send`) с причиной, если уведомлений нет |
| c2 | TG-каналы: подтвердить, что подписка и listen идут по актуальному allowlist/queue; если нет уведомлений — указать точку обрыва (не подписались / нет chat_id / фильтр / send) и дать фикс |
| c3 | → **§ PRE-LAUNCH C** (L2 подписчик: инструменты + отклик) |
| c4 | → **§ PRE-LAUNCH A** (без Брать/Сомнительно; только match %) |
| c5 | → **§ PRE-LAUNCH-UX** (Design перед хостингом; не блокер A–D) |
| c6 | Прокси для бирж: включить ротацию по спискам прокси (`FL_PROXY_URLS`, `KWORK_PROXY_URLS`) с переключением между IP по циклу/ошибкам и понятным логом «какой прокси выбран» (без секретов) |
| c7 | Обновить `STATUS.md`: коротко «что было не так после перезапуска», «что исправлено», «как проверить владельцу за 10 минут» |

## Файлы

| Путь |
|------|
| `src/main.py` |
| `src/tg_monitor.py` / `scripts/tg_main.py` |
| `src/telegram_notify.py` |
| `src/ai_analyze.py` |
| `src/lead_pipeline.py` |
| `src/fl_parser.py` |
| `src/kwork_parser.py` |
| `wordpress/rawlead-kadence-child/assets/js/rawlead-feed.js` |
| `wordpress/rawlead-kadence-child/assets/js/rawlead-cabinet.js` |
| `wordpress/rawlead-kadence-child/assets/css/rawlead.css` |
| `wordpress/rawlead-kadence-child/page-lenta.php` |
| `wordpress/rawlead-kadence-child/page-cabinet.php` |
| `docs/team/common/STATUS.md` |

**Не трогать:** LEGACY-поток (`FILTERS_LEGACY`, consumer) без отдельного запроса владельца.

---

# § NEON-DEDUP-REPLAY — Dup не должен убивать L1 (**→ сейчас**, Lead 2026-05-27)

**Симптом:** Site `main` крутится, в логе `новых N │ dup N`, в Neon **нет новых** строк и **нет** L1 на вчерашних лидах; `/lenta/` пустая при живой бирже.

**Причина (канон):** `neon_ingest_wide` → `INSERT` в Neon → `FILTERS_SITE` → при стопе **выход без L1**. Позже тот же текст → `ON CONFLICT (content_hash)` → **ранний return** в `plan_new_listing` **без** `update_after_lite`. Категория `design` **не участвует** в dedup — только `listing_content_hash(title, snippet)`.

## Задачи

| # | Готово когда |
|---|----------------|
| r1 | **Dup + нет L1:** если `record_new_lead` вернул `False` (dup), загрузить строку из Neon по `content_hash` или `(source, external_id)`. Если `ai_verdict` / `ai_score` **NULL** — **не** `return` сразу: пройти `FILTERS_SITE` → L1 → `update_after_lite` (как для новой вставки) |
| r2 | **Dup + L1 уже был:** оставить короткий путь (не дублировать платный L1 без флага) |
| r3 | **Опц. one-shot:** `scripts/replay_neon_lite_site.py` — `--dry-run` / `--limit N`: SELECT `leads` WHERE `ai_verdict IS NULL` AND `source` ∈ `PUBLIC_FEED_SOURCES` → filter + `analyze_lite` + `update_after_lite` |
| r4 | **Не ломать** legacy consumer: он читает Neon; replay только **site** профиль / биржи+TG из allowlist |
| r5 | Приёмка: после Site ▶ 30 мин в Neon есть строки с `created_at` **сегодня** **или** обновлённые `ai_verdict` у старых design; `/lenta/` — карточки с «Суть задания»; в логе есть `neon_replay` / отдельный счётчик (см. LOG-NEON-CYCLE) |

**Не делать:** снимать `content_hash` UNIQUE; писать ingest с legacy; менять `FILTERS_LEGACY.md`.

## Файлы

| Путь |
|------|
| `src/lead_pipeline.py` |
| `src/pg_storage.py` |
| `src/radar_cycle_log.py` |
| `scripts/replay_neon_lite_site.py` (новый, если r3) |
| `docs/team/common/STATUS.md` |

---

# § LOG-NEON-CYCLE — Понятный лог Site (**→ с NEON-DEDUP-REPLAY**)

| # | Готово когда |
|---|----------------|
| l1 | В `SourceCycleStats` / футере цикла отдельно: `neon_insert`, `neon_dup_replay` (dup, догнали L1), `neon_dup_skip` (dup, L1 уже был) — **не** один общий `dup` |
| l2 | Футер: `Итого в бот: N │ neon_insert: X │ neon_replay: Y` — убрать вводящую в заблуждение копию «на сайт = в бот» или явно подписать «лента после L1» |
| l3 | Ошибки `pg:record:*` / `pg:lite:*` — по-прежнему в `errors[]`, в «Прочее» цикла если не skip |

## Файлы

| Путь |
|------|
| `src/radar_cycle_log.py` |
| `src/main.py` |
| `docs/ops/RADAR_LOG.md` |

---

# § FEED-DECOUPLE — Лента = `is_visible`, не `notified_at` (**P0**, решение владельца 2026-05-27)

**Проблема:** сейчас `/v1/feed` (и значит WP `/lenta/`) зависит от `notified_at`, который ставится только после успешной отправки TG. Любой сбой TG/ИИ превращает ленту в пустоту, хотя Neon наполнен.

**Решение (канон):**

- **Лента (public feed)**: `WHERE is_visible = TRUE` + фильтр `PUBLIC_FEED_SOURCES`
- `notified_at` остаётся **только** как тех.метка “уведомление в TG отправлено”

## Задачи

| # | Готово когда |
|---|----------------|
| f1 | В `src/api_server.py` заменить `_BOT_FEED_WHERE` с `is_visible = TRUE AND notified_at IS NOT NULL` на `is_visible = TRUE` |
| f2 | Проверка: `GET /v1/feed?limit=5` возвращает лиды даже если `notified_at IS NULL` |
| f3 | WP `/lenta/` показывает `is_visible=true` по Neon без зависимости от TG |

## Файлы

| Путь |
|------|
| `src/api_server.py` |
| `wordpress/rawlead-kadence-child/inc/rawlead-api.php` (не требуется менять, только проверка) |
| `docs/ops/RUN.md` (при необходимости обновить формулировку “лента: is_visible”) |

---

# § SITE-AI-FALLBACK — “ИИ недоступен” не должен превращать Site-бот в спам (**P0**, решение владельца 2026-05-27)

**Симптом:** при `AI недоступен` Site шлёт MVP-карточки, которые “не по фильтрам”, потому что L1 не отработал, а `FILTER_WIDE=1` пропускает всё кроме стопа.

**Решение (канон):**

- По умолчанию: **если L1 недоступен**, **не отправлять** в @rawlead_bot (только лог/счётчик).
- Исключение: отдельный флаг `.env.site`, напр. `SITE_NOTIFY_ON_AI_UNAVAILABLE=1` (opt-in для отладки).

## Задачи

| # | Готово когда |
|---|----------------|
| a1 | В `src/lead_pipeline.py`/`telegram_notify.py`: Site-уведомление при `ai_unavailable` управляется флагом; по умолчанию = **не слать** |
| a2 | В логе цикла отдельный счётчик `ai_unavailable` (чтобы видеть проблему без спама в TG) |
| a3 | Приёмка: при искусственном падении L1 (невалидный ключ) — в логах видно `ai_unavailable`, но TG не заспамлен |

## Файлы

| Путь |
|------|
| `src/lead_pipeline.py` |
| `src/config.py` (если нужен новый env-флаг) |
| `src/telegram_notify.py` |

---

# § P5-PREP — Перед деплоем (из аудита, узко) (**→ после NEON-DEDUP-REPLAY**)

**Не тащить весь аудит Gemini** — только под [`PRE_PROD_GATE.md`](PRE_PROD_GATE.md) и решение владельца по хостингу.

| # | Готово когда | Когда |
|---|----------------|--------|
| h1 | `RADAR_CORS_ORIGINS` в `.env` / `radar_control` — не `*` если API доступен не с localhost | P5 / API наружу |
| h2 | Дочерние `main`/`tg_main`: stdout/stderr в файл профиля (не только `DEVNULL`), ротация по размеру | VPS / 24/7 |
| h3 | Locks: `filelock` или `fcntl` fallback **если** владелец подтвердил **Linux VPS** для радара | P5 Linux |
| h4 | `process_guard` — **без** регрессии P1.H; любое смягчение — с тестом «2× main не появляется» | По тикету |
| h5 | Tauri `capabilities` — сузить HTTP до `127.0.0.1:18765/18775/18766` | Сборка пульта перед прод |

**Отложено (не блокер dogfood на Windows):** `sys.path.insert` рефакторинг; лог прокси; `_OWNER_USER_ID` в env.

## Файлы

| Путь |
|------|
| `scripts/radar_control.py` |
| `src/process_guard.py` (только с h4) |
| `desktop/src-tauri/capabilities/default.json` |
| `.env.example` |
| `docs/ops/DEPLOY_VPS.md` (если есть — дописать h1–h3) |

---

# § S-SPLIT — Два контура: LEGACY + SITE (владелец 2026-05-27)

**Решение:** жёсткое разграничение. Старый бот работает как сейчас. Новый бот — сайт и подписка. Отдельные ключи OpenRouter.

## Как выглядит для владельца

1. **LEGACY** — ярлык «Радар Legacy», пульт :18765, старый бот, фильтры **не меняются** при тюнинге сайта.
2. **SITE** — ярлык «Радар Site», пульт :18775, **новый** бот; ты регистрируешься через `/cabinet/` и тестируешь как подписчик.
3. Деньги LLM: **два ключа** OpenRouter — в `.env.legacy` и `.env.site`.

## Задачи Coder

| # | Готово когда |
|---|----------------|
| s1 | `RADAR_PROFILE=legacy|site` в config; загрузка `.env.legacy` / `.env.site` (или `--profile`) |
| s2 | `docs/ops/FILTERS_LEGACY.md` — **копия текущего** `FILTERS.md` на момент split; **не править** при SITE-тюнинге |
| s3 | `docs/ops/FILTERS_SITE.md` — фильтры для сайта (F-LOCAL); `filters.py` читает файл по профилю |
| s4 | Логи: `data/radar_legacy.log` / `data/radar_site.log`; lock-файлы с суффиксом |
| s5 | Пульт SITE: `radar_control` на **другом порту** (напр. 18775), отдельный ярлык VBS |
| s6 | SITE: `TELEGRAM_BOT_TOKEN` + `OPENROUTER_API_KEY` (или `AI_API_KEY`) из `.env.site` |
| s7 | LEGACY: pipeline **без** L1/L2 split — один `analyze_project` как до F-LOCAL (или флаг `AI_MODE=legacy`) |
| s8 | SITE: L1 → лента, L2 → подписчики (новый бот); LEGACY — без изменений поведения |
| s9 | `.env.example` — шаблоны обоих профилей; `FOR_YOU.md` — два ярлыка |

**Не делать:** один `.env` на оба бота; правка `FILTERS_LEGACY` при задаче SITE; один пульт без метки профиля.

**Приёмка:** LEGACY 24 ч без регрессии; SITE — новый бот шлёт L2, `/lenta/` с `task_summary`.

---

# § S-SPLIT-DUAL — Оба пульта ▶ одновременно (**→ сейчас**, владелец 2026-05-27)

**Зачем:** Legacy = **брать заказы** (@FLPARSINGBOT). Site = **продукт** (лента, TG, @rawlead_bot). Оба работают **вместе**, не «или-или».

| Контур | ▶ поднимает | Куда заказы | Биржи FL/Kwork/FH |
|--------|-------------|-------------|-------------------|
| **Legacy** | **не** `main` (см. NEON-DATA) | @FLPARSINGBOT | **нет** — читает Neon |
| **Site** | `main` + `tg_main` | @rawlead_bot + `/lenta/` | **да** — **единственный** парсер бирж |

| # | Готово когда |
|---|----------------|
| d1 | Site **с** `main` (§ NEON-DATA); Legacy **без** spawn `main` |
| d2 | Legacy: `RADAR_TG_ENABLED=0` — без `tg_main` |
| d3 | Сервер: Site ▶ 24/7; Legacy ▶ только consumer (ПК по желанию) |
| d4 | ~~два парсера~~ **отменено** |
| d5 | `kill_non_venv` — один venv на роль |
| d6 | `FOR_YOU.md` — один круглосуточный радар на сервере |

**Не делать:** два `main.py` на биржи; Legacy `record_new_lead` (только Site пишет Neon).

---

# § S-SPLIT-NEON-DATA — Один парсер → Neon; Legacy читает (**→ сейчас**, владелец 2026-05-27)

**Решение владельца (уточнение):** биржи качает **только Site** (сервер 24/7). Legacy **не парсит** FL/Kwork/FH — **подбирает из Neon** по `FILTERS_LEGACY.md` + legacy ИИ → @FLPARSINGBOT. SQLite legacy — только «уже слал в бот».

```text
Сервер 24/7:  Site main + tg → Neon (все новые вакансии с бирж)
              → FILTERS_SITE + L1 → is_visible /lenta/

ПК (опц.):    Legacy consumer → Neon (read) → FILTERS_LEGACY → ИИ → FLPARSING
              SQLite: дедуп «уже в бот»
```

| Контур | Парсит биржи | Neon | Фильтр |
|--------|--------------|------|--------|
| **Site** | **да** (`main`, `.env.site`) | **пишет** | `FILTERS_SITE` + L1 → лента |
| **Legacy** | **нет** | **читает** | `FILTERS_LEGACY` + legacy ИИ → бот |

| # | Готово когда |
|---|----------------|
| n1 | `RADAR_EXCHANGES_ENABLED=0` + **не** spawn `main` в `.env.legacy` / legacy `radar_control` |
| n2 | `RADAR_EXCHANGES_ENABLED=1` в `.env.site`; Site spawn `main` + `tg_main`; `DATABASE_URL` только `.env.site` |
| n3 | **Ingest широкий:** в Neon попадают **новые** листинги с бирж **до** жёсткого отсева Site (или `FILTER_WIDE=1` + только стоп); иначе Legacy не увидит то, что Site отрезал словами |
| n4 | **Legacy consumer:** cron/цикл `legacy` — SELECT новых из Neon → `FILTERS_LEGACY` → `analyze_project` → TG; поле/флаг `legacy_notified_at` (или SQLite), **не** второй парсинг |
| n5 | `.env.legacy`: `DATABASE_URL` = **read** тот же Neon (read-only user ок) **или** read через API — на выбор Coder; **не** писать ingest с legacy |
| n6 | `FOR_YOU.md` / `PROJECT_MAP` — схема выше |

**Фильтры:** см. § **F-SITE-FILTERS-0i** (Site ≠ LEGACY). Ingest в Neon — широкий (`neon_ingest_wide`).

**Не теряем:** те же вакансии с FL/Kwork/FH в Neon, если n3 соблюдён. **Теряем** только то, что Site выкинул **до** записи в Neon — поэтому n3 обязателен.

**Не делать:** два `main` на биржи; отключать Site `main` «чтобы не дублировать» — дублирование снимается **одним** парсером.

**Приёмка:** Site 24 ч — Neon растёт, `/lenta/` живая; Legacy consumer — в бот приходят заказы по **FILTERS_LEGACY**, без `main` legacy на биржах.

**P5:** после n1–n5 + § F-SITE-FILTERS-0i. Прокси Site — опционально позже.

---

# § F-SITE-FILTERS-0i — FILTERS_SITE под аудиторию §0i (**→ сейчас**, PM 2026-05-27)

**Канон Product:** [`LEAD_PRODUCT_PROMPT.md`](../product/LEAD_PRODUCT_PROMPT.md) § «FILTERS_SITE — критерии для /lenta/».

| # | Готово когда |
|---|----------------|
| f0 | `FILTERS_SITE.md` **≠** клон LEGACY: убрать из **стопа** Site токены дизайн/маркетинг (таблица PM); `FILTERS_LEGACY.md` **не менять** |
| f1 | «Берём» Site — 4 ниши §0i (блоки уже в шаблоне — сверить с PM) |
| f2 | Site ingest: `neon_ingest_wide` + после правки стопа — L1 доходит до дизайн/маркетинг карточек |
| f3 | `MIN_AI_SCORE` site: 40 код / 50 нетех — по PM (`ai_analyze.py` / `AI.md`) |
| f4 | Приёмка: заказ с «figma»/«таргет» в title → в Neon → `is_visible` после L1 на `/lenta/`; Legacy consumer — тот же заказ **может** не идти в FLPARSING (стоп LEGACY) |

**Пульт (в этой же задаче):**

| # | Готово когда |
|---|----------------|
| p1 | Legacy ▶: лампа **«Neon»** (consumer), не «Биржи main»; Site ▶: **Биржи** + **TG** |
| p2 | `FOR_YOU.md` / подписи ламп — как § «Два пульта»; после кода — `rebuild-pult.bat` |
| p3 | Site bat: перезапуск API при старте (как site.bat сейчас) — без зомби `main --profile site` |

---

# § S-SPLIT-TG — TG только на SITE (**→ сейчас**, владелец 2026-05-27)

**Решение:** Legacy = **биржи + @FLPARSINGBOT**, **без** Telethon. Site = **acc1–acc3 + join + @rawlead_bot + L1/L2**.

| # | Готово когда |
|---|----------------|
| g1 | `RADAR_TG_ENABLED=0` в `.env.legacy` → `radar_control` **не** spawn `tg_main`; лампа TG серая / «выкл» |
| g2 | `RADAR_TG_ENABLED=1` (default) на site — как сейчас |
| g3 | Два пульта ▶ одновременно **без** дублей TG (только site трогает acc) |
| g4 | `.env.site`: отдельный OpenRouter + `OPENROUTER_MODEL_SUMMARY` / `PREMIUM` (владелец проставил) |

**Не делать:** TG на legacy; один OpenRouter на оба профиля.

---

# § PULT-THEME — Legacy пульт визуально другой (**→ сейчас**, владелец 2026-05-27)

**Зачем:** два пульта на столе — с первого взгляда не перепутать. Site = текущий светлый канон. **Legacy — отдельная тема на выбор Coder** (тёплый/янтарь, тёмный акцент, «инструментальный» вид — без согласования Lead).

| # | Готово когда |
|---|----------------|
| t1 | `data-profile=legacy|site` на `<html>` или `body`; CSS-переменные в `desktop/src/styles/` (legacy ≠ site) |
| t2 | В заголовке пульта бейдж **LEGACY** / **SITE** (не только цвет) |
| t3 | Site-пульт **всегда** API `:18775`: `VITE_RADAR_API` в bat **и** runtime fallback `RADAR_CONTROL_PORT` / query для собранного `RawLead.exe` |
| t4 | Legacy bat не трогает site `radar_control` (уже по profile — проверить) |

**Не делать:** одинаковый UI без метки; site exe на :18765.

---

# § F-PROMPT — Тексты фильтров и промптов (**→ перед / параллельно F-LOCAL**)

**Зачем:** один человек/чат **составляет** слова; другой не выдумывает промпты в коде. Главное — **L2 не дублирует L1** ([`AI.md`](AI.md) § «L1 и L2»).

## § F-RESEARCH — Deep Research для FILTERS (**владелец не пишет стоп-слова**)

**Уже есть:** [`FILTERS_DEEP_RESEARCH_2026.md`](../archive/FILTERS_DEEP_RESEARCH_2026.md) (2026-05-23) — таксономия 20 категорий, ~72 стоп-токена, тест-кейсы §6.

| # | Кто | Готово когда |
|---|-----|----------------|
| r1 | **@coder** (или чат с **Perplexity MCP**, если владелец включил — [`MCP_POOL.md`](../common/MCP_POOL.md)) | Сверить research с **Vision v0.10 §0i** + блок **TG реклама** в [`FILTERS.md`](../../ops/FILTERS.md) § TG |
| r2 | **@coder** | Внести в `FILTERS.md` «Отсекаем» / «Берём» — не с нуля: **merge** archive §3 + v0.10 design/marketing/text + TG |
| r3 | **@coder** | `src/filters.py` = зеркало `FILTERS.md`; опц. `stop_tg` подмножество для listen |
| r4 | **@coder** | Прогон **20 тестов** из research §6 (таблица pass/fail в комментарии к сдаче или `STATUS`) |
| r5 | **Владелец** | Только **1–2 недели dogfood**: «ложный стоп» / «мусор прошёл» — заметки в чат Lead; **не** правка списков руками |

**Опционально r1b:** Perplexity запросы — «TG фриланс чат спам 2025-2026», «FL.ru типовой спам заказов» → 5–10 **новых** фраз в стоп, если нет в archive. Без MCP — только archive + лог `radar.log`.

---

| # | Кто | Готово когда |
|---|-----|----------------|
| p0 | **Владелец** | Только dogfood-заметки (см. F-RESEARCH r5); **не** редактировать `FILTERS.md` |
| p1 | **Автор промптов** (@coder узкий чат *или* владелец+Lead) | В [`AI.md`](AI.md) § L1/L2 — финальные тексты system/user для L1 и L2 |
| p2 | **Автор** | L2 user-шаблон: вставка `verdict`, `task_summary`, `lead_tags` из L1 + полное description |
| p3 | **@coder** | `ai_analyze.py`: `_LITE_SYSTEM` и L2 system **= копия из AI.md**; `analyze_premium(..., lite=...)` передаёт L1 в user |
| p4 | **@coder** | `filters.py` синхрон с `FILTERS.md` (V10.1 + TG) |

**L1 JSON (канон):** `verdict`, `task_summary`, `lead_tags`, `ai_reasons` — **без** `reply_draft`, `approach`, `money`, `risks`, `work_summary`.

**L2 JSON (канон):** `work_summary`, `difficulty`, `approach`, `time_for_client`, `money`, `reply_draft`, `risks`, `lead_tags` — **без** повторного `task_summary` в ответе; verdict не спрашивать.

---

# § F-LOCAL — Фильтры и ИИ на локале (**→ сейчас**, владелец 2026-05-26)

**Цель:** на ПК в ленту и в бот попадает **только нужное**; при большом потоке — **минимум платных вызовов LLM**, как сейчас по духу, но предсказуемо.

**Не делать:** P5 деплой · редизайн концепции (Lead Designer — потом).

### Решения владельца (2026-05-26)

| Тема | Решение |
|------|---------|
| Источники сейчас | Только **проверенные** (3 биржи в env; TG — после подключения) |
| **Дедуп** | ✅ уже есть — `listing_dedup` + `listing_fingerprints` (100%, не трогать логику) |
| **Категория** | Правила в коде, не отдельный LLM |
| **Бот (ты)** | **Подписка / dogfood** — полный **разбор как сейчас** (уведомление с ИИ-полями, черновик при «Брать») |
| **`/lenta/` (публичка)** | **Без** «разбора от бота» — карточка заказа (title, budget, теги, % / чип); не дублировать простыню из TG |
| **TG новые каналы** | Начать: **автоподключение** (как join сейчас) + **фильтр рекламы** в Python до ИИ |
| **ИИ** | См. § **F-LOCAL — два уровня ИИ** (согласование Lead + владелец 2026-05-26): не «2 модели на каждый лид», а **дешёвый ingest + дорогой только в бот** |

## Воронка (порядок, дешёвое → дорогое)

| Этап | Что | Стоимость | Где |
|------|-----|-----------|-----|
| 1 | Стоп-слова + «берём» (`FILTER_WIDE`) | ₽0 | `src/filters.py` ← [`FILTERS.md`](../../ops/FILTERS.md) |
| 2 | Дроп §0i по категориям (VA, диктор, 1С, …) | ₽0 | **V10.1** |
| 3 | Дедуп / fingerprint | ₽0 | `listing_dedup` |
| 4 | Категория `dev/design/…` | ₽0 | `lead_category.py` — **не** в LLM |
| 5 | **Один** короткий вызов OpenRouter на лид | $ | `ai_analyze.py` — title + snippet ≤600 симв |
| 6 | В **бот** (владелец) | — | полный разбор + уведомление при **Брать** |
| 7 | В **`/lenta/`** | — | только карточка; без полного разбора / `reply_draft` в UI |

## Задачи Coder

| # | Готово когда |
|---|----------------|
| f0 | Владелец: `.env` **`PUBLIC_FEED_SOURCES=fl,kwork,freelancehunt`** (без дубля имени в значении) · `FILTER_WIDE` осознанно (`1` = больше в ИИ, `0` = жёстче до ИИ) |
| f1 | **V10.1** — стоп/берём §0i в `filters.py` синхрон с [`FILTERS.md`](../../ops/FILTERS.md) |
| f2 | **P8** — `OPENROUTER_MODEL_SUMMARY` (дешёвая модель), вердикт правилами где можно; промпт без простыни body |
| f3 | Счётчики в `radar.log` (P1.4): доля `filter` / `МИМО` / `dup` — после цикла видно, режет ли Python |
| f4 | **Бот:** только «Брать» → TG с **L2** полным разбором. **`/lenta/`:** в карточке — title, budget, tags, %, **`task_summary`** (L1); **не** сырой `body` целиком; кнопка «На бирже» / ссылка на первоисточник |
| f5 | Кратко в `STATUS.md`: «как крутить FILTERS.md + что смотреть в логе» (3 строки для владельца) |
| f6 | **TG волна:** [`TG_PUBLIC_FEED_ALLOWLIST.txt`](../../ops/TG_PUBLIC_FEED_ALLOWLIST.txt) → join queue v2 (2–3/нед) · listen **только** allowlist · тикет [`2026-05-26-p1-tg-migration-gaps.md`](../../problems/2026-05-26-p1-tg-migration-gaps.md) |
| f7 | **TG реклама:** расширить стоп в `FILTERS.md` + `filters.py` — реклама, промо, курс, «подпишись», «пиши в лс»+оффер, закреп, партнёрка (не резать обычные заказы) |

**Экономия (канон):** [`INGEST_CATEGORY_STRATEGY.md`](INGEST_CATEGORY_STRATEGY.md) §4 — ingest режет мусор словами; при 10k/день — жёсткий стоп (f1).

### Два уровня ИИ (лучше, чем «2 модели на всё»)

**Идея владельца:** дешёвая LLM для ленты, умная — для подписчиков (пока только dogfood-бот).  
**Позиция Lead:** согласен по **смыслу двух уровней**, но **не** два полных прогона на **каждый** лид — иначе при потоке 5–10k/день платим ×2.

| Уровень | Когда | Модель (env) | Что в ответе | Куда |
|---------|--------|--------------|--------------|------|
| **L0** | Всегда до LLM | — | Python стоп, дедуп, `category` правилами | отсев |
| **L1 ingest** | Прошёл L0 | `OPENROUTER_MODEL_SUMMARY` (дешёвая) | `ai_score`, `verdict`, теги; **`task_summary`** — до ~2 предложений «что нужно» (не копипаста body); 2–3 `ai_reasons`; **без** `reply_draft` / архитектуры / L2-простыни | Neon → **`/lenta/`** |
| **L2 premium** | Только **Брать** → уведомление в TG (сейчас владелец; позже JWT `/me`) | `OPENROUTER_MODEL_PREMIUM` или тот же с длинным промптом | полный разбор + черновик отклика | **только бот** / подписчик |

**Лента — без L2-разбора**, но **с L1-кратким смыслом:** заказчики часто пишут «чушь» — в карточке не простыня `body`, а **1–2 предложения «что требуется»** (`task_summary` / `work_summary` короткий); полный текст — **только по ссылке** на биржу/TG. Это **часть L1** (дешевая модель), не вторая модель «для красоты».

**Подписчики позже:** тот же **L2**, не третья модель — триггер «отправить в бот / в кабинет с полным разбором», не второй ingest на всех.

| # | Coder (добавить к f2) |
|---|------------------------|
| ai1 | `analyze_lite()` → L1; `analyze_premium(lite=…)` → L2 только при «Брать» в `send_listing_notification` |
| ai2 | Env: `OPENROUTER_MODEL_SUMMARY`, `OPENROUTER_MODEL_PREMIUM` (fallback: один MODEL) |
| ai3 | Лог/метрика: счётчик L1 vs L2 за цикл; L2 user **содержит** L1, system L2 **запрещает** дубль |
| ai4 | Промпты только из [`AI.md`](AI.md) § L1/L2 после § **F-PROMPT** — не расходиться с каноном |

**Приёмка владельца:** 1–2 дня dogfood — в боте полный разбор; на `/lenta/` — карточки без простыни; в логе L2 ≪ L1.

---

# § P1 — Чистая публичная лента (**→ старт**)

---

# § P1.H — HOTFIX: дубли процессов + красная «Биржи» (✅ принято 2026-05-26, архив)

Тикет: [`docs/problems/2026-05-26-duplicate-workers-regression.md`](../../problems/2026-05-26-duplicate-workers-regression.md) · факты: [`STATUS.md`](../common/STATUS.md) § P1.H

**Следующий Coder:** § **P1.3d** (env биржи) → § **D1** (после Design). Не P1.H.

---

# § P1.3d — Только фриланс-биржи в ленте (✅ принято 2026-05-26, архив)

**Решение:** в публичку — **только биржи**; вакансии позже, **код парсеров не удалять**.

| source | Лента | Код |
|--------|-------|-----|
| `fl`, `kwork`, `freelancehunt` | ✅ | как сейчас |
| `vc_ru`, `habr_career` | ⏸ | парсеры в `src/` оставить; **не** вызывать в цикле, если нет в `PUBLIC_FEED_SOURCES` |
| `habr_freelance` | ❌ | 410, как было |

| # | Готово когда |
|---|----------------|
| b1 | Дефолт / пример env: `PUBLIC_FEED_SOURCES=fl,kwork,freelancehunt` |
| b2 | `run_cycle` / P1.4 лог — строки только для источников из env (3 биржи + итого, не 5) |
| b3 | Канон: [`PUBLIC_FEED_WEB_SOURCES.txt`](../../ops/PUBLIC_FEED_WEB_SOURCES.txt) |
| b4 | **Не** удалять модули `vc_ru` / `habr_career` |

**Владелец:** поправить `.env` (Lead не трогает).

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

**Владелец `.env` (актуально):**  
`PUBLIC_FEED_SOURCES=fl,kwork,freelancehunt`  
(см. § **P1.3d** — `vc_ru` / `habr_career` отложены, парсеры в коде)

**Лог P1.4:** строки только для источников из env (см. P1.3d).

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
| l6 | Debug трейс доставки TG: на каждый кандидат-лид (или хотя бы на `skip`-кейсы) логировать `source/external_id`, `bot_target` (rawlead/FLPARSINGBOT), `stage` (fetch/filter/dedup/ai_notify/ai_skip), `decision` (take/skip/send_fail), `skip_reason`, и флаги `ai_verdict/ai_score/budget_ok` + агрегаты по причинам за цикл |

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

# § D1 — Чипы категорий в `/lenta/` (✅ принято 2026-05-26, архив)

**Спека (принята):** [`feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) §2.1–2.3 — порядок Источник → **Категория** → Бюджет; Handoff: id `filter-category-*`, `name="category"`, query `?category=`.

| # | Готово когда |
|---|----------------|
| d1 | Sidebar + mobile sheet по спеке §2.2–2.3 (5 chips, active `#0A0A0A`) |
| d2 | JS: `GET /v1/feed?category=…`; смена категории → **offset=0**, лента с нуля |
| d3 | Подписи: desktop полные / mobile короткие (Код · Дизайн · SMM · Тексты) — таблица §2.2 |
| d4 | «Сбросить фильтры» снимает category; `/cabinet` — те же чипы (спека Handoff) |

**Не в D1:** регистрация (P4). **Перед D1 или параллельно:** § P1.3d.

---

# § P8 — Дешёвая LLM (summary only)

| # | Готово когда |
|---|----------------|
| m1 | `OPENROUTER_MODEL_SUMMARY` в config |
| m2 | Промпт только title+snippet body |
| m3 | Вердикт: правила или короткий JSON; не GPT-4o на каждый лид |


---

# § P4 — Кабинет: регистрация через Telegram (✅ принято 2026-05-26, архив)

| # | Готово когда |
|---|----------------|
| a1 | `POST /v1/auth/telegram` — body от Login Widget, проверка `hash` ([Telegram docs](https://core.telegram.org/widgets/login#checking-authorization)) |
| a2 | Upsert `users` (tg_id, username, …), JWT `access_token` TTL 7d |
| a3 | `/v1/me/*` — Bearer JWT; убрать 403 для не-owner UUID |
| a4 | WP: кнопка «Войти через Telegram» на `/cabinet/` или отдельная страница; после входа — `localStorage` token → заголовки fetch |
| a5 | `TELEGRAM_LOGIN_BOT_TOKEN` или тот же бот — в `.env.example` |

**Схема:** [`TZ_API.md`](TZ_API.md) · Neon `users` — [`NEON_SCHEMA.md`](NEON_SCHEMA.md)

---

# § PRE-PROD-STRESS — стресс на хосте перед трафиком (**→ после § P5**, владелец 2026-05-27)

**Канон ворот:** [`PRE_PROD_GATE.md`](PRE_PROD_GATE.md) § PRE-PROD-STRESS (S1–S5).

**Когда:** деплой на VPS/хостинг **готов**, URL открывается, **рекламы ещё нет**.

## Задачи

| # | Готово когда |
|---|----------------|
| t1 | `scripts/preprod_ai_matrix.py` — фикстуры по 4 category (≥3 на нишу) → `analyze_lite` + `analyze_premium` → JSON `data/preprod_ai_report.json` (без TG, без парсера) |
| t2 | `scripts/preprod_k6_feed.js` (или `.py` Locust) — 50–100 VU, 5 мин: `GET /health`, `GET /v1/feed?limit=20`, `GET /v1/skills/catalog`; отчёт p50/p95, % ошибок |
| t3 | `scripts/preprod_playwright/` или один spec — prod `BASE_URL`: лента, multi-category, навыки «Применить», `/cabinet/` (smoke login stub ok) |
| t4 | На VPS: Site ▶ 2–4 цикла — в `radar_site.log` время цикла + `ИИ L1=`; в STATUS одна строка baseline |
| t5 | `docs/ops/PREPROD_STRESS_RUN.md` — как запустить t1–t4, пороги S1–S5, красные флаги |

## Файлы (ожидаемые)

| Путь |
|------|
| `scripts/preprod_ai_matrix.py` |
| `scripts/preprod_k6_feed.js` (или `tests/load/…`) |
| `scripts/preprod_playwright/` |
| `docs/ops/PREPROD_STRESS_RUN.md` |
| `docs/team/common/STATUS.md` (блок сдачи) |

**Не делать:** DDoS; 1000× premium OpenRouter; стресс на Legacy consumer без задачи.

**Проверка владельца:** 15 мин `/lenta/` на prod URL; подписать S5 в чат Lead.

---

# § P5 — Деплой бюджет 24/7 (WP shared + VPS API+радар)

**Канон:** [`docs/ops/DEPLOY_BUDGET.md`](../../ops/DEPLOY_BUDGET.md) · владелец: **без ПК**, минимум денег.

**После P5:** § **PRE-PROD-STRESS** (обязательно до трафика).

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
