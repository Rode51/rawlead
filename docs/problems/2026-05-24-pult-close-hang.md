# Пульт: ✕ серый, окно не закрывается (зависание)

**Дата:** 2026-05-24  
**Статус:** fixed ✅ Coder 2026-05-24  
**Связано:** [`2026-05-24-pult-close-stop-logs.md`](2026-05-24-pult-close-stop-logs.md) § C (регрессия приёмки)

## Симптом

1. Радар **▶** (running).
2. Нажать **✕** — кнопка **серая** («Остановка…»), окно **не закрывается**, пульт «завис».

## Вероятная причина (Lead, по коду)

`desktop/src/main.ts`:

- `requestAppClose()` → `setCloseEnabled(false)` → `stopRadarCore()` → `getCurrentWindow().close()`
- `onCloseRequested` всегда делает `event.preventDefault()` и снова вызывает `requestAppClose()`
- При втором входе `closingInProgress === true` → **ранний return**, `close()` больше не вызывается → **deadlock**

Дополнительно: `/stop` до **60 с** — даже без deadlock пользователь видит «зависание».

## Ожидание (Coder)

| # | Готово когда |
|---|----------------|
| D1 | ✕ закрывает окно **≤ 5 с** после стопа (или сразу, если радар не running) |
| D2 | Нет рекурсии `close()` ↔ `onCloseRequested` (флаг `allowClose` / не вызывать `close()` из handler после preventDefault) |
| D3 | При ошибке/таймауте `/stop` — окно **всё равно** закрывается или ✕ снова активен + сообщение |
| D4 | `closingInProgress` сбрасывается в `finally`, кнопка ✕ не залипает |

**Файл:** `desktop/src/main.ts` — `requestAppClose`, `onCloseRequested`, `stopRadarCore`.

## Обходной путь (владелец, пока не починено)

1. **Не жать ✕ повторно** — только усугубляет.
2. `scripts\stop-radar.bat` — убить python-процессы.
3. Диспетчер задач → закрыть **RawLead** / `desktop.exe`.
4. Или **■ Стоп** в пульте, подождать, потом ✕ (может сработать, если running=false).

## Приёмка

1. ▶ → ✕ → окно закрылось, в процессах нет uisness main/tg_main.
2. Alt+F4 — то же.
3. ▶ → ■ → ✕ — закрывается без зависания.
4. API `/stop` недоступен (убить radar_control) — ✕ через **15 с** всё равно закрывает UI или показывает ошибку и разблокирует ✕.

## Решение (2026-05-24)

**v1 (недостаточно):** `allowWindowClose` + `close()` — на Tauri 2 с `onCloseRequested` `close()` может не завершиться; при `closingInProgress` + `preventDefault` — вечный серый ✕.

**v2 (Coder):**

- `forceDestroyWindow()` — `destroy()`, не `close()` (D2)
- `onCloseRequested`: при `closingInProgress` → сразу `destroy()` (не return после preventDefault)
- `stopRadarForClose()` — без `setLogsVisible`/resize; `/stop` 8 с (D1, D3)
- Таймер `CLOSE_FORCE_DESTROY_MS` 12 с — destroy в любом случае (D3)
- Пересборка: `scripts\rebuild-pult.bat` или `desktop\DEV_PULT` + `start-radar-desktop.vbs` (dev)
- ACL: `capabilities/default.json` → `core:window:allow-destroy` (без этого — «destroy not allowed by ACL»)

**Старт мигает и гаснет (2026-05-24):** `radar_control` — Popen с **относительным** `rel_script` (абсолютный путь → exit -1); `process_guard` — `role=main` / `role=tg_main` (не убивать соседа).
