# Запуск с рабочего стола

## Пульт v2 (Tauri + HTML) — рекомендуется

**Один ярлык, без чёрных cmd:**

| Способ | Команда / файл |
|--------|----------------|
| Двойной клик (без консоли) | **`scripts\start-radar-desktop.vbs`** |
| Двойной клик (с консолью в dev) | **`scripts\start-radar-desktop.bat`** |
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

**Без чёрного PowerShell:**

1. Готовый файл: **`scripts\start-radar-desktop.vbs`**
2. ПКМ по **`.vbs`** → **Отправить** → **Рабочий стол (создать ярлык)**

Окно cmd **не** мелькает (режим 0). Пульт **без** стандартной полосы Windows (`decorations: false`); свернуть/закрыть — кнопки в UI справа сверху.

**Через bat (будет консоль в dev-режиме):**

1. Проводник → `uisness\scripts\`
2. ПКМ по **`start-radar-desktop.bat`** → **Отправить** → **Рабочий стол (создать ярлык)**
3. ПКМ по ярлыку → **Свойства** → **Рабочая папка:** `C:\Users\…\uisness` (корень проекта)
4. По желанию: **Сменить значок** → любой `.ico`

**После сборки exe** (удобнее, без окна npm):

1. `cd desktop` → `npm run tauri build`
2. Exe: `desktop\src-tauri\target\release\fl-radar.exe` (или `desktop.exe`)
3. ПКМ по exe → **Отправить** → **Рабочий стол**
4. В свойствах ярлыка **Объект:** полный путь к exe; **Рабочая папка:** `…\uisness` (чтобы находил `.venv` и `data\`)

Пульт **сам** поднимает `radar_control.py` только из bat. Ярлык **только на exe** — сначала один раз запусти bat или добавь в Coder задачу «exe + sidecar API».

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

---

## Проблемы

| Симптом | Причина | Решение |
|---------|---------|---------|
| `cargo metadata` · **program not found** | Rust не установлен или **нет в PATH** | См. ниже § Rust |
| API не отвечает | `radar_control` не запущен | `.venv\Scripts\python.exe scripts\radar_control.py` |
| Второй пульт | lock | Закрыть старый, `scripts\stop-radar.bat` |

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
