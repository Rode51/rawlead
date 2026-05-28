# RawLead — WordPress сайт · дизайн-референс

**Статус:** v4 · NEO-BRUTALIST · 2026-05-28
**Направление:** «Neo-Brutalist Color Blocks» — белая база, жёлтый hero, чёрные рамки, плоские тени
**Поверхности:** лендинг `/` · `/lenta/` (лента) · `/cabinet/` (кабинет) · `/how` · `/faq` · `/contact`
**Отменено (v3 REVOLUTION):** тёплый Indigo `#4F46E5`, shadow-cards, pill-кнопки, `#FAFAF8` фон

Токены: [`../../team/design/DESIGN_SYSTEM.md`](../../team/design/DESIGN_SYSTEM.md) § WordPress NEO-BRUTALIST
Спека `/lenta/` + `/cabinet/`: [`feed-cabinet-mvp.md`](feed-cabinet-mvp.md)

---

## 1. Суть стиля

| Принцип | Решение |
|---------|---------|
| Атмосфера | Смелый, прямой, запоминается — не «ещё один SaaS» |
| Визуальный удар | Жёлтый `#FACC15` hero — первое, что видишь; потом белая чистота |
| Карточки | `border: 2px solid #0A0A0A` + `box-shadow: 4px 4px 0px #0A0A0A` (плоская смещённая, без blur) |
| Кнопки | Чёрные прямоугольные; hover: заливка жёлтая `#FACC15`, текст чёрный |
| Углы | `4px` (карточки), `0px` (кнопки, chips) — без pill |
| Фон | `#FFFFFF` страницы; `#F5F5F0` секции; `#0A0A0A` footer |
| Шрифт | **Manrope** 900 display / 800 heading / 400–600 body |
| Аудитория | Фрилансер 25–35 — интерфейс не боится быть заметным |

---

## 2. Токены (сводка — полные в DESIGN_SYSTEM.md § WP NEO-BRUTALIST)

| Назначение | Токен | Значение |
|------------|-------|----------|
| Фон страницы | `color/bg/page` | `#FFFFFF` |
| Фон секции | `color/bg/section` | `#F5F5F0` |
| Hero / акцент | `color/bg/hero` | `#FACC15` |
| Alt секция | `color/bg/alt` | `#F3E8FF` |
| Footer | `color/bg/inverse` | `#0A0A0A` |
| Основной текст | `color/text/primary` | `#0A0A0A` |
| Body текст | `color/text/body` | `#1A1A1A` |
| Muted | `color/text/muted` | `#525252` |
| Рамка карточки | `color/border` | `#0A0A0A` 2px |
| Тень карточки | `shadow/card` | `4px 4px 0px #0A0A0A` |
| Тень hover | `shadow/card-hover` | `6px 6px 0px #0A0A0A` |
| Радиус карточки | `radius/card` | `4px` |
| Радиус кнопки | `radius/button` | `0px` |
| CTA кнопка | `color/cta/primary` | `#0A0A0A` |
| CTA hover | `color/cta/hover-bg` | `#FACC15` |

---

## 3. Структура страниц

### 3.1 Header (sticky, все страницы)

**Все страницы:**
```
[RawLead]   Лента · Тарифы · Контакты   [Войти в кабинет]
```
- Фон `#FFFFFF`, `border-bottom: 2px solid #0A0A0A` (всегда, не только при скролле)
- Логотип «RawLead» — Manrope 900, `#0A0A0A`, → `/`
- CTA «Войти в кабинет» — чёрная прямоугольная кнопка, `0px` radius
- Мобайл: гамбургер справа; меню — drawer слева

**Продуктовые `/lenta/`, `/cabinet/`:**
```
[RawLead]                                [Войти в кабинет]
```
- Минимальный, не отвлекает от контента

### 3.2 Лендинг `/`

```
Header (sticky, 2px black border-bottom)

Hero (min-height: 100svh, background: #FACC15)
  H1: «Лиды без шума»
      Manrope 900, clamp(56px, 10vw, 96px), #0A0A0A, letter-spacing -0.03em
  Подзаголовок:
      «Биржи и Telegram — в одной ленте. ИИ убирает мусор до тебя.»
      Manrope 400, 20px, #0A0A0A, opacity 0.75
  CTA: [Смотреть ленту →]
      background #0A0A0A, color #FFFFFF, radius 0px, padding 16px 32px
      hover: background #FFFFFF, color #0A0A0A, border 2px solid #0A0A0A
  Нижний декор: толстая чёрная линия 4px как подчёркивание секции

Live Preview Feed (background: #FFFFFF, border-top/bottom 2px solid #0A0A0A)
  Подпись: «Последние заказы из ленты» — Manrope 700 uppercase 12px letter-spacing 0.1em
  3–4 карточки в новом стиле (bordered + flat shadow)
  [Открыть все →] — ghost link, черный, → /lenta/

Блок «Как это работает» (background: #F3E8FF)
  3 пункта, layout 3 col desktop / 1 col mobile
  Каждый: иконка 32px + Manrope 700 18px + 2 строки text
  Без нумерации 01-02-03

Тарифы (якорь id="pricing-preview", background: #F5F5F0)
  Одна карточка «ИИ-агент»
  border: 2px solid #0A0A0A, shadow: 4px 4px 0 #0A0A0A, radius: 4px
  Цена: «от 300 ₽/мес» · Badge «Скоро» (чёрный outline)
  CTA: [Узнать первым →] — чёрная кнопка

Footer (background: #0A0A0A, color: #FFFFFF)
  RawLead | Лента · Тарифы · Контакты | Telegram
  © 2026 RawLead
```

**Убрать:** pill-кнопки, shadow soft-cards (заменяет flat shadow), манифест-полоса, sidebar фильтры, кубики-анимация.

### 3.3 Лента `/lenta/`

Детальная спека: [`feed-cabinet-mvp.md`](feed-cabinet-mvp.md) (обновить под Neo-Brutalist)

Ключевые принципы:
- Фон `#FFFFFF`
- Filter bar горизонтальная sticky под header, `border-bottom: 2px solid #0A0A0A`
- Chips: `border: 2px solid #0A0A0A`, `radius: 2px`; active: black fill, white text
- Карточки: `border: 2px solid #0A0A0A`, `box-shadow: 4px 4px 0 #0A0A0A`, hover: `6px 6px 0 #0A0A0A` + `translate(-2px, -2px)`
- Mobile: 1 col; Desktop: 2 col max-width 900px
- **O11 (copy-волна):** info-strip `.rl-feed-delay-notice` под счётчиком — «~15 мин на бесплатной ленте · подписка мгновенно» (см. Product § TWO-SPEEDS-COPY)

### 3.3a `/pricing/` — строка «Скорость»

В таблице «Бесплатно vs ИИ-агент»:

| | Бесплатно | ИИ-агент |
|--|-----------|----------|
| Скорость | ~15 мин задержка | **Мгновенно** + push TG |

### 3.4 Кабинет `/cabinet/`

Детальная спека: [`feed-cabinet-mvp.md`](feed-cabinet-mvp.md)

- Тот же стиль что на `/lenta/`
- Навыки пользователя: bordered chips, active = yellow fill + black text
- Match-bar: `background: #0A0A0A`

### 3.5 `/how` — Как работает

```
Header

H1: «Как работает RawLead»
    Manrope 800, 44px, на фоне #F3E8FF (полная ширина секция)

4 шага (карточки 2×2 desktop / 1 col mobile):
  border: 2px solid #0A0A0A, shadow: 4px 4px 0 #0A0A0A, radius: 4px
  Каждая: иконка + Manrope 700 18px + 2 строки

Шаги:
  1. «Подключаешь биржи»
  2. «Радар парсит»
  3. «ИИ фильтрует»
  4. «Ты видишь в ленте» (+ подпись O11: бесплатно с задержкой ~15 мин, подписка — сразу)

CTA: [Смотреть ленту →] — чёрная кнопка
Footer
```

### 3.6 `/faq` — Частые вопросы

```
Header

H1: «Частые вопросы» (background: #FACC15 секция)

Аккордеон (фон #FFFFFF):
  border-bottom: 2px solid #0A0A0A
  стрелка → вращается 180° при открытии
  открытый: expand 280ms ease-out

Убрать: «закрытое тестирование», «ранний доступ», «по приглашению»
Footer
```

### 3.7 `/contact` — Контакты

```
Header

H1: «Связаться» (background: #FACC15 секция)

Форма (CF7):
  inputs: border: 2px solid #0A0A0A, radius: 0px, focus: shadow 2px 2px 0 #0A0A0A
  [Отправить] — чёрная прямоугольная кнопка

«Или напишите напрямую →» [Telegram] (ghost link)

Убрать: «заявка на ранний доступ», «закрытое тестирование»
Footer
```

---

## 4. Компоненты

| Компонент | Спека |
|-----------|-------|
| **Кнопка primary** | bg `#0A0A0A`, text `#FFFFFF`, radius `0px`, border `2px solid #0A0A0A`; hover: bg `#FACC15`, text `#0A0A0A`; active: scale 0.97 |
| **Кнопка secondary** | border `2px solid #0A0A0A`, text `#0A0A0A`, bg transparent; hover: bg `#F5F5F0` |
| **Кнопка ghost** | text `#0A0A0A`, underline при hover, без рамки |
| **Карточка лида** | bg `#FFFFFF`, `border: 2px solid #0A0A0A`, `box-shadow: 4px 4px 0 #0A0A0A`, `radius: 4px`, padding `20px 24px`; hover: `box-shadow: 6px 6px 0 #0A0A0A` + `transform: translate(-2px, -2px)` |
| **Chip категории** | active: bg `#0A0A0A` + text `#FFFFFF`; inactive: bg `#FFFFFF` + `border: 2px solid #0A0A0A` + text `#0A0A0A` |
| **Chip навыка** | active: bg `#FACC15` + text `#0A0A0A` + `border: 2px solid #0A0A0A`; inactive: bg `#FFFFFF` + `border: 2px solid #D4D4D4` |
| **Match-bar** | bg `#D4D4D4`, fill `#0A0A0A`, height `4px`, radius `0px`; animate width 500ms |
| **Source badge** | dot 8px + label 12px/700: FL `#00A65A` · Kwork `#EA580C` · TG `#0088CC` |
| **AI-чип «Брать»** | bg `#DCFCE7`, text `#16A34A`, border `1.5px solid #16A34A`, radius `2px` |
| **AI-чип «Сомнительно»** | bg `#F5F5F5`, text `#6B7280`, border `1.5px solid #D4D4D4`, radius `2px` |
| **Report bug FAB** | `?` round 40px, bg `#FFFFFF`, border `2px solid #0A0A0A`, shadow `2px 2px 0 #0A0A0A`, bottom-right fixed |
| **Skeleton-карточка** | bg `#F5F5F0`, `border: 2px solid #D4D4D4`, `box-shadow: 4px 4px 0 #D4D4D4`, radius `4px`, pulse animation |
| **Input / Textarea** | border `2px solid #0A0A0A`, radius `0px`; focus: `box-shadow: 2px 2px 0 #0A0A0A` |

---

## 5. Голос (из Product-канона — без изменений)

- Активный залог: «ИИ убрал мусор», не «заказы были отфильтрованы»
- Без восклицательных знаков
- Кнопки = конкретное действие: «Смотреть ленту», «Войти в кабинет»
- Mobile: короткие метки — «Дизайн» не «Дизайн & Видео»
- Пустые состояния: человечные — «Пока нет заказов по этим навыкам — попробуй шире»
- Контакты: без «заявки» / «раннего доступа»

---

## 6. Анимации

**Принцип:** только `transform` + `opacity`. IntersectionObserver, unobserve после первого срабатывания.

### 6.1 Появление при скролле

```css
.rl-reveal { opacity: 0; transform: translateY(16px); }
.rl-reveal.is-visible {
  opacity: 1; transform: none;
  transition: opacity 200ms ease-out, transform 200ms ease-out;
}
```

### 6.2 Stagger карточек

```css
.rl-card:nth-child(1) { transition-delay: 0ms; }
.rl-card:nth-child(2) { transition-delay: 40ms; }
.rl-card:nth-child(3) { transition-delay: 80ms; }
```

### 6.3 Hover карточки (брутал-стиль: сдвиг + тень растёт)

```css
.rl-lead-card {
  transition: transform 120ms ease-out, box-shadow 120ms ease-out;
}
.rl-lead-card:hover {
  transform: translate(-2px, -2px);
  box-shadow: 6px 6px 0px #0A0A0A;
}
```

### 6.4 Match-bar fill

```css
.rl-match__fill { width: 0; transition: width 500ms ease-out; }
.is-visible .rl-match__fill { width: var(--match-value); }
```

### 6.5 Micro-press кнопки

```css
.rl-btn:active { transform: scale(0.97); transition: transform 60ms ease-out; }
```

### 6.6 Bottom sheet mobile

```css
.rl-sheet { transform: translateY(100%); transition: transform 280ms ease-out; }
.rl-sheet.is-open { transform: translateY(0); }
```

---

## 7. Что не делать

- **Не возвращать** Indigo `#4F46E5`, pill-кнопки (`radius: 999px`), мягкие soft shadows (`box-shadow: 0 2px 12px rgba`)
- **Не делать** sidebar для фильтров — только горизонтальная filter bar
- **Не использовать** `#FAFAF8` или `#F3F3EF` — заменяет `#FFFFFF` и `#F5F5F0`
- **Не скруглять** кнопки — `0px` строго
- **Не добавлять** blur/glow эффекты — плоский стиль

---

## 8. Статус

| Кто | Что |
|-----|-----|
| **Lead Designer** | ✅ NEO-BRUTALIST: токены, страницы, компоненты — этот файл |
| **Designer** | → `DESIGNER_PROMPT.md` § NEO-BRUTALIST CSS |
| **Coder** | → `CODER_PROMPT.md` § NEO-BRUTALIST после Designer |

---

_Lead Designer · NEO-BRUTALIST · 2026-05-28_
