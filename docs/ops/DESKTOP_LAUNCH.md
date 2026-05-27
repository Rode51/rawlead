# Запуск с рабочего стола

## Пульт v2 (Tauri + HTML) — рекомендуется

**Один ярлык, без чёрных cmd:**

| Способ | Команда / файл |
|--------|----------------|
| Site (без консоли) | **`scripts\start-radar-desktop-site.vbs`** |
| Legacy (без консоли) | **`scripts\start-radar-desktop-legacy.vbs`** |
| Legacy / общий bat | `start-radar-desktop.bat` (консоль в dev) |
| **Полный стоп** site+legacy | **`scripts\stop-radar-desktop-full.vbs`** |
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

### Ярлык на рабочий стол

**Только VBS** (не `desktop.exe` — иначе bat не убивает зомби-API):

| Профиль | Файл ярлыка |
|---------|-------------|
| Site | `scripts\start-radar-desktop-site.vbs` |
| Legacy | `scripts\start-radar-desktop-legacy.vbs` |
| Полный стоп | `scripts\stop-radar-desktop-full.vbs` |

1. ПКМ по нужному **`.vbs`** → **Отправить** → **Рабочий стол (создать ярлык)**
2. ПКМ ярлык → **Свойства** → **Объект** должен заканчиваться на этот `.vbs`

Окно cmd **не** мелькает. Пульт **без** стандартной полосы Windows; **✕** — стоп воркеров + завершение API **этого** профиля (`/shutdown`).

**Сборка exe** (`scripts\rebuild-pult.bat` или `npm run tauri build`) — для запуска из bat/VBS, **не** для ярлыка на рабочий стол.

### Legacy PyQt6

`.venv\Scripts\python.exe scripts\radar_desktop.py` — **deprecated**, не развивается. Ярлык переведён на Tauri.

Пауза радара FL/Kwork — только в Telegram-боте (кнопка ℹ), в пульте строки про бота **нет**.

Перед повторным стартом: **`stop-radar-desktop-full.vbs`** — site+legacy: API, `main`, `neon_legacy_consumer`, `tg_main`, join. `stop-radar.bat` — воркеры без API (в т.ч. consumer).

### Антирегресс: пульт / API / ▶ (2026-05-27)

**Симптом:** `health ok`, но ▶ → `error /start`, боты молчат, лог не обновляется.

| Причина | Как не повторить |
|---------|------------------|
| **`health` ≠ радар работает** | `health` = только `radar_control`. Воркеры — после **▶** (`POST /start`). |
| **`kill_non_venv` при ▶** | Убивал **venv** `radar_control`. **Не** вызывать `kill_non_venv` в цепочке `/start` — только `kill_duplicate` по роли `main` / `tg_main`. |
| **`post_spawn` kill** | Убивал только что поднятые воркеры. **Не** возвращать без теста ▶. |
| **`start /B` API в bat** | API умирал с закрытием cmd/VBS. Только **`start /MIN`**, ждать `/health` 8+3 с. |
| **Зомби-lock** | После сбоя — `data\.radar_desktop_site.lock` / `_legacy.lock`. Сбрасывает **full stop** и bat. |
| **Ярлык на `desktop.exe`** | Bat не запускается → нет API. Ярлык **только** на `start-radar-desktop-*-.vbs`. |
| **Проверка health сразу после full stop** | Порт **пустой** — норма. Сначала VBS или `Start-Process pythonw radar_control`. |

**Канон запуска (владелец):**

1. `stop-radar-desktop-full.vbs` → пауза 3 с  
2. `start-radar-desktop-site.vbs` (и при необходимости Legacy) → дождаться **без** красного баннера  
3. **▶ один раз** на профиль  
4. `data\radar_site.log` — свежие `радар:старт` / `тг:пульс`

**Аварийно** (API жив, ▶ красный):  
`.venv\Scripts\python.exe scripts\radar_spawn_workers.py --profile site`

**Coder:** не трогать `radar_spawn_workers.py` / `/start` без приёмки ▶ + `/health` после ▶. Тикет: [`problems/2026-05-27-pult-start-killed-api.md`](../problems/2026-05-27-pult-start-killed-api.md).

**Вкладка «Статус» в пульте:** при открытых логах UI опрашивает `/status-text` каждые ~1.5 с — это не радар, а обновление экрана. Смотреть воронку — вкладка **radar** / файл `data\radar_site.log`.

---

## Три окна cmd (запасной способ)

**`scripts\start-radar-full.bat`** → **3 окна** (биржи + TG + join acc2/acc3).

| Окно | Что делает |
|------|------------|
| **RawLead — birzhi** | FL.ru + Kwork |
| **RawLead — TG** | acc1: слушает чаты + **сам вступает** в новые |
| **RawLead — join** | acc2/acc3: вступление в чаты по очереди |

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
| `scripts\stop-radar.bat` | стоп воркеров (без API) |
| `scripts\stop-radar-desktop-full.bat` / `.vbs` | полный стоп site + legacy |
| `scripts\start-radar-desktop-site.vbs` | пульт Site + API :18775 |
| `scripts\start-radar-desktop-legacy.vbs` | пульт Legacy + API :18765 |
| `scripts\start-radar-desktop.bat` | пульт Legacy (с консолью) |
| `scripts\radar_control.py` | HTTP API пульта |
| `scripts\radar_desktop.py` | legacy PyQt6 |

---

## Проблемы

| Симптом | Причина | Решение |
|---------|---------|---------|
| `cargo metadata` · **program not found** | Rust не установлен или **нет в PATH** | См. ниже § Rust |
| API не отвечает | `radar_control` не запущен | `.venv\Scripts\python.exe scripts\radar_control.py` |
| Второй пульт / зомби API | lock / system python | `stop-radar-desktop-full.vbs`, ярлык только на `.vbs` |

### Rust (обязательно для Tauri)

1. Скачай **rustup**: https://www.rust-lang.org/tools/install → `rustup-init.exe`
2. В установщике: **1) Proceed with installation (default)**
3. **Закрой все cmd/PowerShell** и Cursor-терминал → открой заново
4. Проверка:
   ```powershell
   cargo --version
   rustc --version
   ```
   Должны показать версии, не «не найдено».
5. Если всё ещё нет — в PowerShell:
   ```powershell
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";$env:USERPROFILE\.cargo\bin", "User")
   ```
   Перезапусти терминал.
6. Снова: `scripts\start-radar-desktop.bat`

**Пока Rust чинишь (временно):**

- Только API + UI в браузере:
  ```bat
  .venv\Scripts\pythonw.exe scripts\radar_control.py
  cd desktop
  npm run dev
  ```
  Открыть http://localhost:1420
- Или legacy: `.venv\Scripts\python.exe scripts\radar_desktop.py`
