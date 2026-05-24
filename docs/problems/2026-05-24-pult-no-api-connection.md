# Пульт: «Нет связи с API» при живом radar_control

**Дата:** 2026-05-24  
**Статус:** решено (Mechanic 2026-05-24, доработка после «всё та же проблема»)  
**Связь:** [`2026-05-24-duplicate-python-processes.md`](2026-05-24-duplicate-python-processes.md)

---

## Симптом

Пульт (`desktop.exe`) показывает красную строку  
`Нет связи с API (127.0.0.1:18765). Запустите start-radar-desktop.vbs`  
при том что API **отвечает** (`{"ok": true}` через PowerShell/curl).

## Диагностика (Lead 2026-05-24)

| Проверка | Результат |
|----------|-----------|
| `Invoke-WebRequest http://127.0.0.1:18765/health` | `{"ok": true}` ✅ |
| `Invoke-WebRequest http://127.0.0.1:18765/status` | корректный JSON ✅ |
| `POST /start` через PowerShell | `{"ok": true}` ✅ |
| Пульт показывает соединение | ❌ всегда «Нет связи» |
| Пересборка пульта (rebuild-pult.bat) | выполнена 16:27 — не помогла |
| VPN включён / выключен | не влияет |

## Корневая причина

`desktop/src/main.ts` использует `@tauri-apps/plugin-http` fetch (IPC `plugin:http|fetch`).  
Этот fetch проходит через Rust ACL → **заблокирован** несмотря на разрешения в `capabilities/default.json`.

В `lib.rs` уже есть Rust-команда **`radar_api_request`** (reqwest напрямую, без ACL plugin):

```rust
#[tauri::command]
async fn radar_api_request(path: String, method: Option<String>, body: Option<String>)
  -> Result<RadarApiResponse, String>
```

Она зарегистрирована (`.invoke_handler(tauri::generate_handler![radar_api_request])`), но **JS её не вызывает** — использует plugin-http.

## Ожидание (Mechanic)

| # | Готово когда |
|---|--------------|
| M1 | `main.ts` `apiGet()` и `apiPost()` используют `invoke("radar_api_request", {path, method, body})` вместо `httpFetch` |
| M2 | `RadarApiResponse` парсится: `JSON.parse(result.body)` для GET, `result.status` для проверки |
| M3 | `initHttpFetch()` и import `@tauri-apps/plugin-http` удалены (или отключены) |
| M4 | `scripts\rebuild-pult.bat` запущен — пересборка успешна |
| M5 | Пульт показывает соединение (нет красной строки) при живом `radar_control` |

## Файлы

**Можно трогать:**
- `desktop/src/main.ts` — заменить fetch на invoke
- `desktop/src/styles/pult.css` — без изменений (не трогать)

**Не трогать:**
- `desktop/src-tauri/src/lib.rs` — команда уже есть, не менять
- `desktop/src-tauri/capabilities/default.json` — не трогать
- `src/`, `scripts/` — вне скоупа

## Как проверить

1. `scripts\rebuild-pult.bat` — должно завершиться без ошибок
2. Запустить `start-radar-desktop.vbs`
3. Пульт открылся — **нет красной строки** «Нет связи»
4. API: `http://127.0.0.1:18765/health` → `{"ok": true}`

## Паттерн замены в main.ts

```typescript
// БЫЛО:
const res = await httpFetch(`${API_BASE}${path}`);
const data = await res.json();

// СТАЛО (invoke):
const { invoke } = await import("@tauri-apps/api/core");
const raw = await invoke<{ status: number; body: string }>(
  "radar_api_request",
  { path, method: "GET", body: null }
);
const data = JSON.parse(raw.body) as T;
```

Аналогично для `apiPost` — `method: "POST"`, `body: JSON.stringify(payload)`.

---

## Решение (Mechanic 2026-05-24)

`apiGet` / `apiPost` переведены на Rust-команду `radar_api_request` через `invoke` (reqwest, без ACL `plugin:http`).

- Удалены `initHttpFetch()`, `httpFetch` и импорт `@tauri-apps/plugin-http`.
- Добавлены `radarRequest()` + `parseRadarResponse()`; для `/logs/*` и `/status-text` — ответ как текст.
- В браузерном превью (не Tauri) остаётся `globalThis.fetch` на `API_BASE`.

### Изменённые файлы

- `desktop/src/main.ts`

### Сборка

- `npm run build` + `npm run tauri build` — OK (после закрытия занятого `desktop.exe`, иначе «Отказано в доступе»).
- В `dist` есть `invoke("radar_api_request", …)`, `plugin-http` в бандле нет.

### Как проверить (владелец)

1. Закрыть старый пульт, если был открыт.
2. `scripts\start-radar-desktop.vbs` (или `rebuild-pult.bat`, если меняли код вручную).
3. Пульт открылся — **нет** красной строки «Нет связи с API».
4. `http://127.0.0.1:18765/health` → `{"ok": true}`; кнопка ▶ / лампы обновляются.

### Критерии M1–M5

| # | Статус |
|---|--------|
| M1 | ✅ `apiGet` / `apiPost` → `invoke("radar_api_request")` |
| M2 | ✅ `parseRadarResponse` по `status` + `JSON.parse(body)` |
| M3 | ✅ `initHttpFetch` и plugin-http убраны |
| M4 | ✅ tauri build release OK |
| M5 | ⏳ UI — проверка владельцем после перезапуска vbs |

---

## Доработка (Mechanic, повторный отчёт)

**Симптом:** после первого фикса (invoke) красная строка осталась; API с PowerShell — `{"ok": true}`.

**Доп. причина:** `reqwest` в `radar_api_request` шёл через **системный прокси** (VPN/Windows). `curl`/PowerShell на localhost часто обходят прокси — отсюда расхождение.

**Исправления:**

1. `lib.rs` — `Client::builder().no_proxy()` перед запросом к `127.0.0.1:18765`.
2. `main.ts` — статический `import { invoke }`; при ошибке invoke → **fallback** `globalThis.fetch` (разрешён в CSP).
3. `permissions/allow-radar-api-request.toml` + capability `allow-radar-api-request`.
4. В баннере — текст реальной ошибки (`API: …`), не только общая фраза.

**Файлы:** `desktop/src/main.ts`, `desktop/src-tauri/src/lib.rs`, `desktop/src-tauri/capabilities/default.json`, `desktop/src-tauri/permissions/allow-radar-api-request.toml`

**Пересборка:** `npm run build` + `tauri build` OK.

**Важно:** закрыть старый `desktop.exe`, запускать только `scripts\start-radar-desktop.vbs` (не ярлык из старого MSI, если он на другой путь).

---

## Доработка 2 (Mechanic, «опять ошибка»)

**Логи / факты на машине:**

- `data/radar.log` — API жив (`радар:старт`, `цикл:старт`); **нет** записей об ошибке HTTP.
- PowerShell: `/health` и `/status` → OK.
- **Два** `radar_control.py`: `.venv` + **system Python311** — оба в командной строке (см. тикет duplicate-python-processes).
- Порт `:18765` слушал system-python; venv-экземпляр — лишний.
- У `desktop.exe` десятки `TIME_WAIT` на `:18765` — TCP до API **доходит**, ошибка не «API мёртв».

**Реальные баги пульта (регрессия после перехода на Tauri invoke):**

1. **`invoke` + таймаут 10 с** — зависший IPC → «Таймаут … /status» → красный баннер, хотя API отвечает curl/PowerShell.
2. **Успешный `pollStatus` не вызывал `clearStatus()`** — один сбой при старте → баннер навсегда.
3. Раньше работал обычный **WebView fetch** (до `plugin-http` / invoke).

**Фикс:**

- `radarRequest` = только `webFetch` (как до регрессии; CSP разрешает localhost).
- `clearStatus()` при успешном poll.
- `start-radar-desktop.bat` — двойной sweep `kill_all_radar_control` + `taskkill` порта.

**Файлы:** `desktop/src/main.ts`, `scripts/start-radar-desktop.bat`, `src/process_guard.py`

**Корень «Failed to fetch»:** WebView fetch в Tauri не ходит на localhost надёжно; плюс **API был выключен** (порт :18765 пуст). Вернён **invoke/reqwest** + понятное сообщение «запустите vbs».

**Файлы (доработка 3):** `desktop/src/main.ts` — invoke primary, `formatConnectionError()`.
