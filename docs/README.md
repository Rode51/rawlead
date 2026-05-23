# Документация FL Radar

**С чего начать** — по роли:

| Кто | Файл |
|-----|------|
| **Владелец (ты)** | **[`FOR_YOU.md`](FOR_YOU.md)** — шаги · **[`KAK_ETO_RABOTAET.md`](KAK_ETO_RABOTAET.md)** — как устроено |
| **Куда идём по фазам** | **[`ROADMAP.md`](ROADMAP.md)** |
| **Lead / Coder / Mechanic** | **[`team/`](team/)** — [`team/LEAD.md`](team/LEAD.md), TASKS, STATUS |
| **Настройка радара** | **[`ops/`](ops/)** — фильтры, профиль, запуск |
| **Сломалось** | **[`problems/`](problems/)** — тикеты для Mechanic |
| **Справочник (редко)** | **[`archive/`](archive/)** — промпты исследований, аудит Cursor |

---

## Папки

```
docs/
  README.md           ← ты здесь
  FOR_YOU.md          ← владелец: шаги
  KAK_ETO_RABOTAET.md ← как работает (простым языком)
  ROADMAP.md          ← фазы 0–4
  PORTFOLIO.md        ← текст для резюме (не для запуска)
  ops/                ← FILTERS, PROFILE, RUN, TG, пульт
  team/               ← Lead/Coder: TASKS, STATUS, TZ, …
  problems/           ← инциденты
  archive/            ← не для ежедневной работы
```

---

## ops/ — работоспособность

| Файл | Зачем |
|------|--------|
| [`ops/FILTERS.md`](ops/FILTERS.md) | Слова «берём / стоп» — **читает код** |
| [`ops/PROFILE.md`](ops/PROFILE.md) | Кто ты для ИИ — **читает код** |
| [`ops/RUN.md`](ops/RUN.md) | Запуск, `.env`, пауза в TG |
| [`ops/DESKTOP_LAUNCH.md`](ops/DESKTOP_LAUNCH.md) | Пульт Tauri, ярлык vbs |
| [`ops/TELEGRAM_ACCOUNTS.md`](ops/TELEGRAM_ACCOUNTS.md) | 3 номера, прокси |
| [`ops/BACKUP.md`](ops/BACKUP.md) | Бэкап `.env`, сессий |
| [`ops/SOURCES_POOLS.md`](ops/SOURCES_POOLS.md) | MVP-чаты, chat_id |
| [`ops/WP_LOCAL_SKELETON.md`](ops/WP_LOCAL_SKELETON.md) | Локальный WP |
| [`ops/GIT.md`](ops/GIT.md) | GitHub Rode51/uisness |

Полный список — по мере надобности в папке `ops/`.

---

## team/ — разработка

| Файл | Зачем |
|------|--------|
| [`team/TASKS.md`](team/TASKS.md) | Очередь (активное) |
| [`team/STATUS.md`](team/STATUS.md) | Сейчас / следующий шаг |
| [`team/SCALE.md`](team/SCALE.md) | Цикл задач + чеклисты Lead |
| [`team/HOW_TO_USE_CURSOR.md`](team/HOW_TO_USE_CURSOR.md) | Роли в Cursor |
| [`team/DESIGN_BRIEF.md`](team/DESIGN_BRIEF.md) | UI пульта (эталон) |
| [`team/ARCHITECTURE.md`](team/ARCHITECTURE.md) | Схема модулей |
| [`team/CODE_STRUCTURE.md`](team/CODE_STRUCTURE.md) | Где какой файл; правила Coder |
| [`team/TZ.md`](team/TZ.md) | ТЗ фазы 0 |
| [`team/LEAD.md`](team/LEAD.md) | Регламент Lead |

Архив сданных задач: [`team/archive/TASKS_HISTORY.md`](team/archive/TASKS_HISTORY.md).

**Роли Cursor:** `.cursor/rules/*.mdc` (`@lead-architect` · `@designer` · `@coder` · `@mechanic` · `@owner`).

**Шаблон для нового проекта:** `C:\Users\hramo\Templates\cursor-universal` (вне этого repo).
