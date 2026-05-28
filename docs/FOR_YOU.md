# Для тебя

**Полная карта docs:** [`README.md`](README.md)

| Вопрос | Файл |
|--------|------|
| **Что делать сейчас?** | Ниже «Твои шаги» |
| **Как это работает?** | [`KAK_ETO_RABOTAET.md`](KAK_ETO_RABOTAET.md) |
| **Фазы / приоритет** | [`team/architect/ROADMAP.md`](team/architect/ROADMAP.md) · vision **v0.11** (590–990 ₽, Plan B) |
| **Все твои решения для Lead** | [`team/architect/OWNER_INTENT.md`](team/architect/OWNER_INTENT.md) |
| **План Product** | [`team/product/LEAD_PRODUCT_PROMPT.md`](team/product/LEAD_PRODUCT_PROMPT.md) |
| **Запуск** | [`ops/RUN.md`](ops/RUN.md) |
| **Пульт** | [`ops/DESKTOP_LAUNCH.md`](ops/DESKTOP_LAUNCH.md) |
| **Перед продом (стресс на хосте)** | [`team/architect/PRE_PROD_GATE.md`](team/architect/PRE_PROD_GATE.md) § PRE-PROD-STRESS |
| **TG acc + @FLPARSINGBOT** | [`ops/TELEGRAM_ACCOUNTS.md`](ops/TELEGRAM_ACCOUNTS.md) |
| **Схема (картинка)** | [`design/rawlead/project-map-owner.png`](design/rawlead/project-map-owner.png) |

Роли: `@lead-architect` · `@coder` · `@mechanic` · `@designer` — см. [`README.md`](README.md) § по роли.

---

## Два радара (legacy + site)

| Ярлык | Профиль | Бот | Зачем |
|-------|---------|-----|--------|
| **Радар Site** (VPS 24/7, E2) | `site` | [@rawlead_bot](https://t.me/rawlead_bot) | **Парсит** биржи + TG → Neon → `/lenta/` |
| **Dogfood Legacy** (VPS 24/7, E2b) | `legacy` | @FLPARSINGBOT | **Читает Neon** → карточки тебе; **/status /pause** в боте |

- Фильтры **разные файлы**: `FILTERS_SITE.md` (лента) vs `FILTERS_LEGACY.md` (твой бот)
- **Один парсер** на сервере (Site ▶); Legacy — отбор из той же Neon, SQLite «уже слал»
- `SITE_NOTIFY_OWNER=0` (по умолчанию): Site **не шлёт** owner-уведомления в TG; биржи владельцу идут только через Legacy consumer
- OpenRouter: **два ключа** — legacy и site
- **Ты = подписчик #0:** после PRE-PROD — `/start` @rawlead_bot → `/cabinet/` → L2 «Написать отклик» → потом оплата (§ `3f-OWNER-BETA` в `CODER_PROMPT.md`)

**Legacy ▶ сам гасится?** Это **баг** (не «так надо»): [`OWNER_INTENT.md`](team/architect/OWNER_INTENT.md) § «Legacy сам гасится». После обновления: `rebuild-pult.bat` → full stop → ▶ Legacy 2 мин. Для ленты достаточно **Site ▶**.

Подробно: [`team/common/PROJECT_MAP.md`](team/common/PROJECT_MAP.md) § «Два контура» · **частота и L1/L2:** [`KAK_ETO_RABOTAET.md`](KAK_ETO_RABOTAET.md) § «Как часто» / «L1 и L2»

### Какой `.env` правильный?

| Файл | Когда используется | Что хранить |
|------|-------------------|-------------|
| **`.env`** | Всегда (вторым слоем) | **Общее:** Neon, Telethon, FL/Kwork URL, прокси (**Freelancehunt снят** 2026-05-28) |
| **`.env.legacy`** | Ярлык **Legacy** / `--profile legacy` | **@FLPARSINGBOT**, `RADAR_*` legacy, `FILTERS_LEGACY`, свой OpenRouter |
| **`.env.site`** | Ярлык **Site** / `--profile site` | **@rawlead_bot**, `RADAR_*` site, `FILTERS_SITE`, `TG_JOIN_QUEUE_v2`, свой OpenRouter, `RAWLEAD_API_KEY` |

**Не путать:** бот и `TELEGRAM_CHAT_ID` — **в профильном файле**. В `.env` ботов больше нет (только shared).  
**Site-бот:** напиши `/start` в ЛС [@rawlead_bot](https://t.me/rawlead_bot) — иначе `chat not found` в логе.

---

## TG — коротко

| Факт | Деталь |
|------|--------|
| Бот | [@FLPARSINGBOT](https://t.me/FLPARSINGBOT) — карточки **тебе** |
| Чтение чатов | 3 session-аккаунта (Telethon), **не** телефоны |
| Пересылка | acc → бот → твой чат · `/start` acc — **только код** (§ F) |
| Listen / join | [`ops/TG_JOIN_QUEUE.csv`](ops/TG_JOIN_QUEUE.csv) · [`ops/SOURCES_POOLS.md`](ops/SOURCES_POOLS.md) |

Подробнее TG: [`KAK_ETO_RABOTAET.md`](KAK_ETO_RABOTAET.md) · тикеты: [`problems/2026-05-24-tg-acc-bot-start.md`](problems/2026-05-24-tg-acc-bot-start.md)

---

## Запуск пульта

| Ярлык (создай на рабочем столе) | Скрипт | Пульт API |
|----------------------------------|--------|-----------|
| **RawLead Legacy** (ярлык на столе) | `scripts\start-radar-desktop-legacy.vbs` | `http://127.0.0.1:18765` |
| **RawLead Site** (ярлык на столе) | `scripts\start-radar-desktop-site.vbs` | `http://127.0.0.1:18775` |

Старый ярлык **FL Radar** заменён на **RawLead Legacy**.

1. После обновления Coder: `scripts\rebuild-pult.bat` → ярлык запускает **`desktop.exe`** (свежий), не старый `RawLead.exe` от 25.05.
2. Двойной клик на нужный ярлык → подождать **5 с**.
3. Пульт открылся, нет красного баннера → ▶ один раз.
4. Legacy: бейдж **LEGACY**, янтарь, TG «выкл». Site: бейдж **SITE**, TG живая.

**Не открывается:** `scripts\start-radar-desktop-legacy-debug.bat` — увидишь ошибку в консоли.

`.env.legacy` / `.env.site` уже на ПК. Site: @rawlead_bot. Второй ключ OpenRouter — по желанию (пока может быть тот же).

**Не запускай** `start-radar-full.bat` и `python tg_main` вручную — дубли ломают бота.

## Откуда дубли (ты ничего «лишнего» не делаешь — так устроен пульт)

| Что ты делаешь | Что реально остаётся в Windows |
|----------------|--------------------------------|
| Ярлык → **VBS** → bat | Поднимается **`radar_control.py`** (фон, без окна) + окно **`desktop.exe`** |
| Закрываешь пульт **крестиком ✕** | Окно закрывается, вызывается **Stop** воркеров — но **`radar_control` часто остаётся жить** в фоне |
| Снова ярлык | Bat пытается убить старый API и поднять новый — если остался **старый** API на **system Python** (с прошлых запусков), получаешь **два** `main.py` / два `radar_control` |
| Два ярлыка (Site + Legacy) | Это **норма**: два API (`:18775` и `:18765`). Плохо, если **на один профиль** два python (`.venv` **и** `Python311`) |

**Частая ошибка ярлыка:** «Объект» указывает на **`desktop.exe`** или старый **`RawLead.exe`**, а не на **`start-radar-desktop-site.vbs`**. Тогда bat с `kill_all` **не вызывается**, остаётся зомби-API с system Python.

**Проверка ярлыка (10 сек):** ПКМ ярлык → **Свойства** → **Объект** должен заканчиваться на:
- `...\uisness\scripts\start-radar-desktop-site.vbs` — Site
- `...\uisness\scripts\start-radar-desktop-legacy.vbs` — Legacy  

**Не** `desktop.exe` / **не** `start-radar-desktop.bat` (если не знаешь зачем консоль).

### Полный стоп перед запуском (сделай так)

`scripts\stop-radar.bat` **не убивает** `radar_control` (только воркеры) — из‑за этого и копятся зомби.

1. Закрой все окна пульта (✕) — пульт сам шлёт `/shutdown` и гасит API **своего** профиля.
2. **Полный стоп site + legacy** — двойной клик **`scripts\stop-radar-desktop-full.vbs`** (без окна) или bat с консолью. Убивает оба `radar_control` и все воркеры.
3. Подожди 3 с → **один** двойной клик по ярлыку **Site** (или Legacy) → 5 с → **▶ один раз**.
4. Второй профиль (если нужен) — **другой** ярлык, снова ▶ один раз.

Пока в диспетчере на **один** профиль два `python` (`.venv` + `Python311`) — пиши Lead → **@coder** § SITE-BAT-VENV b7–b9.

**Два пульта — как ты работаешь (цель):**

| | **Legacy ▶** | **Site ▶** |
|---|--------------|------------|
| Зачем | **Брать заказы** | **Продукт** (лента, TG, кабинет) |
| Биржи → Neon | Site `main` (24/7) | — |
| Биржи → бот | Legacy consumer → @FLPARSINGBOT | ❌ (только Neon + `/lenta/`) |
| TG → бот | ❌ | ✅ → @rawlead_bot (owner, если `SITE_NOTIFY_OWNER=1`) |
| Оба ▶ вместе | **да** — Site `main`+`tg_main` + Legacy consumer (без второго `main`) |

**Режим «оба ▶»:** Site ▶ — парсит биржи → Neon + TG. Legacy ▶ — читает Neon → @FLPARSINGBOT (лампа **Neon** = consumer, не биржи). Один парсер бирж.

**Биржи:** только Site (`main` + `RADAR_EXCHANGES_ENABLED=1` в `.env.site`). Legacy — `neon_legacy_consumer` из Neon, не `main`.

**@rawlead_bot /start** — на проде, полный путь регистрации как пользователь.

**Если в `/cabinet/` пустой Telegram Widget (серый блок):**

1. В `wp-config.php` добавь `RAWLEAD_TG_LOGIN_FALLBACK_URL` (прямой Telegram OAuth/deep-link URL для `rawlead_bot` с возвратом на `http://127.0.0.1:10007/cabinet/`).
2. Открой `/cabinet/` на `127.0.0.1` и нажми **«Войти через Telegram (fallback)»**.
3. После возврата на `/cabinet/` токен сохранится автоматически, и откроется кабинет.

**Join в новые 19 каналов (Site ▶):** как в [`ops/TG_JOIN_SCHEDULE.md`](ops/TG_JOIN_SCHEDULE.md) — до **4 в час** на acc, пауза **15–20 мин**, **ночью 02:00–07:00 Irkutsk join не идёт**. Очередь: `TG_JOIN_QUEUE_v2.csv` (`pending` → `done` автоматически в `tg_main`).

## Если пульт не ответил («API не отвечает»)

**После `stop-radar-desktop-full.vbs` порт пустой — это норма.** `Invoke-WebRequest …/health` сразу после стопа **всегда** «не соединиться». Сначала подними API (п.3–4), **потом** health.

1. Закрой пульт (✕).
2. **Полный стоп** — `scripts\stop-radar-desktop-full.vbs`. `stop-radar.bat` один — **недостаточно**.
3. Удали lock: `data\.radar_desktop_legacy.lock` / `data\.radar_desktop_site.lock` (если есть).
4. Ярлык **только .vbs** → подожди **8 с** → проверь health → ▶ **один раз**.

**Обход** (PowerShell из `uisness`, если VBS не поднял API):

```powershell
$wd = (Get-Location).Path
Start-Process "$wd\.venv\Scripts\pythonw.exe" -ArgumentList "$wd\scripts\radar_control.py","--profile","site" -WorkingDirectory $wd -WindowStyle Hidden
Start-Process "$wd\.venv\Scripts\pythonw.exe" -ArgumentList "$wd\scripts\radar_control.py","--profile","legacy" -WorkingDirectory $wd -WindowStyle Hidden
Start-Sleep 5
Invoke-WebRequest http://127.0.0.1:18775/health -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:18765/health -UseBasicParsing
```

Оба `{"ok": true}` → открой пульты (VBS) → ▶.

**Аварийный старт воркеров** (если ▶ красный, API жив):

```powershell
cd C:\Users\hramo\uisness
.\.venv\Scripts\python.exe scripts\radar_spawn_workers.py --profile site
```

**Как не сломать снова:** [`ops/DESKTOP_LAUNCH.md`](ops/DESKTOP_LAUNCH.md) § «Антирегресс: пульт / API / ▶» · тикет [`problems/2026-05-27-pult-start-killed-api.md`](problems/2026-05-27-pult-start-killed-api.md).

## Остановить радар / спам «Статус» в Telegram (сейчас)

**Полный стоп (канон):**

1. `scripts\stop-radar-desktop-full.vbs` — гасит site + legacy: `radar_control`, `main`, `neon_legacy_consumer`, `tg_main`, join.
2. Закрой окна пульта (✕). Проверка: в `data\radar_site.log` и `data\radar_legacy.log` **нет** новых строк с текущим временем; в диспетчере задач **нет** `neon_legacy_consumer` / `main.py` / `tg_main`.

**Если процессы остались** — PowerShell из корня `uisness`:

```powershell
Get-CimInstance Win32_Process | Where-Object {
  ($_.Name -eq 'python.exe' -or $_.Name -eq 'pythonw.exe') -and $_.CommandLine -like '*uisness*'
} | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

**Если спам в TG не прекращается за 1–2 мин:**

1. **Заглуши** чат @FLPARSINGBOT (Mute 8 ч).
2. **Не жми ▶** и **не открывай** ярлыки Site/Legacy — пульт снова поднимет consumer.
3. PowerShell (ещё раз, см. выше).
4. Дождись тишины в TG, затем один VBS → один ▶.

**Только пауза ■ в пульте** — воркеры стоп, но **не** полный kill API/consumer; для тишины в TG — `stop-radar-desktop-full.vbs`.

**Спам вкладки «Статус» в пульте** (не Telegram): открытая панель логов дергает `/status-text` каждые ~1.5 с — сверни лог или закрой пульт.

**Не жми** ℹ «Статус» в боте без нужды — каждое нажатие = одна простыня в ЛС.

---

## Что попадает в ленту `/lenta/` (Site)

| Этап | Куда | Что видишь |
|------|------|------------|
| Биржи FL + Kwork | Site `main` → Neon | footer: `neon_insert`, `ИИ L1=…` |
| Фильтр слов | `FILTERS_SITE` | `filter` / `МИМО` в логе |
| L1 (OpenRouter) | Neon `is_visible`, score | карточка на сайте |
| L2 + TG владельцу | по навыкам / бот | **биржи Site в @rawlead_bot не шлют** (split) |
| Legacy | Neon → @FLPARSINGBOT | Полный разбор + **черновик** (Брать 4–8 предл., Сомнительно 2–4 предл.); **не** в `/lenta/` — там только L1 без простыни ИИ |

**После правки промпта legacy (Coder):** `scripts\stop-radar-desktop-full.vbs` → ярлык **RawLead Legacy** → ▶ **один раз** (иначе consumer на старом коде в памяти).

**Смотреть:** `data\radar_site.log` (вкладка **radar** в пульте или файл) — строки `FL.ru │`, `Итого в бот: 0` на биржах **норма** для Site.

### Как часто (коротко)

| Что | Как часто |
|-----|-----------|
| FL + Kwork | **~1 мин** (конвейер в `.env.site`) |
| TG-чаты | **сразу** при новом посте (не по минутам) |
| @FLPARSINGBOT | когда Legacy consumer видит новую строку в Neon (не парсит сам) |

**Здоровье:** `site:сводка │ 10мин` в логе · `тг:пульс` раз в ~2 мин.

---

## Твои шаги (2026-05-28)

**Сайт:** [rawlead.ru/lenta](https://rawlead.ru). Волна Coder **принята** — [`STATUS.md`](team/common/STATUS.md). **Stress — после** VPS + polish (O1).

| Сейчас | Действие |
|--------|----------|
| 1 | **Site ▶** на ПК — пока нет P5-E2 на VPS |
| 2 | **@coder** § **P5-E2-VPS** — радары на сервер |
| 3 | Polish **B1** → **A1** → **C1** — [`OWNER_INTENT`](team/architect/OWNER_INTENT.md) |
| 4 | **3f** → stress → трафик |
| 5 | Новые идеи → Lead в **OWNER_INTENT** |

### Пульт Site: «POLL_INTERVAL минимум 10, получено 1»

**Не паника:** `radar_control.py` обычно **запущен** — ломается только **текст статуса** в вкладке.

| Шаг | Действие |
|-----|----------|
| 1 | `.env.site`: `POLL_INTERVAL_MINUTES=1` **и** `RADAR_CONVEYOR=1` |
| 2 | `stop-radar-desktop-full.vbs` → ярлык **RawLead Site** → 10 с |
| 3 | ▶ Site — ошибка в «Статус» должна уйти |

Дальше — только если лента снова «застыла»: см. «Свежесть ленты» ниже.

### Очередь L1

**✅ BACKLOG-CLEAR apply:** хвост сброшен; без L1 осталось **~100** (не 1200+). Site ▶ — новые идут первыми. Replay `--fresh-l1 --limit 200` — только если нужно подтянуть TG в ленту (см. `CODER_PROMPT` § FEED-FRESHNESS).

### Свежесть ленты

| Проверка | Ожидание |
|----------|----------|
| Пульт Site **▶**, не ■ | `radar_site.log` — FL/Kwork строки каждые ~1–3 мин |
| Один Site, не два ярлыка | иначе гонки и «застывшая» Neon |
| В логе | footer / `site:сводка` — если нет, пиши Lead |
| На сайте | свежие = карточки с **недавним** временем; много новых в логе может быть **МИМО** и не попасть в ленту |

---

### После stress — ты как первый подписчик (#0)

| # | Действие |
|---|----------|
| 1 | `/start` в [@rawlead_bot](https://t.me/rawlead_bot) |
| 2 | Открыть `/cabinet/` на prod → войти через TG |
| 3 | Выбрать навыки → увидеть match → **«Написать отклик»** → черновик L2 |
| 4 | Сказать Lead/Product если UX/тексты не ок → `@designer` |
| 5 | Новые идеи → Lead в **OWNER_INTENT** |

Код: [`team/architect/CODER_PROMPT.md`](team/architect/CODER_PROMPT.md) § **3f-OWNER-BETA**.

Деплой: [`ops/DEPLOY_VPS.md`](ops/DEPLOY_VPS.md) · лестница: [`team/common/TASKS.md`](team/common/TASKS.md).

---

## Кому писать

| Нужно | Куда |
|-------|------|
| План, docs | **Lead** — не проси код |
| Фича | **Coder** — если есть `team/architect/CODER_PROMPT.md` |
| Поломка | **Mechanic** + `problems/` |

Проверка бота: `.venv\Scripts\python.exe src/tg_smoke.py` — [`ops/RUN.md`](ops/RUN.md) §7.

---

## Cursor — прокси

| В `.env` | Действие |
|----------|----------|
| `CURSOR_PROXY_ENABLED=1` | Прокси **вкл** (по умолчанию `TG_PROXY_URL`) |
| `CURSOR_PROXY_ENABLED=0` | Прокси **выкл** |

После смены: `scripts\sync-cursor-proxy.bat` → **перезапуск Cursor**.
