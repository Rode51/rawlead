# Пульт v2: кнопки снова не работают + дизайн ≠ canvas

**Статус:** решено · 2026-05-23  
**Связано:** [`2026-05-23-pult-tauri-buttons-design.md`](2026-05-23-pult-tauri-buttons-design.md) (было «решено» — регрессия)

---

## Симптомы

- **Play / stop** — не реагирует
- **Свернуть / закрыть** (свои кнопки в шапке) — не работают
- **Вид** — не как у Designer ([`DESIGN_BRIEF`](../team/DESIGN_BRIEF.md), canvas `fl-radar-pult-v2`)

---

## Эталон для Coder

- [`DESIGN_BRIEF.md`](../team/DESIGN_BRIEF.md)
- Canvas: `~\.cursor\projects\c-Users-hramo-uisness\canvases\fl-radar-pult-v2.canvas.tsx`
- [`PULT_DESIGN_PREVIEW.md`](../ops/PULT_DESIGN_PREVIEW.md)

---

## Гипотезы

| # | Что проверить |
|---|----------------|
| 1 | Tauri 2: permissions `core:window:*` (minimize, close, set-size) в `capabilities/default.json` |
| 2 | `@tauri-apps/plugin-http` — `initHttpFetch()` до кликов; ошибки в консоль |
| 3 | `data-tauri-drag-region` не перекрывает кнопки (refresh, win-controls, hero — `no-drag`) |
| 4 | CSS hero: `pointer-events`, z-index, glow не блокирует клик |
| 5 | `radar_control` на :18765 — health в браузере |

---

## Решение

**Причина:** `core:default` включает только `core:window:default` (чтение окна), без `allow-minimize` / `allow-close` / `allow-set-size` / `allow-start-dragging`. Клики по hero/win-кнопкам также перехватывались drag-region без `no-drag` + `stopPropagation`.

**Фикс:** явные permissions в `capabilities/default.json`; `no-drag` + `blockDragOnClick` на интерактивных элементах; баннер `#status-banner` при ошибке `/health` и API.

**Файлы:** `capabilities/default.json`, `main.ts`, `pult.css`, `index.html`.
