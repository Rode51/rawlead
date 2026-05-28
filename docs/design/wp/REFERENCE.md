# RawLead — WordPress сайт · дизайн-референс

**Статус:** v3 · REVOLUTION · 2026-05-28  
**Направление:** «Рабочий инструмент» — тёплый, прямой, для фрилансера 25–35  
**Поверхности:** лендинг `/` · `/lenta/` (лента) · `/cabinet/` (кабинет) · `/how` · `/faq` · `/contact`  
**Отменено (v2):** editorial B2B cold, Unbounded, манифест-полоса, кубики-анимация «источников», «Для кого» 4 карточки

Токены: [`../../team/design/DESIGN_SYSTEM.md`](../../team/design/DESIGN_SYSTEM.md) § WordPress REVOLUTION  
Спека `/lenta/` + `/cabinet/`: [`feed-cabinet-mvp.md`](feed-cabinet-mvp.md)

---

## 1. Суть стиля

| Принцип | Решение |
|---------|---------|
| Атмосфера | Инструмент, не маркетинг. Тёплый белый, чистые отступы |
| Аудитория | Фрилансер в телефоне: большие зоны касания, thumb-zone |
| Акцент | **Один:** `#4F46E5` Indigo — кнопки, match-bar, активные чипы |
| Шрифт | **Только Manrope** 800 display / 400–600 body |
| Карточки | Тень `0 2px 12px rgba(0,0,0,0.07)` + `radius 20px` — как мессенджер-карточка |
| Фон | `#FAFAF8` тёплый белый; секции `#F3F3EF`; footer `#1A1A2E` |
| Mobile | **Mobile-first** — всё работает в одну руку на телефоне |
| Голос | Активный залог, без !; кнопка = конкретное действие |

---

## 2. Токены (сводка — полные в DESIGN_SYSTEM.md § WP REVOLUTION)

| Назначение | Токен | Значение |
|------------|-------|----------|
| Фон страницы | `color/bg/page` | `#FAFAF8` |
| Фон секции | `color/bg/section` | `#F3F3EF` |
| Тёмный inverse | `color/bg/inverse` | `#1A1A2E` |
| Основной текст | `color/text/primary` | `#18181B` |
| Body текст | `color/text/body` | `#3F3F46` |
| Muted | `color/text/muted` | `#71717A` |
| Акцент / CTA | `color/cta/primary` | `#4F46E5` |
| CTA hover | `color/cta/primary-hover` | `#4338CA` |
| Match-bar | `color/match/bar` | `#4F46E5` |
| Граница | `color/border` | `#E4E4E7` |
| Тень карточки | `shadow/card` | `0 2px 12px rgba(0,0,0,0.07)` |
| Тень hover | `shadow/card-hover` | `0 8px 28px rgba(0,0,0,0.12)` |
| Radius карточки | `radius/card` | `20px` |

---

## 3. Структура страниц

### 3.1 Header (sticky, все страницы)

**Лендинг `/`:**
```
[RawLead]   Лента · Тарифы · Контакты   [Войти в кабинет]
```
- Фон `#FAFAF8`, border-bottom `1px solid #E4E4E7` при скролле
- Логотип «RawLead» — Manrope 800, `#18181B`, → `/`
- CTA «Войти в кабинет» — outline pill, `#4F46E5` border+текст
- Мобайл: гамбургер справа; меню — drawer слева (не bottom sheet)

**Продуктовые страницы `/lenta/`, `/cabinet/`:**
```
[RawLead]                                [Войти в кабинет]
```
- Тонкий, минимальный — не отвлекает от контента
- На `/cabinet/`: «Войти в кабинет» → иконка профиля / «Выйти»

### 3.2 Лендинг `/`

```
Header (sticky)

Hero (min-height: 100svh mobile)
  H1: «Лиды без шума»
  Подзаголовок: «Биржи и Telegram — в одной ленте. ИИ убирает мусор до тебя.»
  CTA primary: [Смотреть ленту →]   (indigo pill, 18px/600, padding 16px 32px)
  CTA secondary: [Смотреть тарифы ↓]  (ghost link + ↓)

Live Preview Feed (3–4 реальных карточки из /v1/feed)
  Фон: #F3F3EF
  Карточки — новый стиль (тень, radius 20px)
  Подпись: «Последние заказы из ленты»
  [Открыть все →] → /lenta/

Блок «Как это работает» (3 пункта, без нумерации 01-02-03)
  Layout: 3 col desktop / 1 col mobile, gap 32px
  Каждый пункт: иконка 32px + заголовок Manrope 18/700 + 2 строки текста
  Пункты: «Биржи в одном потоке» · «ИИ убирает шум» · «Ты откликаешься сам»

Тарифы (якорь id="pricing-preview")
  Одна карточка «ИИ-агент»
  shadow/card, radius 20px, фон #FFFFFF на `#F3F3EF` фоне
  Цена: «от 300 ₽/мес» · Badge «Скоро» (серый)
  CTA: [Узнать первым →] → /contact

Footer (фон #1A1A2E, текст #FFFFFF)
  RawLead | Лента · Тарифы · Контакты | Telegram
  © 2026 RawLead
```

**Убрать с лендинга:** манифест-полоса «Не сидите на бирже» (театрально), кубики-анимация источников (трудозатратно), «Для кого» 4 карточки (заменяет live feed).

### 3.3 Лента `/lenta/`

Детальная спека: [`feed-cabinet-mvp.md`](feed-cabinet-mvp.md)

Ключевые принципы:
- **Mobile-first:** 1 колонка на мобайле, 2 колонки на десктопе (max-width 900px по центру)
- Filter bar горизонтальная sticky под header (не боковой sidebar)
- Карточки — shadow-based, без жёсткой рамки
- Infinite scroll

### 3.4 Кабинет `/cabinet/`

Детальная спека: [`feed-cabinet-mvp.md`](feed-cabinet-mvp.md)

Ключевые принципы:
- Навыки пользователя — редактируемые chips sticky под header
- Тот же filter bar что на `/lenta/`
- Match-bar `#4F46E5`, width = match%

### 3.5 `/how` — Как работает

```
Header

H1: «Как работает RawLead»

4 шага (карточки 2×2 desktop / 1 col mobile):
  Каждая: иконка line 28px + Manrope 16/700 + 2 строки

Шаги:
  1. «Подключаешь биржи» — выбираешь FL, Kwork, Telegram-чаты
  2. «Радар парсит» — новые заказы каждые ~15 минут
  3. «ИИ фильтрует» — оставляет только релевантные тебе
  4. «Ты видишь в ленте» — без рекламы и мусора

CTA: [Смотреть ленту →]
Footer
```

Убрать: timeline вертикальный, нумерацию 01-02-03 (шрифтовой артефакт v2).

### 3.6 `/faq` — Частые вопросы

```
Header

H1: «Частые вопросы»

Аккордеон (Manrope, фон #FAFAF8):
  - каждый item: border-bottom #E4E4E7, padding 20px 0
  - открытый: плавное expand (300ms ease-out)
  - стрелка → вращается 180° при открытии

Убрать: «закрытое тестирование», «ранний доступ», «по приглашению»

Footer
```

### 3.7 `/contact` — Контакты

```
Header

H1: «Связаться»

Форма (CF7, primary):
  Имя (input)
  Email (input)
  Сообщение (textarea, min 3 строки)
  [Отправить] (primary pill indigo)

Под формой:
  «Или напишите напрямую →» [Telegram] (ghost link)

Убрать: «заявка на ранний доступ», «закрытое тестирование», «по приглашению»
Оставить: простую форму без полей «Тариф», «Тип аккаунта» и т.п.

Footer
```

---

## 4. Компоненты

| Компонент | Спека |
|-----------|-------|
| **Кнопка primary** | bg `#4F46E5`, text `#FFFFFF`, radius `999px`, hover bg `#4338CA`, active scale 0.97 |
| **Кнопка secondary** | border `1px solid #4F46E5`, text `#4F46E5`, прозрачный фон, hover bg `#EEF2FF` |
| **Кнопка ghost** | только текст + → без рамки, `#4F46E5` color |
| **Карточка лида** | bg `#FFFFFF`, shadow `0 2px 12px rgba(0,0,0,0.07)`, radius `20px`, padding `20px 24px`; hover: shadow↑ + translateY(-2px) |
| **Chip категории** | active: bg `#4F46E5` + text `#FFFFFF`; inactive: bg `#F3F3EF` + border `#E4E4E7` + text `#3F3F46` |
| **Chip навыка** | active: bg `#EEF2FF` + text `#4F46E5`; inactive: bg `#F3F3EF` + border `#E4E4E7` |
| **Match-bar** | bg `#E4E4E7`, fill `#4F46E5`, height `4px`, radius `2px`; animate width 600ms при входе в viewport |
| **Source badge** | dot 8px + label 12px/600: FL `#00A65A` · Kwork `#EA580C` · TG `#0088CC` |
| **AI-чип «Брать»** | bg `#DCFCE7`, text `#16A34A`, radius `999px` |
| **AI-чип «Сомнительно»** | bg `#F3F4F6`, text `#6B7280` |
| **Report bug FAB** | `?` round 40px, bg `#FFFFFF`, border `1px solid #E4E4E7`, shadow, `#4F46E5` text; bottom-right fixed |
| **Иконки категорий** | line-stroke 20px: `</>` dev · `✦` design · `◎` marketing · `Aa` text |
| **Skeleton-карточка** | bg linear-gradient пульс `#F3F3EF → #E4E4E7 → #F3F3EF`, radius `20px` |

---

## 5. Голос (из Product-канона)

- Активный залог: «ИИ убрал мусор», не «заказы были отфильтрованы»
- Без восклицательных знаков
- Кнопки = конкретное действие: «Смотреть ленту», «Войти в кабинет»
- Mobile: короткие метки — «Дизайн» не «Дизайн & Видео»
- Пустые состояния: человечные — «Пока нет заказов по этим навыкам — попробуй шире»
- Контакты: без «заявки» / «раннего доступа» — просто «напишите нам»

---

## 6. Анимации

**Принцип:** только `transform` + `opacity` — нулевая нагрузка на GPU. IntersectionObserver, unobserve после первого срабатывания.

### 6.1 Появление при скролле

```css
.rl-reveal { opacity: 0; transform: translateY(20px); }
.rl-reveal.is-visible {
  opacity: 1; transform: none;
  transition: opacity 240ms ease-out, transform 240ms ease-out;
}
```

### 6.2 Stagger карточек

```css
.rl-card:nth-child(1) { transition-delay: 0ms; }
.rl-card:nth-child(2) { transition-delay: 40ms; }
.rl-card:nth-child(3) { transition-delay: 80ms; }
```

### 6.3 Hover карточки

```css
.rl-lead-card {
  transition: transform 150ms ease-out, box-shadow 150ms ease-out;
}
.rl-lead-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(0,0,0,0.12);
}
```

### 6.4 Match-bar fill

```css
.rl-match__fill { width: 0; transition: width 600ms ease-out; }
.is-visible .rl-match__fill { width: var(--match-value); }
```

### 6.5 Micro-press

```css
.rl-btn:active { transform: scale(0.97); transition: transform 80ms ease-out; }
```

### 6.6 Bottom sheet mobile (filters)

```css
.rl-sheet { transform: translateY(100%); transition: transform 300ms ease-out; }
.rl-sheet.is-open { transform: translateY(0); }
```

### 6.7 IntersectionObserver

```js
const io = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('is-visible'); io.unobserve(e.target); }
  });
}, { threshold: 0.15 });
document.querySelectorAll('.rl-reveal').forEach(el => io.observe(el));
```

---

## 7. Что не делать

- **Не возвращать** Unbounded, манифест-полосу, нумерацию 01/02/03, кубики-анимацию источников
- **Не копировать** холодный B2B стиль (Linear/Notion feel) — это был v2, отменён
- **Не делать** sidebar для фильтров — только горизонтальная filter bar
- **Не ставить** `#0A0A0A` как primary CTA — только Indigo `#4F46E5`
- **Не использовать** восклицательные знаки в текстах
- **Не упоминать** «ранний доступ», «закрытое тестирование», «по приглашению» — продукт открыт

---

## 8. Статус

| Кто | Что |
|-----|-----|
| **Lead Designer** | ✅ REVOLUTION: токены, страницы, компоненты, голос — этот файл |
| **Designer** | → `DESIGNER_PROMPT.md` — CSS REVOLUTION |
| **Coder** | → `CODER_PROMPT.md` § PRE-LAUNCH-UX — PHP/JS после дизайна |

---

_Lead Designer · REVOLUTION · 2026-05-28_
