# RawLead — WordPress сайт · дизайн-референс

**Статус:** v5 · NEO-BRUTALIST · 2026-05-29 (nav W16 · announcement bar W15 · pricing 300⭐ W14 · /how W18 · /contact W19)
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
| Карточки (лента/кабинет) | `border: none` · `box-shadow: 4px 4px 0 #0A0A0A` · radius `4px` · hover offset shadow · **100%:** жёлтая рамка `#FACC15` |
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

**Announcement bar (только лендинг `/`, над шапкой):**
```
Радар онлайн · 800+ лидов в неделю   [Смотреть ленту →]
```
- `background: #0A0A0A`, `color: #FFFFFF`, height `38px`, Manrope 600 13px
- CTA: `color: #FACC15`, без underline, → `/lenta/`
- Mobile: текст короче «800+ лидов · [Смотреть →]»

**Все страницы (кроме `/lenta/`, `/cabinet/`):**
```
[◎ RawLead  by Rode51]   Лента · Тарифы · Как устроено   [Войти →]
```
- Фон `#FFFFFF`, `border-bottom: 2px solid #0A0A0A` (всегда)
- Логотип: марка ◎ 20px + «RawLead» Manrope 900 + «by Rode51» 11px 0.4 opacity
- Nav items: Manrope 700, 13px, uppercase, letter-spacing 0.08em; active: `border-bottom: 2px solid #0A0A0A`
- «Контакты» убрана из primary nav — только в footer
- CTA «Войти →» — чёрная прямоугольная кнопка `0px` radius (не «Войти в кабинет»)
- Мобайл: гамбургер справа; drawer меню

**Продуктовые `/lenta/`, `/cabinet/` (минимальный):**
```
[◎ RawLead]                              [Войти →]
```
- Минимальный, не отвлекает от контента продукта

### 3.2 Лендинг `/`

> **O41 (2026-05-29):** hero = только текст + CTA (жёлтый экран). Live Preview Feed = отдельная белая секция НИЖЕ с `border-top: 4px solid #0A0A0A`. Это разделение — ключевое отличие от Wave 2 «косметики».

```
Header (sticky, 2px black border-bottom)

Hero (min-height: 100svh, background: #FACC15)
  ─── ТОЛЬКО ТЕКСТ + CTA — никаких карточек внутри жёлтого блока ───

  H1: «Лиды без шума»                              ← CANONICAL, не менять
      Manrope 900, clamp(56px, 10vw, 96px), #0A0A0A, letter-spacing -0.03em
      max-width: 720px; margin-bottom: 24px

  Подзаголовок:
      «Биржи и Telegram — в одной ленте. ИИ убирает мусор до тебя.»
      Manrope 400, clamp(18px, 2.5vw, 22px), #0A0A0A, opacity 0.75
      max-width: 560px; margin-bottom: 40px

  CTA-группа (flex-row gap 16px, mobile: flex-column):
    PRIMARY:   [Смотреть ленту →]
                 bg #0A0A0A, color #FFFFFF, radius 0px, padding 16px 32px
                 hover: bg #FACC15, color #0A0A0A, border 2px solid #0A0A0A
    SECONDARY: [Тарифы ↓]
                 bg transparent, border 2px solid #0A0A0A, color #0A0A0A, padding 14px 28px, radius 0px
                 hover: bg #0A0A0A, color #FACC15
                 → якорь #pricing-preview на этой же странице

  Hero geo-декор (W11): SVG-угловые элементы, opacity 0.12, не перекрывают текст
  Нижний отбивщик: border-bottom 4px solid #0A0A0A

Live Preview Feed (background: #FFFFFF, border-top: 4px solid #0A0A0A, border-bottom: 2px solid #0A0A0A)
  ─── ОТДЕЛЬНАЯ БЕЛАЯ СЕКЦИЯ, полностью изолирована от жёлтого ───

  Метка секции: «Последние заказы из ленты»
    Manrope 700, 11px, uppercase, letter-spacing 0.1em, color #0A0A0A
    padding-top: 32px; margin-bottom: 20px

  3 карточки (.rl-lead-card) в полном neo-brutalist стиле:
    border: 2px solid #0A0A0A
    box-shadow: 4px 4px 0 #0A0A0A
    radius: 4px
    hover: box-shadow 6px 6px 0 #0A0A0A + translate(-2px,-2px)
    — НЕ интерактивные (без кнопки «Написать»), только preview

  [Открыть все →] — ghost link, Manrope 700 14px, черный, → /lenta/
    padding: 20px 0 32px; выровнен по левому краю карточек

Блок «Как это работает» (background: #F3E8FF, border-top: 2px solid #0A0A0A)
  3 пункта, layout 3 col desktop / 1 col mobile
  Каждый: иконка 32px + Manrope 700 18px + 2 строки text
  Без нумерации 01-02-03

Тарифы (якорь id="pricing-preview", background: #F5F5F0, border-top: 2px solid #0A0A0A)
  Одна карточка «ИИ-агент»
  border: 2px solid #0A0A0A, shadow: 4px 4px 0 #0A0A0A, radius: 4px
  Цена: «300 ⭐ / мес» (Telegram Stars) · без Badge «Скоро»
  CTA: [Подключить — 300 ⭐ →] — чёрная кнопка → /pricing/

Footer (background: #0A0A0A, color: #FFFFFF)
  RawLead | Лента · Тарифы · Контакты | Telegram
  © 2026 RawLead
```

**Убрать:** pill-кнопки, shadow soft-cards (заменяет flat shadow), манифест-полоса, sidebar фильтры, кубики-анимация.

**O41 checkpoints (для @coder):**
- Hero = NO cards inside yellow zone (только H1 + sub + CTA-группа)
- Live Preview = белая секция, первый элемент после hero-border
- Secondary CTA на жёлтом: `border: 2px solid #0A0A0A` — не ghost-link
- H1 на prod = «Лиды без шума» (если иное — баг, исправить)

### 3.3 Лента `/lenta/`

Детальная спека: [`feed-cabinet-mvp.md`](feed-cabinet-mvp.md) · **sync prod v1.10.9 (2026-05-29)**

Ключевые принципы:
- Фон `#FFFFFF`
- Filter bar горизонтальная sticky под header, `border-bottom: 2px solid #0A0A0A`
- Chips: `border: 2px solid #0A0A0A`, `radius: 2px`; active: black fill, white text
- Карточки: **`border: none`**, `box-shadow: 4px 4px 0 #0A0A0A`, hover: `6px 6px 0` + `translate(-2px, -2px)` · perfect-match: жёлтая рамка
- Mobile: 1 col; Desktop: 2 col max-width 900px
- **O11 (copy-волна):** info-strip `.rl-feed-delay-notice` под счётчиком — «~15 мин на бесплатной ленте · подписка мгновенно» (см. Product § TWO-SPEEDS-COPY)

### 3.3a \/pricing/\ — полная страница

H1 «Тарифы» на жёлтом (\#FACC15\) фоне — отдельная страница, не только якорь.

Таблица сравнения 2 колонки (NEO: \order: 2px solid #0A0A0A\, без зебры):

| | Бесплатно | ИИ-агент |
|--|-----------|----------|
| Скорость | ~15 мин задержка | **Мгновенно** + push TG |
| Отклики | — | Черновик ИИ |
| Push в Telegram | — | ✓ |
| Цена | 0 | **300 ⭐ / мес** |

CTA под таблицей: \[Подключить — 300 ⭐ в Telegram →]\  
Оплата: Telegram Stars (не ЮKassa). Кнопка → Stars-оплата через @rawlead_bot.
### 3.4 Кабинет `/cabinet/`

Детальная спека: [`feed-cabinet-mvp.md`](feed-cabinet-mvp.md)

- Тот же стиль что на `/lenta/`
- Навыки пользователя: bordered chips, active = yellow fill + black text
- Match-bar: `background: #0A0A0A`

**Inbox-карточка = карточка ленты + черновик + удалить:**

```
[Source●] [Бюджет]  [ИДЕАЛЬНО ✦]                [✕ Удалить]
Заголовок заказа
████████░░  73%   👁 234
[Брать]  [Сомнительно]
─────────────────────────────────
Черновик ИИ ▾   (desktop: раскрыт / mobile: collapsed)
«Здравствуйте, готов взяться...»
[Скопировать]
```

- Нет черновика: «Черновик не сгенерирован · [Написать на ленте →]» (muted)
- `[✕ Удалить]` — top-right; удаляет из ЛК, не отзыв с платформы
- Empty paid: «Напишите первый отклик на ленте →»
- Empty free: «Доступно с подпиской · 300 ⭐»

### 3.5 `/how` — Как работает

```
Header

H1: «Как работает»
    Manrope 900, clamp(40px, 8vw, 64px), на фоне #FACC15 (полная ширина секция)

3 горизонтальных шага (desktop: 1 строка 3 col · mobile: 1 col):
  Без карточек — просто номер + текст + подпись
  Разделитель: вертикальная линия 2px solid #0A0A0A между шагами (desktop)

  ① Биржи в одном потоке
    FL · Kwork · Telegram — без ручного мониторинга

  ② ИИ убирает мусор
    ~87% нерелевантного срезается до тебя

  ③ Ты видишь первым
    Платники — мгновенно. Бесплатно — ~15 мин

CTA: [Смотреть ленту →] — чёрная кнопка, full-width mobile
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

Основное:
  [Написать в Telegram →] — чёрная кнопка, padding 16px 32px
  ведёт на t.me/rawlead (или @rawlead_bot)

Дополнительно (muted, 14px):
  «Или напишите на email: hello@rawlead.ru»

Убрать: форму CF7, «заявка», «ранний доступ», «закрытое тестирование»
Footer
```

---

## 4. Компоненты

| Компонент | Спека |
|-----------|-------|
| **Кнопка primary** | bg `#0A0A0A`, text `#FFFFFF`, radius `0px`, border `2px solid #0A0A0A`; hover: bg `#FACC15`, text `#0A0A0A`; active: scale 0.97 |
| **Кнопка secondary** | border `2px solid #0A0A0A`, text `#0A0A0A`, bg transparent; hover: bg `#F5F5F0` |
| **Кнопка ghost** | text `#0A0A0A`, underline при hover, без рамки |
| **Карточка лида** | bg `#FFFFFF`, **`border: none`**, `box-shadow: 4px 4px 0 #0A0A0A`, `radius: 4px`, padding `20px 24px`; hover: `6px 6px 0` + `translate(-2px,-2px)` · **perfect-match:** border `2px #FACC15` + жёлтая тень |
| **Chip категории** | active: bg `#0A0A0A` + text `#FFFFFF`; inactive: bg `#FFFFFF` + `border: 2px solid #0A0A0A` + text `#0A0A0A` |
| **Chip навыка** | active: bg `#FACC15` + text `#0A0A0A` + `border: 2px solid #0A0A0A`; inactive: bg `#FFFFFF` + `border: 2px solid #D4D4D4` |
| **Match-bar** | bg `#D4D4D4`, fill `#0A0A0A`, height `4px`, radius `0px`; animate width 500ms; zero state: fill `#525252` |
| **Match breakdown** | `.rl-match-breakdown` · Manrope 12px/400 · color `#525252` · 1 строка под match row; **с навыками:** `Качество заказа: {ai_score} · Навыки: {keyword_match}%`; **zero state:** `Добавь навыки, чтобы увидеть совместимость →` (ghost link → `[Навыки ▾]`); mobile: 11px, overflow ellipsis |
| **Source badge** | dot 8px + label 12px/700: FL `#00A65A` · Kwork `#EA580C` · TG `#0088CC` |
| **AI-чип «Брать»** | bg `#DCFCE7`, text `#16A34A`, border `1.5px solid #16A34A`, radius `2px`; при 100% match — **скрыт**, показывается `ИДЕАЛЬНО ✦` |
| **AI-чип «Сомнительно»** | bg `#F5F5F5`, text `#6B7280`, border `1.5px solid #D4D4D4`, radius `2px` |
| **Match label (режим A)** | «Совместимость» · Manrope 13px/700 · `#0A0A0A`; tooltip (title): «Качество × 60% + Навыки × 40%» |
| **Match label (режим B)** | «Качество заказа» · Manrope 13px/700 · `#525252`; показывается когда `user_skills = []` |
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
| **Designer** | ✅ Wave 2 → [`wave-2-css-brief.md`](wave-2-css-brief.md) |
| **Coder** | → `CODER_PROMPT.md` § WAVE-2-CSS после Lead |

---

_Lead Designer · NEO-BRUTALIST · 2026-05-29 · O41 hero/card split_
