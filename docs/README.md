# RawLead — документация

**Главный документ проекта.** В корне `docs/` только три файла для ежедневной работы — остальное по папкам ниже.

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

  team/                   ← процесс, фазы, AI, промпты
  ops/                    ← запуск, TG, фильтры, WP
  problems/               ← поломки (Mechanic)
  design/                 ← UI, макеты
  archive/                ← старое, не для каждый день
```

| Папка | Зачем | Частое |
|-------|--------|--------|
| [`team/`](team/) | Lead, Coder, фазы, vision | [`team/ROADMAP.md`](team/ROADMAP.md) · [`team/STATUS.md`](team/STATUS.md) · [`team/TASKS.md`](team/TASKS.md) |
| [`ops/`](ops/) | Запуск и настройка | [`RUN.md`](ops/RUN.md) · [`TELEGRAM_ACCOUNTS.md`](ops/TELEGRAM_ACCOUNTS.md) · [`DESKTOP_LAUNCH.md`](ops/DESKTOP_LAUNCH.md) |
| [`problems/`](problems/) | Тикеты багов | по дате |
| [`design/`](design/) | Дизайн | [`design/rawlead/project-map-owner.png`](design/rawlead/project-map-owner.png) |
| [`archive/`](archive/) | Архив | не открывать без нужды |

Регламент «один канон — один файл»: [`team/DOCS_ARCHITECTURE.md`](team/DOCS_ARCHITECTURE.md) · Cursor: `docs-guard.mdc` при правке docs

---

## По роли

| Кто | С чего начать |
|-----|----------------|
| **Ты** | [`FOR_YOU.md`](FOR_YOU.md) → [`KAK_ETO_RABOTAET.md`](KAK_ETO_RABOTAET.md) |
| **Lead** | [`team/LEAD.md`](team/LEAD.md) · [`team/TASKS.md`](team/TASKS.md) · [`team/STATUS.md`](team/STATUS.md) |
| **Coder** | [`team/CODER_PROMPT.md`](team/CODER_PROMPT.md) · [`team/PROJECT_MAP.md`](team/PROJECT_MAP.md) |
| **Mechanic** | [`problems/`](problems/) |
| **Designer** | [`team/DESIGNER_PROMPT.md`](team/DESIGNER_PROMPT.md) |

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

| Файл | Зачем |
|------|--------|
| [`team/ROADMAP.md`](team/ROADMAP.md) | Фазы и приоритет «сейчас» |
| [`team/STATUS.md`](team/STATUS.md) | Снимок + блокеры |
| [`team/TASKS.md`](team/TASKS.md) | Очередь |
| [`team/PROJECT_MAP.md`](team/PROJECT_MAP.md) | Карта для AI |
| [`team/PORTFOLIO.md`](team/PORTFOLIO.md) | Текст для резюме |

---

_Индекс · корень docs/ = FOR_YOU + KAK_ETO + README_
