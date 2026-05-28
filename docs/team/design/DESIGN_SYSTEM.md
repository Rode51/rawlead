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
|-------|-----|---------------|
| `color/bg/app` | `#0c0e13` | фон окна |
| `color/bg/surface` | `#141820` | панель логов |
| `color/bg/log` | `#090b10` | терминал |
| `color/border` | `#2a3140` | границы |
| `color/text/primary` | `#eceef4` | основной текст |
| `color/text/muted` | `#8b93a7` | подсказки |
| `color/text/log` | `#9bc18a` | mono лог |
| `color/accent/primary` | `#5b8def` | play (idle) + glow |
| `color/hero/running` | `#3dd68c` | stop (running) + glow |
| `color/status/success` | `#3dd68c` | лампа **работает** |
| `color/status/danger` | `#ef6b6b` | лампа **нет** |
| `color/status/neutral` | `#5c6370` | idle |
| `font/title` | Bahnschrift SemiBold | RAWLEAD |
| `font/ui` | Segoe UI Variable Text | UI |
| `font/signature` | Segoe Script | by Rode51 |
| `hero/size` | 220px | круг play/stop |

Полная спека: [`DESIGN_BRIEF.md`](DESIGN_BRIEF.md) (v2)

---

## Компоненты (каталог)

| Компонент | Статусы | Проекты |
|-----------|---------|---------|
| Hero play/stop | idle (синий+glow), running (зелёный+glow), pressed | RawLead пульт v2 |
| Status lamp | idle, ok, error | RawLead пульт |
| Secondary button | default, hover | RawLead |
| Log tabs | default, selected | RawLead |

---

## Токены (WordPress REVOLUTION — 2026-05-28)

Направление: **«Рабочий инструмент»** — тёплый, прямой, для фрилансера (не cold editorial B2B).  
Референс: [`../design/wp/REFERENCE.md`](../../design/wp/REFERENCE.md) v3 · Спека: [`../design/wp/feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) v2

### Цвет

| Token | HEX | Использование |
|-------|-----|---------------|
| `color/bg/page` | `#FAFAF8` | тёплый белый — фон всех страниц |
| `color/bg/section` | `#F3F3EF` | чередующие секции, sidebar-блоки |
| `color/bg/inverse` | `#1A1A2E` | тёплый тёмный footer, hero-overlay |
| `color/text/primary` | `#18181B` | заголовки |
| `color/text/body` | `#3F3F46` | body, описания |
| `color/text/muted` | `#71717A` | подписи, вторичный, placeholder |
| `color/text/inverse` | `#FFFFFF` | текст на тёмном фоне |
| `color/border` | `#E4E4E7` | тонкие разделители |
| `color/cta/primary` | `#4F46E5` | Indigo — главный акцент |
| `color/cta/primary-text` | `#FFFFFF` | текст на primary CTA |
| `color/cta/primary-hover` | `#4338CA` | hover primary |
| `color/cta/secondary-border` | `#4F46E5` | outline-кнопка |
| `color/cta/secondary-text` | `#4F46E5` | текст outline-кнопки |
| `color/match/bar` | `#4F46E5` | полоса совпадения % (один акцент) |
| `color/source/fl` | `#00A65A` | FL.ru (бренд-зелёный) |
| `color/source/kwork` | `#EA580C` | Kwork |
| `color/source/tg` | `#0088CC` | Telegram (официальный) |
| `color/chip/take` | `#16A34A` | чип «Брать» |
| `color/chip/maybe` | `#6B7280` | чип «Сомнительно» |
| `color/chip/active` | `#4F46E5` | активный chip категории/навыка |
| `color/chip/active-text` | `#FFFFFF` | текст активного chip |
| `color/chip/skill/active-bg` | `#EEF2FF` | активный skill chip (indigo-100) |
| `color/chip/skill/active-text` | `#4F46E5` | текст активного skill chip |

### Шрифты

| Token | Значение | Применение |
|-------|----------|------------|
| `font/display` | **Manrope** 800 | H1, H2 — только Manrope (Unbounded удалён) |
| `font/body` | **Manrope** 400–600 | body, UI, подписи, кнопки |
| `font/hero` | 52–64px / 800 / −0.02em | H1 «Лиды без шума» |
| `font/h2` | 28–36px / 700 | заголовки секций |
| `font/body-size` | 16–18px / 400 / 1.55 | абзацы |
| `font/label` | 12–13px / 600 | чипы, badge, время, метки |

### Форма и тень

| Token | Значение | Применение |
|-------|----------|------------|
| `radius/card` | `20px` | карточки лидов — как мессенджер |
| `radius/button` | `999px` | pill-кнопки |
| `radius/chip` | `999px` | все chip-элементы |
| `radius/section` | `16px` | блоки на лендинге |
| `shadow/card` | `0 2px 12px rgba(0,0,0,0.07)` | дефолтная тень карточки |
| `shadow/card-hover` | `0 8px 28px rgba(0,0,0,0.12)` | тень при hover |
| `space/unit` | `8px` | baseline grid |
| `space/section-y` | `88px` desktop / `56px` mobile | между секциями |
| `container/max` | `900px` | лента (2 col); `1120px` лендинг |

### Анимации (motion tokens)

| Token | Значение | Применение |
|-------|----------|------------|
| `motion/duration/appear` | `240ms` | fade+translate при скролле |
| `motion/duration/expand` | `300ms` | раскрытие карточки лида |
| `motion/duration/bar` | `600ms` | fill match-bar |
| `motion/duration/cube` | `400ms` | сборка кубиков источников |
| `motion/duration/press` | `80ms` | micro-press кнопок |
| `motion/duration/hover` | `150ms` | hover карточки |
| `motion/duration/sheet` | `300ms` | bottom sheet mobile |
| `motion/easing/default` | `ease-out` | всё движение |
| `motion/stagger/card` | `40ms` | задержка между карточками |
| `motion/scale/press` | `0.97` | scale при клике |
| `motion/lift/hover` | `translateY(-2px)` | подъём карточки при hover |

Пульт (тёмный `#0c0e13`) и сайт — **разные поверхности**; не смешивать без запроса Lead.

---

## История изменений

| Дата | Проект | Что |
|------|--------|-----|
| 2026-05-20 | RawLead пульт v1 | Токены ops-dashboard, green/red lamps |
| 2026-05-23 | RawLead пульт v2 | Буст-референс, play/stop, glow, логи вниз, палитра v2 |
| 2026-05-23 | WordPress сайт v1 | Editorial light; REFERENCE + Unbounded/Manrope в child theme |
| 2026-05-25 | WordPress сайт v2 | Исправлен цвет FL.ru, TG; motion-токены; /feed + /cabinet; шрифтовые токены |
| 2026-05-28 | WordPress REVOLUTION | Смена направления: warm working tool; Indigo accent; только Manrope; shadow-cards; mobile-first |
