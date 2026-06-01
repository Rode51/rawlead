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
| **Перед рекламой проекта** | [`ops/PRE_LAUNCH_MARKETING.md`](ops/PRE_LAUNCH_MARKETING.md) |
| **TG acc + @FLPARSINGBOT** | [`ops/TELEGRAM_ACCOUNTS.md`](ops/TELEGRAM_ACCOUNTS.md) |
| **Схема (картинка)** | [`design/rawlead/project-map-owner.png`](design/rawlead/project-map-owner.png) |

Роли: `@lead-architect` · `@coder` · `@mechanic` · `@designer` — см. [`README.md`](README.md) § по роли.

---

## Секреты и Git

| Файл | В Git? | Где хранить |
|------|--------|-------------|
| `.env` · `.env.site` · `.env.legacy` | **нет** (`.gitignore`) | только на ПК / VPS |
| `*.session` Telethon | **нет** | Desktop или `data/sessions/` |
| `data/wp-vps-credentials.txt` | **нет** | локальный блокнот после `install-wp-vps.py` |
| `mcp.pool.json` (MCP ключи) | **нет** | копия из `mcp.pool.example.json` |
| `.env.example` | **да** | шаблон без реальных значений |

**Перед `git add .`:** `git status` — не должно быть `.env`, `*credentials*`, `*.session`, `mcp.pool.json`.

**Если ключ уже улетел в GitHub:** сменить ключ/пароль на сервисе → не полагаться только на удаление из истории.

**Проверка:** `git check-ignore -v .env data/wp-vps-credentials.txt` — оба должны показать правило из `.gitignore`.

**O72c judge:** модель **`anthropic/claude-sonnet-4`** — Lead прописал в `.env.site` как `OPENROUTER_MODEL_JUDGE` · ключ OpenRouter там же.

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

## Запуск без бюджета (честно)

**В репо нет платной «рекламной кампании»** — есть только [`PRE_LAUNCH_MARKETING.md`](ops/PRE_LAUNCH_MARKETING.md): **когда продукт готов** звать людей, а не куда тратить ₽.

**«Soft ads» у нас** = **осторожно позвать первых 5–20 человек**, не Яндекс.Директ.

### Сейчас (0 ₽, только время)

| Канал | Что сделать |
|-------|-------------|
| **Сам (dogfood)** | **Главный канал без людей:** TG-бот + `/lenta/` + «Написать отклик» — по vision **Канал 1** не требует подписчиков и знакомых |
| **@rawlead_bot** | Ссылка в **био** личного TG (не канал) · `/start` → кабинет |
| **Metrika / Clarity** | Бесплатно · видно, если кто-то пришёл сами (O73, не срочно) |

**Если есть круг / свой канал** (не у всех):

| Канал | Что сделать |
|-------|-------------|
| **5–10 знакомых** | Ссылка rawlead.ru/lenta/ · 1 отзыв в личку |
| **Свой TG** | 1 пост «тестирую агрегатор» · **не** спам в чужих |

### Нет знакомых и нет канала (2026-05-31, владелец)

Это **нормально** для этапа MVP — не «провал маркетинга».

| Что | Реальность |
|-----|------------|
| **Сейчас** | Продукт и **личный ROI** важнее первых чужих юзеров · реклама **⏸** до O72d + O76 |
| **Лента без трафика** | Открытая `/lenta/` может жить как **SEO-магнит** (медленно, месяцы): индексация, свежие заказы, без рассылки |
| **0 ₽, без аудитории** | Профиль на FL/Kwork с ссылкой на ленту (если есть аккаунт) · 1 **полезный** комментарий в **открытом** чате фриланса, когда уместно (не реклама) · позже — кейс Habr/VC **когда** есть что показать |
| **Не обещаем** | «Пост в канале» / «5 друзей» — **не** обязательный шаг, если сети нет |
| **Дальше** | `@lead-product` — отдельный блок GTM «нулевая сеть» в vision/OWNER_INTENT (не срочно) |

### Потом (когда O72d + O76 ✅)

| Канал | Стоимость |
|-------|-----------|
| Пост в **тематическом TG** (договориться с админом) | 0–3k ₽ или бартер |
| **Habr / VC** кейс «как собрал ленту» | 0 ₽, нужен текст |
| **Яндекс / VK / TG ads** | от ~5–15k ₽/мес — **не сейчас** |

### Не нужны деньги на

- VPS, WP, радар — уже есть  
- Первые чужие юзеры — **медленная органика** (SEO, ссылка в профиле) · знакомые — **если есть**, не обязательны  
- OpenRouter на regen/judge — копейки на фоне regen 80 лидов  

**Реклама с бюджетом** — только когда **сам** скажешь «готов платить X» · Product зафиксирует в `OWNER_INTENT`.

---

## После гейтов — что дальше (записано 2026-05-31)

**Сейчас:** сначала **дожимаем** (O72d → O76 → тесты) — ты так и решил, это канон.

**Потом — два параллельных трека** (оба можно без большого бюджета):

### Трек A — RawLead (продукт)

| Шаг | Действие |
|-----|----------|
| 1 | Soft launch: ссылка на `/lenta/`, честный MVP-дисклеймер по черновикам |
| 2 | Нулевая сеть: SEO, био TG, FL-профиль с **ссылкой на портфолио** (трек B) |
| 3 | По желанию: Habr/VC кейс «как собрал ленту» · тематический TG (бартер) |
| 4 | Платная реклама — только когда сам скажешь «готов платить X» |

Канон: [`PRE_LAUNCH_MARKETING.md`](ops/PRE_LAUNCH_MARKETING.md) · GTM без сети → `@lead-product`.

### Трек B — личное портфолио на том же VPS (**P-PORTFOLIO**)

**Зачем:** пока RawLead рекламируем, **параллельно заходишь на FL** — заказчикам нужна **одна красивая ссылка**, не «показать нечего».

| | |
|--|--|
| **Хост** | Тот же VPS / WordPress, что rawlead.ru (отдельная страница или префикс, **не** ломаем ленту) |
| **Стиль** | Отдельный визуал «исполнитель» — **интерактив** (скролл, карточки проектов, мини-демо, hover), не скучный PDF |
| **Ссылка в FL** | Одна постоянная URL в профиль и в отклики |

**Кейсы на сайте (владелец):**

| # | Проект | Как показать |
|---|--------|--------------|
| 1 | **RawLead** | Живая `/lenta/` + 3–5 скринов · «агрегатор + ИИ» |
| 2 | **Fin MVP** | 1 фин-приложение (MVP) — скрины / embed / «открыть демо» |
| 3 | **Михалыч** (= «умный чат-бот») | `C:\Users\hramo\Miha` — ИИ-бот для групповых чатов · на портфолио: **WIP** или демо в личке |
| 4 | **Crystal Debt** (= fin MVP) | `C:\Users\hramo\crystal-debt-core` — **без живого сервера** (хостинг выключен) · на портфолио: **скрины/видео + «MVP, paused»**, не ссылка «открыть продукт» |

**Порядок работ (когда гейты зелёные):**

1. Ты: скрины/тексты/ссылки по каждому кейсу (+ абсолютные пути к папкам Crystal Debt и Михалыч).  
2. `@lead-designer` — макет интерактивного портфолио (отдельно от RawLead DS).  
3. `@designer` → `@coder` — вёрстка на VPS (WP child или статика под nginx).  
4. Ты: обновляешь FL-профиль → отклики с этой ссылкой.

**Не путать:** RawLead = **продукт для фрилансеров** · P-PORTFOLIO = **ты как исполнитель** для заказчиков на FL.

### Концепция (владелец 2026-05-31): не «видео в лоб», а интерактив + ИИ

| Идея | Решение Lead |
|------|----------------|
| Просто залить видео | **Нет** — слабая витрина |
| Поднять весь Crystal Debt на VPS | **Нет** — лишние деньги · Supabase · поддержка |
| Взять **наработки UI** Crystal Debt + «прицепить API-ключи» | **Частично да**, но **не ключи в браузере** и **не полный бэкенд CD** |

**Канон P-PORTFOLIO v1:**

1. **Отдельная страница** `rawlead.ru/portfolio/` (или `/works/`) — **не** клон CD, **не** отдельный платный хост CD.
2. **Визуальный язык** — заимствовать из CD: карточки, «журнал», мягкий неон/пиксель (как в `assets/web/`), **данные фейковые** в JSON на странице (демо, не Supabase).
3. **Интерактив без сервера CD:** раскрытие кейсов, hover, мини-свайп «журнал демо», скролл-истории — чистый HTML/CSS/JS.
4. **ИИ на портфолио (v4)** — **стильно, не форма.** Главное: **«До/После»** scrub (хаос заявок → с ИИ-слоем) + **«Выбери боль»** → brutalist-схема «завод». Без МИМО. LLM только в финале («план под нишу»). Детали: `LEAD_DESIGN_PROMPT` § D-P-PORTFOLIO v4 · выбор A/B — у `@lead-designer`.
5. **Дизайн** — база **`labs.rawlead.ru`** (твой скрин: фото, жёлтый hero, брутализм) + **wow-scroll** как [Richard Ekwonye](https://www.richardekwonye.com/) (fullscreen covers, индекс кейсов), без отказа от NEO-BRUTALIST.
5. **Crystal Debt** — блок **Case study + интерактив-макет** (paused), опционально 30 с **локального** записи внутри карточки, не YouTube-простыня на весь сайт.
6. **RawLead** — живая ссылка + 1 экран встроенный превью или скрин.
7. **Михалыч** — галерея диалогов / «демо по запросу в TG».

**Запрещено:** OpenRouter/Supabase ключи в фронте · поднятие полного `crystal-debt-core` ради портфолио · обещание «это сейчас мой фин-сервис в проде».

**Следующий шаг после гейтов:** `@lead-designer` § **D-P-PORTFOLIO** — wireframe «витрина + фейк-журнал + чат-гид».

---

## Твои шаги (2026-06-01)

| # | Сейчас | Действие |
|---|--------|----------|
| **1** | **@designer** | **D-O81** — лендинг flow |
| **2** | **@coder** | **O63-w2** — FreelanceJob + Пчёл.нет (параллельно Design) |
| **3** | **@designer** → **@coder** | **D-O82b** → **O82-w1b** (после D-O81) |
| **4** | **@coder** | **O82-w2** — живой match % | **✅** |
| **5** | **@coder** | **O72e-3** — промпты L1+L2 · deploy VPS | **→ сейчас** |
| **5b** | **@coder** + **ты** | **O72e-4** — `qa_prompt_loop.py --apply` (автомат, ты смотришь терминал) | после **5** |
| **6** | **Гейты** | Soft ads **после** judge PASS (≥4.0 · send ≥50% · L1 ≥70%) |

**Запуск автомата (после deploy O72e-3):**

```powershell
cd C:\Users\hramo\uisness
.venv\Scripts\python.exe scripts\qa_prompt_loop.py --profile site --apply --llm-edit-prompt
```

Логи: `data/qa_prompt_loop_*.json` · патчи: `data/qa_prompt_patches/` · стоп сам через 5 итераций или Ctrl+C.

Draft **9/10** — [`problems/…`](problems/2026-05-30-owner-draft-accept-9of10.md)

Theme prod **v1.11.15**.

### ИИ «недоступен» — что это

| | |
|--|--|
| **L1 (лenta, теги)** | **работает** на VPS |
| **L2 (черновик отклика)** | **иногда падает** — OpenRouter; другие draft сразу после OK |
| **Тебе** | «Повторить» через минуту; если часто — проверь баланс **OpenRouter** (ключ в `.env.site`) |

Тикет: [`problems/2026-05-30-ai-draft-unavailable.md`](problems/2026-05-30-ai-draft-unavailable.md)

### @FLPARSINGBOT опоздал — почему

Legacy consumer на VPS ходит в Neon **раз ~10 мин** (не каждую секунду). Заказ мог быть в ленте раньше, бот догнал позже. **O66** — poll 1 мин + «догонять visible». См. `CODER_PROMPT` § O66.

### «Без L1 (48 ч)=95» в /status

**Не задержка ленты на 48 ч.** Счётчик строк в БД без штампа ИИ. **O64** — разбивка fl/tg/kwork + чистка хвоста.

| Факт | Значение |
|------|----------|
| Сервис | `rawlead-radar` **active** · цикл **~13 с** |
| FL.ru | скачано **90** · **новых 0** · много `dup_fast_skip` + `pipeline:skip filter` |
| Kwork | скачано **0** — подозрительно, но не «упал весь радар» |
| TG acc1 | **здравье:ок** · пульс ~77 с |
| Почему тихо в ленте | filter/dup/L1 МИМО — заказ мог уйти в **Legacy-бот** или отсечься **до** `is_visible` |

Если Kwork долго **0** — скажи Lead → **O63** / Mechanic отдельно от UX.

### Local-first — theme на radarzakaz.local

**Зачем:** правим CSS/JS локально, на prod — **один deploy** когда ок.

1. **Local** → **radarzakaz** → **Start**
2. PowerShell:

```powershell
cd C:\Users\hramo\uisness
.venv\Scripts\python.exe scripts\wp_install_rawlead_theme.py
```

3. **http://radarzakaz.local/lenta/** · F12 → **390×844** · Ctrl+F5  
   Burger · [Фильтры] · карточки не обрезаны · `/cabinet/`

**Важно:** slug **`/lenta/`** — не `/feed/` (это RSS WordPress).

### Local → «сеть» (чтобы лента грузилась)

Local WP **сам по себе** Neon не видит. Браузер → WP → **API** → Neon.

**Способ B — локальный API (Neon, рекомендуется для local):**

Окно PowerShell **из корня repo** (`.env` с `DATABASE_URL`). **Важно:** `PYTHONPATH=src`:

```powershell
cd C:\Users\hramo\uisness
$env:PYTHONPATH="C:\Users\hramo\uisness\src"
.venv\Scripts\uvicorn.exe src.api_server:app --host 127.0.0.1 --port 18766
```

Проверка: `http://127.0.0.1:18766/health` → `{"status":"ok"}`.

В `wp-config.php` radarzakaz (уже добавлено Lead):

```php
define('RAWLEAD_API_URL', 'http://127.0.0.1:18766');
```

Проверка WP: `http://radarzakaz.local/wp-json/rawlead/v1/feed?limit=2` → JSON `items`.

**Способ A (prod API):** `https://api.rawlead.ru` с ПК **не работает** (404/RSS) — не использовать.

**Пока uvicorn запущен** — лента на local живая. Закрыл окно → снова команда выше.

[`ops/WP_CURSOR_CONNECT.md`](ops/WP_CURSOR_CONNECT.md)

### O37c — прогон UX audit (после deploy)

```powershell
cd C:\Users\hramo\uisness
.venv\Scripts\python.exe scripts\preprod_mint_token.py --account acc1 --write-env-site
```

В stdout: `user_id=895912a1-...` (не `164786fe-...`) · `token written → .env.site`.

**Шаг 1 — audit:**

```powershell
.venv\Scripts\python.exe scripts\preprod_playwright\ux_audit.py --base-url https://rawlead.ru --browser chromium --headed
```

| Файл | Что смотреть |
|------|--------------|
| `data/preprod_ux_audit_human.md` | **Критично / Раздражает** |
| `data/preprod_ux_audit.json` | U1–U10 pass/fail |

Напиши `@lead-architect` «прогон готов».

~~DevTools / ручной token~~ — не для gate. [`ops/PREPROD_ACCOUNTS.md`](ops/PREPROD_ACCOUNTS.md).

~~stress до Wave 2~~ — отменено владельцем 2026-05-29.

**Не трогать:** Site/Legacy ■ на ПК — радар 24/7 только VPS systemd.

### Радар на VPS — пульт на ПК не нужен

| Что | Где живёт |
|-----|-----------|
| Парсинг FL/Kwork + TG | VPS `rawlead-radar` (systemd) |
| API + `/lenta/` | VPS `rawlead-api` + WP |
| Dogfood карточки тебе | VPS `rawlead-radar-legacy` → @FLPARSINGBOT |
| **Пульт Tauri** | **опционально** — только если отлаживаешь на ПК; в проде **■ оба ярлыка** |

**Управление без пульта:** `/status` · `/pause` · `/стоп` в @FLPARSINGBOT · `systemctl restart rawlead-radar` на VPS.

**Прокси на VPS:** карта 5 IP → [`ops/DEPLOY_VPS.md`](ops/DEPLOY_VPS.md) § «Карта прокси» · после правки `.env` — `systemctl restart rawlead-radar`.

---

| Шаг | Действие |
|-----|----------|
| 1 | **Cursor → Reload Window** (или перезапуск) — в MCP должен быть `recraft` |
| 2 | Новый чат `@designer` → при первой генерации — **OAuth Recraft** в браузере |
| 3 | Ассеты → `docs/design/assets/` · канон: [`design/assets/README.md`](design/assets/README.md) |

Если credits на **API balance**, а не Studio — см. local setup в [`MCP_POOL.md`](team/common/MCP_POOL.md) § Recraft local.

### Хвост L1 в Neon (153 без ИИ)

**Не паника:** после O34 это **не блокирует** ленту. `/status` пока пугает зря — **O40** починит.

| Шаг | Когда | Действие |
|-----|-------|----------|
| 1 | **✅ O40 на VPS** | `/status` — «Без L1 (48 ч)» + «Хвост исторический» (без ложного «конвейер») |
| 2 | **apply** | Сейчас **`to_clear=0`** — все 153 **моложе 7 дней** в Neon. Повтор `--by-age --days-old 1` когда часть старше 48 ч |

Текущий `--apply` без `--by-age` **не чистит** 153 — все под защитой top-100 id.

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

### SITE-ACCEPT-GATE — **✅ закрыт 2026-05-28**

Gate принят. Чеклист: `CODER_PROMPT.md` § **SITE-ACCEPT-GATE** (архив).

### Coder — **сейчас P0 (TG 500)**

```
@coder
Правила: .cursor/rules/coder.mdc
Задача: docs/team/architect/CODER_PROMPT.md — § TG-AUTH-500-HOTFIX
Тикет: docs/problems/2026-05-29-cabinet-tg-auth-500.md
После fix — restart rawlead-api на VPS.
```

### Lead ops (перед Coder O32)

1. Deploy site radar (O34) на VPS + restart `rawlead-radar`
2. `clear_l1_backlog.py --profile site --apply`
3. Theme v1.8.2 уже на prod — **ты:** реальный вход TG на `/cabinet/`

### O38 ✅ · O59 → O37

O38 Mechanic audit **закрыт** · verdict **NO-GO O37**. Design **принят as-is** (D-O39 docs ✅).

```
@coder
docs/team/architect/CODER_PROMPT.md — § O59a draft stability (post-O38 P0)
```

---

### После stress — первый внешний платящий

| # | Действие |
|---|----------|
| 1 | Stars → `is_active=true` (§ **3f-C-STARS**) |

Код: § **3f-OWNER-BETA** · § **3f-C-STARS**.

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

## Cursor — прокси (из РФ)

**Ошибка «Model not available / region»** — Cursor видит **страну выхода IP**, не «прокси вкл/выкл».

| Прокси (host) | Exit (geo) | Cursor |
|---------------|------------|--------|
| **38.154.16.60** | **US** | ✅ для моделей |
| **45.152.197.25** | **NL** | ✅ (раньше работало = TG_PROXY) |
| **168.90.199.99** | **PT** | ✅ запасной |
| 185.147.131.15 | **RU** | ❌ region error |
| 212.102.151.153 | BY | ⚠️ может резать |

В `.env`:
```env
CURSOR_PROXY_ENABLED=1
CURSOR_PROXY_URL=http://38.154.16.60:8000:USER:PASS
```
(не 185.147 · не пусто, если TG=45.152 а тебе нужен US — явно укажи 38.154)

После смены: `scripts\sync-cursor-proxy.bat` → **полный Quit Cursor** → открой снова.

**В Cursor:** Settings → Network → **HTTP Compatibility = HTTP/1.1** (если есть). Модель **Auto** или Claude/GPT, не заблокированная вручную.

**TG/бот** — по-прежнему `TG_PROXY_URL` (45.152), не путать с Cursor.
