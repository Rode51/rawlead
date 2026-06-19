# Lead Designer — активный план

**Обновлено:** 2026-06-19 · **Регламент:** [`LEAD_DESIGN.md`](LEAD_DESIGN.md)

| | |
|--|--|
| **→ Сейчас** | **O280** — next UI (`rawlead-next/`): визуал **TBD owner + Claude**; Design — advisor по копирайту/tier UX **по вызову** |
| **WP prod** | theme **1.19.20** · строки/экраны — [`PAGES_INVENTORY.md`](../../migration/PAGES_INVENTORY.md) § Prod snapshot |
| **Shipped** | O209 match-first ✅ (1.18.84+) · O215 polish ✅ · O272 quiz→feed ✅ |
| **⛔ Снято** | Skill Tree · manual picker · «max 12 навыков» — owner **2026-06-15** → `feed-cabinet-mvp` §0.1 |
| **Вне scope** | `rawlead.ru/portfolio/` — Rode51, отдельный продукт |
| **Vision** | [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.12** |

**Архив волн O81–O209 (детали):** git history до 2026-06-19 · краткий индекс — [`../archive/DESIGNER_PROMPT_ARCHIVE.md`](../archive/DESIGNER_PROMPT_ARCHIVE.md). **Не читать** без задачи.

---

## § O280-RAWLEAD-NEXT — Design strategy

**Цель:** UI продукта на Next до рекламы (STATUS § O280). **Не диктуем** NEO-clone — owner выбирает визуал с Claude; WP + [`DESIGN_TOKENS.md`](../../migration/DESIGN_TOKENS.md) = optional reference.

### Канон UX (не пересматривать без владельца)

| Тема | Источник |
|------|----------|
| Quiz-first profile | `feed-cabinet-mvp` §0.1 |
| Match-first copy + tiers | `wave-o209-match-brief.md` — **сверять с prod** (`quiz.php`: Мимо/Берем) |
| Экраны и гости/auth | `PAGES_INVENTORY.md` |
| Продуктовые факты | `PRODUCT_CANON` · `OWNER_INTENT` § O208-B |

### Роли

| Кто | Что |
|-----|-----|
| **Owner + Claude** | Визуал next, layout, компоненты в `rawlead-next/` |
| **Lead Designer** | Стратегия, спорные UX, новый `wave-*-brief` если нужен Coder |
| **Designer** | § `DESIGNER_PROMPT` O280 advisor — copy/hierarchy |
| **Lead Architect** | `CODER_PROMPT` · handoff в код |

### Deliverables (когда owner откроет design gate)

1. **Scope doc** — какие P0-экраны Next нуждаются в wire до кода (lenta, quiz overlay, cabinet, pricing).
2. **Copy sheet** — tier states, empty/error, quiz finale — aligned с O209 lexicon.
3. **Optional:** `docs/design/next/` brief (только с «да» владельца на новую папку) — иначе правки в `PAGES_INVENTORY` supplement.

### Guard

- **Не** возвращать Skill Tree / manual skills в UI.
- **Не** менять tier matrix (30м / 3д trial / 5 черновиков / 790₽) без PM.
- WP **P1 delta only** (copy/banners) если hotfix — структура grid/filter bar по O209 guard.

### Handoff

`@lead-designer` → `@designer` (advisor) · `@lead-architect` → `CODER_PROMPT` § O280 · owner+Claude в `rawlead-next/CLAUDE.md`

---

## § O209-MATCH-EXPERIENCE — ✅ delivered (reference)

**Shipped:** 2026-06-14 · theme 1.18.84+ · spec [`wave-o209-match-brief.md`](../../design/wp/wave-o209-match-brief.md).

| Уровень | Страницы |
|---------|----------|
| P0 rebuild | `/quiz/` (done) |
| P1 copy+delta | lenta · cabinet · home · pricing · faq · how (done) |

**Baseline визуала WP:** [`REFERENCE.md`](../../design/wp/REFERENCE.md) v5 · [`feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) v5.

---

## § O215-WP-LIVE-POLISH — ✅ closed

BrowserSync polish · prod **1.19.20**. Perf wave — backlog, не блокирует O280.

---

## Backlog (не активно)

| ID | Тема | Примечание |
|----|------|------------|
| Perf wave | lenta/home/quiz load | после O280 P0 screens |
| O174-D | YooKassa pay UI deltas | если pricing flow меняется в Next |
| D-O82b | Match breakdown v2 | ⏸ |

---

_Длинные § O81–O208, Skill Tree O98-w — архив / git до 2026-06-19. Активная задача Designer: [`DESIGNER_PROMPT.md`](DESIGNER_PROMPT.md)._
