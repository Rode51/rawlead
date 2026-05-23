# Запуск с рабочего стола

## Пульт (рекомендуется)

**Один ярлык, без чёрных cmd:**

| Способ | Команда / файл |
|--------|----------------|
| Двойной клик | **`scripts\start-radar-desktop.bat`** |
| Вручную | из корня repo: `.venv\Scripts\python.exe scripts\radar_desktop.py` |

В окне пульта: **▶ Старт** / **⏹ Стоп**, индикаторы **Биржи · TG · Join**, вкладки логов `data\radar.log` и `data\tg_join.log`, кнопка **Обновить статус** (то же, что ℹ в боте).

Пауза радара — только в Telegram-боте (кнопка ℹ / «Пауза»), в пульте не дублируется.

Перед повторным стартом пульт сам вызывает стоп (как `stop-radar.bat`). Второй экземпляр пульта не откроется (`data\.radar_desktop.lock`).

---

## Три окна cmd (запасной способ)

**`scripts\start-radar-full.bat`** → **3 окна** (биржи + TG + join acc2/acc3).

| Окно | Что делает |
|------|------------|
| **FL Radar — birzhi** | FL.ru + Kwork |
| **FL Radar — TG** | acc1: слушает чаты + **сам вступает** в новые |
| **FL Radar — join** | acc2/acc3: вступление в чаты по очереди |

**Только 2 окна** — если ярлык на **`start-radar-all.bat`** или **`start-radar.bat`** (биржи + TG, **без** join acc2/acc3). Для волны 2 на acc2/acc3 нужен **full** или отдельно `scripts\start-join-daemons.bat`.

Перед перезапуском: **`scripts\stop-radar.bat`** или **⏹ Стоп** в пульте (убирает дубли `tg_main`).

---

## Кнопки «Пауза / Статус» в боте

Работают, если **хотя бы одно** окно радара запущено (опрос бота с lock — не 409 между двумя окнами).

Если **не отвечает**:

1. Нет окна **birzhi** и **TG** — запусти `start-radar.bat` снова.
2. Другой софт с тем же ботом (uvicorn `app.telegram.bot` и т.п.) — закрой, иначе **HTTP 409**.
3. В логе нет строк `radar_main_start` / `tg_main_start` — радар не стартовал.

---

## Лог «не идёт»

| Строка в логе | Значение |
|---------------|----------|
| `радар:старт` | окно бирж запущено |
| `цикл:старт` / `карточки_fl=` | биржи крутятся |
| `тг:старт` / `тг:пульс` | TG-окно живое |
| `тг:сообщ` | пришло сообщение в чат |
| `пропуск:пауза` | TG на паузе, уведомления не шлём |
| `тг:команда:статус` | бот ответил на кнопку |

Файл: **`data\radar.log`** (не `src\data\radar.log`).

---

## Neon

```sql
SELECT source, COUNT(*) FROM leads GROUP BY source ORDER BY source;
```

---

## Отдельные bat

| Файл | Назначение |
|------|------------|
| `scripts\start-radar.bat` | только биржи |
| `scripts\start-radar-tg.bat` | только TG |
| `scripts\start-radar-all.bat` | **2 окна:** биржи + TG |
| `scripts\start-radar-full.bat` | **3 окна:** + join acc2/acc3 (рекомендуется) |
| `scripts\start-join-daemons.bat` | только окно join (если birzhi+TG уже работают) |
| `scripts\stop-radar.bat` | стоп процессов |
| `scripts\start-radar-desktop.bat` | пульт (GUI, без cmd) |
| `scripts\radar_desktop.py` | то же, из консоли |
