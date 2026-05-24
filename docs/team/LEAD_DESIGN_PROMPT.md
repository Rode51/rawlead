# Lead Designer — активный план

**Дата:** 2026-05-24 · принято Lead Architect из [`LEAD_PRODUCT_PROMPT.md`](LEAD_PRODUCT_PROMPT.md)  
**Vision:** [`PRODUCT_VISION.md`](PRODUCT_VISION.md) **v0.9** (ставка B)  
**Статус:** активно — UX для `/feed` и `/cabinet`

---

## Цель

Спецификация UI для **двух новых страниц WP** под MVP: открытая лента и персональный кабинет (single-user). Стиль — REFERENCE E, канон токенов — `DESIGN_SYSTEM.md`. Лендинг и `/uslugi` **не трогаем**.

---

## Scope

| В scope | Вне scope |
|---------|-----------|
| WP **`/feed`** — anon, фильтры, поиск, сортировки, карточка лида | `/uslugi`, FL.ru тексты, Habr-статья, GitHub README |
| WP **`/cabinet`** — `user_id=1`, match %, теги, `final_rank` | Лендинг главная (тарифы — после MVP) |
| Visual feedback ИИ-агента (кнопка, модалка, «push в TG») — **макет**; код кнопки после фазы 3f | Отдельный сайт-визитка, mobile app |
| Handoff → `DESIGNER_PROMPT.md` + `DESIGN_BRIEF.md` | Правки child theme кодом (это Coder) |

---

## Готово когда

| # | Критерий |
|---|----------|
| 1 | Wireframe/описание **`/feed`**: карточка (заголовок, источник, бюджет, теги, ai_score), фильтры, сортировки, поиск, пагинация или infinite scroll |
| 2 | Wireframe/описание **`/cabinet`**: match % (синяя полоса REFERENCE), `final_rank`, «Мои теги» 8–12 chip, кнопка «Сгенерировать отклик» (disabled до 3f — ок) |
| 3 | Состояния: empty, loading, error — для обеих страниц |
| 4 | `DESIGNER_PROMPT.md` заполнен; Coder-§ в `DESIGN_BRIEF.md` (блоки, не код) |
| 5 | Lead Architect принял handoff → очередь Coder **после** 3b/3c API (см. `ROADMAP.md`) |

---

## Handoff

| Кому | Файл | Что передать |
|------|------|--------------|
| Designer | `DESIGNER_PROMPT.md` | исполнение макетов/текстов в `docs/design/` |
| Lead Architect | `DESIGN_BRIEF.md` § Coder | блоки WP для фаз 3c–3d |

---

## Референсы (из Product)

- [`docs/design/wp/REFERENCE.md`](../design/wp/REFERENCE.md) — стиль E (Unbounded/Manrope, светлый)
- [`docs/team/DESIGN_SYSTEM.md`](DESIGN_SYSTEM.md) — токены v1
- Уже есть: лендинг ✅, пульт (внутренний) ✅, PNG-карта ✅

---

_После сдачи — архив в `team/archive/TASKS_HISTORY.md`; очистить или заменить этот файл._
