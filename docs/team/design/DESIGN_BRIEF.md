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

## WP лендинг + пульт — handoff (DESIGNER_PROMPT 2026-05-25)

**Статус:** ✅ в коде 2026-05-25 (Coder § W по этому handoff)  
**Источник:** [`DESIGNER_PROMPT.md`](DESIGNER_PROMPT.md) · [`REFERENCE.md`](../../design/wp/REFERENCE.md) §6 · [`feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) §6.1

### Приёмка (владелец / Local)

| # | Проверка |
|---|----------|
| 1 | Скролл главной: секции `.rl-reveal` появляются; кубики FL/Kwork/TG «собираются»; match-bar 0→88% |
| 2 | Hover карточки лида и тарифа — лёгкий lift + тень |
| 3 | FL зелёный `#00A65A`, TG `#0088CC` на кубиках и рамках |
| 4 | Тарифы: **одна** карточка «ИИ-агент», badge «Скоро» справа сверху |
| 5 | Header: **Лента** → `/feed`, CTA **Попробовать →** → `/feed` |
| 6 | Пульт: лампа ok — медленный пульс glow (`prefers-reduced-motion` — без анимации) |

---

### 1. `rawlead.css` — токены (задача 2)

В `:root` заменить:

```css
--rl-source-fl: #00a65a;
--rl-source-tg: #0088cc;
```

В `.rl-source-cube--tg` gradient — убрать хардкод `#0284c7`, использовать:

```css
background: linear-gradient(145deg, #006699, var(--rl-source-tg));
```

---

### 2. `rawlead.css` — motion (задача 1)

**2.1 Reveal** — привести к REFERENCE §6.1 (сейчас 0.85s — слишком медленно):

```css
.rl-reveal {
  opacity: 0;
  transform: translate3d(0, 20px, 0);
  transition: opacity 240ms ease-out, transform 240ms ease-out;
}
.rl-reveal.is-visible {
  opacity: 1;
  transform: none;
}
```

**2.2 Stagger** — реальные классы в теме:

```css
.rl-reveal.is-visible .rl-audience-card,
.rl-reveal.is-visible .rl-feature,
.rl-reveal.is-visible .rl-price-card {
  opacity: 1;
  transform: none;
}
.rl-audience-card,
.rl-feature,
.rl-price-card {
  opacity: 0;
  transform: translate3d(0, 16px, 0);
  transition: opacity 240ms ease-out, transform 240ms ease-out;
}
.rl-reveal.is-visible .rl-audience-card:nth-child(1),
.rl-reveal.is-visible .rl-feature:nth-child(1),
.rl-reveal.is-visible .rl-price-card:nth-child(1) { transition-delay: 0ms; }
.rl-reveal.is-visible .rl-audience-card:nth-child(2),
.rl-reveal.is-visible .rl-feature:nth-child(2) { transition-delay: 40ms; }
.rl-reveal.is-visible .rl-audience-card:nth-child(3),
.rl-reveal.is-visible .rl-feature:nth-child(3) { transition-delay: 80ms; }
```

**2.3 Hover** — REFERENCE §6.3 (добавить в конец блока motion):

```css
.rl-lead-card,
.rl-price-card {
  transition: transform 150ms ease-out, box-shadow 150ms ease-out, border-color 150ms ease-out;
}
.rl-lead-card:hover,
.rl-price-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  border-color: #c8c8d0;
}
```

**2.4 Match-bar** — REFERENCE §6.4:

```css
.rl-match__fill {
  width: 0;
  transition: width 600ms ease-out;
}
.rl-reveal.is-visible .rl-match__fill,
.rl-match.is-visible .rl-match__fill {
  width: var(--match-value, 0%);
}
```

**2.5 Micro-press** — §6.5:

```css
.rl-btn:active {
  transform: scale(0.97);
  transition: transform 80ms ease-out;
}
```

**2.6 Кубики** — §6.6 (до `is-visible` на `.rl-flow__sources`):

```css
.rl-flow__sources .rl-source-cube {
  opacity: 0;
  transition: transform 400ms ease-out, opacity 400ms ease-out;
}
.rl-flow__sources .rl-source-cube:nth-child(1) {
  transform: translateX(-80px) translateY(40px) rotate(-8deg);
}
.rl-flow__sources .rl-source-cube:nth-child(2) {
  transform: translateX(0) translateY(60px) rotate(4deg);
}
.rl-flow__sources .rl-source-cube:nth-child(3) {
  transform: translateX(80px) translateY(40px) rotate(-6deg);
}
.rl-flow__sources.is-visible .rl-source-cube:nth-child(1) {
  transform: rotate(-7deg) translateX(-6px);
  opacity: 1;
  transition-delay: 0ms;
}
.rl-flow__sources.is-visible .rl-source-cube:nth-child(2) {
  transform: rotate(5deg) translateX(10px);
  opacity: 1;
  transition-delay: 80ms;
}
.rl-flow__sources.is-visible .rl-source-cube:nth-child(3) {
  transform: rotate(-4deg) translateX(-4px);
  opacity: 1;
  transition-delay: 160ms;
}
```

Убрать дублирующие `transform` из базовых `.rl-source-cube--fl` … `--tg` **или** оставить только в блоке `is-visible` выше.

**2.7 Pricing single + badge** (задача 3):

```css
.rl-pricing--single {
  display: grid;
  grid-template-columns: minmax(280px, 400px);
  justify-content: center;
}
.rl-price-card__badge {
  position: absolute;
  top: 1rem;
  right: 1rem;
  margin: 0;
}
```

**2.8 `prefers-reduced-motion`** — расширить существующий `@media`:

```css
@media (prefers-reduced-motion: reduce) {
  .rl-audience-card,
  .rl-feature,
  .rl-price-card,
  .rl-flow__sources .rl-source-cube {
    opacity: 1;
    transform: none;
    transition: none;
  }
  .rl-match__fill {
    width: var(--match-value, 88%);
    transition: none;
  }
  .rl-btn:active {
    transform: none;
  }
}
```

---

### 3. `flow.php` — match-bar (задача 1)

Заменить span fill:

```html
<span class="rl-match__fill" style="--match-value: 88%"></span>
```

(убрать `width:88%` из inline)

---

### 4. `rawlead-scroll.js` — IO (задача 1 / §6.7)

Добавить к селектору наблюдения:

```js
var motionTargets = main.querySelectorAll(".rl-reveal, .rl-flow__sources");
```

Порог для sources: `threshold: 0.15` (как REFERENCE). Остальная логика — без изменений (unobserve после срабатывания).

---

### 5. `pricing-preview.php` (задача 3)

Один план, без цикла `foreach` по трём тарифам:

```php
$contact = rawlead_page_url('contact');
$plan = [
    'name'  => __('ИИ-агент', 'rawlead-kadence-child'),
    'price' => __('от 300 ₽/мес', 'rawlead-kadence-child'),
    'items' => [
        __('Match по тегам', 'rawlead-kadence-child'),
        __('Рыночная цена', 'rawlead-kadence-child'),
        __('Черновик отклика', 'rawlead-kadence-child'),
        __('Push в TG', 'rawlead-kadence-child'),
    ],
    'badge' => __('Скоро', 'rawlead-kadence-child'),
    'cta'   => __('Ранний доступ', 'rawlead-kadence-child'),
];
```

Разметка: `<div class="rl-pricing rl-pricing--single">` · одна `<article class="rl-price-card">` · badge · CTA → `$contact` · убрать ссылку «Все тарифы» внизу (или заменить на «Связаться →» → contact).

Заголовок секции: **«Тариф»** или оставить «Тарифы» — на усмотрение Lead; в промпте — блок про один продукт.

---

### 6. `header.php` (задача 4)

```php
$feed = rawlead_page_url('feed');

$nav = [
    'home'    => [__('Главная', 'rawlead-kadence-child'), $home],
    'feed'    => [__('Лента', 'rawlead-kadence-child'), $feed],
    'how'     => [__('Как работает', 'rawlead-kadence-child'), rawlead_page_url('how')],
    'pricing' => [__('Тарифы', 'rawlead-kadence-child'), $pricing],
    'faq'     => [__('FAQ', 'rawlead-kadence-child'), rawlead_page_url('faq')],
    'contact' => [__('Контакты', 'rawlead-kadence-child'), rawlead_page_url('contact')],
];
```

CTA:

```php
<a class="rl-btn rl-btn--primary" href="<?php echo esc_url($feed); ?>">
  <?php esc_html_e('Попробовать →', 'rawlead-kadence-child'); ?>
</a>
```

Active state: если `is_page('feed')` или path `feed` — класс `is-active` на пункте «Лента».

---

### 7. `desktop/src/styles/pult.css` (задача 5)

После блока `.lamp__dot--ok { … }`:

```css
@keyframes lamp-pulse {
  0%,
  100% {
    box-shadow:
      0 0 1px 0 rgba(255, 255, 255, 0.5) inset,
      0 0 3px 1px var(--color-status-ok-glow),
      0 0 12px 5px var(--color-status-ok-glow),
      0 0 26px 12px var(--color-status-ok-bloom);
  }
  50% {
    box-shadow:
      0 0 1px 0 rgba(255, 255, 255, 0.5) inset,
      0 0 6px 3px var(--color-status-ok-glow),
      0 0 22px 10px var(--color-status-ok-bloom),
      0 0 36px 16px rgba(22, 163, 74, 0.08);
  }
}

.lamp__dot--ok {
  animation: lamp-pulse 3s ease-in-out infinite;
}

@media (prefers-reduced-motion: reduce) {
  .lamp__dot--ok {
    animation: none;
  }
}
```

---

### Файлы (итого для Coder)

| Файл | Задачи |
|------|--------|
| `wordpress/.../assets/css/rawlead.css` | 1, 2 |
| `wordpress/.../assets/js/rawlead-scroll.js` | 1 |
| `wordpress/.../template-parts/rawlead/flow.php` | 1 |
| `wordpress/.../template-parts/rawlead/pricing-preview.php` | 3 |
| `wordpress/.../template-parts/rawlead/header.php` | 4 |
| `desktop/src/styles/pult.css` | 5 |

**Не трогать:** `src/`, API, шаблоны `/feed` `/cabinet` (фаза 3d).

---

## Ссылка на v1

Старая спека (PyQt/QSS): git history `DESIGN_BRIEF.md` до 2026-05-23. Логика процессов и вкладок **без изменений**.

---

_Утверждено Lead 2026-05-23_
