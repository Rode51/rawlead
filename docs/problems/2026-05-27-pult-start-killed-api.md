# Пульт: ▶ убивает API, health ok но радар мёртв

**Дата:** 2026-05-27  
**Статус:** ✅ решено (Lead hotfix, владелец подтвердил «заработало»)

## Симптом

- `GET /health` → `{"ok": true}`
- Пульт: `Радар: error sending request …/start`
- `GET /status`: `running: false`, `ever_started: false`
- Telegram «молчит» — нет `main.py` / `tg_main.py`
- После `POST /start` API часто **падает** (порт пустой)

## Корень

1. **`kill_non_venv_radar_workers` в цепочке `/start`** — матчил `radar_control.py` в `.venv` и **убивал API** вместе с «чужими» python.
2. **`post_spawn` kill** — после spawn резало только что поднятые воркеры.
3. **Bat:** `start /B` + VBS без ожидания → API не живёт; зомби-lock без сброса.

## Решение (2026-05-27)

| Файл | Изменение |
|------|-----------|
| `scripts/radar_spawn_workers.py` | Отдельный spawn; pre-kill только `kill_duplicate(role=main/tg_main)` |
| `scripts/radar_control.py` | `/start` → subprocess `radar_spawn_workers.py`; убран `post_spawn` |
| `scripts/start-radar-desktop-*.bat` | lock, `/MIN`, `/health`, MsgBox |
| `scripts/stop-radar-desktop-full.bat` | удаление lock site+legacy |

## Приёмка

- `POST /start` → `200 {"ok":true}`; `/health` после ▶ жив
- Владелец: пульт Site ▶, радар в логе

## Как не повторить

Канон: [`docs/ops/DESKTOP_LAUNCH.md`](../ops/DESKTOP_LAUNCH.md) § «Антирегресс: пульт / API / ▶».

**Запрещено без теста:** `kill_non_venv` в `/start`; `post_spawn` после spawn; `start /B` для API.
