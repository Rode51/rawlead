# Запуск с рабочего стола

## Пульт v2 (Tauri + HTML) — рекомендуется

**Один ярлык, без чёрных cmd:**

| Способ | Команда / файл |
|--------|----------------|
| Двойной клик | **`scripts\start-radar-desktop.bat`** |
| API вручную | `.venv\Scripts\python.exe scripts\radar_control.py` |
| UI dev (после Rust) | `cd desktop` → `npm run tauri dev` |
| UI в браузере (отладка) | API + `cd desktop` → `npm run dev` → http://localhost:1420 |

Пульт **Tauri 2 + WebView2**: compact 400×560 → **Play** (синий `#5B8DEF`) → логи вниз → **Stop** (зелёный `#3DD68C`). Справа вверху — **Обновить статус**. Лампы **Биржи · TG · Join**: зелёный = работает, красный = упал после старта, серый = idle (без «ожидание»).

### Первый раз (один раз на ПК)

1. Python venv: `py -3.11 -m venv .venv` → `pip install -r requirements.txt`
2. **Node.js** LTS (уже нужен для `desktop/`)
3. **Rust** — https://www.rust-lang.org/tools/install (для `npm run tauri dev` / сборки exe)
4. WebView2 — обычно уже есть в Windows 10/11
5. В `desktop/`: `npm install`

`start-radar-desktop.bat` сам поднимает **`radar_control.py`** (HTTP `127.0.0.1:18765`), затем Tauri. Второй API не откроется (`data\.radar_desktop.lock`).

### Сборка exe (после установки Rust)

```bat
cd desktop
npm run tauri build
```

Exe: `desktop\src-tauri\target\release\` (имя по `productName` в `tauri.conf.json`).

### Legacy PyQt6

`.venv\Scripts\python.exe scripts\radar_desktop.py` — **deprecated**, не развивается. Ярлык переведён на Tauri.

Пауза радара FL/Kwork — только в Telegram-боте (кнопка ℹ), в пульте строки про бота **нет**.

Перед повторным стартом пульт вызывает стоп (как `stop-radar.bat`).

---

## Три окна cmd (запасной способ)

**`scripts\start-radar-full.bat`** → **3 окна** (биржи + TG + join acc2/acc3).

| Окно | Что делает |
|------|------------|
| **FL Radar — birzhi** | FL.ru + Kwork |
| **FL Radar — TG** | acc1: слушает чаты + **сам вступает** в новые |
| **FL Radar — join** | acc2/acc3: вступление в чаты по очереди |

**Только 2 окна** — если ярлык на **`start-radar-all.bat`** или **`start-radar.bat`** (биржи + TG, **без** join acc2/acc3). Для волны 2 на acc2/acc3 нужен **full** или отдельно `scripts\start-join-daemons.bat`.

Перед перезапуском: **`scripts\stop-radar.bat`** или **Stop** в пульте (убирает дубли `tg_main`).

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
| `scripts\start-radar-desktop.bat` | пульт v2 (Tauri + API) |
| `scripts\radar_control.py` | HTTP API пульта |
| `scripts\radar_desktop.py` | legacy PyQt6 |
