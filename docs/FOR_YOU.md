# Для тебя

**Полная карта docs:** [`README.md`](README.md)

| Вопрос | Файл |
|--------|------|
| **Что делать сейчас?** | Ниже «Твои шаги» |
| **Как это работает?** | [`KAK_ETO_RABOTAET.md`](KAK_ETO_RABOTAET.md) |
| **Фазы / приоритет** | [`team/architect/ROADMAP.md`](team/architect/ROADMAP.md) · vision v0.9 |
| **План Product** | [`team/product/LEAD_PRODUCT_PROMPT.md`](team/product/LEAD_PRODUCT_PROMPT.md) |
| **Запуск** | [`ops/RUN.md`](ops/RUN.md) |
| **Пульт** | [`ops/DESKTOP_LAUNCH.md`](ops/DESKTOP_LAUNCH.md) |
| **TG acc + @FLPARSINGBOT** | [`ops/TELEGRAM_ACCOUNTS.md`](ops/TELEGRAM_ACCOUNTS.md) |
| **Схема (картинка)** | [`design/rawlead/project-map-owner.png`](design/rawlead/project-map-owner.png) |

Роли: `@lead-architect` · `@coder` · `@mechanic` · `@designer` — см. [`README.md`](README.md) § по роли.

---

## Два радара (legacy + site)

| Ярлык | Профиль | Бот | Зачем |
|-------|---------|-----|--------|
| **Радар Site** (сервер 24/7) | `site` | [@rawlead_bot](https://t.me/rawlead_bot) | **Парсит** биржи + TG → **Neon** → `/lenta/` |
| **Радар Legacy** (ПК, по желанию) | `legacy` | @FLPARSINGBOT | **Не парсит** биржи — **читает Neon**, `FILTERS_LEGACY` → бот |

- Фильтры **разные файлы**: `FILTERS_SITE.md` (лента) vs `FILTERS_LEGACY.md` (твой бот)
- **Один парсер** на сервере (Site ▶); Legacy — отбор из той же Neon, SQLite «уже слал»
- `SITE_NOTIFY_OWNER=0` (по умолчанию): Site **не шлёт** owner-уведомления в TG; биржи владельцу идут только через Legacy consumer
- OpenRouter: **два ключа** — legacy и site
- На прод: регистрируешься на сайте → новый бот → тест как платный подписчик

Подробно: [`team/common/PROJECT_MAP.md`](team/common/PROJECT_MAP.md) § «Два контура»

### Какой `.env` правильный?

| Файл | Когда используется | Что хранить |
|------|-------------------|-------------|
| **`.env`** | Всегда (вторым слоем) | **Общее:** Neon `DATABASE_URL`, Telethon acc1–3, FL/Kwork URL, прокси, `FREELANCEHUNT_API_TOKEN` |
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

## Твои шаги сейчас — к прод (2026-05-27)

**Канон:** [`team/architect/PRE_PROD_GATE.md`](team/architect/PRE_PROD_GATE.md) · Coder: § **NEON-DEDUP-REPLAY**

1. **Site ▶** (`start-radar-desktop-site.vbs`) — **единственный** писатель в Neon (биржи). Legacy ▶ — только consumer, **не** должен крутить `main` с FL в логе.
2. **`.env.site`:** `TELEGRAM_CHAT_ID` = чат, куда **уже писал** [@rawlead_bot](https://t.me/rawlead_bot) (напиши `/start`). Иначе в `radar_site.log`: `chat not found`.
3. **`.env.site`:** `PUBLIC_FEED_SOURCES=fl,kwork,freelancehunt` · `DATABASE_URL` = тот же Neon, что в Console.
4. **Дождись @coder** § NEON-DEDUP-REPLAY → перезапуск Site ▶ → проверь `/lenta/` и Neon (строки с L1 / `is_visible`).
5. **Лог Site:** `data/radar_site.log` — после Coder смотри `neon_insert` / `neon_replay`, не только `dup`.
6. **Прод P5** — только после п.4 + твоё **«едем на прод»** в чат Lead.

**Не прод:** пока в Neon 0 обновлений за сутки и лента пустая — это баг воронки, не «на бирже нет дизайна».

Neon ✅ · dogfood бот — как был.

С понедельника: отклики **по боту** (вердикт «Брать»), 1–2 сильных в день.

| Блокер | Кто |
|--------|-----|
| **`/lenta/` не грузится** | **@mechanic** · [`problems/2026-05-25-wp-lenta-feed-not-loading.md`](problems/2026-05-25-wp-lenta-feed-not-loading.md) |
| pythonw.exe = launcher (2 процесса) | **@mechanic** |
| TG relay+card | ✅ acc шлют в бот; при сбое — prompt-test · [`problems/2026-05-24-tg-forward-not-via-bot.md`](problems/2026-05-24-tg-forward-not-via-bot.md) |

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
