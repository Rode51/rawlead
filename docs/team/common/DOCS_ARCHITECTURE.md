# Архитектура документации — один источник правды

**Lead Architect ведёт этот файл** (`docs/team/common/`).

---

## Корень `docs/` — только 3 файла

| Файл | Канон |
|------|--------|
| **`README.md`** | Главная карта всего repo docs |
| **`FOR_YOU.md`** | Шаги владельца **сейчас** |
| **`KAK_ETO_RABOTAET.md`** | Как работает (простым языком) |

**Всё остальное — в подпапках.** Новый файл в корень **запрещён** без согласия владельца.

---

## PROD_FACTS — анти-drift (2026-06-16)

**Проблема:** агенты читают старые `problems/`, архив или устаревший § CODER → путают Playwright/Chromium с Camoufox, «deploy ⏳» с prod.

**Решение:** [`PROD_FACTS.md`](PROD_FACTS.md) — **единый снимок prod** (browser stack, deploy, theme, systemd).

| Когда | Кто | Действие |
|-------|-----|----------|
| **Перед triage / «что на prod»** | Lead · Mechanic · Coder | Прочитать `PROD_FACTS` + `STATUS` hot |
| **После verify/deploy** | Lead | Обновить `PROD_FACTS` (5 мин) · `STATUS` · при необходимости `FOR_YOU` |
| **Новый факт о prod** | Lead | Только в `PROD_FACTS`, не в чат и не в новый md |
| **Исторический тикет** | Mechanic | Не менять задним числом · в шапке «сверять PROD_FACTS» |

**Иерархия правды (новое > старое):**

```
PROD_FACTS.md  →  STATUS.md hot  →  CODER_PROMPT hot  →  problems/ (дата тикета)  →  archive (не трогать)
```

---

## Папки `docs/team/`

| Папка | Кто | Содержание |
|-------|-----|------------|
| **`common/`** | все AI | PROJECT_MAP, **PROD_FACTS**, STATUS, TASKS, DOCS_ARCHITECTURE, MCP |
| **`architect/`** | Lead Architect, Coder (промпт) | LEAD, ROADMAP, CODER_PROMPT, ARCHITECTURE, CODE_STRUCTURE |
| **`product/`** | Lead Product | PRODUCT_VISION, LEAD_PRODUCT* |
| **`design/`** | Lead Designer | LEAD_DESIGN*, DESIGNER_PROMPT |
| **`archive/`** | — | история (не обновлять) |

Другие папки `docs/`: `ops/`, `problems/`, `design/` (макеты PNG), `archive/`.

---

## Канон по темам

| Тема | Файл |
|------|------|
| **Prod snapshot (browser, deploy)** | **`team/common/PROD_FACTS.md`** |
| **Навигация AI** | `team/common/PROJECT_MAP.md` |
| Фазы | `team/architect/ROADMAP.md` |
| Мысли владельца | `team/architect/OWNER_INTENT.md` |
| Vision | `team/product/PRODUCT_VISION.md` v0.12 |
| Шаги владельца | `FOR_YOU.md` |
| Как устроено | `KAK_ETO_RABOTAET.md` |
| Очередь | `TASKS.md` |
| Снимок задач | `STATUS.md` (≤~80) · `STATUS_ARCHIVE` |
| Coder ТЗ | `CODER_PROMPT.md` (≤~120 hot) · `CODER_PROMPT_ARCHIVE` |
| Поломка | `problems/` — **дата + сверка PROD_FACTS** |
| Deploy runbook | `ops/DEPLOY_VPS.md` |
| Биржи env | `ops/SOURCES_POOLS.md` + **PROD_FACTS § browser** |

---

## Правила

1. Одна тема = один канон (таблица выше).
2. **PROD_FACTS** обязателен при любом ответе «как у нас на prod».
3. FOR_YOU ≤ 1 экран; детали → README / KAK_ETO / PROD_FACTS.
4. **STATUS ≤ ~80** · **CODER_PROMPT ≤ ~120** · закрытое → archive.
5. Новый `.md` — с согласия владельца + строка в § Канон.
6. `problems/` — исторический снимок; не переписывать прошлое, добавлять resolution §.

---

## Проверка чистоты (Lead, раз в неделю или после волны)

- [ ] `PROD_FACTS` дата ≤ 7 дней или после последнего deploy
- [ ] `FOR_YOU` «Сейчас» совпадает с `STATUS` Next
- [ ] `ARCHITECTURE` / `CODE_STRUCTURE` browser stack = `PROD_FACTS`
- [ ] `CODER_PROMPT` ≤ 120 строк · closed § только index
- [ ] Нет «deploy ⏳» в index для уже prod §

---

_Lead Architect · 2026-05-24 · PROD_FACTS anti-drift 2026-06-16_
