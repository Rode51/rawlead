# Радар: лог молчит, бот не отвечает, TG шлёт на «паузе»

**Статус:** решено

## Симптом

1. **Лог «не идёт»** — владелец не видит обновлений (ожидает `cycle_start` / биржи).
2. **Бот при запуске не откликается** — кнопки **ℹ Статус**, **▶ Старт**, **⏸ Пауза** без ответа.
3. **Уведомления из TG-чатов приходили, когда радар «выключен»** (окно бирж закрыто / пауза в боте).

## Ожидалось

- Лог: `C:\Users\hramo\uisness\data\radar.log` — строки `radar_main_start`, `cycle_start`, `cards_fl=…` (биржи) и/или `tg_heartbeat`, `tg_msg` (TG).
- Бот: ответ на **Статус** ≤ ~30 с при запущенном `start-radar.bat` (2 окна), см. `docs/ops/DESKTOP_LAUNCH.md`.
- **Пауза** (`/pause` или ⏸): **ни биржи, ни TG** не шлют уведомления в личный чат.

## Фактически

По `data/radar.log` (без секретов):

- После **2026-05-22T14:36:44Z** `cycle_start` **нет** новых `cycle_start` — окно **birzhi** (`src/main.py`) скорее всего **не работает**.
- Идут только **`tg_msg`** (окно **TG** / `scripts/tg_main.py` живо), в т.ч. **`notify=1`** (2026-05-22T22:00:05Z) — уведомление ушло **без** активного цикла бирж.
- Строк **`radar_main_start`**, **`tg_main_start`**, **`tg_heartbeat`** в логе **может не быть** (фичи добавлены Lead/Coder 2026-05-22; владелец мог не перезапустить после обновления).
- Ранее в логе: **`tg:control:getUpdates HTTP 409`** — второй процесс с тем же `TELEGRAM_BOT_TOKEN` (дубль `tg_main`, Cursor, **uvicorn** `app.telegram.bot` на портах 10000–10002).

Запуск владельца: **`Desktop\start-radar.bat`** → `scripts\start-radar-all.bat`.

## Контекст

- ОС: Windows 10.
- Два процесса: `src/main.py` (бот + FL/Kwork) и `scripts/tg_main.py` (Telethon).
- Пауза хранится в SQLite: `settings.radar_paused` — **`main.py` проверяет**, **`tg_monitor.py` — нет** (вероятная причина п.3).
- Недавние правки (проверить на месте): `src/bot_poll.py` (lock getUpdates), `scripts/tg_main.py` (опрос бота + heartbeat), `scripts/stop-radar.bat`.

Связанные тикеты: `2026-05-20-tg-pause-no-response.md` (решено), `2026-05-22-tg-notify-zero.md` (ИИ МИМО vs notify).

---

## Задача Mechanic

### 1. Пауза должна глушить TG

- В **`src/tg_monitor.py`** (или перед `process_new_listing`): если `storage.is_radar_paused()` — **не** вызывать notify; в лог: `tg_msg … skip:paused` (без текста поста/секретов).
- Убедиться: после **⏸ Пауза** в боте TG-уведомления **не** приходят, пока не **▶ Старт**.

### 2. Бот отвечает на Статус при штатном запуске

- Проверить цепочку: `bot_poll.try_poll_commands` → `telegram_control.poll_commands` → `sendMessage` через `TG_PROXY_URL`.
- Сценарий: `stop-radar.bat` → только **один** `main.py` + **один** `tg_main.py` → `/status` → ответ + `tg:action:status` в логе.
- Если **409**: в тикете описать, какой процесс конфликтует; по возможности — понятное сообщение в консоль/лог (уже частично в `main.py`).

### 3. Лог понятен владельцу

- При старте **`main.py`**: строка `radar_main_start` в `data/radar.log`.
- При старте **`tg_main.py`**: `tg_main_start` + **`tg_heartbeat`** раз в ~2 мин, пока процесс жив.
- Документировать в **тикете** (не в `docs/ops/`): «нет `cycle_start` = окно birzhi закрыто; есть только `tg_msg` = работает только TG».

### 4. Дубли процессов (по возможности)

- При втором запуске `tg_main` — предупреждение в консоль или exit 1 (опционально, минимальный diff).
- Не ломать `start-radar-all.bat`.

### Как проверить

1. `scripts\stop-radar.bat` → `Desktop\start-radar.bat` — 2 окна открыты.
2. `data\radar.log`: в течение 3 мин есть `radar_main_start` или `cycle_start` **и** `tg_heartbeat`.
3. В боте: **Статус** → ответ ≤ 30 с.
4. **Пауза** → пост в TG-чате → **нет** уведомления; **Старт** → снова по правилам пайплайна.
5. `python src/main.py` — регрессия FL/Kwork без поломки.

---

## Решение (заполняет Mechanic)

**Статус:** решено  
**Дата:** 2026-05-23

### Причина

1. **TG на паузе:** `scripts/tg_main.py` → `tg_monitor.py` вызывал `process_new_listing` без проверки `storage.is_radar_paused()` — уведомления шли, пока биржи (`main.py`) были на паузе.
2. **Бот молчит:** `tg:control:getUpdates HTTP 409` — второй процесс с тем же `TELEGRAM_BOT_TOKEN` (дубль радара, uvicorn `app.telegram.bot`, Cursor). Цепочка `bot_poll` → `telegram_control` рабочая; при 409 Telegram отклоняет getUpdates.
3. **Лог «не идёт»:** после последнего `cycle_start` окно **birzhi** (`src/main.py`) не работало; жив только TG → в логе только `tg_msg`. Строки `radar_main_start` / `tg_heartbeat` уже были в коде — нужен перезапуск через `stop-radar.bat` → `start-radar.bat`.

**Как читать лог:** нет `cycle_start` = окно birzhi закрыто; есть только `tg_msg` / `tg_heartbeat` = работает только TG.

### Что сделано

- В `tg_monitor.py`: при `is_radar_paused()` — не вызывать pipeline, лог `tg_msg … err=skip:paused`.
- В `tg_main.py`: предупреждение в консоль при HTTP 409 (как в `main.py`); lock `.tg_main.lock` — второй `tg_main` выходит с кодом 1.

### Изменённые файлы

- `src/tg_monitor.py`
- `scripts/tg_main.py`
- `scripts/start-radar-all.bat` — `\"%PY%\"` внутри `cmd /k "..."` ломало запуск (окно TG/birzhi сразу падало, Python не стартовал)

### Как проверить

1. `scripts\stop-radar.bat` → `Desktop\start-radar.bat` — 2 окна.
2. `data\radar.log`: за 3 мин — `radar_main_start` или `cycle_start` **и** `tg_heartbeat`.
3. В боте: **Статус** → ответ ≤ 30 с, в логе `tg:action:status`.
4. **Пауза** → пост в TG-чате → **нет** уведомления, в логе `skip:paused`; **Старт** → снова по правилам.
5. При 409: закрыть лишние процессы с тем же ботом (`stop-radar.bat`, uvicorn на 10000–10002).
6. Второй запуск `tg_main.py` — сообщение в консоль и exit 1.
