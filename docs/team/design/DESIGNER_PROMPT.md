# Designer — промпт исполнителя

| | |
|--|--|
| **→ Сейчас** | § **WAVE-UX-MOBILE** (прокрутить к якорю ниже) · handoff → **@lead-architect** → `@coder` |
| **Кто читает что** | [`LEAD_DESIGN.md`](LEAD_DESIGN.md) § «Один активный план» |
| **Канон WP** | [`REFERENCE.md`](../../design/wp/REFERENCE.md) v5 · [`feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) |

⛔ **Всё ниже первого блока «АРХИВ»** — сданные волны. **@designer / @coder не читать** без явной ссылки Lead.

**Решения владельца:** [`LEAD_DESIGN_PROMPT.md`](LEAD_DESIGN_PROMPT.md) § WAVE-4-UX-FIX

---

# ⛔ АРХИВ — не читать по умолчанию

---

# Designer — § WAVE-2-CSS (**✅ сдано 2026-05-29 → brief**)

**Роль:** Designer (Staff UI/UX) · Senior CSS  
**Сдача:** [`docs/design/wp/wave-2-css-brief.md`](../../design/wp/wave-2-css-brief.md) — **канон для Coder** (аудит кода + финальные сниппеты)  
**Ассеты:** [`docs/design/assets/`](../../design/assets/) — концепты ✅ · production SVG — в brief § w2-7/w2-8  
**Решения:** [`LEAD_DESIGN_PROMPT.md`](LEAD_DESIGN_PROMPT.md) § DESIGN-WAVE-2

**Wave 1 (NEO CSS) ✅ prod.** Wave 2 = анимации + 100%-взрыв + пагинация + марка + иконки категорий + `by Rode51` — **реализация → @coder** после ревью Lead.

---

## § O41-WAVE3 — Gumroad-level: hero/card split + H1 + secondary CTA (**✅ prod 2026-05-29**)

**Дата:** 2026-05-29 · **Приоритет:** P0 (после Wave 2 деплоя)  
**Спека:** [`docs/design/wp/wave-2-css-brief.md`](../../design/wp/wave-2-css-brief.md) § w3-delta-O41  
**Решения Lead:** [`LEAD_DESIGN_PROMPT.md`](LEAD_DESIGN_PROMPT.md) § DESIGN-WAVE-3/O41  
**REFERENCE:** [`docs/design/wp/REFERENCE.md`](../../design/wp/REFERENCE.md) §3.2 (обновлено O41)

### Суть задачи

Wave 2 деплоен, но владелец видит «косметику, не пересборку». Цель: **Gumroad-уровень**.  
Ключевое изменение: hero = только текст+CTA, live preview = отдельная белая секция.

### Файлы для правки

| Файл | Что делать |
|------|-----------|
| `wordpress/rawlead-kadence-child/template-parts/rawlead/hero.php` | Убрать карточки из hero; проверить H1 = «Лиды без шума»; добавить `.rl-hero__cta-group` с primary + secondary |
| `wordpress/rawlead-kadence-child/template-parts/rawlead/` | Создать `live-preview.php` — белая секция с 3 preview-карточками |
| `wordpress/rawlead-kadence-child/functions.php` | Подключить `live-preview.php` в `page-home.php` после hero (или где hero вызывается) |
| `wordpress/rawlead-kadence-child/assets/css/rawlead.css` | Добавить CSS из brief § w3-delta-O41 (hero split, secondary CTA, typography spacing) |

**Не трогать:** `src/`, `scripts/`, API-логика, все остальные страницы кроме лендинга `/`.

### Задачи (порядок)

#### O41-1 — Hero: убрать карточки из жёлтой зоны

1. В `hero.php` — найти и убрать блок live preview (если он там)
2. Убедиться что `.rl-hero` содержит только: H1 + sub + `.rl-hero__cta-group`
3. Добавить `border-bottom: 4px solid #0a0a0a` к `.rl-hero`

#### O41-2 — H1: канонический текст

В `hero.php` строго:
```html
<h1 class="rl-hero__title">Лиды без шума</h1>
```
Если там любой другой текст — заменить.

#### O41-3 — CTA-группа: primary + secondary

```html
<div class="rl-hero__cta-group">
  <a href="/lenta/" class="rl-btn rl-btn--primary">Смотреть ленту →</a>
  <a href="#pricing-preview" class="rl-btn rl-btn--secondary">Тарифы ↓</a>
</div>
```

CSS: см. brief § w3-delta-O41 «Проблема 3».

#### O41-4 — Live Preview: отдельная белая секция

Создать `live-preview.php`:
```html
<section class="rl-live-preview">
  <div class="rl-container">
    <p class="rl-live-preview__label">Последние заказы из ленты</p>
    <div class="rl-live-preview__cards">
      <!-- 3 статичных карточки (не из API, mock данные) -->
      <!-- используют тот же HTML что .rl-lead-card в ленте -->
    </div>
    <a href="/lenta/" class="rl-live-preview__link">Открыть все →</a>
  </div>
</section>
```

CSS: см. brief § w3-delta-O41 «Проблема 1».

#### O41-5 — Hero typography: breathing room

CSS из brief § w3-delta-O41 «Проблема 4» — `.rl-hero__title`, `.rl-hero__sub`, `.rl-hero__inner`.

### Приёмка (сдать Lead Designer)

- [ ] `Ctrl+F5` `/` — hero фон жёлтый, только H1 + sub + 2 кнопки
- [ ] H1 текст = «Лиды без шума»
- [ ] Secondary CTA видна на жёлтом фоне (чёрная рамка)
- [ ] Live Preview = белая секция ниже hero с `border-top: 4px solid #0A0A0A`
- [ ] 3 карточки в preview: `border: 2px solid #0A0A0A` + shadow
- [ ] Mobile 390px: CTA вертикально, кнопки full-width, нет горизонтального скролла

### Не в scope O41

- Правки ленты `/lenta/` — не трогать
- Правки `/cabinet/` — не трогать  
- Кабинет, api_server, scripts — не трогать

---

## § WAVE-2-CSS — задача исполнителю

### Файлы

| Файл | Действие |
|------|----------|
| `wordpress/rawlead-kadence-child/assets/css/rawlead.css` | **Главный** — всё CSS сюда |
| `wordpress/rawlead-kadence-child/assets/js/rawlead-feed.js` | Только читать классы + добавить IntersectionObserver и пагинацию |
| `wordpress/rawlead-kadence-child/assets/js/rawlead-cabinet.js` | Только читать классы |

**Не трогать:** `src/`, `scripts/`, PHP-шаблоны, API-логика в JS.

---

### w2-1 — Scroll-анимации (IntersectionObserver)

Добавить в `rawlead-feed.js` (JS-блок scroll observe):

```js
// Wave 2: scroll reveal
const rlObserver = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.classList.add('is-visible');
      rlObserver.unobserve(e.target);
    }
  });
}, { threshold: 0.08 });

document.querySelectorAll('.rl-lead-card, .rl-section-reveal').forEach(el => rlObserver.observe(el));
```

CSS для reveal (добавить в `rawlead.css`):

```css
/* --- Wave 2: scroll reveal --- */
/* Карточка ленты = .rl-lead-card (не .rl-card — канон brief § w2-1) */
.rl-feed-list > .rl-lead-card,
#rl-cabinet-list > .rl-lead-card {
  opacity: 0;
  transform: translateY(24px);
}
.rl-feed-list > .rl-lead-card.is-visible,
#rl-cabinet-list > .rl-lead-card.is-visible {
  opacity: 1;
  transform: none;
  transition: opacity 320ms ease-out, transform 320ms ease-out;
}
.rl-feed-list > .rl-lead-card.is-visible:nth-child(2),
#rl-cabinet-list > .rl-lead-card.is-visible:nth-child(2) { transition-delay: 60ms; }
.rl-feed-list > .rl-lead-card.is-visible:nth-child(3),
#rl-cabinet-list > .rl-lead-card.is-visible:nth-child(3) { transition-delay: 120ms; }
.rl-feed-list > .rl-lead-card.is-visible:nth-child(4),
#rl-cabinet-list > .rl-lead-card.is-visible:nth-child(4) { transition-delay: 180ms; }
.rl-feed-list > .rl-lead-card.is-visible:nth-child(5),
#rl-cabinet-list > .rl-lead-card.is-visible:nth-child(5) { transition-delay: 240ms; }

.rl-section-reveal {
  opacity: 0;
  transform: translateY(16px);
}
.rl-section-reveal.is-visible {
  opacity: 1;
  transform: none;
  transition: opacity 400ms ease-out, transform 400ms ease-out;
}
```

Применить класс `.rl-section-reveal` к блокам лендинга (через PHP добавить класс или JS querySelectorAll по нужным секциям).

---

### w2-2 — Match-бар: анимированное заполнение

Текущая проблема: бар не анимируется. Исправить в CSS:

```css
/* --- Wave 2: match-bar animate --- */
.rl-match__fill {
  width: 0 !important; /* старт */
  transition: width 600ms ease-out;
}
.rl-card.is-visible .rl-match__fill {
  width: var(--match-value) !important; /* берём из inline style */
}
```

В JS (`rawlead-feed.js`) убедиться, что `--match-value` проставляется как `style="--match-value: 88%"` на `.rl-match__fill` (или на родителе). Если сейчас проставляется как `width: 88%` напрямую — переделать на CSS-переменную.

---

### w2-3 — 100% match: «взрыв»

Карточка с `keyword_match === 100` должна получать класс `.rl-lead-card--perfect` (добавить в JS при рендере карточки).

```css
/* --- Wave 2: perfect match card --- */
.rl-lead-card--perfect {
  border: 2px solid #FACC15;
  box-shadow: 4px 4px 0 #FACC15;
}
.rl-lead-card--perfect.is-visible {
  animation: rl-perfect-pulse 700ms ease-out forwards;
}
@keyframes rl-perfect-pulse {
  0%   { box-shadow: 4px 4px 0 #FACC15, 0 0 0 0 rgba(250,204,21,0.5); }
  50%  { box-shadow: 4px 4px 0 #FACC15, 0 0 0 14px rgba(250,204,21,0.25); }
  100% { box-shadow: 4px 4px 0 #FACC15, 0 0 0 22px rgba(250,204,21,0); }
}

.rl-badge--perfect {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #FACC15;
  color: #0A0A0A;
  border: 2px solid #0A0A0A;
  border-radius: 2px;
  font-family: var(--rl-font);
  font-weight: 800;
  font-size: 11px;
  letter-spacing: 0.06em;
  padding: 2px 8px;
  text-transform: uppercase;
}
```

Бейдж «ИДЕАЛЬНО ✦» — добавить в JS при `keyword_match === 100` рядом с source badge.

---

### w2-4 — Пагинация (замена infinite scroll)

Убрать infinite scroll trigger. Добавить кнопку «Загрузить ещё»:

```css
/* --- Wave 2: пагинация --- */
.rl-feed-pagination {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px 0 24px;
}
.rl-btn--load-more {
  min-width: 200px;
  position: relative;
}
.rl-btn--load-more.is-loading {
  opacity: 0.6;
  pointer-events: none;
}
.rl-feed-pagination__count {
  font-size: 13px;
  color: var(--rl-text-muted);
  font-family: var(--rl-font);
}
```

HTML (JS вставляет после карточек):
```html
<div class="rl-feed-pagination">
  <button class="rl-btn rl-btn--load-more">Загрузить ещё →</button>
  <span class="rl-feed-pagination__count">Показано 20 из 87</span>
</div>
```

---

### w2-5 — Иконки категорий

Заменить текстовые лейблы чипов на иконка + текст:

| Категория | Иконка (inline SVG или символ) |
|-----------|-------------------------------|
| Разработка | `</>` |
| Дизайн | `✦` |
| Маркетинг | мегафон SVG 16px |
| Тексты | `Aa` |

```css
.rl-chip--category .rl-chip__icon {
  display: inline-block;
  width: 16px;
  height: 16px;
  line-height: 16px;
  font-size: 12px;
  font-weight: 800;
  margin-right: 4px;
  vertical-align: middle;
}
```

---

### w2-6 — «by Rode51»

**Header** (`.rl-header__logo` или рядом с лого-текстом):

```css
.rl-logo-byline {
  display: block;
  font-size: 11px;
  font-weight: 400;
  color: var(--rl-text-primary);
  opacity: 0.4;
  letter-spacing: 0.02em;
  line-height: 1;
  margin-top: 1px;
}
```

HTML внутри логотипа:
```html
<a class="rl-header__logo" href="/">
  RawLead
  <span class="rl-logo-byline">by Rode51</span>
</a>
```

**Footer** (в `.rl-footer__copy`):
```html
<span class="rl-footer__byline">RawLead · by Rode51</span>
```
```css
.rl-footer__byline { opacity: 0.5; font-size: 12px; }
```

---

### w2-7 — Марка (favicon / header icon)

Концепт: `docs/design/assets/rawlead-mark-concept.png`

Генерить production SVG в [recraft.ai](https://recraft.ai):
```
"Bold geometric radar signal mark, 3 concentric quarter-circle arcs from bottom-left corner,
flat black vector, SVG, no text, favicon-safe, neo-brutalist"
style: Vector art, model: recraftv3
```

После генерации:
- Сохранить как `docs/design/assets/rawlead-mark-v1.svg`
- В header рядом с текстом (опционально): `<img src="rawlead-mark-v1.svg" width="20" height="20" alt="">`

---

### w2-8 — Hero geo-декор

Концепт: `docs/design/assets/rawlead-hero-bg-concept.png`

**Не делать полным фоном** — только угловые декоративные элементы:

```css
.rl-hero {
  position: relative;
  overflow: hidden;
}
.rl-hero::before,
.rl-hero::after {
  content: '';
  position: absolute;
  /* SVG-фигуры как background-image — добавить после генерации SVG */
  opacity: 0.12;
  pointer-events: none;
}
.rl-hero::before {
  top: -20px; right: -20px;
  width: 240px; height: 240px;
  /* background-image: url('../images/hero-geo-corner.svg'); */
}
.rl-hero::after {
  bottom: -20px; left: -20px;
  width: 180px; height: 180px;
  transform: rotate(180deg);
}
```

---

### Приёмка (Lead Designer чеклист)

- [ ] Карточки появляются с stagger при скролле
- [ ] Match-бар заполняется анимированно (0→N%)
- [ ] 100%-карточка: жёлтая рамка + пульс-кольцо + бейдж «ИДЕАЛЬНО ✦»
- [ ] Кнопка hover: тень `4→6px` + `translate(-2px, -2px)` за 120ms
- [ ] Кнопка active: scale 0.96 за 60ms
- [ ] «Загрузить ещё» работает, счётчик обновляется
- [ ] «by Rode51» в header (мелко) и footer
- [ ] Иконки категорий в чипах
- [ ] Mobile (390px): анимации работают, touch тапы ≥44px
- [ ] `prefers-reduced-motion`: все transition/animation отключены

```css
@media (prefers-reduced-motion: reduce) {
  .rl-card, .rl-section-reveal { transition: none; opacity: 1; transform: none; }
  .rl-match__fill { transition: none; }
  .rl-lead-card--perfect { animation: none; }
}
```

---

# § NEO-BRUTALIST CSS (Wave 1 — справка, **не переписывать без Lead**)

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

### T13 — TG Login кнопка (кастомная, без iframe)

```css
.rl-tg-login-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  max-width: 400px;
  min-height: 52px;
  background: var(--rl-cta);
  color: var(--rl-cta-text);
  border: var(--rl-border-width) solid var(--rl-border);
  border-radius: var(--rl-radius-btn);
  font: 700 16px/1 var(--font-main);
  letter-spacing: 0.01em;
  cursor: pointer;
  text-decoration: none;
  transition: background 120ms, color 120ms;
}
.rl-tg-login-btn:hover {
  background: var(--rl-cta-hover-bg);
  color: var(--rl-cta-hover-text);
}
@media (max-width: 767px) {
  .rl-tg-login-btn { max-width: 100%; }
}
```

### T14 — Inbox карточки (`/cabinet/` O23)

```css
/* Список откликов */
.rl-inbox-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 640px;
  margin: 0 auto;
  padding: 20px 16px;
}

/* Карточка отклика */
.rl-inbox-card {
  background: #FFFFFF;
  border: var(--rl-border-width) solid var(--rl-border);
  border-radius: var(--rl-radius-card);
  box-shadow: var(--rl-shadow-card);
  overflow: hidden;
}
.rl-inbox-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 20px;
  cursor: pointer;
  min-height: 56px;
}
.rl-inbox-card__title {
  font: 600 15px/1.4 var(--font-main);
  color: var(--rl-text-primary);
  flex: 1;
}
.rl-inbox-card__meta {
  font: 400 12px/1 var(--font-main);
  color: var(--rl-text-muted);
  white-space: nowrap;
}
/* Аккордеон */
.rl-inbox-card__body {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows 280ms ease-out;
}
.rl-inbox-card__body-inner {
  overflow: hidden;
}
.rl-inbox-card.is-open .rl-inbox-card__body {
  grid-template-rows: 1fr;
}
.rl-inbox-card__draft {
  padding: 0 20px 16px;
  border-top: var(--rl-border-width) solid var(--rl-border);
  font: 400 13px/1.6 var(--font-main);
  color: var(--rl-text-body);
  padding-top: 14px;
}
.rl-inbox-card__actions {
  display: flex;
  gap: 8px;
  padding: 0 20px 16px;
}
/* Удалить — деструктивный */
.rl-btn--danger-ghost {
  background: none;
  border: none;
  color: #DC2626;
  padding: 0;
  font: 600 13px/1 var(--font-main);
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 3px;
  min-height: 44px;
}

/* Подписка-блок */
.rl-cabinet-sub {
  max-width: 640px;
  margin: 0 auto;
  padding: 0 16px 20px;
}
.rl-cabinet-sub__card {
  border: var(--rl-border-width) solid var(--rl-border);
  border-radius: var(--rl-radius-card);
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
```

### T15 — TWO-SPEEDS strip

```css
.rl-feed-delay-notice {
  padding: 8px 16px;
  font: 400 13px/1.4 var(--font-main);
  color: var(--rl-text-muted);
  border-bottom: 1px solid var(--rl-border-light);
  /* НЕ sticky — скроллится вместе с контентом */
}
.rl-feed-delay-notice a {
  color: var(--rl-text-muted);
  text-decoration: underline;
  text-underline-offset: 2px;
}
```

### T16 — Hero mobile CTA (full-width stack)

```css
@media (max-width: 767px) {
  .rl-hero {
    padding: 24px 16px 40px;
    min-height: 100svh;
  }
  .rl-hero__h1 {
    font-size: 32px;
    line-height: 1.1;
  }
  .rl-hero__sub {
    font-size: 16px;
    margin-bottom: 32px;
  }
  .rl-hero__cta-group {
    display: flex;
    flex-direction: column;
    gap: 12px;
    width: 100%;
  }
  .rl-hero__cta-group .rl-btn {
    width: 100%;
    min-height: 52px;
    justify-content: center;
  }
  .rl-hero__cta-group .rl-btn--secondary {
    min-height: 48px;
  }
}
```

### T17 — Bottom sheet — базовый слой

```css
.rl-sheet-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 400;
  opacity: 0;
  transition: opacity 280ms ease-out;
  pointer-events: none;
}
.rl-sheet-overlay.is-open {
  opacity: 1;
  pointer-events: auto;
}
.rl-sheet {
  position: fixed;
  bottom: 0; left: 0; right: 0;
  z-index: 410;
  background: #FFFFFF;
  border: var(--rl-border-width) solid var(--rl-border);
  border-radius: 4px 4px 0 0;
  border-bottom: none;
  transform: translateY(100%);
  transition: transform 280ms ease-out;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
}
.rl-sheet.is-open { transform: translateY(0); }

/* Полный sheet (навыки) — 95vh */
.rl-sheet--full {
  max-height: 95vh;
  overflow-y: auto;
}
/* Половинный sheet (сортировка) — 40vh */
.rl-sheet--half {
  max-height: 40vh;
}
/* Handle */
.rl-sheet__handle {
  width: 40px; height: 4px;
  background: var(--rl-border-light);
  border-radius: 2px;
  margin: 12px auto 0;
}
.rl-sheet__content {
  padding: 16px 16px 32px;
}
.rl-sheet__apply-btn {
  position: sticky;
  bottom: 0;
  background: #FFFFFF;
  border-top: var(--rl-border-width) solid var(--rl-border);
  padding: 12px 16px;
}
.rl-sheet__apply-btn .rl-btn {
  width: 100%;
  min-height: 52px;
}
/* Категорийные табы внутри sheet */
.rl-sheet__cat-tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 0 0 12px;
  border-bottom: var(--rl-border-width) solid var(--rl-border);
  margin-bottom: 16px;
}
.rl-sheet__cat-tabs::-webkit-scrollbar { display: none; }
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

_Lead Designer → @designer · NEO-BRUTALIST CSS + Mobile C1 · 2026-05-29_

---

---

---

# → СЕЙЧАС: § WAVE-4-UX-FIX

---

## § WAVE-4-UX-FIX — Coder-ready спека (согласовано владельцем 2026-05-29)

**Приоритет:** P0 — в работу сразу после ревью Lead Architect
**Файлы:** `page-lenta.php` · `page-cabinet.php` · `rawlead-cabinet.js` · `rawlead-feed.js` · `rawlead.css` · `header.php` · `footer.php`
**Решения:** `LEAD_DESIGN_PROMPT.md` § WAVE-4-UX-FIX

---

### V1 — Карточки в /cabinet/ = полная карточка

**Текущее:** тонкие строки «Заголовок · Черновик · Дата».
**Нужно:** та же карточка что в `/lenta/` + блок черновика + удалить.

#### HTML-структура `.rl-inbox-card`

```html
<article class="rl-lead-card rl-inbox-card" data-id="{{id}}">
  <!-- Шапка карточки -->
  <div class="rl-lead-card__head">
    <div class="rl-lead-card__badges">
      <span class="rl-badge rl-badge--source rl-badge--{{source}}">{{source_label}}</span>
      <!-- если keyword_match === 100: -->
      <span class="rl-badge rl-badge--perfect">ИДЕАЛЬНО ✦</span>
    </div>
    <button class="rl-inbox-card__delete" aria-label="Удалить отклик" data-reply-id="{{reply_id}}">✕</button>
  </div>

  <!-- Заголовок -->
  <h3 class="rl-lead-card__title">{{title}}</h3>

  <!-- Бюджет -->
  <div class="rl-lead-card__budget">Бюджет: {{budget}}</div>

  <!-- Match-bar -->
  <div class="rl-match" aria-label="Совместимость {{match}}%">
    <div class="rl-match__fill" style="--match-value: {{match}}%"></div>
  </div>
  <div class="rl-lead-card__meta">
    <span class="rl-match__label">{{match}}%</span>
    <span class="rl-views">👁 {{views}}</span>
  </div>

  <!-- Чипы навыков -->
  <div class="rl-lead-card__chips">
    {{#each skills}}<span class="rl-chip">{{this}}</span>{{/each}}
  </div>

  <!-- Черновик ИИ -->
  <div class="rl-inbox-card__draft">
    {{#if reply_draft}}
      <div class="rl-inbox-card__draft-head">
        <span class="rl-inbox-card__draft-label">Черновик ИИ</span>
        <button class="rl-inbox-card__copy rl-btn rl-btn--ghost" data-copy="{{reply_draft}}">Скопировать</button>
      </div>
      <div class="rl-inbox-card__draft-body">{{reply_draft}}</div>
    {{else}}
      <div class="rl-inbox-card__draft-empty">
        Черновик не сгенерирован · <a href="/lenta/">Открыть в ленте →</a>
      </div>
    {{/if}}
  </div>
</article>
```

#### CSS — добавить в rawlead.css

```css
/* Карточка ЛК */
.rl-inbox-card {
  position: relative;
}

/* Шапка карточки: badges + кнопка удалить */
.rl-lead-card__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

/* Кнопка удалить */
.rl-inbox-card__delete {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  color: var(--rl-text-muted);
  padding: 0 0 0 12px;
  line-height: 1;
  transition: color 120ms ease-out;
  flex-shrink: 0;
}
.rl-inbox-card__delete:hover { color: #0A0A0A; }

/* Блок черновика */
.rl-inbox-card__draft {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--rl-border);
}
.rl-inbox-card__draft-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.rl-inbox-card__draft-label {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--rl-text-muted);
}
.rl-inbox-card__draft-body {
  font-size: 14px;
  line-height: 1.6;
  color: var(--rl-text-body);
  white-space: pre-wrap;
  max-height: 160px;
  overflow-y: auto;
}
.rl-inbox-card__draft-empty {
  font-size: 13px;
  color: var(--rl-text-muted);
}
.rl-inbox-card__draft-empty a {
  color: #0A0A0A;
  text-decoration: underline;
}

/* Состояние после копирования */
.rl-inbox-card__copy.is-copied::after {
  content: ' ✓';
}
```

#### JS — в rawlead-cabinet.js

```js
// Копировать черновик
document.querySelectorAll('.rl-inbox-card__copy').forEach(btn => {
  btn.addEventListener('click', () => {
    navigator.clipboard.writeText(btn.dataset.copy).then(() => {
      btn.classList.add('is-copied');
      btn.textContent = 'Скопировано ✓';
      setTimeout(() => {
        btn.classList.remove('is-copied');
        btn.textContent = 'Скопировать';
      }, 2000);
    });
  });
});

// Удалить отклик
document.querySelectorAll('.rl-inbox-card__delete').forEach(btn => {
  btn.addEventListener('click', async () => {
    const card = btn.closest('.rl-inbox-card');
    const replyId = btn.dataset.replyId;
    btn.disabled = true;
    try {
      await fetch(`/wp-json/rawlead/v1/me/replies/${replyId}`, {
        method: 'DELETE',
        headers: { 'Authorization': 'Bearer ' + getRawleadToken() }
      });
      card.style.transition = 'opacity 200ms ease-out';
      card.style.opacity = '0';
      setTimeout(() => card.remove(), 200);
    } catch (e) {
      btn.disabled = false;
    }
  });
});
```

---

### V2+V3 — «Загрузить ещё»: логика показа + loading state

**V2:** Кнопка скрыта если `shown >= total`.
**V3:** Спиннер/текст «Загружаем...» — только в момент загрузки.

#### PHP (`page-cabinet.php`, `page-lenta.php`)

Элемент пагинации — рендерить всегда (JS управляет видимостью):

```html
<div class="rl-feed-pagination" id="rl-pagination">
  <button class="rl-btn rl-btn--load-more" id="rl-load-more">
    Ещё лиды <span class="rl-btn__arrow">→</span>
  </button>
  <span class="rl-feed-pagination__count" id="rl-count">Показано <span id="rl-shown">0</span> из <span id="rl-total">0</span></span>
  <div class="rl-feed-loading" id="rl-loading" hidden>
    <span class="rl-feed-loading__spinner"></span>
    <span>Подбираем...</span>
  </div>
</div>
```

#### JS — логика (`rawlead-feed.js` и `rawlead-cabinet.js`)

```js
function updatePagination(shown, total) {
  const btn = document.getElementById('rl-load-more');
  const count = document.getElementById('rl-count');
  const shownEl = document.getElementById('rl-shown');
  const totalEl = document.getElementById('rl-total');

  if (!btn) return;
  shownEl.textContent = shown;
  totalEl.textContent = total;

  // Скрыть кнопку если все загружены
  btn.style.display = (shown >= total) ? 'none' : '';
  count.style.display = (shown >= total) ? 'none' : '';
}

async function loadMore() {
  const btn = document.getElementById('rl-load-more');
  const loading = document.getElementById('rl-loading');
  btn.hidden = true;
  loading.hidden = false;

  try {
    // ... fetch new cards ...
    // После получения данных:
    loading.hidden = true;
    btn.hidden = false;
    // Новые карточки добавить с классом .is-new для stagger-анимации
  } catch (e) {
    loading.hidden = true;
    btn.hidden = false;
  }
}

document.getElementById('rl-load-more')?.addEventListener('click', loadMore);
```

#### CSS — спиннер

```css
.rl-feed-loading {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--rl-text-muted);
  padding: 16px 0;
}
.rl-feed-loading__spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid var(--rl-border);
  border-top-color: #0A0A0A;
  border-radius: 50%;
  animation: rl-spin 600ms linear infinite;
}
@keyframes rl-spin {
  to { transform: rotate(360deg); }
}

/* Stagger для новых карточек после Load More */
.rl-lead-card.is-new {
  opacity: 0;
  transform: translateY(16px);
}
.rl-lead-card.is-new.is-visible {
  opacity: 1;
  transform: none;
  transition: opacity 280ms ease-out, transform 280ms ease-out;
}
```

---

### V4 — Полная навигация на всех страницах

**Текущее:** на `/lenta/` в header только лого + «Кабинет». «Тарифы» и «Как устроено» недоступны.

**Нужно:** в `header.php` — единая навигация для всех страниц кроме специальных случаев.

#### `header.php` — обновить nav

```html
<nav class="rl-nav__links" aria-label="Основная навигация">
  <a href="/lenta/" class="rl-nav__link <?php echo (is_page('lenta') ? 'is-active' : ''); ?>">Лента</a>
  <a href="/pricing/" class="rl-nav__link <?php echo (is_page('pricing') ? 'is-active' : ''); ?>">Тарифы</a>
  <a href="/how/" class="rl-nav__link <?php echo (is_page('how') ? 'is-active' : ''); ?>">Как устроено</a>
</nav>
```

CSS (уже есть в NEO — проверить active):
```css
.rl-nav__link.is-active {
  text-decoration: underline;
  text-decoration-thickness: 2px;
  text-underline-offset: 3px;
}
```

---

### V5 — FAB «Поддержка»

Sticky кнопка снизу-справа на всех страницах. При клике — модалка с textarea.
**Backend:** пока placeholder — форма отправляет в `/wp-json/rawlead/v1/support` (endpoint создать или заглушить 200).

#### HTML — в `footer.php` перед `</body>`

```html
<!-- Support FAB -->
<button class="rl-support-fab" id="rl-support-fab" aria-label="Поддержка">
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="10" cy="10" r="9" stroke="#0A0A0A" stroke-width="2"/>
    <path d="M10 6v5M10 13v1" stroke="#0A0A0A" stroke-width="2" stroke-linecap="round"/>
  </svg>
  <span>Поддержка</span>
</button>

<!-- Support Modal -->
<div class="rl-support-modal" id="rl-support-modal" hidden aria-modal="true" role="dialog">
  <div class="rl-support-modal__overlay" id="rl-support-overlay"></div>
  <div class="rl-support-modal__box">
    <div class="rl-support-modal__head">
      <span class="rl-support-modal__title">Написать в поддержку</span>
      <button class="rl-support-modal__close" id="rl-support-close" aria-label="Закрыть">✕</button>
    </div>
    <textarea class="rl-support-modal__input" id="rl-support-text"
      placeholder="Опиши, что случилось — URL, что делал(а), что ожидал(а)..."
      rows="5"></textarea>
    <button class="rl-btn rl-support-modal__submit" id="rl-support-submit">Отправить →</button>
    <div class="rl-support-modal__success" id="rl-support-success" hidden>
      Получили — ответим в Telegram 🙌
    </div>
  </div>
</div>
```

#### CSS

```css
/* FAB */
.rl-support-fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 900;
  display: flex;
  align-items: center;
  gap: 8px;
  background: #FFFFFF;
  border: 2px solid #0A0A0A;
  box-shadow: 3px 3px 0 #0A0A0A;
  padding: 10px 16px;
  font-size: 13px;
  font-weight: 700;
  font-family: var(--rl-font);
  cursor: pointer;
  transition: transform 120ms ease-out, box-shadow 120ms ease-out;
}
.rl-support-fab:hover {
  transform: translate(-2px, -2px);
  box-shadow: 5px 5px 0 #0A0A0A;
}
.rl-support-fab:active {
  transform: scale(0.96);
  box-shadow: 2px 2px 0 #0A0A0A;
}

@media (max-width: 767px) {
  .rl-support-fab span { display: none; }
  .rl-support-fab { padding: 10px 12px; bottom: 16px; right: 16px; }
}

/* Modal overlay */
.rl-support-modal { position: fixed; inset: 0; z-index: 1000; display: flex; align-items: flex-end; justify-content: flex-end; padding: 24px; }
.rl-support-modal[hidden] { display: none; }
.rl-support-modal__overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.3); }

/* Modal box */
.rl-support-modal__box {
  position: relative;
  background: #FFFFFF;
  border: 2px solid #0A0A0A;
  box-shadow: 5px 5px 0 #0A0A0A;
  padding: 20px;
  width: 360px;
  max-width: calc(100vw - 32px);
  animation: rl-modal-in 200ms ease-out;
}
@keyframes rl-modal-in {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: none; }
}
.rl-support-modal__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.rl-support-modal__title { font-size: 15px; font-weight: 800; }
.rl-support-modal__close {
  background: none; border: none; cursor: pointer;
  font-size: 16px; color: var(--rl-text-muted);
}
.rl-support-modal__close:hover { color: #0A0A0A; }
.rl-support-modal__input {
  width: 100%;
  border: 2px solid #0A0A0A;
  padding: 10px 12px;
  font-family: var(--rl-font);
  font-size: 14px;
  resize: vertical;
  margin-bottom: 12px;
  box-sizing: border-box;
}
.rl-support-modal__input:focus { outline: none; box-shadow: 2px 2px 0 #0A0A0A; }
.rl-support-modal__submit { width: 100%; }
.rl-support-modal__success {
  margin-top: 12px;
  font-size: 14px;
  font-weight: 600;
  text-align: center;
  color: #0A0A0A;
}
```

#### JS — в `rawlead.js` или `footer.php` inline

```js
(function() {
  const fab   = document.getElementById('rl-support-fab');
  const modal = document.getElementById('rl-support-modal');
  const close = document.getElementById('rl-support-close');
  const overlay = document.getElementById('rl-support-overlay');
  const submit  = document.getElementById('rl-support-submit');
  const success = document.getElementById('rl-support-success');
  const textarea = document.getElementById('rl-support-text');

  function openModal() { modal.hidden = false; textarea.focus(); }
  function closeModal() { modal.hidden = true; }

  fab?.addEventListener('click', openModal);
  close?.addEventListener('click', closeModal);
  overlay?.addEventListener('click', closeModal);

  submit?.addEventListener('click', async () => {
    const msg = textarea.value.trim();
    if (!msg) return;
    submit.disabled = true;
    submit.textContent = 'Отправляем...';
    try {
      await fetch('/wp-json/rawlead/v1/support', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, url: location.href })
      });
    } catch (e) { /* ignore — show success anyway */ }
    submit.hidden = true;
    textarea.hidden = true;
    success.hidden = false;
    setTimeout(closeModal, 2500);
  });
})();
```

**API endpoint (заглушка):** в `rawlead-api.php` зарегистрировать `POST /wp-json/rawlead/v1/support` → всегда возвращать `{"ok": true}`. Реальную отправку (TG / email) — в отдельной задаче.

---

### V6 — Копирайт: нейтральный род + дерзкий стиль

**Правило:** `ты` остаётся. Избегать прошедшего времени с родовым согласованием. Заменять на инфинитивы, существительные, настоящее время.

#### Полный список замен

| Где | Было | Стало |
|-----|------|-------|
| `page-cabinet.php` — TG-login плашка | «Ты вошёл как @username» | «В системе: @username» |
| `page-cabinet.php` — описание inbox | «Заказы, где ты нажал «Написать отклик» на ленте» | «Отклики с ленты — здесь» |
| `page-cabinet.php` — ссылка на ленту | «Ленту заказов смотри на /lenta/» | «Новые заказы → [Лента]» |
| `page-cabinet.php` — empty state paid | (нет) | «Ещё ни одного отклика — самое время» |
| `page-cabinet.php` — empty state free | (нет) | «Доступно с подпиской · 300 ⭐ → [Подключить]» |
| `page-lenta.php` — H1 | «Лента заказов» | **«Лента заказов»** *(нейтрально — ок, оставить)* |
| `page-lenta.php` — подзаголовок | «847 лидов за 7 дней» | «{{N}} заказов · по совместимости» |
| `rawlead-feed.js` — TWO-SPEEDS strip (free) | «Обновляется раз в 15 мин для незарегистрированных» | «⏱ Лента обновляется раз в 15 мин · [Ускорить →]» |
| `rawlead-cabinet.js` — навыки section title | «Твои навыки:» | «Твои навыки» *(ок)* |
| `rawlead-cabinet.js` — кнопка «Очистить теги» | «Очистить теги» | «Сбросить» |
| `rawlead-cabinet.js` — подписка: статус | «Подписка активна» | «Подписка активна ✓» *(ок)* |
| `rawlead-cabinet.js` — «Загружаем ещё заказы...» | «Загружаем ещё заказы...» | **убрать** (заменён V3 spinner) |
| `rawlead-cabinet.js` / `page-cabinet.php` — оплата | «Оплатить Stars» | «Оплатить Stars» *(нейтрально — ок)* |
| `/lenta/` announcement bar | «Радар онлайн · 800+ лидов в неделю» | «Радар онлайн · {{N}}+ лидов в неделю · [Смотреть →]» |
| `header.php` — кнопка входа | «Войти →» | «Войти →» *(нейтрально — ок)* |
| Footer | «by Rode51» | «RawLead · by Rode51» *(ок)* |

**Отдельно проверить в PHP и JS:** любые строки с `вошёл`, `добавил`, `настроил`, `нажал`, `сохранил` — заменить по правилу выше.

---

### V7 — Skeleton + интерактив

#### Skeleton loading (первая загрузка карточек)

При `DOMContentLoaded` до получения ответа API — показывать 4 skeleton-карточки.

```html
<!-- Шаблон skeleton-карточки (добавить в PHP или JS) -->
<div class="rl-lead-card rl-lead-card--skeleton" aria-hidden="true">
  <div class="rl-skeleton rl-skeleton--badge"></div>
  <div class="rl-skeleton rl-skeleton--title"></div>
  <div class="rl-skeleton rl-skeleton--meta"></div>
  <div class="rl-skeleton rl-skeleton--bar"></div>
  <div class="rl-skeleton rl-skeleton--chips"></div>
</div>
```

```css
.rl-lead-card--skeleton {
  pointer-events: none;
  border: 2px solid var(--rl-border);
  box-shadow: none;
}
.rl-skeleton {
  background: linear-gradient(90deg, #F0F0EC 25%, #E8E8E4 50%, #F0F0EC 75%);
  background-size: 200% 100%;
  animation: rl-shimmer 1.4s infinite;
  border-radius: 2px;
}
@keyframes rl-shimmer {
  from { background-position: 200% 0; }
  to   { background-position: -200% 0; }
}
.rl-skeleton--badge  { height: 20px; width: 60px; margin-bottom: 12px; }
.rl-skeleton--title  { height: 20px; width: 85%; margin-bottom: 10px; }
.rl-skeleton--meta   { height: 14px; width: 50%; margin-bottom: 12px; }
.rl-skeleton--bar    { height: 4px;  width: 100%; margin-bottom: 12px; }
.rl-skeleton--chips  { height: 28px; width: 70%; }
```

JS: перед fetch — рендерить 4 skeleton, после получения данных — удалить все `.rl-lead-card--skeleton` и добавить реальные карточки с `.is-new` (stagger уже в V3 CSS).

#### Press-анимация кнопок (глобально)

Уже в Wave 2 CSS — проверить что применяется ко **всем** `.rl-btn`:
```css
.rl-btn:active {
  transform: scale(0.96);
  transition: transform 60ms ease-out;
}
```

Добавить также для `.rl-inbox-card__delete` и `.rl-support-fab`.

---

### Приёмка (Coder чек-лист)

| # | Проверить |
|---|-----------|
| a | `/cabinet/` — карточки выглядят как в ленте: source badge, бюджет, match-бар, чипы, черновик |
| b | `/cabinet/` — кнопка «Загрузить ещё» скрыта когда `shown >= total` |
| c | `/cabinet/` + `/lenta/` — «Загружаем...» не висит при старте, появляется только после клика «Ещё лиды» |
| d | `/lenta/` header — видны пункты «Тарифы» и «Как устроено» |
| e | Все страницы — FAB «Поддержка» bottom-right; клик → модалка; отправка → success-сообщение; ESC/overlay → закрытие |
| f | Тексты — нет «вошёл», «нажал», «добавил»; все замены из V6 applied |
| g | Skeleton — при первом открытии ленты/кабинета 4 shimmer-карточки до загрузки данных |
| h | Кнопки — press scale(0.96) на всех `.rl-btn` + FAB + delete |
| i | Mobile 390px — FAB только иконка (без текста), модалка полная ширина |

---

_Lead Designer → @coder (через @lead-architect) · WAVE-4-UX-FIX · 2026-05-29_

---

---

---

# → СЕЙЧАС: § WAVE-UX-MOBILE

---

## § WAVE-UX-MOBILE — Полная пересборка mobile feed + ЛК (**D-O40 · 2026-05-30**)

**Приоритет:** P0 · владелец увидел скрин 2026-05-30  
**Файлы:** `header.php` · `page-lenta.php` · `page-cabinet.php` · `rawlead-feed.js` · `rawlead-cabinet.js` · `rawlead.css` · `functions.php`  
**Решения:** `LEAD_DESIGN_PROMPT.md` § D-O40  
**Wire + спека страниц:** `feed-cabinet-mvp.md` §7.6  
**Не трогать:** desktop layout (≥768px) · `src/` · `scripts/` · API-логика

---

### M1 — Карточки не влезают (overflow fix)

**Root:** нет `box-sizing: border-box` + `overflow-x` на контейнерах.

```css
@media (max-width: 767px) {
  html, body { overflow-x: hidden; }

  .rl-feed-list {
    grid-template-columns: 1fr;
    padding: 12px 16px;
    box-sizing: border-box;
    width: 100%;
  }

  .rl-lead-card {
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
    overflow: hidden;
    padding: 16px 18px;
  }

  /* cabinet inbox */
  .rl-inbox-list {
    padding: 12px 16px;
    box-sizing: border-box;
  }
  .rl-inbox-card {
    box-sizing: border-box;
    overflow: hidden;
  }

  /* chips не выходят за карточку */
  .rl-lead-card__chips,
  .rl-lead-card__tags {
    flex-wrap: wrap;
    gap: 6px;
  }
}
```

---

### M2 — Burger header (mobile nav)

**Цель:** скрыть desktop nav-links; добавить [☰] + slide-drawer.

#### HTML — `header.php`

Добавить внутрь `.rl-header__inner` (рядом с лого):

```html
<!-- Burger — только mobile (CSS скрывает на desktop) -->
<button class="rl-header__burger" id="rl-burger"
        aria-label="Открыть меню" aria-expanded="false" aria-controls="rl-nav-drawer">
  <span aria-hidden="true"></span>
  <span aria-hidden="true"></span>
  <span aria-hidden="true"></span>
</button>

<!-- Nav drawer + overlay — добавить перед </header> -->
<div class="rl-nav-drawer" id="rl-nav-drawer" hidden>
  <div class="rl-nav-drawer__overlay" id="rl-nav-overlay"></div>
  <nav class="rl-nav-drawer__panel" aria-label="Мобильная навигация">
    <button class="rl-nav-drawer__close" id="rl-nav-close" aria-label="Закрыть меню">✕</button>
    <a href="/lenta/"    class="rl-nav-drawer__link <?php echo is_page('lenta')   ? 'is-active' : ''; ?>">Лента</a>
    <a href="/pricing/"  class="rl-nav-drawer__link <?php echo is_page('pricing') ? 'is-active' : ''; ?>">Тарифы</a>
    <a href="/how/"      class="rl-nav-drawer__link <?php echo is_page('how')     ? 'is-active' : ''; ?>">Как устроено</a>
    <?php if (!is_user_logged_in()): ?>
    <a href="/cabinet/" class="rl-btn rl-nav-drawer__cta">Войти →</a>
    <?php endif; ?>
  </nav>
</div>
```

#### CSS

```css
/* Burger — скрыт на desktop */
.rl-header__burger { display: none; }

@media (max-width: 767px) {
  /* Скрыть desktop nav */
  .rl-nav__links { display: none !important; }

  /* Показать burger */
  .rl-header__burger {
    display: flex;
    flex-direction: column;
    justify-content: space-around;
    width: 44px;
    height: 44px;
    padding: 10px 8px;
    background: none;
    border: none;
    cursor: pointer;
    flex-shrink: 0;
  }
  .rl-header__burger span {
    display: block;
    height: 2px;
    background: var(--rl-text-primary);
    border-radius: 1px;
    transition: transform 200ms ease-out, opacity 200ms ease-out;
  }

  /* Drawer — overlay + panel */
  .rl-nav-drawer {
    position: fixed;
    inset: 0;
    z-index: 600;
    display: flex;
  }
  .rl-nav-drawer[hidden] { display: none; }
  .rl-nav-drawer__overlay {
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
  }
  .rl-nav-drawer__panel {
    position: relative;
    width: 280px;
    margin-left: auto;
    background: #FFFFFF;
    border-left: 2px solid #0A0A0A;
    display: flex;
    flex-direction: column;
    padding: 16px 24px 32px;
    gap: 0;
    animation: rl-drawer-in 220ms ease-out;
    overflow-y: auto;
  }
  @keyframes rl-drawer-in {
    from { transform: translateX(100%); }
    to   { transform: translateX(0); }
  }
  .rl-nav-drawer__close {
    align-self: flex-end;
    background: none;
    border: none;
    font-size: 20px;
    cursor: pointer;
    min-width: 44px;
    min-height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 8px;
    color: var(--rl-text-primary);
  }
  .rl-nav-drawer__link {
    display: block;
    padding: 16px 0;
    font: 700 18px/1 var(--font-main);
    color: #0A0A0A;
    text-decoration: none;
    border-bottom: 1px solid #F0F0EC;
    min-height: 44px;
  }
  .rl-nav-drawer__link.is-active {
    text-decoration: underline;
    text-decoration-thickness: 2px;
    text-underline-offset: 3px;
  }
  .rl-nav-drawer__cta {
    margin-top: 24px;
    min-height: 52px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-decoration: none;
  }
}
```

#### JS — в `rawlead.js` (или inline `footer.php`)

```js
(function () {
  const burger  = document.getElementById('rl-burger');
  const drawer  = document.getElementById('rl-nav-drawer');
  const overlay = document.getElementById('rl-nav-overlay');
  const close   = document.getElementById('rl-nav-close');

  function openNav() {
    if (!drawer) return;
    drawer.hidden = false;
    burger?.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
  }
  function closeNav() {
    if (!drawer) return;
    drawer.hidden = true;
    burger?.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  }

  burger?.addEventListener('click', openNav);
  close?.addEventListener('click', closeNav);
  overlay?.addEventListener('click', closeNav);

  // Закрыть по Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !drawer?.hidden) closeNav();
  });
})();
```

---

### M3 — Unified filter sheet «Фильтры» (mobile)

На mobile `[Навыки ▾]` и `[Сорт ▾]` скрыты; появляется одна кнопка `[Фильтры ▾]`.

#### HTML — `page-lenta.php` filter bar

Добавить в `.rl-filter-bar` (рядом с категорийными чипами):

```html
<!-- Только mobile — desktop скрывает через CSS -->
<button class="rl-filter-dropdown-btn rl-filter-mobile-trigger"
        id="rl-feed-filters-open"
        aria-controls="rl-feed-sheet"
        aria-expanded="false">
  Фильтры ▾
</button>
```

Unified sheet (добавить перед `</main>` или в `footer.php`):

```html
<!-- Overlay -->
<div class="rl-sheet-overlay" id="rl-feed-sheet-overlay"></div>

<!-- Unified filter sheet -->
<div class="rl-sheet rl-sheet--full" id="rl-feed-sheet"
     aria-modal="true" role="dialog" aria-label="Фильтры">
  <div class="rl-sheet__handle" aria-hidden="true"></div>
  <div class="rl-sheet__head">
    <span class="rl-sheet__title">Фильтры</span>
    <button class="rl-sheet__close" id="rl-feed-sheet-close" aria-label="Закрыть фильтры">✕</button>
  </div>
  <div class="rl-sheet__content">

    <!-- Специализация -->
    <div class="rl-sheet__section">
      <div class="rl-sheet__section-label">Специализация</div>
      <div class="rl-sheet__cat-tabs" id="rl-sheet-cats">
        <button class="rl-cat-chip is-active" data-category="">Все</button>
        <button class="rl-cat-chip" data-category="dev">&lt;/&gt; Разработка</button>
        <button class="rl-cat-chip" data-category="design">✦ Дизайн</button>
        <button class="rl-cat-chip" data-category="marketing">◎ Маркетинг</button>
        <button class="rl-cat-chip" data-category="text">Aa Тексты</button>
      </div>
    </div>

    <!-- Навыки -->
    <div class="rl-sheet__section">
      <div class="rl-sheet__section-label">Навыки</div>
      <div class="rl-sheet__skills" id="rl-sheet-skills">
        <!-- JS рендерит чипы навыков по выбранной категории -->
      </div>
    </div>

    <!-- Сортировка -->
    <div class="rl-sheet__section">
      <div class="rl-sheet__section-label">Сортировка</div>
      <label class="rl-sheet__radio">
        <input type="radio" name="rl-sheet-sort" value="date" checked>
        <span>Новые</span>
      </label>
      <label class="rl-sheet__radio">
        <input type="radio" name="rl-sheet-sort" value="match">
        <span>По совместимости</span>
      </label>
    </div>

  </div><!-- /.rl-sheet__content -->

  <!-- Sticky apply -->
  <div class="rl-sheet__apply-btn">
    <button class="rl-btn" id="rl-sheet-apply">Применить →</button>
  </div>
</div>
```

#### CSS — дополнения к `.rl-sheet`

```css
/* Sheet header */
.rl-sheet__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 16px 12px;
  border-bottom: 1px solid var(--rl-border-light);
}
.rl-sheet__title {
  font: 700 18px/1 var(--font-main);
  color: var(--rl-text-primary);
}
.rl-sheet__close {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  min-width: 44px;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--rl-text-muted);
}
.rl-sheet__close:hover { color: #0A0A0A; }

/* Секции внутри sheet */
.rl-sheet__section {
  margin-bottom: 20px;
}
.rl-sheet__section-label {
  font: 700 11px/1 var(--font-main);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--rl-text-muted);
  margin-bottom: 10px;
}
.rl-sheet__skills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* Radio-строки сортировки */
.rl-sheet__radio {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  font: 500 16px/1 var(--font-main);
  cursor: pointer;
  min-height: 44px;
  border-bottom: 1px solid var(--rl-border-light);
}
.rl-sheet__radio:last-child { border-bottom: none; }
.rl-sheet__radio input { width: 18px; height: 18px; cursor: pointer; }

/* Мобайл: показываем unified trigger, скрываем desktop-only кнопки */
@media (max-width: 767px) {
  #rl-skills-dropdown-btn,
  #rl-sort-dropdown-btn { display: none; }
  .rl-filter-mobile-trigger { display: inline-flex; }
}
@media (min-width: 768px) {
  .rl-filter-mobile-trigger { display: none; }
}
```

#### JS — `rawlead-feed.js` (M5 fix + sheet logic)

```js
// M5 — открыть sheet по кнопке [Фильтры▾]
const feedSheetOpenBtn  = document.getElementById('rl-feed-filters-open');
const feedSheet         = document.getElementById('rl-feed-sheet');
const feedSheetOverlay  = document.getElementById('rl-feed-sheet-overlay');
const feedSheetCloseBtn = document.getElementById('rl-feed-sheet-close');
const sheetApplyBtn     = document.getElementById('rl-sheet-apply');

function openFeedSheet() {
  if (!feedSheet) return;
  feedSheet.classList.add('is-open');
  feedSheetOverlay?.classList.add('is-open');
  feedSheetOpenBtn?.setAttribute('aria-expanded', 'true');
  document.body.style.overflow = 'hidden';
}

function closeFeedSheet() {
  feedSheet?.classList.remove('is-open');
  feedSheetOverlay?.classList.remove('is-open');
  feedSheetOpenBtn?.setAttribute('aria-expanded', 'false');
  document.body.style.overflow = '';
}

feedSheetOpenBtn?.addEventListener('click', openFeedSheet);
feedSheetCloseBtn?.addEventListener('click', closeFeedSheet);
feedSheetOverlay?.addEventListener('click', closeFeedSheet);  // M4: tap-outside

// Apply — собрать state → применить к ленте
sheetApplyBtn?.addEventListener('click', () => {
  const activeCat  = document.querySelector('#rl-sheet-cats .rl-cat-chip.is-active');
  const activeSkills = [...document.querySelectorAll('#rl-sheet-skills .rl-feed-skill.is-active')];
  const sortInput  = document.querySelector('input[name="rl-sheet-sort"]:checked');

  if (activeCat)   window.rlCurrentCategory = activeCat.dataset.category || '';
  if (activeSkills.length) window.rlCurrentSkills = activeSkills.map(c => c.dataset.skill);
  if (sortInput)   window.rlCurrentSort = sortInput.value;

  closeFeedSheet();
  if (typeof rlReloadFeed === 'function') rlReloadFeed();
});

// Обновлять навыки в sheet при смене категории
document.getElementById('rl-sheet-cats')?.addEventListener('click', (e) => {
  const chip = e.target.closest('.rl-cat-chip');
  if (!chip) return;
  document.querySelectorAll('#rl-sheet-cats .rl-cat-chip').forEach(c => c.classList.remove('is-active'));
  chip.classList.add('is-active');
  // renderSkillsForCategory(chip.dataset.category) — вызвать существующую функцию рендера навыков
  if (typeof renderSkillsForCategory === 'function') {
    renderSkillsForCategory(chip.dataset.category, '#rl-sheet-skills');
  }
});
```

---

### M4 — Tap-outside: overlay закрывает, карточка collapse

#### W2 — `rawlead-feed.js`: collapse при клике вне карточки

```js
// W2: tap outside card → collapse expanded card
document.addEventListener('click', (e) => {
  if (!e.target.closest('.rl-lead-card')) {
    document.querySelectorAll('.rl-lead-card.is-expanded').forEach(card => {
      card.classList.remove('is-expanded');
    });
  }
});
```

#### W3 — `rawlead-cabinet.js`: overlay закрывает modal навыков

```js
// W3: cabinet skills modal overlay → close
const skillsOverlay = document.getElementById('rl-skills-overlay');
const skillsModal   = document.getElementById('rl-skills-modal') || document.querySelector('.rl-skills-panel');

skillsOverlay?.addEventListener('click', () => {
  skillsModal?.classList.remove('is-open');
  skillsOverlay.classList.remove('is-open');
  document.body.style.overflow = '';
});
```

---

### Приёмка — 390×844

| # | Проверить |
|---|-----------|
| **m1** | `/lenta/` — нет горизонтального скролла · карточки 100% ширины экрана |
| **m2** | Header — нет текстового «Лента/Тарифы/Как устроено» · есть `[☰]` · клик → drawer slide-in |
| **m3** | Drawer — overlay + 3 ссылки + CTA «Войти →» · tap overlay / [✕] → закрывает |
| **m4** | Filter bar — есть `[Фильтры ▾]` · `[Навыки ▾]` / `[Сорт ▾]` не видны |
| **m5** | `[Фильтры ▾]` → открывает sheet · в sheet: категории + навыки + сортировка |
| **m6** | Sheet overlay — tap закрывает |
| **m7** | [Применить →] sticky 52px — виден при прокрутке sheet |
| **m8** | Tap вне карточки → карточка collapsing |
| **m9** | ЛК навыки modal → overlay tap закрывает |
| **m10** | Все tap-зоны ≥ 44px (burger, sheet close, radio, nav drawer links) |
| **m11** | Desktop 768px+ — burger скрыт; desktop nav-links видны; `[Навыки▾]` + `[Сорт▾]` работают |

---

_Lead Designer → @lead-architect → @coder · WAVE-UX-MOBILE · D-O40 · 2026-05-30_
