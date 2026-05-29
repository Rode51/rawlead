# Lead Designer — активный план

**Обновлено:** 2026-05-29 · **Регламент:** [`LEAD_DESIGN.md`](LEAD_DESIGN.md) — **кто какой файл читает**

| | |
|--|--|
| **→ Сейчас** | § **WAVE-4-UX-FIX** — спека в `DESIGNER_PROMPT` · **→ @lead-architect** → `@coder` |
| **Prod** | theme v1.9.0 · O35/O41/WAVE-4 ✅ prod |
| **Vision** | [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.11** |

**Gate:** PRE-PROD stress (O37) — после UI OK владельца.

---

## § WAVE-4-UX-FIX — согласовано владельцем 2026-05-29 (**→ СЕЙЧАС**)

**Статус:** ✅ согласовано · → @coder через Lead Architect
**Дата:** 2026-05-29
**Бриф для Coder:** `DESIGNER_PROMPT.md` § WAVE-4-UX-FIX

### Контекст (ЦА и голос)

**Аудитория:** фрилансеры 25–35, микс (dev-heavy → 60–65% мужчины, но дизайн/тексты/маркетинг — значимая женская доля). Работают в Telegram и с телефона. Ценят конкретику, не любят корпоративщину. Сленг понимают, но не обязателен.

**Стиль текста:** «Лиды без шума» — коротко, прямо, с характером. Никаких «пожалуйста» и «уважаемый(ая)».

**Правило рода:** `ты` остаётся. **Запрещены** глаголы прошедшего времени с родовым согласованием: `вошёл/вошла`, `нажал/нажала`, `добавил/добавила` → заменяем на нейтральные конструкции (инфинитивы, существительные, настоящее время).

### Решения (не менять без нового слова владельца)

| # | Проблема | Решение |
|---|---------|---------|
| V1 | Карточки ЛК — тонкие строки, не карточки | Полная карточка = та же структура что в ленте + черновик ИИ + `[✕ Удалить]` |
| V2 | «Загрузить ещё» висит даже когда всё загружено | Кнопка скрыта если `shown >= total` |
| V3 | «Загружаем ещё заказы...» висит всегда | Spinner/текст — только в состоянии loading (после клика, до ответа API) |
| V4 | /lenta/ header без полной навигации | Добавить `Тарифы · Как устроено` на все страницы (кроме `/cabinet/` — там уже есть) |
| V5 | Нет кнопки поддержки | FAB bottom-right на всех страницах → открывает inline chat-модалку (UI: textarea + кнопка «Отправить»; backend — placeholder, задача Coder отдельно) |
| V6 | Тексты — мужской род / нейтральные | Полный список замен в `DESIGNER_PROMPT.md` § WAVE-4-COPY |
| V7 | Мало интерактива | Skeleton-loading при первой загрузке; press-анимация кнопок; stagger для новых карточек после «Загрузить ещё» |

### Конвейер

| Этап | Кто | Статус |
|------|-----|--------|
| Решения + бриф | @lead-designer | ✅ 2026-05-29 |
| Спека в DESIGNER_PROMPT | @lead-designer | ✅ 2026-05-29 |
| CODER_PROMPT + deploy | @lead-architect → @coder | **✅ prod 2026-05-29** |

---

## § DESIGN-WAVE-3 / O41 — Gumroad hero (**✅ prod 2026-05-29 · АРХИВ**)

**Дата:** 2026-05-29  
**Статус:** ✅ **Lead Designer — docs сданы** · → @lead-architect → @coder

**Факт:** владелец видит Wave 2 на prod и говорит «это не тотальная пересборка». Цель: **gumroad.com** — максимально приблизиться к этому уровню качества.

**Конкретные проблемы (скрин 2026-05-29):**

| # | Проблема | Что сделать |
|---|---------|------------|
| 1 | **Белая карточка на жёлтом** hero-фоне | → добавить order: 2px solid #0A0A0A + ox-shadow: 4px 4px 0 #0A0A0A или убрать из hero вовсе |
| 2 | **H1 не обновлён** — «Заказы под твой стек» вместо «Лиды без шума» | выяснить: не применено в Coder или нет в REFERENCE — в любом случае зафиксировать |
| 3 | **Secondary CTA** («Вход в ЛК» / «Тарифы ↓») выглядят слабо | специфицировать стиль: ghost-кнопка с order: 2px solid #0A0A0A или простой link-underline |
| 4 | **Общее** — косметика поверх старого, не пересборка | описать, что конкретно отличает RawLead от Gumroad-уровня |

**Решения зафиксированы (2026-05-29):**

| # | Проблема | Решение Lead |
|---|---------|-------------|
| 1 | **Белая карточка на жёлтом** | Hero = только текст+CTA. Live Preview = отдельная белая секция ниже с `border-top: 4px solid #0A0A0A`. Карточки: `border: 2px solid #0A0A0A` + `box-shadow: 4px 4px 0 #0A0A0A` |
| 2 | **H1 не обновлён** | Канон = «Лиды без шума». Если иное — баг Coder. @coder: проверить `hero.php` |
| 3 | **Secondary CTA слабая** | neo-brutalist secondary: `bg transparent` + `border: 2px solid #0A0A0A`; hover: `bg #0A0A0A` + `color #FACC15` |
| 4 | **Общее** | Gumroad-принцип: каждая секция делает ОДНО. Hero = H1+sub+CTA. Preview = отдельный белый блок |

**Документы обновлены (2026-05-29):**

| Файл | Что изменено |
|------|-------------|
| [`REFERENCE.md`](../../design/wp/REFERENCE.md) **§3.2** | Hero = pure text zone. Live Preview = отдельная секция. Secondary CTA spec |
| [`wave-2-css-brief.md`](../../design/wp/wave-2-css-brief.md) **§ w3-delta-O41** | CSS delta: hero split, secondary CTA, H1 verify, breathing room |
| [`DESIGNER_PROMPT.md`](DESIGNER_PROMPT.md) **§ O41-WAVE3** | Handoff @coder: файлы, задачи O41-1–5, приёмка |

**Конвейер O41:**

| Этап | Кто | Статус |
|------|-----|--------|
| 1 — Анализ + решения | @lead-designer | ✅ 2026-05-29 |
| 2 — REFERENCE §3.2 + wave-2-css-brief delta | @lead-designer | ✅ 2026-05-29 |
| 3 — § O41-WAVE3 в DESIGNER_PROMPT | @lead-designer | ✅ 2026-05-29 |
| 4 — Тема + deploy | @coder + Lead ops | **✅ WAVE-4 prod 2026-05-29** |

## § DESIGN-WAVE-2 — полный план (зафиксировано 2026-05-29)

**Решение владельца:** полное переосмысление UI/UX — не патч поверх Wave 1.
**Источники инспирации:** [gumroad.com](https://gumroad.com) · [feastables.com](https://feastables.com) · [99percentoffsale.com](https://www.99percentoffsale.com) · [retroui.dev](https://retroui.dev)

### Конвейер

| Этап | Кто | Выход | Статус |
|------|-----|-------|--------|
| 1 | `@lead-designer` | Все решения + Recraft концепты | ✅ этот файл |
| 2 | `@lead-designer` | `REFERENCE.md` v5 · `DESIGN_SYSTEM.md` обновление | → после Designer |
| 3 | `@designer` | CSS-спека → [`wave-2-css-brief.md`](../../design/wp/wave-2-css-brief.md) | ✅ 2026-05-29 |
| 4 | `@lead-designer` | ревью brief + REFERENCE v5 | ✅ 2026-05-29 |
| 5 | `@coder` | theme + deploy | **✅** v1.9.0 prod 2026-05-29 |

---

### Решения владельца (финал, не менять без нового слова)

| # | Параметр | Решение |
|---|----------|---------|
| W1 | **Стиль** | NEO-BRUTALIST остаётся (жёлтый hero, чёрные рамки, плоские тени, Manrope) — оживляем анимациями, не меняем язык |
| W2 | **Анимации scroll** | Театральные — элементы «влетают» при входе в viewport (stagger, slide-in с разных направлений, 300–400ms ease-out) |
| W3 | **Анимации hover/click** | Тактильные — быстрые (80–120ms), физичные (shadow растёт, кнопка «нажимается», карточка сдвигается) |
| W4 | **100% совпадение** | Карточка «взрывается»: пульс-кольцо при появлении + жёлтый glow + бейдж «Идеально ✦» |
| W5 | **Match-бар** | Анимированное заполнение при входе в viewport (0% → N%, 600ms ease-out) |
| W6 | **Пагинация** | Кнопка «Загрузить ещё →» вместо infinite scroll |
| W7 | **Баланс** | 50/50 удовольствие / инструмент |
| W8 | **«by Rode51»** | Footer: `RawLead · by Rode51` (muted, 12px) · Header: рядом с лого `by Rode51` (11px, 40% opacity) |
| W9 | **Марка** | Radar-сигнал (3 дуги из угла) — для favicon/TG-аватара · текстовый лого «RawLead» Manrope 900 остаётся |
| W10 | **Иконки категорий** | `</>` dev · `✦` design · мегафон marketing · `Aa` text — единый stroke 2px |
| W11 | **Hero-фон** | Геометрические чёрные фигуры по краям/углам hero-секции — не перекрывают текст |
| W12 | **Карточка лида** | Заголовок + источник badge + бюджет + match-бар (animated) + % совпадения + eye+число просмотров + чипы «Брать»/«Сомнительно» |
| W13 | **Старый дизайн** | Кубики FL/Kwork/TG, белые мягкие карточки — удалить полностью |
| W14 | **Ценник** | **300 ⭐ Telegram Stars / мес** (не 590 ₽) — везде на сайте |
| W15 | **Announcement bar** | Чёрная полоска над шапкой: «Радар онлайн · 800+ лидов в неделю [Смотреть ленту →]» · bg `#0A0A0A` · 38px · Manrope 600 · CTA жёлтый — только лендинг |
| W16 | **Навигация** | `[◎ RawLead by Rode51]  Лента · Тарифы · Как устроено  [Войти →]` · убрать «Контакты» из primary nav · items Manrope 700 13px uppercase letter-spacing 0.08em · active: underline 2px solid #0A0A0A · «Войти →» вместо «Войти в кабинет» |
| W17 | **`/pricing/`** | Полноценная страница: H1 на жёлтом + таблица 2 колонки (Бесплатно vs ИИ-агент: Скорость / Отклики / Push TG / Цена 300 ⭐) + CTA `[Подключить — 300 ⭐ →]` |
| W18 | **`/how/`** | 3 горизонтальных шага вместо 4 карточек 2×2: «Биржи в потоке / ИИ убирает мусор / Ты видишь первым» — одна строка под каждым, без абстракций |
| W19 | **`/contact/`** | Убрать форму CF7; только `[Написать в Telegram →]` + email строчкой muted |

---

### Recraft-ассеты (концепты сгенерированы 2026-05-29)

| Файл | Описание | Статус |
|------|----------|--------|
| `docs/design/assets/rawlead-mark-concept.png` | Radar-марка (3 дуги) — концепт | ✅ |
| `docs/design/assets/rawlead-hero-bg-concept.png` | Hero geo-паттерн чёрный/жёлтый — концепт | ✅ |
| `docs/design/assets/rawlead-category-icons-concept.png` | 4 иконки категорий в сетке — концепт | ✅ |

**Production SVG** — генерить в [recraft.ai](https://recraft.ai) по промптам:

```
Марка (favicon):
"Bold geometric radar signal mark, 3 concentric quarter-circle arcs from bottom-left corner,
flat black vector, SVG, no text, favicon-safe, neo-brutalist"
style: Vector art, model: recraftv3

Hero decoration:
"Neo-brutalist abstract geometry, bold black diagonal lines and rectangles scattered
on transparent/yellow background, flat vector SVG, no gradients, high contrast"
style: Vector art, model: recraftv3

Иконки (по одной):
"Minimal flat icon: [code brackets </> / four-pointed star / megaphone / letters Aa],
black 2px stroke, white fill, consistent with icon set, SVG"
style: Icon, model: recraftv2
```

---

### Анимации — спека (для DESIGNER_PROMPT и Coder)

#### Scroll-театральные (IntersectionObserver, unobserve after first trigger)

```css
/* Карточка — влетает снизу */
.rl-card { opacity: 0; transform: translateY(24px); }
.rl-card.is-visible {
  opacity: 1; transform: none;
  transition: opacity 320ms ease-out, transform 320ms ease-out;
}
/* Stagger: n-я карточка задерживается на n*60ms (max 5-я = 300ms) */
.rl-card:nth-child(2) { transition-delay: 60ms; }
.rl-card:nth-child(3) { transition-delay: 120ms; }
.rl-card:nth-child(4) { transition-delay: 180ms; }
.rl-card:nth-child(5) { transition-delay: 240ms; }

/* Секции лендинга — влетают с небольшим сдвигом */
.rl-section-reveal { opacity: 0; transform: translateY(16px); }
.rl-section-reveal.is-visible { opacity: 1; transform: none;
  transition: opacity 400ms ease-out, transform 400ms ease-out; }
```

#### Hover/click тактильные

```css
/* Карточка hover: тень растёт + сдвиг */
.rl-lead-card { transition: transform 120ms ease-out, box-shadow 120ms ease-out; }
.rl-lead-card:hover { transform: translate(-2px, -2px); box-shadow: 6px 6px 0 #0A0A0A; }

/* Кнопка press: micro-scale */
.rl-btn:active { transform: scale(0.96); transition: transform 60ms ease-out; }

/* Match-bar fill (scroll-trigger) */
.rl-match__fill { width: 0; transition: width 600ms ease-out; }
.rl-card.is-visible .rl-match__fill { width: var(--match-value); }
```

#### 100% match — «взрыв»

```css
.rl-lead-card--perfect {
  border-color: #FACC15;
  box-shadow: 4px 4px 0 #FACC15, 0 0 0 0 rgba(250,204,21,0.4);
}
.rl-lead-card--perfect.is-visible {
  animation: rl-perfect-pulse 600ms ease-out forwards;
}
@keyframes rl-perfect-pulse {
  0%   { box-shadow: 4px 4px 0 #FACC15, 0 0 0 0 rgba(250,204,21,0.6); }
  50%  { box-shadow: 4px 4px 0 #FACC15, 0 0 0 16px rgba(250,204,21,0.2); }
  100% { box-shadow: 4px 4px 0 #FACC15, 0 0 0 24px rgba(250,204,21,0); }
}
.rl-badge--perfect {
  background: #FACC15; color: #0A0A0A;
  border: 2px solid #0A0A0A;
  font-weight: 800; font-size: 11px;
  padding: 2px 8px; letter-spacing: 0.05em;
}
```

---

### Страницы — что изменится (delta от Wave 1)

| Поверхность | Что меняется |
|-------------|-------------|
| **Лендинг hero** | Geo-паттерн по краям (декоративный) · марка рядом с лого · `by Rode51` в header + footer |
| **`/lenta/`** | Карточки с scroll-stagger · match-бар animated · 100%-взрыв · кнопка «Загрузить ещё» вместо scroll · иконки категорий |
| **`/cabinet/`** | Те же анимации · inbox с тактильными hover |
| **Все страницы** | Секции влетают при скролле · hover везде тактильный |
| **Удалить** | Кубики-иллюстрация источников · «кубики собираются» анимация · белые мягкие карточки (если остались) |
| **Шапка (все страницы)** | Announcement bar (лендинг) · новые nav items W16 · «Войти →» |
| **`/pricing/`** | Полная страница W17 · ценник 300 ⭐ |
| **`/how/`** | 3 шага W18 вместо 4 карточек |
| **`/contact/`** | Убрать форму W19 · только TG |

---

### Пагинация — спека

```html
<!-- Вместо infinite scroll: -->
<div class="rl-feed-pagination">
  <button class="rl-btn rl-btn--load-more">
    Загрузить ещё <span class="rl-btn__arrow">→</span>
  </button>
  <span class="rl-feed-pagination__count">Показано 20 из 87</span>
</div>
```

```css
.rl-feed-pagination { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 32px 0; }
.rl-btn--load-more { min-width: 200px; }
.rl-feed-pagination__count { font-size: 13px; color: var(--rl-text-muted); }
```

---

### Handoff → @designer

**Задача:** CSS Wave 2 по спеке выше.
**Файл промпта:** [`DESIGNER_PROMPT.md`](DESIGNER_PROMPT.md) § WAVE-2-CSS
**Ассеты:** `docs/design/assets/` (концепты) + Recraft SVG-промпты выше
**После:** Lead Designer ревью → brief → Lead Architect → CODER_PROMPT

---

## § DESIGN-WAVE-1 — **✅ docs сдано 2026-05-29**

**Prod:** v1.7.24 · функции приняты (O20).

| Приоритет | Задача | Файл |
|-----------|--------|------|
| **1** | NEO-BRUTALIST CSS — `rawlead.css` | [`DESIGNER_PROMPT.md`](DESIGNER_PROMPT.md) § NEO-BRUTALIST |
| **2** | Inbox UI `/cabinet/` (не match-лента) | § **CABINET-INBOX-UI** ниже |
| **3** | Mobile-first лента + filter bar | § структура `/lenta/` ниже |
| **4** | TWO-SPEEDS UI-спека (strip, pricing) | § **TWO-SPEEDS-UI** · copy от PM |
| **5** | **C1** mobile UX polish | [`OWNER_INTENT.md`](../architect/OWNER_INTENT.md) § **C1** |

**Не в этой волне:** O11 в коде (3r) · P4b per-user draft.

**Handoff Coder:** после CSS + PM copy → Lead пишет § **PRE-LAUNCH-UX** в `CODER_PROMPT.md`.

## § NEO-BRUTALIST — финальный стиль (2026-05-28) — **✅ docs сдано**

**Выбор владельца:** Style 13 из сессии перебора стилей (2026-05-28).
**Все предыдущие решения по стилю (REFERENCE v2/v3, REVOLUTION, editorial, Unbounded, Indigo) — отменены.**

> **Актуальный канон:** [`DESIGN_SYSTEM.md`](DESIGN_SYSTEM.md) § NEO-BRUTALIST · [`../../design/wp/REFERENCE.md`](../../design/wp/REFERENCE.md) v4 · [`DESIGNER_PROMPT.md`](DESIGNER_PROMPT.md) § NEO-BRUTALIST CSS

### Что меняется (REVOLUTION → NEO-BRUTALIST)

| Параметр | Было | Стало |
|----------|------|-------|
| Атмосфера | Холодный editorial B2B (Linear/Notion) | **«Рабочий инструмент»** — тёплый, прямой, для реального человека |
| Аудитория | SaaS-пользователь | Фрилансер 25–35, работает в Telegram и на телефоне |
| Фон | `#FFFFFF` холодный | **`#FAFAF8`** тёплый белый |
| Акцент | `#0A0A0A` чёрный CTA | **`#4F46E5` Indigo** — один акцент, тёплый, не «стартап синий» |
| Шрифт | Unbounded (агрессивный) + Manrope | **Только Manrope** — чистый, читаемый |
| Карточки | Жёсткая рамка `#E8E8EC` | **Мягкая тень + radius 20px** — как мессенджер-карточка |
| Mobile | Responsive к desktop | **Mobile-first** — большие зоны касания, thumb-zone |
| Навигация | Top header | **Top header** — остаётся (решение владельца) |

### Новые токены (обновить `DESIGN_SYSTEM.md` + `REFERENCE.md`)

| Token | Значение |
|-------|----------|
| `color/bg/page` | `#FAFAF8` |
| `color/bg/section` | `#F3F3EF` |
| `color/bg/inverse` | `#1A1A2E` (тёплый тёмный, не холодный `#0A0A0A`) |
| `color/cta/primary` | `#4F46E5` |
| `color/cta/primary-text` | `#FFFFFF` |
| `color/cta/primary-hover` | `#4338CA` |
| `color/text/primary` | `#18181B` |
| `color/text/body` | `#3F3F46` |
| `color/text/muted` | `#71717A` |
| `color/border` | `#E4E4E7` |
| `color/match/bar` | `#4F46E5` (один акцент) |
| `font/display` | **Manrope** 800 |
| `font/body` | **Manrope** 400–600 |
| `radius/card` | `20px` |
| `shadow/card` | `0 2px 12px rgba(0,0,0,0.07)` |
| `shadow/card-hover` | `0 8px 28px rgba(0,0,0,0.12)` |

### Структура страниц — НОВАЯ

#### 1. Лендинг `/` — продуктовый (не маркетинговый)

Фрилансер не читает features — он смотрит «а что там за заказы». Поэтому:

```
Header (sticky)
  Logo RawLead | Лента · Тарифы · Контакты | [Войти в кабинет]

Hero (viewport height mobile)
  H1: «Лиды без шума»
  Подзаголовок: «Биржи и Telegram — в одной ленте. ИИ убирает мусор до тебя.»
  CTA: [Смотреть ленту →]  (indigo pill, большой)
  
Live Preview Feed (3–4 реальных карточки из /v1/feed)
  — карточки в новом стиле, не интерактивные
  — подпись: «Последние заказы из ленты»
  — [Открыть все →] → /lenta/

Блок «Как это работает» (3 пункта, без нумерации 01-02-03)
  Биржи в одном потоке | ИИ убирает шум | Ты откликаешься сам

Один тариф — карточка ИИ-агент
  [Узнать первым →] → /contact

Footer (тёмный `#1A1A2E`)
  RawLead | Лента · Тарифы · FAQ · Контакты | Telegram
```

**Убрать:** манифест-полоса (слишком театрально), кубики-анимация источников (время не окупается), блок «Для кого» 4 карточки (заменяет live feed).

---

## § CABINET-INBOX-UI — inbox вместо ленты (**O23**)

**Канон:** Product §0j/0k · Coder § **CABINET-INBOX-O23**.

| Поверхность | Было | Стало |
|-------------|------|-------|
| **`/lenta/`** | все видят одинаково | paid: кнопка «Написать отклик»; anon strip про 15 мин |
| **`/cabinet/`** | match-лента + фильтры | **«Мои отклики»** — компактный список; **удалить**; профиль/навыки/подписка сверху |
| **Empty ЛК** | «нет match» | «Напишите отклик на ленте» |

Фильтры sort/min_match (O22) — **на `/lenta/`**, не в sidebar ЛК.

### Три состояния /cabinet/

| Состояние | UI |
|-----------|-----|
| **Anon** | редирект → TG Login (кастомная кнопка, без iframe) |
| **Free** (TG login, не paid) | навыки-чипы (collapsed) + upsell подписки + inbox locked |
| **Paid** (`is_active`) | навыки-чипы (collapsed) + статус подписки + inbox откликов |

**Inbox карточка (paid):** та же карточка что в ленте + черновик + удалить.

Структура (сверху вниз):
```
[Source badge] [Бюджет]  [ИДЕАЛЬНО ✦ — если 100%]   [✕ Удалить]
Заголовок заказа
Match-bar [N%]   👁 N просмотров
[Брать] [Сомнительно]
──────────────────────────
Черновик ИИ ▾              ← всегда раскрыт на desktop; collapsed на mobile
«Текст черновика...»
[Скопировать]
```

Состояния черновика:
- **Есть** — блок «Черновик ИИ» + текст + `[Скопировать]`
- **Нет** — строка «Черновик не сгенерирован · [Написать на ленте →]» (muted)

- `[✕ Удалить]` — top-right угол карточки; удаляет только из ЛК, не отзыв с платформы
- Статус: только дата отклика (нет «просмотрен заказчиком»)
- Empty paid: «Напишите первый отклик на ленте →»
- Empty free: «Доступно с подпиской · 300 ⭐»

---

## § C1-MOBILE-UX — Mobile UX пересбор (**2026-05-29**) ✅ согласовано

**Решение владельца:** 2026-05-28 · волна C E-polish  
**Scope:** WP-сайт на телефоне (390×844) · не Tauri-пульт, не радар  
**Канон:** NEO-BRUTALIST токены + acceptance-слой thumb-zone/sheets/viewport

### Принципы

- Все зоны касания ≥ 44px
- Sticky header 48px + sticky filter bar 44px
- Bottom sheets вместо dropdown на mobile
- Full-width CTA pill 52px
- TG Login: кастомная кнопка deep link, без iframe Telegram

### /lenta/ mobile

| Элемент | Решение |
|---------|---------|
| Filter bar | 1 sticky row: горизонтальный скролл категорий + [Навыки▾] [Сорт▾] справа |
| Навыки sheet | Full-sheet 95vh: табы категорий → чипы → sticky [Применить →] 52px |
| Сортировка sheet | Half-sheet 40vh: 2 варианта |
| TWO-SPEEDS strip | 1 строка под filter bar, не sticky: «⏱ Обновляется раз в 15 мин · Подробнее →» |
| Карточки | 1 col, padding 16px, touch target ≥ 44px |

### /cabinet/ mobile

| Элемент | Решение |
|---------|---------|
| Навыки | Collapsed 1 строка чипов, tap → sheet |
| Stack | навыки → подписка → inbox |
| TG Login | Кастомная кнопка full-width indigo pill 52px; deep link в TG |

### Лендинг + how/pricing/faq mobile

| Элемент | Решение |
|---------|---------|
| Hero H1 | 32px/800, padding-top 24px |
| Hero gap | 32px между sub и CTA |
| CTA primary | full-width pill 52px |
| CTA secondary | border pill 48px, full-width, стек под primary |
| Live preview | 2 карточки (не 3–4) |
| Горизонтальный скролл | убрать везде — 1 колонка |

**Handoff Coder:** TG Login deep link + sheet JS → Lead Architect после CSS.

---

## § TWO-SPEEDS-UI — две скорости (**O11+O23**)


**Не в CSS-спринте NEO сейчас** — заложить в макет/REFERENCE; Coder подключит после фазы **3r**.

| Поверхность | UI-элемент | Спека |
|-------------|------------|--------|
| **`/lenta/`** | Info-strip `.rl-feed-delay-notice` | Под `rl-feed-head__count`, muted 13–14px, ссылка на `/pricing/` |
| **`/lenta/`** | (опц.) иконка часов на карточке | Только если O11 в коде и лид «задержанный» — не обязательно в MVP copy |
| **`/pricing/`** | Таблица сравнения | 2 колонки: «Бесплатно» / «ИИ-агент» — строка **Скорость** |
| **`/how/`**, **`/faq/`** | Текстовый блок / accordion | см. TWO-SPEEDS-COPY |
| **`/cabinet/`** | В блоке подписки | Upsell: «Без задержки» рядом со Stars |

**Mobile:** strip не sticky — одна строка + «Подробнее → pricing».

---

#### 2. Лента `/lenta/` — mobile-first

```
Header (sticky, тонкий)
  RawLead | [Войти в кабинет]

Filter Bar (горизонтальная, sticky под header)
  [Все] [Разработка] [Дизайн] [Маркетинг] [Тексты]  ← горизонтальный скролл на mobile
  [Навыки ▾]  ← dropdown/sheet с чипами из каталога
  [Сортировка ▾]  ← Новые / По совместимости

Feed (карточки)
  — новый стиль: тень, radius 20px, без жёсткой рамки
  — mobile: 1 колонка, full width с padding
  — desktop: 2 колонки max-width 900px по центру
  — infinite scroll

Report bug (FAB внизу справа или footer-ссылка)
```

#### 3. Кабинет `/cabinet/` — тот же стиль, + match

```
Header (sticky)
  RawLead | [Профиль / теги]

Мои навыки (chips, редактируемые, sticky под header)
  [python] [figma] [seo] [+Добавить] ← из каталога

Filter Bar (та же что на /lenta/)

Feed (с match %)
  — карточки идентичны /lenta/ + match-bar indigo
```

#### 4. /how и /faq — оставить отдельными, пересобрать стиль

```
/how — 4 шага (не 5), без timeline-вертикали:
  Карточки 2×2 desktop, 1 col mobile
  Каждая: иконка + заголовок + 2 строки

/faq — аккордеон, тот же тёплый фон
  Убрать «закрытое тестирование», «ранний доступ»
```

### Компоненты — новые

| Компонент | Описание |
|-----------|----------|
| **Кнопка primary** | `#4F46E5` fill, белый текст, radius 999px, hover `#4338CA` |
| **Кнопка secondary** | border `#4F46E5`, текст `#4F46E5`, прозрачный фон |
| **Кнопка ghost** | только текст + → , без рамки |
| **Карточка лида** | shadow `0 2px 12px rgba(0,0,0,0.07)`, radius 20px, hover shadow ↑ + translateY(-2px) |
| **Чип категории** | active: `#4F46E5` fill, inactive: `#F3F3EF` + border `#E4E4E7` |
| **Чип навыка** | active: indigo-100 `#EEF2FF` + indigo text, inactive: серый |
| **Match-bar** | `#4F46E5`, height 4px, radius 2px |
| **Иконки категорий** | line-иконки 20px: `</>` dev · `✦` design · `◎` marketing · `Aa` text |
| **Source badge** | FL зелёный · Kwork оранжевый · TG синий — без изменений |
| **Report bug FAB** | `?` круглая кнопка, bottom-right, `#4F46E5` ghost |

### Голос (из Product-канона)

- Активный залог: «ИИ убрал мусор», не «заказы были отфильтрованы»
- Без восклицательных знаков
- Кнопки = конкретное действие: «Смотреть ленту», «Войти в кабинет»
- Mobile: короткие метки — «Дизайн» не «Дизайн & Видео»
- Пустые состояния: человечные — «Пока нет заказов по этим навыкам — попробуй шире»

### Что сдать Lead Designer

| # | Артефакт | Куда |
|---|----------|------|
| 1 | Обновлённый `DESIGN_SYSTEM.md` — новые токены | `docs/team/design/DESIGN_SYSTEM.md` |
| 2 | Новый `REFERENCE.md` — страницы, компоненты, голос | `docs/design/wp/REFERENCE.md` |
| 3 | Обновлённый `feed-cabinet-mvp.md` — новая структура + компоненты | `docs/design/wp/feed-cabinet-mvp.md` |
| 4 | Handoff → `@designer` (DESIGNER_PROMPT) — CSS-задачи | `docs/team/design/DESIGNER_PROMPT.md` |

**Согласовать с владельцем перед передачей @designer:** финальный вид карточки лида (mockup или описание достаточно), навигация header (список пунктов).

---

---

## Что согласовано (2026-05-25)

Полный диалог: [Lead Designer UI/UX Vision Session](../../../.cursor/projects/c-Users-hramo-uisness)

| Решение | Зафиксировано |
|---------|--------------|
| Карточка лида: раскрывающаяся плашка (вариант C) | ✅ |
| Анимации: «Живой» стиль (stagger, lift, bar, press, cubes) | ✅ |
| Кубики источников: собираются из горизонтали в вертикаль при скролле | ✅ |
| FL.ru цвет: `#00A65A` зелёный | ✅ |
| TG цвет: `#0088CC` официальный | ✅ |
| Навигация: добавить «Лента» → `/feed` | ✅ |
| `/feed` фильтры: sticky sidebar desktop + bottom sheet mobile | ✅ |
| `/feed` scroll: infinite scroll | ✅ |
| `/cabinet` теги: редактируемые чипы прямо на странице | ✅ |
| `/cabinet` ощущение: отдельная «продуктовая» страница (не копия feed) | ✅ |
| Лендинг тарифы: 1 карточка ИИ-агент 300–990 ₽/мес | ✅ |
| Пульт: пульсация лампы ok в running-режиме | ✅ |
| Пульт: структурированный статус в вкладке «Статус» (задача Coder) | ✅ |

---

## § D1 — Чипы категорий в `/lenta/` (**→ перед продом**)

**Триггер:** владелец 2026-05-26 — прод только с рабочим продуктом. API `?category=` есть, UI нет.

**Исполнитель:** **`@designer`** — ✅ **сдано 2026-05-26** ([`feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) §2.2–2.3).

| # | Задача | Статус |
|---|--------|--------|
| 1 | §2.2 блок **«Категория»** — 4 ниши §0i + «Все» | ✅ |
| 2 | Active chip `#0A0A0A` | ✅ |
| 3 | Mobile bottom sheet | ✅ |
| 4 | Handoff → `@coder` § D1 | ✅ |

Канон названий: [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) §0i.

---

## Документы (все готовы)

| Файл | Что |
|------|-----|
| [`docs/design/wp/REFERENCE.md`](../../design/wp/REFERENCE.md) v2 | Лендинг + анимации (§6) + обновлённые токены |
| [`docs/design/wp/feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) | **Полная спека** `/feed` + `/cabinet` + пульт |
| [`DESIGN_SYSTEM.md`](DESIGN_SYSTEM.md) | Токены v2 (источники + motion-токены) |
| [`DESIGNER_PROMPT.md`](DESIGNER_PROMPT.md) | Задача для Designer (CSS + pricing + nav + лампа) |

---

## Волна 2 — ✅ согласовано владельцем 2026-05-25

| # | Решение | Зафиксировано |
|---|---------|--------------|
| W2.1 | «Смотреть тарифы» → якорь `#pricing-preview`, не `/pricing` | ✅ `REFERENCE` §3.2, §3.7 |
| W2.2 | «Главная» убрана из nav; логотип RawLead → `/` | ✅ `REFERENCE` §3.1 |
| W2.3 | Hero primary: «Смотреть ленту» → `/lenta/`; secondary: «Смотреть тарифы ↓» → `#pricing-preview` | ✅ `REFERENCE` §3.2 |
| W2.4 | § 3h карточки ленты — после волны 2 | ⏸ |

→ UX волны 2 **закрыт** (достаточно `REFERENCE` §3). **@designer** для волны 2 **не нужен** — волна 1 сдана. Дальше: **@lead-product** (тексты) → **@coder** (nav/hero/якорь в PHP).

---

## Следующие шаги (волна 1 — закрыта)

| Кто | Что | Когда |
|-----|-----|-------|
| **@designer** | Handoff → `DESIGN_BRIEF` §195 | ✅ 2026-05-25 |
| **@coder** | § W · 3d · 3e · 3g | ✅ |

---

## § PRE-LAUNCH-UX v2 — финальный слой перед продом (**→ @lead-designer**, 2026-05-27)

**Когда:** после § PRE-LAUNCH A–D (@coder) и **после** deep research навыков/инструментов ([`LEAD_PRODUCT_PROMPT.md`](../product/LEAD_PRODUCT_PROMPT.md) § SKILLS-TOOLS-RESEARCH).  
**Порядок:** Design (спор с владельцем) → **@lead-product** (тексты) → **@coder** (вёрстка).

**Регламент владельца:** Lead Designer **может и должен спорить**, пока не найдём решение, которое владелец считает идеальным по UX — не «сдать быстрее».

### Бриф владельца (факты)

| # | Задача | Направление (не финал — обсудить) |
|---|--------|-----------------------------------|
| ux1 | **Контакты** | Убрать приглашение на «ранний доступ» |
| ux2 | **Фильтры `/lenta/`** | Сейчас неудобно: специализацию трудно найти; от неё зависят навыки; навыки не в «маленьком окошке» |
| ux3 | **Плашка фильтров** | Предложение владельца: **горизонтальная плашка сверху** (специализация → навыки), быстро и интуитивно |
| ux4 | **«Лента заказов»** | Заголовок и блоки **зажаты** верхней плашкой; дать **больше воздуха** (отступы, иерархия) |
| ux5 | **Сообщить об ошибке** | Пользователь может отправить репорт (что сломалось / скрин / URL) — UX + куда ведёт CTA |
| ux6 | **Мобилка** | Полноценная адаптация (не только bottom sheet «как есть») |

### Что сдать Design

| # | Артефакт |
|---|----------|
| 1 | Wireframe/desktop + mobile: **верхняя** filter-bar (category multi → skills), сравнение с текущим sidebar |
| 2 | Типографика/отступы: hero «Лента заказов» + подзаголовки — «воздух» |
| 3 | Паттерн **Report bug** (footer? FAB? modal?) + поля формы |
| 4 | Контакты **без** closed beta / «заявка» / «ранний доступ» (решение владельца 2026-05-27) — CTA: лента, кабинет, связь |
| 5 | Handoff в `feed-cabinet-mvp.md` или addendum + список для @lead-product (подписи, empty states, ошибки)

**Не в scope Design:** реализация API feedback (Coder после макета); биллинг.

→ Coder: [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md) § PRE-LAUNCH-UX · Product: [`LEAD_PRODUCT_PROMPT.md`](../product/LEAD_PRODUCT_PROMPT.md) § PRE-LAUNCH-UX copy.

---

## Scope (итог)

| В scope ✅ | Вне scope ❌ |
|-----------|------------|
| WP лендинг: анимации, цвета, pricing 1-тариф, nav «Лента» | `/uslugi`, FL.ru тексты, Habr-статья |
| WP `/feed`: карточка, фильтры, sidebar, infinite scroll, состояния | Mobile app, отдельный сайт |
| WP `/cabinet`: теги-чипы, match, AI-агент кнопка (disabled до 3f) | Coder-часть PHP (это CODER_PROMPT) |
| Пульт: пульс лампы ok | Новый функционал пульта |

---

_Lead Designer · 2026-05-25 · после сдачи Designer — архив в `team/archive/TASKS_HISTORY.md`_
