# Design System — воркспейс (общий)

**Владелец:** Designer · обновляет при каждом утверждённом проекте.

Цель: один язык UI для **RawLead**, **WordPress-пульт**, будущих SaaS — без пересборки палитры с нуля.

---

## Принципы

- 8px baseline grid
- Dark-first (операторские панели)
- Primary action — один на viewport
- Status: цвет + текст + форма (a11y)
- Motion: 150–250 ms, ease-out; без отвлекающих анимаций
- Семантика **зелёный/красный/серый** — только индикаторы процессов, не вся палитра

---

## Токены (RawLead пульт v2 — 2026-05-23)

| Token | HEX | Использование |
||-------|-----|---------------|
|| `color/bg/app` | `#0c0e13` | фон окна |
|| `color/bg/surface` | `#141820` | панель логов |
|| `color/bg/log` | `#090b10` | терминал |
|| `color/border` | `#2a3140` | границы |
|| `color/text/primary` | `#eceef4` | основной текст |
|| `color/text/muted` | `#8b93a7` | подсказки |
|| `color/text/log` | `#9bc18a` | mono лог |
|| `color/accent/primary` | `#5b8def` | play (idle) + glow |
|| `color/hero/running` | `#3dd68c` | stop (running) + glow |
|| `color/status/success` | `#3dd68c` | лампа **работает** |
|| `color/status/danger` | `#ef6b6b` | лампа **нет** |
|| `color/status/neutral` | `#5c6370` | idle |
|| `font/title` | Bahnschrift SemiBold | RAWLEAD |
|| `font/ui` | Segoe UI Variable Text | UI |
|| `font/signature` | Segoe Script | by Rode51 |
|| `hero/size` | 220px | круг play/stop |

Полная спека: [`DESIGN_BRIEF.md`](DESIGN_BRIEF.md) (v2)

---

## Компоненты (каталог)

| Компонент | Статусы | Проекты |
||-----------|---------|---------|
|| Hero play/stop | idle (синий+glow), running (зелёный+glow), pressed | RawLead пульт v2 |
|| Status lamp | idle, ok, error | RawLead пульт |
|| Secondary button | default, hover | RawLead |
|| Log tabs | default, selected | RawLead |

---

## Токены (WordPress NEO-BRUTALIST — 2026-05-28)

Направление: **«Neo-Brutalist Color Blocks»** — белая база, жирная типографика, плоские тени, цветные блоки-секции.
Предыдущее (REVOLUTION тёплый Indigo) — **отменено**.
Референс: [`../../design/wp/REFERENCE.md`](../../design/wp/REFERENCE.md) v4 · Спека: [`../../design/wp/feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md)

### Цвет

| Token | HEX | Использование |
|-------|-----|---------------|
| `color/bg/page` | `#FFFFFF` | чистый белый — база всех страниц |
| `color/bg/section` | `#F5F5F0` | off-white — нейтральные чередующие секции |
| `color/bg/hero` | `#FACC15` | **фирменный жёлтый** — hero, акцентные секции |
| `color/bg/alt` | `#F3E8FF` | светло-фиолетовый — блок «Как работает» |
| `color/bg/inverse` | `#0A0A0A` | чёрный footer |
| `color/text/primary` | `#0A0A0A` | заголовки, основной текст |
| `color/text/body` | `#1A1A1A` | body, описания |
| `color/text/muted` | `#525252` | подписи, вторичный, placeholder |
| `color/text/inverse` | `#FFFFFF` | текст на чёрном/тёмном фоне |
| `color/text/on-hero` | `#0A0A0A` | текст на жёлтом фоне |
| `color/border` | `#0A0A0A` | **основная рамка: чёрная 2px** |
| `color/border/light` | `#D4D4D4` | вторичный разделитель |
| `color/cta/primary` | `#0A0A0A` | кнопка default: чёрная |
| `color/cta/primary-text` | `#FFFFFF` | текст на чёрной кнопке |
| `color/cta/hover-bg` | `#FACC15` | кнопка hover: жёлтая |
| `color/cta/hover-text` | `#0A0A0A` | текст на жёлтой кнопке |
| `color/match/bar` | `#0A0A0A` | полоса совпадения % |
| `color/source/fl` | `#00A65A` | FL.ru (без изменений) |
| `color/source/kwork` | `#EA580C` | Kwork (без изменений) |
| `color/source/tg` | `#0088CC` | Telegram (без изменений) |
| `color/chip/take` | `#16A34A` | чип «Брать» |
| `color/chip/maybe` | `#6B7280` | чип «Сомнительно» |
| `color/chip/active` | `#0A0A0A` | активный chip: чёрная заливка |
| `color/chip/active-text` | `#FFFFFF` | текст активного chip |
| `color/chip/skill/active-bg` | `#FACC15` | активный skill chip: жёлтый |
| `color/chip/skill/active-text` | `#0A0A0A` | текст активного skill chip |

### Шрифты

| Token | Значение | Применение |
|-------|----------|------------|
| `font/display` | **Manrope** 900 | H1 hero — максимальный вес |
| `font/heading` | **Manrope** 800 | H2, H3 |
| `font/body` | **Manrope** 400–600 | body, UI, подписи, кнопки |
| `font/hero` | `clamp(56px, 10vw, 96px)` / 900 / `−0.03em` | H1 «Лиды без шума» |
| `font/h2` | `32–44px` / 800 | заголовки секций |
| `font/body-size` | `16–18px` / 400 / 1.55 | абзацы |
| `font/label` | `12–13px` / 700 | чипы, badge, метки |

### Форма и тень

| Token | Значение | Применение |
|-------|----------|------------|
| `radius/card` | `4px` | карточки — почти квадрат |
| `radius/button` | `0px` | кнопки — прямые углы |
| `radius/chip` | `2px` | chips — минимальный скос |
| `radius/section` | `0px` | секции без скруглений |
| `shadow/card` | `4px 4px 0px #0A0A0A` | **плоская смещённая тень** (без blur) |
| `shadow/card-hover` | `6px 6px 0px #0A0A0A` | hover: тень сильнее + сдвиг карточки |
| `space/unit` | `8px` | baseline grid |
| `space/section-y` | `80px` desktop / `48px` mobile | между секциями |
| `container/max` | `900px` | лента (2 col); `1120px` лендинг |

### Анимации (motion tokens)

| Token | Значение | Применение |
|-------|----------|------------|
| `motion/duration/appear` | `320ms` | карточка ленты: fade+translateY(24px) |
| `motion/duration/section` | `400ms` | секция лендинга `.rl-reveal` |
| `motion/duration/expand` | `280ms` | раскрытие карточки лида |
| `motion/duration/bar` | `600ms` | fill match-bar (viewport trigger) |
| `motion/duration/perfect` | `700ms` | pulse ring 100% match |
| `motion/duration/press` | `60ms` | micro-press кнопок |
| `motion/duration/hover` | `120ms` | hover карточки |
| `motion/duration/sheet` | `280ms` | bottom sheet mobile |
| `motion/easing/default` | `ease-out` | всё движение |
| `motion/stagger/card` | `60ms` × n (max 4 шагов) | карточки 2–5 в ряду |
| `motion/scale/press` | `0.96` | scale при клике `.rl-btn` |
| `motion/lift/hover` | `translate(-2px, -2px)` | сдвиг карточки при hover (брутал-стиль) |

Спека Wave 2: [`../../design/wp/wave-2-css-brief.md`](../../design/wp/wave-2-css-brief.md)

Пульт (тёмный `#0c0e13`) и сайт — **разные поверхности**; не смешивать без запроса Lead.

---

## История изменений

| Дата | Проект | Что |
|------|--------|-----|
| 2026-05-20 | RawLead пульт v1 | Токены ops-dashboard, green/red lamps |
| 2026-05-23 | RawLead пульт v2 | Буст-референс, play/stop, glow, логи вниз, палитра v2 |
| 2026-05-23 | WordPress сайт v1 | Editorial light; REFERENCE + Unbounded/Manrope в child theme |
| 2026-05-25 | WordPress сайт v2 | Исправлен цвет FL.ru, TG; motion-токены; /feed + /cabinet |
| 2026-05-28 | WordPress REVOLUTION | Тёплый Indigo; Manrope; shadow-cards; mobile-first — **отменено** |
| 2026-05-28 | WordPress NEO-BRUTALIST | Белая база; жёлтый `#FACC15` hero; чёрные рамки; плоские тени; кнопка black→yellow |
| 2026-05-29 | WordPress Wave 2 motion | IO stagger, match-bar 600ms, perfect pulse, load-more; brief `wave-2-css-brief.md` |
