# Designer — § NEO-BRUTALIST CSS (2026-05-28) **⏸ после SITE-ACCEPT-GATE**

**Роль:** Designer (CSS-исполнитель)
**Токены:** [`DESIGN_SYSTEM.md`](DESIGN_SYSTEM.md) § WordPress NEO-BRUTALIST
**Спека страниц:** [`../../design/wp/REFERENCE.md`](../../design/wp/REFERENCE.md) v4 · [`../../design/wp/feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md)

**Файлы (можно трогать):**
- `wordpress/rawlead-kadence-child/assets/css/rawlead.css` — **главный файл**

**Файлы (не трогать):**
- `src/`, `scripts/`, `desktop/`, PHP-шаблоны, JS-логика
- `rawlead-feed.js`, `rawlead-cabinet.js` — только CSS-имена классов читать, не менять

---

## Задача

Пересобрать CSS сайта под **NEO-BRUTALIST** направление.
Всё в `rawlead.css`. PHP и JS не трогаешь — только CSS-классы по спеке.

---

## CSS-переменные (Custom Properties) — установить в `:root`

```css
:root {
  /* NEO-BRUTALIST WP */
  --rl-bg-page:          #FFFFFF;
  --rl-bg-section:       #F5F5F0;
  --rl-bg-hero:          #FACC15;
  --rl-bg-alt:           #F3E8FF;
  --rl-bg-inverse:       #0A0A0A;

  --rl-text-primary:     #0A0A0A;
  --rl-text-body:        #1A1A1A;
  --rl-text-muted:       #525252;
  --rl-text-inverse:     #FFFFFF;
  --rl-text-on-hero:     #0A0A0A;

  --rl-border:           #0A0A0A;
  --rl-border-light:     #D4D4D4;
  --rl-border-width:     2px;

  --rl-cta:              #0A0A0A;
  --rl-cta-text:         #FFFFFF;
  --rl-cta-hover-bg:     #FACC15;
  --rl-cta-hover-text:   #0A0A0A;

  --rl-match-fill:       #0A0A0A;

  --rl-source-fl:        #00A65A;
  --rl-source-kwork:     #EA580C;
  --rl-source-tg:        #0088CC;

  --rl-shadow-card:      4px 4px 0px #0A0A0A;
  --rl-shadow-hover:     6px 6px 0px #0A0A0A;
  --rl-shadow-fab:       2px 2px 0px #0A0A0A;

  --rl-radius-card:      4px;
  --rl-radius-btn:       0px;
  --rl-radius-chip:      2px;

  --rl-chip-active-bg:   #0A0A0A;
  --rl-chip-active-txt:  #FFFFFF;
  --rl-chip-skill-bg:    #FACC15;
  --rl-chip-skill-txt:   #0A0A0A;

  --font-main:           'Manrope', sans-serif;
}
```

---

## Задачи по блокам

### T1 — Глобальный фон и типографика

- `body`: `background: var(--rl-bg-page); font-family: var(--font-main); color: var(--rl-text-primary)`
- H1 hero: `font: 900 clamp(56px, 10vw, 96px)/1.05 var(--font-main); letter-spacing: -0.03em`
- H2 секции: `font: 800 clamp(32px, 5vw, 44px)/1.1 var(--font-main); letter-spacing: -0.02em`
- Body text: `font: 400 16px/1.55 var(--font-main); color: var(--rl-text-body)`
- Секции с чередующимся фоном: `background: var(--rl-bg-section)`
- Hero секция: `background: var(--rl-bg-hero)`
- Alt секция (Как работает): `background: var(--rl-bg-alt)`
- Footer: `background: var(--rl-bg-inverse); color: var(--rl-text-inverse)`

### T2 — Кнопки

```css
/* primary — чёрная, hover жёлтая */
.rl-btn, .rl-btn--primary {
  background: var(--rl-cta);
  color: var(--rl-cta-text);
  border: var(--rl-border-width) solid var(--rl-border);
  border-radius: var(--rl-radius-btn);
  padding: 14px 28px;
  font: 700 15px/1 var(--font-main);
  letter-spacing: 0.01em;
  cursor: pointer;
  transition: background 120ms ease-out, color 120ms ease-out, transform 60ms ease-out;
}
.rl-btn:hover, .rl-btn--primary:hover {
  background: var(--rl-cta-hover-bg);
  color: var(--rl-cta-hover-text);
}
.rl-btn:active { transform: scale(0.97); }

/* secondary — белая, чёрная рамка */
.rl-btn--secondary {
  background: transparent;
  border: var(--rl-border-width) solid var(--rl-border);
  color: var(--rl-text-primary);
}
.rl-btn--secondary:hover { background: var(--rl-bg-section); }

/* ghost — только текст */
.rl-btn--ghost {
  background: none;
  border: none;
  color: var(--rl-text-primary);
  padding: 0;
  text-decoration: underline;
  text-underline-offset: 3px;
}
```

### T3 — Header продуктовых страниц

```css
.rl-header {
  position: sticky; top: 0; z-index: 100;
  height: 56px;
  background: var(--rl-bg-page);
  border-bottom: var(--rl-border-width) solid var(--rl-border);
  /* НЕ transparent — чёрная рамка всегда */
}
```

Mobile: height `52px`

### T4 — Filter Bar (горизонтальная плашка)

```css
.rl-filter-bar {
  position: sticky;
  top: 56px;
  z-index: 90;
  background: var(--rl-bg-page);
  border-bottom: var(--rl-border-width) solid var(--rl-border);
  height: 52px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 16px;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
}
.rl-filter-bar::-webkit-scrollbar { display: none; }
```

**Чипы категорий:**
```css
.rl-cat-chip {
  flex-shrink: 0;
  scroll-snap-align: start;
  display: inline-flex; align-items: center; gap: 4px;
  padding: 6px 14px;
  border-radius: var(--rl-radius-chip);
  background: var(--rl-bg-page);
  border: var(--rl-border-width) solid var(--rl-border);
  color: var(--rl-text-primary);
  font: 700 13px/1 var(--font-main);
  cursor: pointer; white-space: nowrap;
  transition: background 120ms, color 120ms;
}
.rl-cat-chip.is-active {
  background: var(--rl-chip-active-bg);
  color: var(--rl-chip-active-txt);
}
```

**Dropdown-кнопки [Навыки ▾] [Сортировка ▾]:**
```css
.rl-filter-dropdown-btn {
  margin-left: auto;
  flex-shrink: 0;
  padding: 6px 12px;
  /* те же стили что .rl-cat-chip */
}
.rl-filter-dropdown-btn.has-selection {
  background: var(--rl-chip-skill-bg);
  color: var(--rl-chip-skill-txt);
  border-color: var(--rl-border);
}
```

### T5 — Карточка лида (NEO-BRUTALIST)

```css
.rl-lead-card {
  background: #FFFFFF;
  border: var(--rl-border-width) solid var(--rl-border);
  border-radius: var(--rl-radius-card);
  box-shadow: var(--rl-shadow-card);
  padding: 20px 24px;
  cursor: pointer;
  transition: box-shadow 120ms ease-out, transform 120ms ease-out;
}
.rl-lead-card:hover {
  box-shadow: var(--rl-shadow-hover);
  transform: translate(-2px, -2px);
}
```

Mobile: padding `16px 18px`

**Match-bar:**
```css
.rl-match__track {
  height: 4px;
  border-radius: 0px;  /* без скругления — брутал */
  background: var(--rl-border-light);
  overflow: hidden;
}
.rl-match__fill {
  height: 100%;
  background: var(--rl-match-fill);
  width: 0;
  transition: width 500ms ease-out;
}
.is-visible .rl-match__fill { width: var(--match-value); }
```

**Теги-чипы навыков:**
```css
.rl-skill-chip {
  display: inline-block;
  padding: 3px 10px;
  border-radius: var(--rl-radius-chip);
  background: var(--rl-bg-page);
  border: var(--rl-border-width) solid var(--rl-border-light);
  color: var(--rl-text-muted);
  font: 700 11px/1.4 var(--font-main);
}
.rl-skill-chip.is-active {
  background: var(--rl-chip-skill-bg);
  color: var(--rl-chip-skill-txt);
  border-color: var(--rl-border);
}
```

### T6 — Skills dropdown panel

```css
.rl-skills-panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 420px;
  max-width: calc(100vw - 32px);
  background: #FFFFFF;
  border: var(--rl-border-width) solid var(--rl-border);
  border-radius: var(--rl-radius-card);
  box-shadow: var(--rl-shadow-hover);
  padding: 20px;
  z-index: 200;
}
@media (max-width: 767px) {
  .rl-skills-panel {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    top: auto;
    width: 100%;
    max-width: 100%;
    border-radius: 4px 4px 0 0;
    border-bottom: none;
    transform: translateY(100%);
    transition: transform 280ms ease-out;
    max-height: 80vh;
    overflow-y: auto;
  }
  .rl-skills-panel.is-open { transform: translateY(0); }
}
```

### T7 — My Skills strip (кабинет)

```css
.rl-my-skills {
  position: sticky;
  top: 56px;
  z-index: 85;
  background: var(--rl-bg-page);
  border-bottom: var(--rl-border-width) solid var(--rl-border);
  padding: 8px 16px;
  display: flex; flex-wrap: wrap; gap: 6px; align-items: center;
  min-height: 48px;
}
.rl-my-skill-chip {
  /* как rl-skill-chip.is-active — жёлтый + чёрная рамка */
  padding: 5px 10px 5px 12px;
  gap: 6px;
}
.rl-filter-bar--under-my-skills { top: calc(56px + 48px); }
```

### T8 — Сетка ленты (2 колонки desktop, 1 mobile)

```css
.rl-feed-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  max-width: 900px;
  margin: 0 auto;
  padding: 24px 16px;
}
@media (max-width: 767px) {
  .rl-feed-list { grid-template-columns: 1fr; }
}
```

### T9 — Report bug FAB

```css
.rl-bug-fab {
  position: fixed;
  bottom: 24px; right: 20px;
  z-index: 300;
  width: 40px; height: 40px;
  border-radius: 50%;
  background: #FFFFFF;
  border: var(--rl-border-width) solid var(--rl-border);
  box-shadow: var(--rl-shadow-fab);
  color: var(--rl-text-primary);
  font: 700 16px/1 var(--font-main);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: box-shadow 120ms, transform 120ms;
}
.rl-bug-fab:hover {
  box-shadow: 3px 3px 0px #0A0A0A;
  transform: translate(-1px, -1px);
}
@media (max-width: 767px) {
  .rl-bug-fab { bottom: 80px; right: 16px; }
}
```

### T10 — Skeleton-карточки

```css
@keyframes rl-pulse {
  0%, 100% { background-color: var(--rl-bg-section); }
  50%       { background-color: var(--rl-border-light); }
}
.rl-skeleton-card {
  border: var(--rl-border-width) solid var(--rl-border-light);
  border-radius: var(--rl-radius-card);
  box-shadow: 4px 4px 0px var(--rl-border-light);
  height: 140px;
  animation: rl-pulse 1.4s ease-in-out infinite;
}
```

### T11 — Лендинг: Hero, Live Preview, Тарифы

**Hero (жёлтый блок):**
```css
.rl-hero {
  min-height: 100svh;
  background: var(--rl-bg-hero);
  display: flex; flex-direction: column; justify-content: center;
  padding: 80px 16px 48px;
  border-bottom: var(--rl-border-width) solid var(--rl-border);
}
.rl-hero__h1 {
  font: 900 clamp(56px, 10vw, 96px)/1.05 var(--font-main);
  letter-spacing: -0.03em;
  color: var(--rl-text-on-hero);
  margin-bottom: 20px;
}
.rl-hero__sub {
  font: 400 20px/1.55 var(--font-main);
  color: var(--rl-text-on-hero);
  opacity: 0.75;
  max-width: 560px;
  margin-bottom: 36px;
}
/* Кнопка в hero: чёрная → hover белая с рамкой */
.rl-hero .rl-btn--primary:hover {
  background: #FFFFFF;
  color: #0A0A0A;
  border-color: #0A0A0A;
}
```

**Live Preview:**
```css
.rl-live-preview {
  background: var(--rl-bg-page);
  border-top: var(--rl-border-width) solid var(--rl-border);
  border-bottom: var(--rl-border-width) solid var(--rl-border);
  padding: 48px 16px;
}
.rl-live-preview__label {
  font: 700 12px/1 var(--font-main);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--rl-text-muted);
  margin-bottom: 24px;
}
.rl-live-preview .rl-lead-card { pointer-events: none; }
```

**Как работает (фиолетовый блок):**
```css
.rl-how-section {
  background: var(--rl-bg-alt);
  border-top: var(--rl-border-width) solid var(--rl-border);
  border-bottom: var(--rl-border-width) solid var(--rl-border);
  padding: 80px 16px;
}
```

**Тариф-карточка:**
```css
.rl-pricing-card {
  background: #FFFFFF;
  border: var(--rl-border-width) solid var(--rl-border);
  border-radius: var(--rl-radius-card);
  box-shadow: var(--rl-shadow-card);
  padding: 32px;
  max-width: 360px;
  margin: 0 auto;
}
```

**Form inputs:**
```css
.rl-input, .rl-textarea {
  width: 100%;
  border: var(--rl-border-width) solid var(--rl-border);
  border-radius: var(--rl-radius-btn);
  padding: 12px 16px;
  font: 400 16px/1 var(--font-main);
  color: var(--rl-text-primary);
  background: #FFFFFF;
  transition: box-shadow 120ms;
}
.rl-input:focus, .rl-textarea:focus {
  outline: none;
  box-shadow: 2px 2px 0px #0A0A0A;
}
```

### T12 — Анимации (scroll-reveal)

```css
.rl-reveal {
  opacity: 0;
  transform: translateY(16px);
}
.rl-reveal.is-visible {
  opacity: 1; transform: none;
  transition: opacity 200ms ease-out, transform 200ms ease-out;
}
.rl-reveal:nth-child(1) { transition-delay: 0ms; }
.rl-reveal:nth-child(2) { transition-delay: 40ms; }
.rl-reveal:nth-child(3) { transition-delay: 80ms; }
.rl-reveal:nth-child(4) { transition-delay: 120ms; }
```

---

## Что убрать из rawlead.css

- `border-radius: 20px` на карточках → `4px`
- `border-radius: 999px` на кнопках и chips → `0px` / `2px`
- `box-shadow: 0 2px 12px rgba(0,0,0,0.07)` → `4px 4px 0px #0A0A0A`
- `background: #FAFAF8` на body → `#FFFFFF`
- `background: #F3F3EF` на секциях → `#F5F5F0`
- `background: #4F46E5` на кнопках → `#0A0A0A`
- `background: #4338CA` hover кнопки → `#FACC15`
- `background: #1A1A2E` footer → `#0A0A0A`
- `background: #EEF2FF` skill chip active → `#FACC15`
- `.rl-lead-card { border-color: ... }` — заменить на `border: 2px solid #0A0A0A`
- `transform: translateY(-2px)` hover → `transform: translate(-2px, -2px)`
- `transition: border-color 150ms` в header → убрать (рамка всегда)
- Стиль манифест-полосы — секция убрана
- `ghost-num` серые цифры 01/02/03 — убрать

---

## Сдача

По завершении обнови `docs/team/common/STATUS.md` — строку NEO-BRUTALIST Designer.
Handoff → `@lead-architect` для `CODER_PROMPT § NEO-BRUTALIST`.

---

_Lead Designer → @designer · NEO-BRUTALIST CSS · 2026-05-28_
