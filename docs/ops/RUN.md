# Запуск RawLead на Windows

Работает **Python 3.11+**. Команды ниже — из **PowerShell**. Запускайте из **корня репозитория** (папка, где лежат `src/`, `docs/`, `requirements.txt`), чтобы пути по умолчанию `data/projects.db` и `data/radar.log` совпадали с каталогом `data/` в корне проекта.

**Пульт на рабочем столе** — [`DESKTOP_LAUNCH.md`](DESKTOP_LAUNCH.md): `scripts\start-radar-desktop.bat` (биржи + TG + join, без трёх чёрных cmd). Запасной вариант: `start-radar-full.bat` (3 окна cmd). Только биржи — `start-radar.bat`.

---

## 1. Папка с проектом

- **Клон из Git:** `git clone <url-репозитория> uisness` → `cd uisness`
- **Или** распакованный архив: откройте папку с `src` и `docs`, в PowerShell: `cd C:\путь\к\uisness`

---

## 2. (Опционально) виртуальное окружение

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Если политика запрещает скрипты: один раз для текущего пользователя можно разрешить выполнение локальных скриптов (решение за вами), либо ставьте зависимости в глобальный Python без venv.

---

## 3. Зависимости

```powershell
pip install -r requirements.txt
```

---

## 4. Настройка `.env`

1. В корне репозитория скопируйте шаблон:  
   `Copy-Item .env.example .env`
2. Откройте `.env` в редакторе и подставьте свои значения. **Список переменных и смысл полей** — в `.env.example` и в `src/config.py`.  
   Примеры URL ленты FL.ru — в `docs/ops/SOURCES.md`; слова «берём / стоп» — в `docs/ops/FILTERS.md`.

Обязательно задайте как минимум: `FL_PROJECTS_URL`, `POLL_INTERVAL_MINUTES` (≥ 10), `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, **`TG_PROXY_URL`** (только для Bot API; парсер FL — без прокси).

### ИИ-разбор (этап 2, опционально)

Подробности: **`docs/team/AI.md`**, UX — **`docs/team/TZ.md` §5**. Ключ: [openrouter.ai/keys](https://openrouter.ai/keys) (**в Git не коммитить**).

| Переменная | Значение по умолчанию в example |
|------------|----------------------------------|
| `AI_ENABLED` | `0` (MVP) / `1` — разбор после фильтра слов |
| `AI_PROVIDER` | `openrouter` |
| `AI_MODEL` | `google/gemini-2.5-flash-lite` |
| `AI_API_KEY` | ключ OpenRouter |
| `MIN_BUDGET_RUB` | `1000` (ниже — не вызываем ИИ и не шлём в TG) |
| `AI_NOTIFY_SKIP` | `0` — **не** слать при вердикте «Пропустить» |

Перед включением заполните **`docs/ops/PROFILE.md`**. При `AI_ENABLED=0` или пустом `AI_API_KEY` — только короткое MVP-сообщение. При ошибке API — MVP + «разбор ИИ недоступен».

```powershell
# AI выключен — как раньше
# AI_ENABLED=0 → python src/main.py

# AI включен (ключ в .env)
# AI_ENABLED=1, AI_MODEL=google/gemini-2.5-flash-lite, MIN_BUDGET_RUB=1000
```

---

## 5. Запуск радара

```powershell
python src/main.py
```

Или двойной клик **`scripts/start-radar.bat`** (копия на рабочий стол — `start-radar.bat`).

В **чёрном окне** дублируются строки цикла (`cycle_start`, `cards_fl=…`, `cycle_paused`) — по ним видно, что радар **не завис**. Полный лог: **`data/radar.log`**.

Процесс крутится в цикле (опрос раз в `POLL_INTERVAL_MINUTES`). Остановка: **Ctrl+C** в том же окне PowerShell.

**Не запускайте два радара с одним ботом** (Cursor + bat одновременно) — в логе `tg:control:getUpdates HTTP 409`, Telegram и кнопки ломаются.

---

## 6. Где смотреть лог и базу

| Что | По умолчанию | Если задали в `.env` |
|-----|----------------|----------------------|
| Лог циклов | `data/radar.log` | файл из `RADAR_LOG_PATH` |
| SQLite (виденные `project_id`) | `data/projects.db` | файл из `SQLITE_PATH` |

Пути в `SQLITE_PATH` / `RADAR_LOG_PATH` задаются **как в `.env`**: относительные — от **текущей рабочей папки** при запуске (поэтому удобно всегда `cd` в корень репозитория перед `python src/main.py`).

Папку `data/` программа создаст при необходимости.

---

## 7. Проверка связи с Telegram (если в логе **HTTP 400**)

Команды из **корня репозитория**. Токен из `.env` подставится сам, **не копируйте** его в чаты.

**Прокси:** в `.env` задайте **`TG_PROXY_URL`** — тогда **только** запросы к `api.telegram.org` идут через прокси (формат `http://host:port:user:pass` или `http://user:pass@host:port`). Парсер FL **не** использует прокси. Для проверки **отключите системный VPN** и запустите smoke ниже.

### Шаг 0 — одна команда (рекомендуется)

Тот же `load_config()`, что у радара, плюс подсказки в консоли:

```powershell
python src/tg_smoke.py
```

или эквивалент:

```powershell
python src/main.py --telegram-smoke
```

Успех: в конце **sendMessage ок**, в Telegram приходит тестовое сообщение, код выхода **0**. Подробный чеклист и типичные ошибки — в тикете **`docs/problems/2026-05-20-telegram-e2e-unblock.md`**.

### Мониторинговый +66 (Session / Telethon)

Автоматически в радаре + вручную:

```powershell
python scripts/tg_health.py
```

При сбое — сообщение в бота «аккаунт … не отвечает». Подробнее: [`HEALTH_CHECK.md`](HEALTH_CHECK.md).

### Шаг A — токен бота живой или нет

```powershell
python -c "import sys,json; sys.path.insert(0,'src'); from config import load_config; import requests; c=load_config(); r=requests.get('https://api.telegram.org/bot'+c.telegram_bot_token+'/getMe', timeout=25); print('HTTP', r.status_code); print(r.text)"
```

- **`HTTP 200`** и в тексте `"ok":true` — токен **верный**, бот существует.
- **`401`** или `"ok":false` про токен — в `.env` опечатка или **старый** токен после revoke; возьмите новый у **@BotFather**.

### Шаг B — может ли бот написать **именно в твой чат**

Сначала в Telegram открой **чат с этим ботом** и отправь **`/start`**.

```powershell
python -c "import sys,json; sys.path.insert(0,'src'); from config import load_config; import requests; c=load_config(); r=requests.post('https://api.telegram.org/bot'+c.telegram_bot_token+'/sendMessage', data={'chat_id': c.telegram_chat_id.strip(), 'text': 'Тест RawLead'}, timeout=25); print('HTTP', r.status_code); print(r.text)"
```

- **`HTTP 200`** и `"ok":true` — связь **ок**, радар должен уметь слать уведомления; если в радаре всё ещё 400 — пришли Coder **полный вывод этой команды** (там **нет** токена в ответе при ошибке `description`, но если боишься — замажь вручную).
- **`HTTP 400`** — в ответе JSON будет поле **`description`** (например *chat not found*, *bot was blocked*). По нему и чиним: чаще всего неверный **`TELEGRAM_CHAT_ID`** (нужно **число** из **@userinfobot** / **@getidsbot**, без кавычек и пробелов в `.env`).

---

## 8. Если что-то не стартует

Сообщения об отсутствующих переменных или неверном URL — из `load_config()` в `src/config.py`. Проверьте `.env` и что вы в корне проекта.

---

## 9. Пауза из Telegram

Радар **не закрываешь** (`Ctrl+C`), но на ночь выключаешь FL/Kwork и ИИ.

### Кнопки (основной способ)

При запуске `python src/main.py` бот присылает **«Панель управления»** и показывает **постоянную клавиатуру** внизу чата:

| Кнопка | Эффект |
|--------|--------|
| **⏸ Пауза** | парсеры и ИИ off |
| **▶ Старт** | снова обычный цикл |
| **ℹ Статус** | биржи + acc1/2/3: чаты, вакансии, ошибки, join |

Ответы на кнопки тоже приходят с этой клавиатурой.

### Команды (запасной способ)

| Команда | Эффект |
|---------|--------|
| `/pause` или `/стоп` | пауза |
| `/resume` или `/старт` | старт |
| `/status` | статус |

**Условия:**
- Только **твой** чат (`TELEGRAM_CHAT_ID`).
- **`python src/main.py` запущен** — иначе кнопки/команды не обрабатываются.
- Ответ — **до ~30 сек** (Mechanic: опрос `getUpdates` между циклами, см. тикет `docs/problems/2026-05-20-tg-pause-no-response.md`).
- На паузе в логе `cycle_paused`, без `cards_fl=`; пауза в SQLite переживает перезапуск.

`/start` у BotFather — регистрация чата; для старта радара — **▶ Старт** или `/resume`.

---

## 10. Telegram-чаты (фаза 1, отдельно от FL/Kwork)

Нужны в `.env`: `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELETHON_PROXY_ACC*` (отдельно на acc1–3), `TELETHON_SESSION_*`, `TELETHON_CHAT_IDS`, `TELETHON_PROXY_PROBE=1` (TCP до connect; мёртвый прокси → стоп + алерт). Бот: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TG_PROXY_URL`.

**VPN на ПК:** при включённом системном VPN прокси из `.env` часто **недоступны** → бот молчит, TG красная. Держи VPN **выкл.** на время работы радара или проверь `src/tg_smoke.py`.

**Список чатов для монитора (multi-session):** в `.env`:

```env
TELETHON_MONITOR_ACCOUNTS=acc1,acc2,acc3
TELETHON_CHAT_IDS=data/telethon_chat_ids_acc1.txt
```

Файлы `data/telethon_chat_ids_acc1.txt`, `_acc2.txt`, `_acc3.txt` (gitignore). При первом запуске `tg_main` пустой файл сидится из `done` в [`TG_JOIN_QUEUE.csv`](TG_JOIN_QUEUE.csv) для своего `account`. После join id дописывается в **свой** файл; все monitor acc подхватывают listen без рестарта (`TG_JOIN_IN_TG_MAIN=1`, join внутри `tg_main`).

Пересобрать все listen-файлы из CSV: `python scripts/tg_sync_chat_ids.py --account all`

**Запуск «всё само» (рекомендуется):** один раз `scripts\start-radar-full.bat` — биржи + TG (join acc1/2/3 внутри `tg_main`). Остановка: `scripts\stop-radar.bat`.


```powershell
# Полный радар (2 окна: биржи + TG) — см. start-radar-full.bat
scripts\start-radar-full.bat

# Только биржи + TG
scripts\start-radar-all.bat

# Разовый join одного acc (без daemon)
python scripts/tg_join_queue.py --account acc2

# acc1 в отдельном процессе — запрещено (database locked на сессии tg_main)

# Legacy: все ссылки сразу
python scripts/tg_join.py

# Список диалогов
python scripts/tg_list_dialogs.py --account acc2
```

**Очередь join (волна 3):** ссылки в [`TG_CHANNELS_EXPORT.txt`](TG_CHANNELS_EXPORT.txt) → `python scripts/tg_queue_import.py --dry-run` → `python scripts/tg_queue_import.py`.

Лог очереди join: `data/tg_join.log`. Расписание и лимиты — [`TG_JOIN_SCHEDULE.md`](TG_JOIN_SCHEDULE.md).

Лог тех же строк, что у радара: `data/radar.log` (или `RADAR_LOG_PATH`). Ночью 02:00–07:00 Irkutsk пауза переподключения длиннее (`TG_RECONNECT_NIGHT_SEC`).
