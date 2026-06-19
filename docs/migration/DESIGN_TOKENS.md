# RawLead — визуал: справочник WP (не ТЗ на дизайн)

**Статус:** владелец + Claude Code **сами решают**, как будет выглядеть Next UI.  
Этот файл — **опциональный reference** «что на prod сейчас», не обязательство копировать 1:1.

---

## Что зафиксировано (не дизайн)

| Тема | Где | Обязательно? |
|------|-----|--------------|
| Страницы и экраны | [`PAGES_INVENTORY.md`](PAGES_INVENTORY.md) | да — функционал |
| API | [`API_CONTRACTS.md`](API_CONTRACTS.md) | да |
| UX-логика (квиз-first, inbox ≠ лента) | `docs/design/wp/feed-cabinet-mvp.md` | да — поведение |
| Цвета / шрифты / «как красиво» | **этот файл** | **нет** — на усмотрение вас с Claude |

**Нет** отдельных design-промптов в стиле `portfolio/CLAUDE_CODE_HANDOFF.md` (design-system search, skills install). Визуал — ваша сессия с Claude.

---

## Если нужен reference: текущий WP (NEO-BRUTALIST)

Prod сейчас: светлая база, жёлтый hero `#FACC15`, чёрные рамки 2px, Manrope, offset-тени.  
Источник: `wordpress/.../assets/css/rawlead.css` `:root` (`--rl-*`) · [`DESIGN_SYSTEM.md`](../team/design/DESIGN_SYSTEM.md) § WP.

### Цвета (как на prod — для сравнения)

| Token CSS | HEX |
|-----------|-----|
| `--rl-bg-page` | `#FFFFFF` |
| `--rl-bg-hero` | `#FACC15` |
| `--rl-text-primary` | `#0A0A0A` |
| `--rl-border` | `#0A0A0A` |
| `--rl-cta` | `#0A0A0A` |
| `--rl-cta-hover-bg` | `#FACC15` |

Полный список — в `rawlead.css` строки 4–56.

### Типографика (prod)

Manrope 400–900 · hero H1 `clamp(56px, 10vw, 96px)` weight 900.

### Spacing (prod)

8px grid · header 56px · feed max-width 900px · landing container 1120px.

---

## Что не смешивать

| Пакет | Визуал | Отношение к RawLead product |
|-------|--------|----------------------------|
| `portfolio/` | тёмный + amber + Barlow | **другой сайт** (`rawlead.ru/portfolio/`) |
| `rawlead-next/` | **решите вы** | продукт rawlead.ru |

Копировать portfolio в product **не требуется** и **не запрещено** — решение за владельцем в чате с Claude.

---

## Практика для Claude Code

1. Сначала **PAGES + API + UX** (inventory, contracts, feed-cabinet-mvp).
2. Визуал — отдельный шаг: «owner + Claude выбирают направление» → зафиксировать в `rawlead-next/CLAUDE.md` § Visual direction (as-built).
3. При желании сверяться с WP — этот файл или `rawlead.css`, не обязательно.

_Lead Architect · 2026-06-19 · revised: дизайн не предписан_
