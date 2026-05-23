# Как посмотреть макет пульта (Designer)

Три источника — **эталон**, с чем Coder должен совпасть.

---

## 1. Текст + ASCII (в репозитории)

[`docs/team/DESIGN_BRIEF.md`](../team/DESIGN_BRIEF.md) — токены, размеры, макеты compact/expanded.

---

## 2. Интерактивный макет (Canvas в Cursor)

Файл (вне `uisness/`, в данных Cursor):

`%USERPROFILE%\.cursor\projects\c-Users-hramo-uisness\canvases\fl-radar-pult-v2.canvas.tsx`

**Как открыть:** в Cursor **File → Open File** → вставь путь выше → открой как **Canvas** (если предложит).

Там можно переключать: idle / running / логи открыты / лампы error — ревизия `r7`.

---

## 3. Референс «как ЮБуст»

[`docs/design/references/u-boost-ref.png`](../design/references/u-boost-ref.png)

---

## Сравнить с тем, что собрал Coder

| Способ | Что |
|--------|-----|
| **Браузер** | `radar_control` запущен → `cd desktop` → `npm run dev` → http://localhost:1420 |
| **Tauri** | ярлык `start-radar-desktop.vbs` |

Если в **браузере** кнопки работают, а в Tauri — нет → баг в Tauri (permissions / drag-region).

---

_Lead · 2026-05-23_
