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

## Токены (WordPress v2 — 2026-05-25)

Утверждённый референс: [`../design/wp/REFERENCE.md`](../../design/wp/REFERENCE.md) — **editorial light** (не пульт).  
Спека страниц `/feed` и `/cabinet`: [`../design/wp/feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md)

### Цвет

| Token | HEX | Использование |
|-------|-----|---------------|
| `color/bg/page` | `#FFFFFF` | фон сайта |
| `color/bg/section` | `#F5F5F7` | чередующие секции |
| `color/bg/inverse` | `#0A0A0A` | манифест-полоса, footer |
| `color/text/primary` | `#0A0A0A` | заголовки |
| `color/text/body` | `#3D3D3D` | body |
| `color/text/muted` | `#6B6B6B` | подписи, вторичный |
| `color/text/inverse` | `#FFFFFF` | на тёмном фоне |
| `color/border` | `#E8E8EC` | карточки |
| `color/cta/primary` | `#0A0A0A` | pill-кнопки |
| `color/cta/primary-text` | `#FFFFFF` | текст primary CTA |
| `color/accent/match` | `#2563EB` | полоса совпадения % |
| `color/source/fl` | `#00A65A` | рамка/акцент FL.ru (бренд-зелёный) |
| `color/source/kwork` | `#EA580C` | рамка/акцент Kwork |
| `color/source/tg` | `#0088CC` | рамка/акцент Telegram |
| `color/chip/take` | `#16A34A` | чип «Брать» |
| `color/chip/maybe` | `#6B7280` | чип «Сомнительно» |

### Шрифты

| Token | Значение | Применение |
|-------|----------|------------|
| `font/display` | **Unbounded** 700–900 | H1, H2, логотип |
| `font/body` | **Manrope** 400–700 | body, UI, подписи |
| `font/hero` | 56–72px / 900 / −0.02em | H1 «Лиды без шума» |
| `font/h2` | 32–40px / 700 | секции |
| `font/body-size` | 16–18px / 400 / 1.5 | абзацы |
| `font/label` | 12px / 600 | чипы, badge, время |

### Анимации (motion tokens)

| Token | Значение | Применение |
|-------|----------|------------|
| `motion/duration/appear` | `240ms` | fade+translate при скролле |
| `motion/duration/expand` | `300ms` | раскрытие карточки лида |
| `motion/duration/bar` | `600ms` | fill match-bar |
| `motion/duration/cube` | `400ms` | сборка кубиков источников |
| `motion/duration/press` | `80ms` | micro-press кнопок |
| `motion/duration/hover` | `150ms` | hover карточки |
| `motion/easing/default` | `ease-out` | всё движение |
| `motion/stagger/card` | `40ms` | задержка между карточками в ленте |
| `motion/scale/press` | `0.97` | scale при клике на кнопку |
| `motion/lift/hover` | `translateY(-2px)` | подъём карточки при hover |

Пульт (тёмный `#0c0e13`) и сайт — **разные поверхности**; не смешивать без запроса Lead.

---

## История изменений

| Дата | Проект | Что |
|------|--------|-----|
| 2026-05-20 | RawLead пульт v1 | Токены ops-dashboard, green/red lamps |
| 2026-05-23 | RawLead пульт v2 | ЮБуст-референс, play/stop, glow, логи вниз, палитра v2 |
| 2026-05-23 | WordPress сайт v1 | Editorial light; REFERENCE + Unbounded/Manrope в child theme |
| 2026-05-25 | WordPress сайт v2 | Исправлен цвет FL.ru (#00A65A), TG (#0088CC); добавлены motion-токены; /feed + /cabinet токены; шрифтовые токены |
