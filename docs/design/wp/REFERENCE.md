# RawLead — WordPress сайт · утверждённый референс

**Статус:** v2 · согласовано Lead Designer + владелец · 2026-05-25  
**Направление:** E — editorial / Pitch / Framer (светлый, типографика, сетка)  
**Поверхности:** лендинг (главная) · `/feed` (открытая лента) · `/cabinet` (кабинет)  
**Не использовать:** тёмный вариант A (Linear-dark), пульт Tauri, play/stop, терминал логов

Файл-референс: [`bold-editorial-saas-full-page-landing-page-ui-mock.png`](bold-editorial-saas-full-page-landing-page-ui-mock.png) · приёмка владельца 2026-05-23.

Спека `/feed` и `/cabinet`: [`feed-cabinet-mvp.md`](feed-cabinet-mvp.md)

Скелет контента: [`../../archive/wp-skeleton/`](../../archive/wp-skeleton/) · установка: [`../../ops/WP_LOCAL_SKELETON.md`](../../ops/WP_LOCAL_SKELETON.md)

---

## 1. Суть стиля

| Принцип | Решение |
|---------|---------|
| Первое впечатление | Крупная типографика, много воздуха, **чёрно-белая** база |
| Акцент | Только функционально: полоса match %, тонкие рамки источников (синий / оранж / голубой) |
| Тон | Уверенный B2B, без неона и «киберпанка» |
| Отличие от конкурентов | Блок **источники → стрелка → карточка лида** (биржи + TG в одном потоке) |
| Реализация WP | Kadence или Astra + блоки Cover / Columns / Group — макет **собирается вручную по сетке**, не вставлять PNG как сайт |

---

## 2. Токены (v1 — под референс)

| Token | Значение | Использование |
|-------|----------|---------------|
| `color/bg/page` | `#FFFFFF` | фон страницы |
| `color/bg/section` | `#F5F5F7` | чередующие секции (опционально) |
| `color/bg/inverse` | `#0A0A0A` | полоса-цитата, footer |
| `color/text/primary` | `#0A0A0A` | заголовки, лого |
| `color/text/body` | `#3D3D3D` | подзаголовки, body |
| `color/text/muted` | `#6B6B6B` | подписи, вторичный текст |
| `color/text/inverse` | `#FFFFFF` | текст на тёмной полосе |
| `color/border` | `#E8E8EC` | карточки, тарифы |
| `color/cta/primary` | `#0A0A0A` | кнопки «Смотреть тарифы», «Начать» |
| `color/cta/primary-text` | `#FFFFFF` | текст на primary |
| `color/cta/secondary` | transparent | «Как это работает» — текст + стрелка |
| `color/source/fl` | `#00A65A` | рамка/акцент FL.ru (бренд-зелёный) |
| `color/source/kwork` | `#EA580C` | рамка/акцент Kwork |
| `color/source/tg` | `#0088CC` | рамка/акцент Telegram (официальный) |
| `color/match/bar` | `#2563EB` | прогресс «совпадение %» |
| `color/status/success` | `#16A34A` | только чипы «Брать» (не вся палитра) |
| `radius/card` | `16px` | карточки источников, лид, тарифы |
| `radius/button` | `999px` | pill-кнопки |
| `space/unit` | `8px` | baseline grid |
| `space/section-y` | `96px` desktop / `64px` mobile | между секциями |
| `font/display` | **Unbounded** 700–900 | заголовки H1–H3 |
| `font/body` | **Manrope** 400–700 | body, UI, подписи |
| `font/hero` | 56–72px / 700 / −0.02em | H1 «Лиды без шума» |
| `font/h2` | 32–40px / 700 | секции |
| `font/body` | 16–18px / 400 / 1.5 | абзацы |
| `font/ghost-num` | 120px / 200 / `#E8E8EC` | 01, 02, 03 в «Функции» |
| `container/max` | `1120px` | контент, центр |

Статусы радара (зелёный/красный) — **только** в будущем кабинете/админке, не на маркетинговой главной.

---

## 3. Структура главной (сверху вниз)

### 3.1 Header (sticky, светлый)

- Слева: **RawLead** (wordmark, без иконки на MVP)
- Справа: **Главная** · **Лента** · **Как работает** · **Тарифы** · **FAQ** · **Контакты**
- «Лента» → `/feed` (открытая лента заказов без регистрации)
- CTA в шапке: pill **«Попробовать»** → `/feed`

### 3.2 Hero

- **H1:** «Лиды без шума»
- **Подзаголовок** (из [`home.md`](../../archive/wp-skeleton/home.md)): FL.ru, Kwork, Telegram — фильтры, ИИ, без спама
- **Primary:** «Смотреть тарифы»
- **Secondary:** «Как это работает →» (ссылка, не кнопка-заливка)
- Справа/ниже на mobile — не обязательно в первом MVP; главный акцент — типографика

### 3.3 Блок «Поток» (ключевой визуал референса)

Слева направо (на mobile — колонка):

1. Три мини-карточки: **FL.ru** · **Kwork** · **Telegram** (тонкая цветная рамка)
2. Стрелка → (иконка или CSS)
3. Карточка **отфильтрованного лида:**
   - заголовок заказа (пример)
   - строка бюджета
   - полоса **«Совпадение 88%»** (синяя)
   - чип ИИ: «Брать» / «Сомнительно»
   - кнопка-ghost «Откликнуться» (на сайте = «вы сами в TG», не автоклик)

Текст под блоком (мелко): «Биржи и чаты в одном потоке».

### 3.4 Полоса-манифест (тёмная)

Полная ширина, фон `#0A0A0A`, белый текст, крупная кавычка:

> **«Не сидите на бирже. Решайте по карточке в телефоне.»**

Альтернатива из продукта: «Мы не пишем заказчикам за вас.»

### 3.5 Функции (01 · 02 · 03)

| № | Заголовок | Смысл |
|---|-----------|--------|
| 01 | Один поток | FL + Kwork + TG без переключения вкладок |
| 02 | ИИ-разбор | брать / сомнительно / пропустить |
| 03 | Вы решаете | пуш в Telegram, отклик вручную |

Большие серые цифры на фоне, как на референсе.

### 3.6 Для кого

Три карточки (из скелета): разработчик · WordPress · устал мониторить чаты.

### 3.7 Тарифы (превью на главной или только `/pricing`)

**Одна карточка** — ИИ-агент (Product Vision v0.9, один тариф):

| Поле | Значение |
|------|----------|
| Название | **ИИ-агент** |
| Цена | **от 300 ₽/мес** (точная — после MVP) |
| Что включено | Match по тегам · рыночная цена · черновик отклика · push в TG при новом матче |
| CTA | pill «Ранний доступ» → `/contact` |
| Badge | «Скоро» (серый, правый верхний угол карточки) |

Под карточкой: ссылка «Узнать первым →` → `/contact` или форма email-листа.

**Не делать:** 3 колонки Старт/Про/Команда — устарело (v0.8), отменено.

### 3.8 Footer

Тёмный `#0A0A0A`, лого, ссылки, **Telegram**, © RawLead.

---

## 4. Остальные страницы (тот же язык)

| Страница | Особенности |
|----------|-------------|
| **Как работает** | 5 шагов из [`how.md`](../../archive/wp-skeleton/how.md); timeline вертикальный, те же pill-кнопки |
| **Тарифы** | полная сетка 3 колонок + FAQ-якорь |
| **FAQ** | аккордеон, светлый фон, без тёмной «админки» |
| **Контакты** | форма CF7 + кнопка Telegram; одна primary CTA |

---

## 5. Компоненты (handoff Coder / владелец WP)

| Компонент | default | hover | disabled |
|-----------|---------|-------|----------|
| Button primary | bg `#0A0A0A`, text white | opacity 0.9 | opacity 0.4 |
| Button secondary | border 1px, bg white | border dark | — |
| Link arrow | text + → | underline | — |
| Card | border `#E8E8EC`, radius 16px | border чуть темнее | — |
| Pricing featured | ribbon «Популярный», primary CTA | — | «Скоро» серый |

**a11y:** контраст текста на белом ≥ 4.5:1; match % дублировать числом, не только полосой.

---

## 6. Анимации (согласовано 2026-05-25)

**Принцип:** «Живой» стиль (Framer/Raycast). Только CSS transform + opacity — нулевая нагрузка на GPU, без layout reflow. IntersectionObserver для scroll-триггеров.

### 6.1 Появление элементов при скролле

```css
/* Базовое состояние — невидим, смещён вниз */
.rl-reveal { opacity: 0; transform: translateY(20px); }
/* После входа в viewport */
.rl-reveal.is-visible { opacity: 1; transform: none; transition: opacity 240ms ease-out, transform 240ms ease-out; }
```

### 6.2 Stagger карточек (feed / features / audience)

Карточки появляются по очереди: задержка `40ms` между каждой через `transition-delay`.

```css
.rl-card:nth-child(1) { transition-delay: 0ms; }
.rl-card:nth-child(2) { transition-delay: 40ms; }
.rl-card:nth-child(3) { transition-delay: 80ms; }
/* и т.д. */
```

### 6.3 Hover карточки

```css
.rl-lead-card, .rl-price-card {
  transition: transform 150ms ease-out, box-shadow 150ms ease-out, border-color 150ms ease-out;
}
.rl-lead-card:hover, .rl-price-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.10);
  border-color: #C8C8D0;
}
```

### 6.4 Match-bar (fill on viewport entry)

Полоса совпадения начинает анимироваться от 0% до реального значения при первом появлении в viewport:

```css
.rl-match__fill { width: 0; transition: width 600ms ease-out; }
.is-visible .rl-match__fill { width: var(--match-value); /* задаётся inline */ }
```

### 6.5 Micro-press на кнопках

```css
.rl-btn:active { transform: scale(0.97); transition: transform 80ms ease-out; }
```

### 6.6 Кубики источников — сборка при скролле

На главной: кубики FL.ru / Kwork / Telegram при входе в viewport анимируются из горизонтального ряда в вертикальную стопку.

**Начальное состояние (inline style на каждом кубике):**
```css
/* Все три — в строку (translateX разные) */
.rl-source-cube:nth-child(1) { transform: translateX(-80px) translateY(40px) rotate(-8deg); opacity: 0; }
.rl-source-cube:nth-child(2) { transform: translateX(0px)   translateY(60px) rotate(4deg);  opacity: 0; }
.rl-source-cube:nth-child(3) { transform: translateX(80px)  translateY(40px) rotate(-6deg); opacity: 0; }
```

**Финальное состояние (is-visible на родителе):**
```css
.rl-flow__sources.is-visible .rl-source-cube:nth-child(1) { transform: none; opacity: 1; transition: all 400ms ease-out 0ms; }
.rl-flow__sources.is-visible .rl-source-cube:nth-child(2) { transform: none; opacity: 1; transition: all 400ms ease-out 80ms; }
.rl-flow__sources.is-visible .rl-source-cube:nth-child(3) { transform: none; opacity: 1; transition: all 400ms ease-out 160ms; }
```

### 6.7 IntersectionObserver — один скрипт

```js
const io = new IntersectionObserver(entries => {
  entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('is-visible'); io.unobserve(e.target); } });
}, { threshold: 0.15 });
document.querySelectorAll('.rl-reveal, .rl-flow__sources').forEach(el => io.observe(el));
```

**Производительность:** только transform + opacity (GPU), unobserve после первого срабатывания. Не влияет на FCP/LCP.

---

## 7. Что не переносить с референса буквально

- Искажённый/английский мелкий текст с картинки — брать тексты из **wp-skeleton**
- Кнопка «Apply» → **«Откликнуться сами»** или убрать (мы не биржа)
- Логотипы FL/Kwork/TG — **текстовые плашки** или generic icons (без нарушения TM)
- PNG Recraft — только **картинка в hero** опционально; вёрстка — блоки темы

---

## 8. Статус

| Кто | Действие |
|-----|----------|
| **Designer** | ✅ REFERENCE E + bold type (Unbounded/Manrope) |
| **Coder** | ✅ `wordpress/rawlead-kadence-child/` · [`WP_KADENCE_INSTALL.md`](../../ops/WP_KADENCE_INSTALL.md) |
| **Владелец** | Local `radarzakaz.local` · Primary menu RawLead |

Следующий продуктовый шаг: **match %** в боте — [`PRODUCT_VISION.md`](../../team/product/PRODUCT_VISION.md) §0.

---

_Утверждённый референс: editorial light, Recraft 2026-05-23._
