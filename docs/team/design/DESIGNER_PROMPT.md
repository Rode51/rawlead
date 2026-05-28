# Designer — § SITE-POLISH (2026-05-28) **→ сейчас**

**Контекст:** [rawlead.ru](https://rawlead.ru) на VPS · stress отложен · владелец хочет **ЛК + регистрация + UX + тексты** до нагрузочных тестов.

**→ Сейчас @designer:** макет/спека для Coder (CSS в `rawlead.css`, PHP только если Lead согласует отдельно).

| # | Экран | Суть |
|---|--------|------|
| **sp1** | **`/cabinet/`** | Вход (TG Widget + fallback), блок навыков, match-лента, кнопка «Написать отклик», пустые состояния, mobile thumb-zone |
| **sp2** | **Регистрация/вход** | Один путь: «Войти через Telegram» → кабинет; ошибки: бот не стартовал, домен не в BotFather |
| **sp3** | **`/lenta/` на прод** | Filter-bar, skeleton, «Горячий», фильтр источника (после API `?source=`) |
| **sp4** | **Лендинг** | Hero + live feed preview — тексты с Product c1–c4 |

**Файлы:** обновить [`feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) § «Кабинет polish» · [`REFERENCE.md`](../../design/wp/REFERENCE.md) при расхождении с прод.

**Сдача:** `DESIGNER_PROMPT` § SITE-POLISH ✅ · handoff `@coder` § SITE-POLISH p5.

---

# Designer — § REVOLUTION CSS (E3, 2026-05-28)

**Роль:** Designer (CSS-исполнитель)  
**Токены:** [`DESIGN_SYSTEM.md`](DESIGN_SYSTEM.md) § WordPress REVOLUTION  
**Спека страниц:** [`../../design/wp/REFERENCE.md`](../../design/wp/REFERENCE.md) v3 · [`../../design/wp/feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) v2  
**Каталог навыков:** [`../product/SKILLS_TOOLS_CATALOG.md`](../product/SKILLS_TOOLS_CATALOG.md)

**Файлы (можно трогать):**
- `wordpress/rawlead-kadence-child/assets/css/rawlead.css` — **главный файл**

**Файлы (не трогать):**
- `src/`, `scripts/`, `desktop/`, PHP-шаблоны, JS-логика
- `rawlead-feed.js`, `rawlead-cabinet.js` — только CSS-имена классов читать, не менять

---

## Задача

Пересобрать CSS сайта под **REVOLUTION**-направление.  
Всё в `rawlead.css`. PHP и JS не трогаешь — только CSS-классы по спеке.

---

## CSS-переменные (Custom Properties) — установить в `:root`

```css
:root {
  /* REVOLUTION WP */
  --rl-bg-page:        #FAFAF8;
  --rl-bg-section:     #F3F3EF;
  --rl-bg-inverse:     #1A1A2E;
  --rl-text-primary:   #18181B;
  --rl-text-body:      #3F3F46;
  --rl-text-muted:     #71717A;
  --rl-text-inverse:   #FFFFFF;
  --rl-border:         #E4E4E7;
  --rl-cta:            #4F46E5;
  --rl-cta-hover:      #4338CA;
  --rl-cta-text:       #FFFFFF;
  --rl-match-fill:     #4F46E5;
  --rl-source-fl:      #00A65A;
  --rl-source-kwork:   #EA580C;
  --rl-source-tg:      #0088CC;
  --rl-shadow-card:    0 2px 12px rgba(0,0,0,0.07);
  --rl-shadow-hover:   0 8px 28px rgba(0,0,0,0.12);
  --rl-radius-card:    20px;
  --rl-radius-btn:     999px;
  --rl-radius-chip:    999px;
  --rl-chip-active-bg: #4F46E5;
  --rl-chip-skill-bg:  #EEF2FF;
  --rl-chip-skill-txt: #4F46E5;
  --font-main:         'Manrope', sans-serif;
}
```

---

## Задачи по блокам

### T1 — Глобальный фон и типографика

- `body`: `background: var(--rl-bg-page); font-family: var(--font-main); color: var(--rl-text-primary)`
- Убрать `font-family: 'Unbounded'` везде — заменить на Manrope 800 для display
- H1/H2 всего сайта: Manrope 800, letter-spacing `-0.02em`
- Секции с чередующимся фоном: `background: var(--rl-bg-section)`
- Footer: `background: var(--rl-bg-inverse); color: var(--rl-text-inverse)`

### T2 — Кнопки

```css
/* primary */
.rl-btn, .rl-btn--primary {
  background: var(--rl-cta);
  color: var(--rl-cta-text);
  border-radius: var(--rl-radius-btn);
  border: none;
  padding: 12px 24px;
  font: 600 15px/1 var(--font-main);
  transition: background 150ms ease-out, transform 80ms ease-out;
}
.rl-btn:hover { background: var(--rl-cta-hover); }
.rl-btn:active { transform: scale(0.97); }

/* secondary */
.rl-btn--secondary {
  background: transparent;
  border: 1.5px solid var(--rl-cta);
  color: var(--rl-cta);
}
.rl-btn--secondary:hover { background: var(--rl-chip-skill-bg); }

/* ghost */
.rl-btn--ghost {
  background: none; border: none;
  color: var(--rl-cta);
  padding: 0;
}
```

### T3 — Header продуктовых страниц

```css
.rl-header {
  position: sticky; top: 0; z-index: 100;
  height: 56px;
  background: var(--rl-bg-page);
  border-bottom: 1px solid transparent;
  transition: border-color 150ms;
}
.rl-header--scrolled { border-bottom-color: var(--rl-border); }
```

Mobile: height `52px`

### T4 — Filter Bar (горизонтальная плашка)

```css
.rl-filter-bar {
  position: sticky;
  top: 56px; /* высота header */
  z-index: 90;
  background: var(--rl-bg-page);
  border-bottom: 1px solid var(--rl-border);
  height: 52px;
  display: flex;
  align-items: center;
  gap: 6px;
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
  background: var(--rl-bg-section);
  border: 1px solid var(--rl-border);
  color: var(--rl-text-body);
  font: 600 13px/1 var(--font-main);
  cursor: pointer; white-space: nowrap;
  transition: background 150ms, color 150ms, border-color 150ms;
}
.rl-cat-chip.is-active {
  background: var(--rl-chip-active-bg);
  color: #FFFFFF;
  border-color: var(--rl-chip-active-bg);
}
```

**Dropdown-кнопки [Навыки ▾] [Сортировка ▾]:**
```css
.rl-filter-dropdown-btn {
  margin-left: auto; /* прижать вправо */
  flex-shrink: 0;
  /* те же стили что у .rl-cat-chip */
  padding: 6px 12px;
}
.rl-filter-dropdown-btn.has-selection {
  background: var(--rl-chip-skill-bg);
  border-color: var(--rl-cta);
  color: var(--rl-cta);
}
```

### T5 — Карточка лида (REVOLUTION)

```css
.rl-lead-card {
  background: #FFFFFF;
  border-radius: var(--rl-radius-card);
  box-shadow: var(--rl-shadow-card);
  padding: 20px 24px;
  cursor: pointer;
  transition: box-shadow 150ms ease-out, transform 150ms ease-out;
  /* убрать: border, border-color */
}
.rl-lead-card:hover {
  box-shadow: var(--rl-shadow-hover);
  transform: translateY(-2px);
}
```

Mobile: padding `16px 18px`

**Match-bar:**
```css
.rl-match__track {
  height: 4px; border-radius: 2px;
  background: var(--rl-border);
  overflow: hidden;
}
.rl-match__fill {
  height: 100%;
  background: var(--rl-match-fill);
  width: 0;
  transition: width 600ms ease-out;
}
.is-visible .rl-match__fill { width: var(--match-value); }
```

**Теги-чипы навыков:**
```css
.rl-skill-chip {
  display: inline-block;
  padding: 3px 10px;
  border-radius: var(--rl-radius-chip);
  background: var(--rl-bg-section);
  border: 1px solid var(--rl-border);
  color: var(--rl-text-muted);
  font: 600 11px/1.4 var(--font-main);
}
.rl-skill-chip.is-active {
  background: var(--rl-chip-skill-bg);
  color: var(--rl-chip-skill-txt);
  border-color: #C7D2FE;
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
  border: 1px solid var(--rl-border);
  border-radius: 16px;
  box-shadow: var(--rl-shadow-hover);
  padding: 20px;
  z-index: 200;
}
/* Mobile — bottom sheet */
@media (max-width: 767px) {
  .rl-skills-panel {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    top: auto;
    width: 100%;
    max-width: 100%;
    border-radius: 20px 20px 0 0;
    transform: translateY(100%);
    transition: transform 300ms ease-out;
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
  top: 56px; /* под header */
  z-index: 85;
  background: var(--rl-bg-page);
  border-bottom: 1px solid var(--rl-border);
  padding: 8px 16px;
  display: flex; flex-wrap: wrap; gap: 6px; align-items: center;
  min-height: 48px;
}
.rl-my-skill-chip {
  /* как rl-skill-chip.is-active, плюс × */
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
  gap: 16px;
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
  border: 1px solid var(--rl-border);
  box-shadow: var(--rl-shadow-card);
  color: var(--rl-cta);
  font: 700 16px/1 var(--font-main);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: box-shadow 150ms;
}
.rl-bug-fab:hover { box-shadow: var(--rl-shadow-hover); }
@media (max-width: 767px) {
  .rl-bug-fab { bottom: 80px; right: 16px; }
}
```

### T10 — Skeleton-карточки

```css
@keyframes rl-pulse {
  0%, 100% { background-color: var(--rl-bg-section); }
  50%       { background-color: var(--rl-border); }
}
.rl-skeleton-card {
  border-radius: var(--rl-radius-card);
  height: 140px;
  animation: rl-pulse 1.4s ease-in-out infinite;
}
```

### T11 — Лендинг: Hero, Live Preview, Тарифы

**Hero:**
```css
.rl-hero {
  min-height: 100svh;
  display: flex; flex-direction: column; justify-content: center;
  padding: 80px 16px 48px;
}
.rl-hero__h1 {
  font: 800 clamp(40px, 8vw, 64px)/1.1 var(--font-main);
  letter-spacing: -0.02em;
  color: var(--rl-text-primary);
  margin-bottom: 20px;
}
.rl-hero__sub {
  font: 400 18px/1.55 var(--font-main);
  color: var(--rl-text-body);
  max-width: 520px;
  margin-bottom: 32px;
}
```

**Live Preview:**
```css
.rl-live-preview {
  background: var(--rl-bg-section);
  padding: 48px 16px;
}
/* Карточки превью — те же .rl-lead-card, но non-interactive */
.rl-live-preview .rl-lead-card { pointer-events: none; }
```

**Тариф-карточка:**
```css
.rl-pricing-card {
  background: #FFFFFF;
  border-radius: var(--rl-radius-card);
  box-shadow: var(--rl-shadow-card);
  padding: 32px;
  max-width: 360px;
  margin: 0 auto;
}
```

### T12 — Анимации (scroll-reveal)

```css
.rl-reveal {
  opacity: 0;
  transform: translateY(20px);
}
.rl-reveal.is-visible {
  opacity: 1; transform: none;
  transition: opacity 240ms ease-out, transform 240ms ease-out;
}
.rl-reveal:nth-child(1) { transition-delay: 0ms; }
.rl-reveal:nth-child(2) { transition-delay: 40ms; }
.rl-reveal:nth-child(3) { transition-delay: 80ms; }
.rl-reveal:nth-child(4) { transition-delay: 120ms; }
```

---

## Что убрать из rawlead.css

- Любые `font-family: 'Unbounded'` → Manrope 800
- `background: #FFFFFF` на body → `#FAFAF8`
- `background: #0A0A0A` на .rl-btn → `#4F46E5`
- `.rl-lead-card { border: 1px solid #E8E8EC }` → убрать border, добавить shadow
- `border-radius: 16px` на карточках → `20px`
- `.rl-match__fill { background: #2563EB }` → `#4F46E5`
- `.rl-filter-sidebar` (sidebar 280px) — убрать или скрыть (`display: none`); заменяет filter bar
- Стиль манифест-полосы `#0A0A0A` → не нужна (секция убрана с лендинга)
- `ghost-num` 120px серые цифры 01/02/03 — убрать

---

## Сдача

По завершении обнови `docs/team/common/STATUS.md` — строку E3 Designer.  
Handoff → `@lead-architect` для `CODER_PROMPT § PRE-LAUNCH-UX`.

---

_Lead Designer → @designer · REVOLUTION CSS · 2026-05-28_
