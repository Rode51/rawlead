# Lead Designer — активный план

**Дата:** 2026-05-25 · согласовано с владельцем (сессия Lead Designer)  
**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.9** (ставка B)  
**Статус:** ✅ согласование завершено → передано Designer + ожидает Coder (после 3b/3c API)

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

| # | Задача |
|---|--------|
| 1 | Дополнить [`feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) §2.2: блок **«Категория»** — 4 ниши §0i + «Все» |
| 2 | Визуал: как «Источник» / «ИИ-оценка» — active chip `#0A0A0A` |
| 3 | Mobile: в bottom sheet после «Фильтры» |
| 4 | Handoff → `@coder` § D1 в [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md) |

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

## Scope (итог)

| В scope ✅ | Вне scope ❌ |
|-----------|------------|
| WP лендинг: анимации, цвета, pricing 1-тариф, nav «Лента» | `/uslugi`, FL.ru тексты, Habr-статья |
| WP `/feed`: карточка, фильтры, sidebar, infinite scroll, состояния | Mobile app, отдельный сайт |
| WP `/cabinet`: теги-чипы, match, AI-агент кнопка (disabled до 3f) | Coder-часть PHP (это CODER_PROMPT) |
| Пульт: пульс лампы ok | Новый функционал пульта |

---

_Lead Designer · 2026-05-25 · после сдачи Designer — архив в `team/archive/TASKS_HISTORY.md`_
