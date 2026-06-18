# RawLead — документация

**Главный документ проекта.** В корне `docs/` только **три** файла — остальное в подпапках.

---

## AI: с чего начать (все роли)

1. [`team/common/PROJECT_MAP.md`](team/common/PROJECT_MAP.md) — **навигация**, зоны, «куда не лезть»
2. Файл роли: `team/architect/CODER_PROMPT` · `team/design/DESIGNER_PROMPT` · `team/product/LEAD_PRODUCT_PROMPT` · `docs/problems/…`
3. Vision v0.12: [`team/product/PRODUCT_VISION.md`](team/product/PRODUCT_VISION.md) · фазы: [`team/architect/ROADMAP.md`](team/architect/ROADMAP.md) · **prod snapshot:** [`team/common/PROD_FACTS.md`](team/common/PROD_FACTS.md)

Промпт задачи — **только в файле**; в чат владельцу — копипаст `@роль` + `.mdc` + путь к промпту ([`team/architect/LEAD.md`](team/architect/LEAD.md)).

**Новый проект с той же командой AI:** [`team/templates/cursor-team-kit/README.md`](team/templates/cursor-team-kit/README.md)

---

## Три файла в корне (открывай их)

| Файл | Когда |
|------|--------|
| **[`FOR_YOU.md`](FOR_YOU.md)** | **Что делать сейчас** — шаги, TG, пульт |
| **[`KAK_ETO_RABOTAET.md`](KAK_ETO_RABOTAET.md)** | **Как устроено** — простым языком |
| **README.md** | **Карта всего** — ты здесь |

---

## Папки

```
docs/
  FOR_YOU.md              ← твои шаги
  KAK_ETO_RABOTAET.md     ← как работает
  README.md               ← этот файл

  team/
    common/               ← PROJECT_MAP, STATUS, TASKS, MCP
    architect/            ← ROADMAP, CODER_PROMPT, LEAD, TZ
    product/              ← PRODUCT_VISION, LEAD_PRODUCT
    design/               ← DESIGN_SYSTEM, DESIGNER_PROMPT
    archive/
  ops/                    ← запуск, TG, фильтры, WP
  problems/               ← поломки (Mechanic)
  design/                 ← UI, макеты
  archive/                ← старое, не для каждый день
```

| Папка | Зачем | Частое |
|-------|--------|--------|
| [`team/`](team/) | Lead, Coder, фазы, vision | [`team/architect/ROADMAP.md`](team/architect/ROADMAP.md) · [`team/common/STATUS.md`](team/common/STATUS.md) · [`team/common/TASKS.md`](team/common/TASKS.md) · [`team/common/MCP_POOL.md`](team/common/MCP_POOL.md) (MCP) |
| [`ops/`](ops/) | Запуск и настройка | [`RUN.md`](ops/RUN.md) · [`TELEGRAM_ACCOUNTS.md`](ops/TELEGRAM_ACCOUNTS.md) · [`DESKTOP_LAUNCH.md`](ops/DESKTOP_LAUNCH.md) |
| [`problems/`](problems/) | Тикеты багов | по дате |
| [`design/`](design/) | Дизайн | [`design/rawlead/project-map-owner.png`](design/rawlead/project-map-owner.png) |
| [`archive/`](archive/) | Архив | не открывать без нужды |

Регламент «один канон — один файл»: [`team/common/DOCS_ARCHITECTURE.md`](team/common/DOCS_ARCHITECTURE.md) · Cursor: `docs-guard.mdc` при правке docs

---

## По роли

| Кто | С чего начать |
|-----|----------------|
| **Ты** | [`FOR_YOU.md`](FOR_YOU.md) → [`KAK_ETO_RABOTAET.md`](KAK_ETO_RABOTAET.md) |
| **Lead** | [`team/architect/LEAD.md`](team/architect/LEAD.md) · [`team/architect/OWNER_INTENT.md`](team/architect/OWNER_INTENT.md) · [`team/common/TASKS.md`](team/common/TASKS.md) · [`team/common/STATUS.md`](team/common/STATUS.md) |
| **Coder** | [`team/architect/CODER_PROMPT.md`](team/architect/CODER_PROMPT.md) · [`team/common/PROJECT_MAP.md`](team/common/PROJECT_MAP.md) |
| **Mechanic** | [`problems/`](problems/) |
| **Designer** | [`team/design/DESIGNER_PROMPT.md`](team/design/DESIGNER_PROMPT.md) |

Cursor: `@lead-architect` · `@coder` · `@mechanic` · `@designer` · правила — `.cursor/rules/`

---

## ops/ — быстрые ссылки

| Файл | Зачем |
|------|--------|
| [`ops/RUN.md`](ops/RUN.md) | `.env`, smoke, пауза бота |
| [`ops/DESKTOP_LAUNCH.md`](ops/DESKTOP_LAUNCH.md) | Пульт Tauri, vbs |
| [`ops/TELEGRAM_ACCOUNTS.md`](ops/TELEGRAM_ACCOUNTS.md) | acc1/2/3, @FLPARSINGBOT /start |
| [`ops/FILTERS.md`](ops/FILTERS.md) | Слова «берём/стоп» — **читает код** |
| [`ops/PROFILE.md`](ops/PROFILE.md) | Профиль ИИ — **читает код** |
| [`ops/SOURCES_POOLS.md`](ops/SOURCES_POOLS.md) | TG-чаты, FL/Kwork URL |
| [`ops/BACKUP.md`](ops/BACKUP.md) | Бэкап |
| [`ops/GIT.md`](ops/GIT.md) | GitHub |

---

## team/ — разработка

Индекс папок: [`team/README.md`](team/README.md) (`common/` · `architect/` · `product/` · `design/`)

| Файл | Зачем |
|------|--------|
| [`team/architect/ROADMAP.md`](team/architect/ROADMAP.md) | Фазы и приоритет «сейчас» |
| [`team/architect/OWNER_INTENT.md`](team/architect/OWNER_INTENT.md) | Решения и мысли владельца (handoff Lead) |
| [`team/common/STATUS.md`](team/common/STATUS.md) | Снимок + блокеры |
| [`team/common/PROD_FACTS.md`](team/common/PROD_FACTS.md) | **Prod snapshot** — browser stack, deploy, theme |
| [`team/common/TASKS.md`](team/common/TASKS.md) | Очередь |
| [`team/common/PROJECT_MAP.md`](team/common/PROJECT_MAP.md) | Карта для AI |
| [`team/common/PORTFOLIO.md`](team/common/PORTFOLIO.md) | Текст для резюме |

---

_Индекс · корень docs/ = FOR_YOU + KAK_ETO + README_
