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

## Токены (WordPress маркетинг v1 — 2026-05-23)

Утверждённый референс: [`../design/wp/REFERENCE.md`](../design/wp/REFERENCE.md) — **editorial light** (не пульт).

| Token | HEX | Использование |
|-------|-----|---------------|
| `color/bg/page` | `#FFFFFF` | фон сайта |
| `color/bg/inverse` | `#0A0A0A` | цитата, footer |
| `color/text/primary` | `#0A0A0A` | заголовки |
| `color/cta/primary` | `#0A0A0A` | pill-кнопки |
| `color/border` | `#E8E8EC` | карточки |
| `color/accent/match` | `#2563EB` | полоса совпадения |
| `font/family` | **Manrope** body · **Unbounded** display | child theme (bold editorial) |

Пульт (тёмный `#0c0e13`) и сайт — **разные поверхности**; не смешивать без запроса Lead.

---

## История изменений

| Дата | Проект | Что |
|------|--------|-----|
| 2026-05-20 | RawLead пульт v1 | Токены ops-dashboard, green/red lamps |
| 2026-05-23 | RawLead пульт v2 | ЮБуст-референс, play/stop, glow, логи вниз, палитра v2 |
| 2026-05-23 | WordPress сайт v1 | Editorial light; REFERENCE + Unbounded/Manrope в child theme |
