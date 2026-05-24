# DESIGN_BRIEF — пульт RawLead v2

**Статус:** v2 · утверждено Lead 2026-05-23 · canvas `r7` · Coder: [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md)  
**Задача:** [`DESIGNER_PROMPT.md`](DESIGNER_PROMPT.md)  
**Live-превью:** `.cursor/projects/c-Users-hramo-uisness/canvases/fl-radar-pult-v2.canvas.tsx`  
**Стек:** Tauri 2 + HTML/CSS · **без PyQt6** (решение Lead 2026-05-20, ADR в git history)

---

## Research

| Референс | Что берём |
|----------|-----------|
| **ЮБуст** ([`u-boost-ref.png`](../design/references/u-boost-ref.png)) | Узкое окно, одна круглая CTA по центру, glow, премиум-тёмный |
| **Tailscale** | Компактный пульт: hero + ряд статусов |
| **Raycast** | Чистая типографика, один фокус |
| **Linear** (dark) | Нейтральный фон, один accent, без неона |

**Не берём:** красный бренд ЮБуст, VPN-копирайт, строка «Пауза FL/Kwork — в Telegram-боте».

---

## Решения владельца (фиксировано)

| Тема | Решение |
|------|---------|
| Главная кнопка | **Play** (idle) / **Stop** (running), иконки, не текст |
| Idle CTA | Синий `#5B8DEF` + **свечение** |
| Running CTA | **Зелёный** `#3DD68C` + свечение; иконка stop белая |
| Нажатие CTA | **Вдавливание** (scale ~0.94, translateY +4px, слабее glow) |
| Заголовок | **RAWLEAD** — слева сверху, крупно (Bahnschrift ~32px) |
| Действие | **Обновить статус** — справа сверху, uppercase link |
| Footer | **by Rode51** — по центру снизу, белый, мелкий рукописный (~15px) |
| Лампы | Подписи «работает» / «нет»; для idle **без** «ожидание» |
| Лампы glow | Свечение по цвету состояния |
| Логи | Раскрываются **вниз** (наружу), не сжимают hero; **свернуть** — белый треугольник |
| by Rode51 | Всегда **под** блоком логов, если логи открыты |
| Статусы | зелёный = работает, красный = упал, серый = idle |
| UX-поток | compact → play → логи вниз → stop → compact |

---

## Токены (CSS variables)

```css
:root {
  --color-bg-app: #0c0e13;
  --color-bg-surface: #141820;
  --color-bg-log: #090b10;
  --color-border: #2a3140;
  --color-border-soft: #1f2430;
  --color-text: #eceef4;
  --color-text-muted: #8b93a7;
  --color-white: #ffffff;
  --color-accent: #5b8def;
  --color-accent-glow: rgba(91, 141, 239, 0.55);
  --color-hero-on: #f8faff;
  --color-status-ok: #3dd68c;
  --color-status-ok-glow: rgba(61, 214, 140, 0.5);
  --color-status-error: #ef6b6b;
  --color-status-error-glow: rgba(239, 107, 107, 0.45);
  --color-status-idle: #5c6370;
  --color-status-idle-glow: rgba(92, 99, 112, 0.35);
  --color-log-text: #9bc18a;
  --font-title: "Bahnschrift SemiBold", "Segoe UI Variable Display", system-ui, sans-serif;
  --font-ui: "Segoe UI Variable Text", "Segoe UI", system-ui, sans-serif;
  --font-signature: "Segoe Script", "Bradley Hand ITC", cursive;
  --hero-size: 220px;
  --icon-play: 128px;
  --icon-stop: 96px;
  --window-width: 400px;
  --radius-window: 16px;
  --radius-pill: 9999px;
}
```

---

## Размеры окна

| Режим | Ширина | Высота |
|-------|--------|--------|
| **Compact** | 400px | ~560px (без панели логов) |
| **Expanded** | 400px | растёт вниз (+ панель логов ~168px) |

Окно **не сжимает** hero при открытии логов — контент добавляется снизу.

---

## Макет (ASCII)

### Compact (idle)

```
┌──────────────────────── 400px ────────────────────────┐
│ RAWLEAD                    [Обновить статус]         │
│                                                       │
│                    (  PLAY 220px )                    │
│                      синий + glow                     │
│                                                       │
│         (●) Биржи    (●) TG    (●) Join              │
│              (без «ожидание»)                         │
│                  by Rode51                            │
└───────────────────────────────────────────────────────┘
```

### Expanded (running, логи открыты)

```
┌──────────────────────── 400px ────────────────────────┐
│ RAWLEAD                    [Обновить статус]         │
│                    (  STOP зелёный )                  │
│         (●) лампы + glow                              │
│ ┌─ Логи ───────────────────────────── [▽ свернуть] ─┐ │
│ │ radar.log | tg_join.log | Статус                  │ │
│ │ …моноширинный хвост…                              │ │
│ └───────────────────────────────────────────────────┘ │
│                  by Rode51                            │
└───────────────────────────────────────────────────────┘
```

---

## Компоненты

### Hero (play / stop)

| Свойство | Idle (play) | Running (stop) |
|----------|-------------|----------------|
| Размер | 220×220 px круг | то же |
| Иконка | play **128px** | stop **96px** |
| Фон | `--color-accent` | `--color-status-ok` |
| Свечение | accent glow | ok glow |
| `:active` | scale 0.94, translateY 4px, glow слабее | то же |
| Цвет иконки | `--color-hero-on` | то же |

### Индикатор процесса

| Свойство | Значение |
|----------|----------|
| Точка | 14×14, круг |
| Glow | по ok / error / idle |
| Подпись | 12px semibold, название процесса |
| Статус-текст | «работает» / «нет» только; idle — пусто |

### Панель логов

| Свойство | Значение |
|----------|----------|
| Позиция | Под лампами, **margin снаружи** вниз |
| Сворачивание | Кнопка: белый треугольник ▼ (открыто) / ▶ (свернуто) |
| Табы | pill: `radar.log` · `tg_join.log` · `Статус` |
| Тело | `--color-bg-log`, mono 11px, `--color-log-text` |

### Подпись

| Элемент | Стиль |
|---------|--------|
| by Rode51 | `--font-signature`, 15px, italic, `--color-white`, center |

---

## Handoff Coder

| Файл (предложение) | Содержимое |
|--------------------|------------|
| `src-tauri/ui/index.html` | Разметка: header, main.hero, lamps, `.log-panel`, footer.signature |
| `src-tauri/ui/styles/tokens.css` | Variables из § Токены |
| `src-tauri/ui/styles/pult.css` | Layout, hero, lamps, logs, pressed state |
| `src-tauri/ui/assets/` | SVG play/stop при необходимости |

**Поведение JS:**

1. Play → start processes, `body.running`, открыть логи (`logsOpen = true`), окно растёт вниз.
2. Stop → stop, compact, закрыть логи.
3. Треугольник — toggle `.log-panel--collapsed` без остановки процессов.
4. Poll ламп ~2.5s; цвета по таблице статусов.

**Не делать:** PyQt6, QSS, текст «ПУСК/ПАУЗА» на кнопке, строка про Telegram-бота, янтарь на running (только зелёный).

---

## Как посмотреть макет

| # | Источник |
|---|----------|
| 1 | Этот brief — токены, ASCII compact/expanded |
| 2 | Canvas: `%USERPROFILE%\.cursor\projects\c-Users-hramo-uisness\canvases\fl-radar-pult-v2.canvas.tsx` |
| 3 | Референс: [`../design/references/u-boost-ref.png`](../design/references/u-boost-ref.png) |

**Сравнить с Coder:** `npm run dev` → http://localhost:1420 (нужен `radar_control`) · или `start-radar-desktop.vbs`. Если в браузере кнопки ок, в Tauri нет — permissions / drag-region.

---

## Ссылка на v1

Старая спека (PyQt/QSS): git history `DESIGN_BRIEF.md` до 2026-05-23. Логика процессов и вкладок **без изменений**.

---

_Утверждено Lead 2026-05-23_
