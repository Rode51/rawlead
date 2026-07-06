# Health check: OperationalError database is locked (+7XXXXXXXXX1)

**Статус:** решено  
**Дата:** 2026-05-23

## Симптом

⚠️ Аккаунт +7XXXXXXXXX1 не отвечает. Алерт бота: `OperationalError: database is locked`.

## Ожидалось

При `start-radar-all.bat` (окна «биржи» + «TG») health check не падает, если монитор уже подключён к сессии.

## Фактически

`data/radar.log`:

```
2026-05-23 13:25:18 тг:монитор:старт чатов=6 …
2026-05-23 13:25:27 здравье:сбой акк=+7XXXXXXXXX1 OperationalError: database is locked
```

Два процесса (`src/main.py` и `scripts/tg_main.py`) вызывали `run_health_check` → второй `TelegramClient` на тот же `*_telethon.session` → SQLite lock.

Прокси и файл сессии в порядке: `+7XXXXXXXXX1_telethon.session` существует, монитор стартует.

## Контекст

Windows, `start-radar-all.bat`. Не перезапуск радара — конфликт в коде.

---

## Решение

### Причина

Telethon хранит сессию в SQLite; одновременно открыть её из `tg_main` (монитор) и `health_check` (отдельный connect) нельзя.

### Что сделано

1. **`src/health_check.py`:** если активен `data/.tg_main.lock`, не открываем вторую сессию — проверкаем по `tg_monitor_last_pulse` в SQLite.
2. **`scripts/tg_main.py`:** при `тг:пульс` пишем метку времени пульса в storage.

### Изменённые файлы

- `src/health_check.py`
- `scripts/tg_main.py`

### Как проверить

1. `scripts\stop-radar.bat` → `scripts\start-radar-all.bat`
2. Подождать 3–5 мин, в `data/radar.log` — `здравье:ок … монитор активен`, без `database is locked`
3. При только `start-radar.bat` (без TG) — health check по-прежнему делает `get_me` через Telethon
