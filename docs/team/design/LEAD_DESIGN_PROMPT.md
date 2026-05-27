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

**Исполнитель:** **`@designer`** — ✅ **сдано 2026-05-26** ([`feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) §2.2–2.3).

| # | Задача | Статус |
|---|--------|--------|
| 1 | §2.2 блок **«Категория»** — 4 ниши §0i + «Все» | ✅ |
| 2 | Active chip `#0A0A0A` | ✅ |
| 3 | Mobile bottom sheet | ✅ |
| 4 | Handoff → `@coder` § D1 | ✅ |

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

## § PRE-LAUNCH-UX v2 — финальный слой перед продом (**→ @lead-designer**, 2026-05-27)

**Когда:** после § PRE-LAUNCH A–D (@coder) и **после** deep research навыков/инструментов ([`LEAD_PRODUCT_PROMPT.md`](../product/LEAD_PRODUCT_PROMPT.md) § SKILLS-TOOLS-RESEARCH).  
**Порядок:** Design (спор с владельцем) → **@lead-product** (тексты) → **@coder** (вёрстка).

**Регламент владельца:** Lead Designer **может и должен спорить**, пока не найдём решение, которое владелец считает идеальным по UX — не «сдать быстрее».

### Бриф владельца (факты)

| # | Задача | Направление (не финал — обсудить) |
|---|--------|-----------------------------------|
| ux1 | **Контакты** | Убрать приглашение на «ранний доступ» |
| ux2 | **Фильтры `/lenta/`** | Сейчас неудобно: специализацию трудно найти; от неё зависят навыки; навыки не в «маленьком окошке» |
| ux3 | **Плашка фильтров** | Предложение владельца: **горизонтальная плашка сверху** (специализация → навыки), быстро и интуитивно |
| ux4 | **«Лента заказов»** | Заголовок и блоки **зажаты** верхней плашкой; дать **больше воздуха** (отступы, иерархия) |
| ux5 | **Сообщить об ошибке** | Пользователь может отправить репорт (что сломалось / скрин / URL) — UX + куда ведёт CTA |
| ux6 | **Мобилка** | Полноценная адаптация (не только bottom sheet «как есть») |

### Что сдать Design

| # | Артефакт |
|---|----------|
| 1 | Wireframe/desktop + mobile: **верхняя** filter-bar (category multi → skills), сравнение с текущим sidebar |
| 2 | Типографика/отступы: hero «Лента заказов» + подзаголовки — «воздух» |
| 3 | Паттерн **Report bug** (footer? FAB? modal?) + поля формы |
| 4 | Контакты без early-access CTA — что остаётся (email/TG/форма) |
| 5 | Handoff в `feed-cabinet-mvp.md` или addendum + список для @lead-product (подписи, empty states, ошибки)

**Не в scope Design:** реализация API feedback (Coder после макета); биллинг.

→ Coder: [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md) § PRE-LAUNCH-UX · Product: [`LEAD_PRODUCT_PROMPT.md`](../product/LEAD_PRODUCT_PROMPT.md) § PRE-LAUNCH-UX copy.

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
