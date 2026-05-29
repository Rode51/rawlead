# RawLead WP — Wave 2 CSS/JS brief

**Статус:** сдано Designer **2026-05-29** · на ревью `@lead-designer`  
**Источник:** [`DESIGNER_PROMPT.md`](../../team/design/DESIGNER_PROMPT.md) § WAVE-2-CSS · [`LEAD_DESIGN_PROMPT.md`](../../team/design/LEAD_DESIGN_PROMPT.md) § DESIGN-WAVE-2  
**Токены:** [`DESIGN_SYSTEM.md`](../../team/design/DESIGN_SYSTEM.md) § WordPress NEO-BRUTALIST  
**Концепты:** [`../assets/`](../assets/) (`rawlead-mark-concept.png`, `rawlead-hero-bg-concept.png`, `rawlead-category-icons-concept.png`)

---

## Research (что берём)

| Референс | Что берём |
|----------|-----------|
| [retroui.dev](https://retroui.dev) | Плоская тень + сдвиг при hover/press |
| [gumroad.com](https://gumroad.com) | Уверенная типографика, один CTA на блок |
| Lead W1–W13 | NEO не меняем; оживляем motion + пагинация + perfect-match |

**Не берём:** indigo `#4F46E5`, pill-бейджи, soft `box-shadow: 0 2px 12px`, кубики-источники на лендинге (W13 — удалить).

---

## Аудит prod-кода (delta)

| Пункт | Сейчас в theme | Wave 2 |
|-------|----------------|--------|
| Лендинг reveal | `.rl-reveal` + `rawlead-scroll.js` | **Оставить**; не дублировать логику вторым observer |
| Лента reveal | Нет IO на `.rl-lead-card` | IO в `rawlead-feed.js` + CSS stagger |
| Match-bar | CSS `width:0→var(--match-value)` есть; JS сразу ставит `.rl-match-ready` (без viewport) | Триггер только при `.rl-lead-card.is-visible` |
| 100% match | `.rl-lead-card--perfect-match` — **старый REVOLUTION** (indigo, green fill) | NEO: жёлтая рамка, pulse, бейдж `ИДЕАЛЬНО ✦` |
| Пагинация | `#rl-feed-sentinel` + IO → `loadMore` | Кнопка «Загрузить ещё» + счётчик; sentinel убрать |
| Категории | Иконки в `page-lenta.php`; маркетинг = `◎` | Мегафон SVG 16px (ниже) |
| by Rode51 | Только `console` в feed/cabinet JS | Header + footer (PHP) |
| Кубики FL/Kwork/TG | `flow.php` + CSS + `rawlead-scroll.js` | **Удалить** блок и стили (Lead W13) |

**Имена классов (фиксация):** в ленте карточка = `.rl-lead-card`, не `.rl-card`. Perfect = **`.rl-lead-card--perfect-match`** (уже в JS) — CSS переписать, класс в JS не переименовывать.

---

## Файлы для @coder

| Файл | Действие |
|------|----------|
| `wordpress/.../assets/css/rawlead.css` | Wave 2 блоки ниже; удалить REVOLUTION perfect + cube-анимации |
| `wordpress/.../assets/js/rawlead-feed.js` | IO reveal, perfect badge, пагинация, убрать sentinel IO |
| `wordpress/.../assets/js/rawlead-cabinet.js` | Те же reveal + пагинация (inbox) |
| `wordpress/.../assets/js/rawlead-scroll.js` | Убрать `.rl-flow__sources` из observer |
| `wordpress/.../template-parts/rawlead/header.php` | byline + опц. mark |
| `wordpress/.../template-parts/rawlead/footer.php` | `RawLead · by Rode51` |
| `wordpress/.../page-lenta.php` | Мегафон SVG; опц. `#rl-feed-pagination` placeholder |
| `wordpress/.../template-parts/rawlead/flow.php` | Заменить кубики на статичные badge/source chips (см. Lead) или убрать секцию — согласовать с Lead |

**Не трогать:** `src/`, `scripts/`, API.

---

## w2-1 — Scroll reveal

### Лента и кабинет (`rawlead-feed.js`, `rawlead-cabinet.js`)

После `bindCards()` / вставки карточек — один observer на список:

```js
var rlCardIo = new IntersectionObserver(function (entries) {
  entries.forEach(function (entry) {
    if (entry.isIntersecting) {
      entry.target.classList.add("is-visible");
      rlCardIo.unobserve(entry.target);
    }
  });
}, { threshold: 0.08, rootMargin: "0px 0px -5% 0px" });

function observeLeadCards(root) {
  if (!root || !("IntersectionObserver" in window)) return;
  root.querySelectorAll(".rl-lead-card:not(.is-visible)").forEach(function (el) {
    rlCardIo.observe(el);
  });
}
```

Вызов: после каждого `insertAdjacentHTML` карточек. **Удалить** `requestAnimationFrame` → `.rl-match-ready` (строки ~1175–1181 feed).

`prefers-reduced-motion`: сразу `.is-visible` на всех карточках.

### Лендинг

Оставить `rawlead-scroll.js` + `.rl-reveal`. Опционально добавить класс `.rl-section-reveal` на секции без `.rl-reveal` — в CSS **алиас**:

```css
.rl-section-reveal {
  opacity: 0;
  transform: translateY(16px);
}
.rl-section-reveal.is-visible,
.rl-reveal.is-visible {
  opacity: 1;
  transform: none;
  transition: opacity 400ms ease-out, transform 400ms ease-out;
}
```

### CSS — карточки ленты

```css
/* --- Wave 2: feed card reveal --- */
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
```

---

## w2-2 — Match-bar (animated fill)

`--match-value` уже в JS (`style="--match-value:88%"`). CSS:

```css
.rl-feed-list .rl-lead-card .rl-match__fill,
#rl-cabinet-list .rl-lead-card .rl-match__fill {
  width: 0 !important;
  transition: width 600ms ease-out;
}
.rl-feed-list .rl-lead-card.is-visible .rl-match__fill,
#rl-cabinet-list > .rl-lead-card.is-visible .rl-match__fill {
  width: var(--match-value, 0%) !important;
}
```

Удалить правила с `.rl-match-ready` и дубли в `.rl-reveal.is-visible .rl-match__fill` для **продуктовых** карточек (лендинг preview в `.rl-flow` — отдельно, можно оставить reveal-секцию).

---

## w2-3 — 100% match «взрыв»

### JS (`renderCard`)

- Класс: `rl-lead-card--perfect-match` (как сейчас).
- Бейдж: заменить `rl-feed-card__match-badge` + текст «Точное совпадение» на:

```html
<span class="rl-badge rl-badge--perfect">ИДЕАЛЬНО ✦</span>
```

Рядом с source badge в `.rl-feed-card__head-start` (после source).

### CSS — заменить блок ~2246–2270 в `rawlead.css`

```css
/* --- Wave 2: perfect match --- */
.rl-lead-card--perfect-match {
  border: 2px solid #facc15;
  box-shadow: 4px 4px 0 #facc15;
}
.rl-lead-card--perfect-match.is-visible {
  animation: rl-perfect-pulse 700ms ease-out forwards;
}
@keyframes rl-perfect-pulse {
  0%   { box-shadow: 4px 4px 0 #facc15, 0 0 0 0 rgba(250, 204, 21, 0.5); }
  50%  { box-shadow: 4px 4px 0 #facc15, 0 0 0 14px rgba(250, 204, 21, 0.25); }
  100% { box-shadow: 4px 4px 0 #facc15, 0 0 0 22px rgba(250, 204, 21, 0); }
}
.rl-badge--perfect {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #facc15;
  color: #0a0a0a;
  border: 2px solid #0a0a0a;
  border-radius: 2px;
  font-family: var(--rl-font);
  font-weight: 800;
  font-size: 11px;
  letter-spacing: 0.06em;
  padding: 2px 8px;
  text-transform: uppercase;
}
.rl-lead-card--perfect-match .rl-match__fill {
  background: var(--rl-match-fill); /* не зелёный REVOLUTION */
}
```

---

## w2-4 — Пагинация

1. Удалить IO на `#rl-feed-sentinel` / `#rl-cabinet-sentinel`.
2. После списка рендерить (или держать в PHP пустой `#rl-feed-pagination`):

```html
<div class="rl-feed-pagination" id="rl-feed-pagination" hidden>
  <button type="button" class="rl-btn rl-btn--primary rl-btn--load-more" id="rl-feed-load-more">
    Загрузить ещё <span aria-hidden="true">→</span>
  </button>
  <span class="rl-feed-pagination__count" id="rl-feed-pagination-count"></span>
</div>
```

3. `updateCount()` / аналог: текст `Показано {shown} из {total}` (`total` из API если есть, иначе `shown+` или «ещё есть»).
4. `hidden` на pagination когда `state.done && !hasMore`.
5. `.rl-btn--load-more.is-loading` на время `loadMore`.

```css
.rl-feed-pagination {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px 0 24px;
}
.rl-btn--load-more {
  min-width: 200px;
  min-height: 44px;
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

Скрыть `#rl-feed-sentinel` (`display:none` или удалить из DOM).

---

## w2-5 — Иконки категорий

В `page-lenta.php` для маркетинга заменить `◎` на:

```html
<span class="rl-cat-chip__icon" aria-hidden="true">
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M3 6.5L8 3v10L3 9.5V6.5z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
    <path d="M8 5l5 2v4l-5 2V5z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
  </svg>
</span>
```

```css
.rl-cat-chip__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  margin-right: 4px;
  vertical-align: middle;
  flex-shrink: 0;
}
.rl-cat-chip__icon svg {
  display: block;
}
```

Остальные: `</>`, `✦`, `Aa` — без изменений.

---

## w2-6 — by Rode51

### `header.php` — `.rl-header__brand`

```html
<a class="rl-header__brand" href="…">
  <span class="rl-header__brand-text">RawLead</span>
  <span class="rl-logo-byline">by Rode51</span>
</a>
```

```css
.rl-header__brand {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  text-decoration: none;
  color: inherit;
}
.rl-logo-byline {
  display: block;
  font-size: 11px;
  font-weight: 400;
  opacity: 0.4;
  letter-spacing: 0.02em;
  line-height: 1;
  margin-top: 1px;
}
```

### `footer.php`

```html
<p class="rl-footer__copy">
  <span class="rl-footer__byline">RawLead · by Rode51</span>
  · © <?php echo $year; ?>
</p>
```

```css
.rl-footer__byline { font-size: 12px; opacity: 0.5; }
```

---

## w2-7 — Марка (favicon / header)

**Концепт:** `docs/design/assets/rawlead-mark-concept.png`

**Production (Recraft / ручная векторизация):**

- Имя: `docs/design/assets/wave2-mark-radar-v1.svg`
- Копия в theme: `wordpress/.../assets/images/wave2-mark-radar-v1.svg`
- Favicon: 32×32 PNG из SVG

**Header (опционально v1):**

```html
<img class="rl-header__mark" src="…/wave2-mark-radar-v1.svg" width="20" height="20" alt="" decoding="async">
```

```css
.rl-header__mark { display: block; margin-right: 8px; }
.rl-header__brand { flex-direction: row; align-items: center; }
```

Промпт Recraft: см. `LEAD_DESIGN_PROMPT.md` § Recraft «Марка».

---

## w2-8 — Hero geo-декор

**Концепт:** `rawlead-hero-bg-concept.png`  
**Файл:** `wave2-hero-geo-corner-v1.svg` в `assets/images/`

Угловые псевдоэлементы, **opacity 0.12**, не перекрывают H1/CTA:

```css
.rl-hero {
  position: relative;
  overflow: hidden;
}
.rl-hero::before,
.rl-hero::after {
  content: "";
  position: absolute;
  pointer-events: none;
  opacity: 0.12;
  background-repeat: no-repeat;
  background-size: contain;
}
.rl-hero::before {
  top: -20px;
  right: -20px;
  width: 240px;
  height: 240px;
  background-image: url("../images/wave2-hero-geo-corner-v1.svg");
}
.rl-hero::after {
  bottom: -20px;
  left: -20px;
  width: 180px;
  height: 180px;
  transform: rotate(180deg);
  background-image: url("../images/wave2-hero-geo-corner-v1.svg");
}
```

До появления SVG — закомментировать `background-image`, не ломать hero.

---

## w2-3b — Тактильные hover/press (уточнение)

Согласовать с существующим блоком ~412–436:

| Элемент | Значение |
|---------|----------|
| `.rl-lead-card:hover` | `120ms`, shadow `6px 6px 0 #0A0A0A`, `translate(-2px,-2px)` |
| `.rl-btn:active` | `scale(0.96)`, `60ms` (сейчас 0.97/80ms — **подтянуть**) |

---

## `prefers-reduced-motion`

```css
@media (prefers-reduced-motion: reduce) {
  .rl-feed-list > .rl-lead-card,
  #rl-cabinet-list > .rl-lead-card,
  .rl-section-reveal,
  .rl-reveal {
    opacity: 1;
    transform: none;
    transition: none;
  }
  .rl-feed-list .rl-lead-card .rl-match__fill,
  #rl-cabinet-list .rl-lead-card .rl-match__fill {
    width: var(--match-value, 0%) !important;
    transition: none;
  }
  .rl-lead-card--perfect-match { animation: none; }
}
```

---

## Приёмка (Designer → Lead)

- [ ] Карточки ленты/кабинета: stagger при первом входе в viewport
- [ ] Match-bar: 0→N% только после `.is-visible`
- [ ] 100%: жёлтая рамка + pulse + `ИДЕАЛЬНО ✦`, без indigo
- [ ] «Загрузить ещё» + счётчик; нет auto-load по sentinel
- [ ] by Rode51 в header и footer
- [ ] Маркетинг: мегафон SVG
- [ ] Кубики flow удалены
- [ ] `prefers-reduced-motion` ок
- [ ] Mobile 390px: кнопки ≥44px, анимации не ломают layout

---

## Lead Designer: решения по ревью (2026-05-29)

### flow.php — финальное решение

**Удалить секцию `.rl-flow__sources` полностью** (W13: кубики FL/Kwork/TG — удалить, не заменять).  
Coder: убрать PHP-блок в `flow.php` + все CSS/JS `.rl-flow__sources` анимации из `rawlead.css` / `rawlead-scroll.js`.

### Match-bar `!important` — порядок операций

В CSS w2-2 используется `!important` для перебития старых `.rl-match-ready` правил.  
**Coder:** сначала удалить все блоки с `.rl-match-ready` из `rawlead.css` → затем убрать `!important` из нового правила match-bar.  
Оставлять `!important` в финальном коде нельзя.

### Stagger при пагинации (nota bene)

`:nth-child()` не сбрасывается при `append` в DOM. Стаггер работает корректно только для первого батча. Для «Загрузить ещё» — по желанию добавить `data-card-i` в `renderCard` и CSS `transition-delay: calc(var(--card-i, 0) * 60ms)`.  
В MVP — не обязательно.

---

## Handoff

✅ **Ревью Lead Designer 2026-05-29** — brief одобрен с правками выше.  
После ✅ Lead Designer → Lead Architect пишет `CODER_PROMPT.md` § WAVE-2-CSS со ссылкой на **этот файл** (не дублировать ТЗ в чат).

---

## § w3-delta-O41 — Wave 3 delta (Gumroad-level, 2026-05-29)

**Триггер:** O41 — владелец видит Wave 2 как «косметику», цель: Gumroad-уровень.  
**Решения:** [`REFERENCE.md`](REFERENCE.md) §3.2 (обновлено) · [`LEAD_DESIGN_PROMPT.md`](../../team/design/LEAD_DESIGN_PROMPT.md) § DESIGN-WAVE-3/O41  
**Промпт Coder:** [`DESIGNER_PROMPT.md`](../../team/design/DESIGNER_PROMPT.md) § O41-WAVE3

### Проблема 1 — Hero card на жёлтом: разделение секций

**Было (Wave 2):** карточки live preview внутри `.rl-hero` (жёлтый фон) без чёткой рамки.  
**Стало (O41):** Hero = только H1 + sub + CTA. Live Preview = отдельная белая секция НИЖЕ.

```css
/* --- O41: Hero — только текст + CTA, никаких карточек внутри --- */
.rl-hero {
  padding-bottom: 0;          /* убрать padding если был */
  border-bottom: 4px solid #0a0a0a;
}

/* --- O41: Live Preview Feed — отдельная белая секция --- */
.rl-live-preview {
  background: #ffffff;
  border-bottom: 2px solid #0a0a0a;
  padding: 32px 0 40px;
}

.rl-live-preview__label {
  font-family: var(--rl-font, 'Manrope', sans-serif);
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #0a0a0a;
  margin-bottom: 20px;
}

/* Карточки в live preview — полный neo-brutalist */
.rl-live-preview .rl-lead-card {
  background: #ffffff;
  border: 2px solid #0a0a0a;
  box-shadow: 4px 4px 0 #0a0a0a;
  border-radius: 4px;
}
.rl-live-preview .rl-lead-card:hover {
  box-shadow: 6px 6px 0 #0a0a0a;
  transform: translate(-2px, -2px);
  transition: box-shadow 120ms ease-out, transform 120ms ease-out;
}
```

**PHP:** вынести блок карточек из `hero.php` в отдельный `template-parts/rawlead/live-preview.php` — после `</section>` hero.

### Проблема 2 — H1 «Лиды без шума»: принудительная верификация

H1 в PHP-шаблоне `hero.php` должен быть строго:

```html
<h1 class="rl-hero__title">Лиды без шума</h1>
```

**Coder:** проверить `hero.php` — если там «Заказы под твой стек» или любой другой текст → исправить на канонический. Это **не** WP-редактор, это hard-coded в шаблоне.

### Проблема 3 — Secondary CTA на жёлтом фоне

**Было:** ghost-link или слабая кнопка без видимой рамки.  
**Стало:** neo-brutalist secondary — полная рамка на прозрачном фоне.

```css
/* --- O41: Secondary CTA — neo-brutalist на жёлтом фоне --- */
.rl-btn--secondary {
  background: transparent;
  border: 2px solid #0a0a0a;
  color: #0a0a0a;
  border-radius: 0;
  padding: 14px 28px;
  font-family: var(--rl-font, 'Manrope', sans-serif);
  font-weight: 700;
  font-size: 16px;
  cursor: pointer;
  transition: background 100ms ease-out, color 100ms ease-out;
  display: inline-block;
  text-decoration: none;
}
.rl-btn--secondary:hover {
  background: #0a0a0a;
  color: #facc15;
}
.rl-btn--secondary:active {
  transform: scale(0.97);
  transition: transform 60ms ease-out;
}
```

CTA-группа в hero:

```css
/* --- O41: Hero CTA group --- */
.rl-hero__cta-group {
  display: flex;
  flex-direction: row;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
  margin-top: 40px;
}

@media (max-width: 640px) {
  .rl-hero__cta-group {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  .rl-hero__cta-group .rl-btn,
  .rl-hero__cta-group .rl-btn--secondary {
    width: 100%;
    text-align: center;
  }
}
```

### Проблема 4 — Типографика hero: breathing room

**Gumroad-разрыв:** H1 должен быть ОДИН визуальный якорь экрана. Сейчас Wave 2 может иметь недостаточно воздуха.

```css
/* --- O41: Hero typography spacing --- */
.rl-hero__title {
  font-family: var(--rl-font, 'Manrope', sans-serif);
  font-weight: 900;
  font-size: clamp(56px, 10vw, 96px);
  color: #0a0a0a;
  letter-spacing: -0.03em;
  line-height: 1.0;
  max-width: 720px;
  margin: 0 0 24px;
}
.rl-hero__sub {
  font-family: var(--rl-font, 'Manrope', sans-serif);
  font-weight: 400;
  font-size: clamp(18px, 2.5vw, 22px);
  color: #0a0a0a;
  opacity: 0.75;
  max-width: 560px;
  margin: 0 0 40px;
  line-height: 1.5;
}
/* Hero content max-width + центровка */
.rl-hero__inner {
  max-width: 1100px;
  margin: 0 auto;
  padding: 80px 24px 60px;
}
@media (max-width: 768px) {
  .rl-hero__inner { padding: 40px 16px 48px; }
  .rl-hero__title { font-size: clamp(40px, 10vw, 64px); }
}
```

### Приёмка O41 (для @coder → @lead-designer)

- [ ] Hero фон #FACC15 — только H1 + sub + CTA-группа (без карточек)
- [ ] Live Preview = отдельная белая секция, `border-top: 4px solid #0A0A0A`
- [ ] Карточки в preview: `border: 2px solid #0A0A0A` + `box-shadow: 4px 4px 0 #0A0A0A`
- [ ] H1 на проде = «Лиды без шума» (Ctrl+F5)
- [ ] Secondary CTA: рамка видна на жёлтом фоне, hover = чёрный + жёлтый текст
- [ ] Mobile 390px: CTA-группа вертикальная, кнопки full-width ≥48px
- [ ] Нет горизонтального скролла на 390px
