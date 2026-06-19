# Designer — активная задача

**Обновлено:** 2026-06-19 · **Prod verify:** Playwright + `wordpress/` · theme **1.19.20**  
**Регламент:** [`DESIGNER.md`](DESIGNER.md) · план Lead: [`LEAD_DESIGN_PROMPT.md`](LEAD_DESIGN_PROMPT.md)

| | |
|--|--|
| **→ Сейчас** | **O280-RAWLEAD-NEXT** — copy/UX advisor **по вызову** Lead/владельца |
| **WP prod** | theme **1.19.20** · канон строк — [`PAGES_INVENTORY.md`](../../migration/PAGES_INVENTORY.md) § Prod snapshot |
| **Закрыто** | O209 match UX shipped · O215 polish · O272 quiz→feed |
| **⛔ Не проектировать** | Skill Tree как primary · ручной picker для auth |

**Архив:** [`../archive/DESIGNER_PROMPT_ARCHIVE.md`](../archive/DESIGNER_PROMPT_ARCHIVE.md) — Skill Tree O92–O98 **не читать**.

---

## Prod snapshot (как на rawlead.ru сейчас)

Сверено Playwright **2026-06-19** · не выдумывать из старых brief.

| Экран | Факт на prod |
|-------|----------------|
| `/` hero | H1 **«Заказы под твой стек. Без мусора.»** · CTA лента + **«Настроить ленту →»** |
| `/lenta/` | H1 **«Лента заказов»** · **«Показать ещё»** · anon strip **30 мин** + TG trial |
| Filter | Категории Все/Разработка/… · **«Навыки» скрыт для залогиненных** (O199 CSS) |
| `/quiz/` | Intro **«Ответь на карточки…»** · кнопки **«Мимо»** / **«Берем»** |
| `/pricing/` | **790 ₽/мес** · **3 дня** trial auto |
| `/cabinet/` gate | **«Войти через Telegram»** |

**Drift:** `wave-o209-match-brief.md` § lexicon («Да, близко») **≠ prod** — ориентир **PAGES_INVENTORY** и `quiz.php`.

---

## § O280-RAWLEAD-NEXT — Design advisor (по вызову)

**Функционал Next:** [`PAGES_INVENTORY.md`](../../migration/PAGES_INVENTORY.md) · [`API_CONTRACTS.md`](../../migration/API_CONTRACTS.md).  
**Поведение:** `feed-cabinet-mvp.md` §0.1 (quiz-first, inbox ≠ lenta).  
**Визуал Next:** владелец + Claude — **не** в migration-пакете.

**Не путать:** `rawlead.ru/portfolio/` — Rode51, вне product UI.

### Read (первый ход)

| # | Файл |
|---|------|
| 1 | `PAGES_INVENTORY.md` § Prod snapshot |
| 2 | `feed-cabinet-mvp.md` §0 + §0.1 |
| 3 | `wave-o209-match-brief.md` — tiers + match **только где не противоречит prod** |
| 4 | `REFERENCE.md` v5 — если нужен WP layout reference |

### Tier facts (prod)

| Tier | Задержка | Черновики | Trial / цена |
|------|----------|-----------|--------------|
| Anon / expired | **30 мин** | ❌ | — |
| Trial / Premium | instant | **5/ч** | **3 дня** auto · **790 ₽/мес** |

### Advisor format (RU)

1. Контекст (экран/блок) · 2. Copy (≤3, ⭐) · 3. Layout · 4. Guard · 5. Handoff → `@lead-architect` / `@coder`  
**No code** в advisor-чате.

---

## § O215-COPY-UX-ADVISOR — reuse

Тот же advisor format · строки сверять с **PAGES_INVENTORY prod snapshot**.

---

_Probe: `scripts/_probe_prod_playwright.py` (local) · WP theme `RAWLEAD_CHILD_VERSION` = 1.19.20_
