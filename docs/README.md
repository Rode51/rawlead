# Документация FL Radar

**С чего начать** — по роли:

| Кто | Файл |
|-----|------|
| Кто | Файл |
|-----|------|
| **Владелец (ты)** | **[`FOR_YOU.md`](FOR_YOU.md)** — шаги · **[`KAK_ETO_RABOTAET.md`](KAK_ETO_RABOTAET.md)** — как устроено |
| **Куда идём по фазам** | **[`ROADMAP.md`](ROADMAP.md)** — что готово, что дальше |
| **Lead / Coder / Mechanic** | **[`team/`](team/)** — задачи, ТЗ, [`team/LEAD.md`](team/LEAD.md) |
| **Настройка радара** | **[`ops/`](ops/)** — фильтры, профиль, запуск, URL |
| **Сломалось** | **[`problems/`](problems/)** — тикеты для Mechanic |

---

## Папки

```
docs/
  README.md      ← ты здесь
  FOR_YOU.md     ← владелец: шаги
  KAK_ETO_RABOTAET.md  ← как работает (простым языком)
  ROADMAP.md     ← фазы 0–4, одна карта
  PORTFOLIO.md   ← текст для резюме (не для запуска)

  ops/           ← радар читает FILTERS + PROFILE; ты правишь и RUN
  team/          ← Lead/Coder: TASKS, STATUS, TZ, AI, …
  problems/      ← инциденты
```

---

## ops/ — работоспособность приложения

| Файл | Зачем |
|------|--------|
| [`ops/FILTERS.md`](ops/FILTERS.md) | Слова «берём / стоп» — **читает код** |
| [`ops/PROFILE.md`](ops/PROFILE.md) | Кто ты для ИИ — **читает код** |
| [`ops/RUN.md`](ops/RUN.md) | Запуск на Windows, `.env`, пауза в TG |
| [`ops/SOURCES.md`](ops/SOURCES.md) | URL FL / Kwork |
| [`ops/TELEGRAM_ACCOUNTS.md`](ops/TELEGRAM_ACCOUNTS.md) | 3 номера, прокси, шаблон `.env` |
| [`ops/BACKUP.md`](ops/BACKUP.md) | Бэкап `.env`, сессий, SQLite |
| [`ops/SOURCES_POOLS.md`](ops/SOURCES_POOLS.md) | MVP-чаты, chat_id |
| [`ops/TG_CHANNELS_BASE.md`](ops/TG_CHANNELS_BASE.md) | База TG-каналов (MVP + волна 2) |
| [`ops/TELEGRAM_LOGIN.md`](ops/TELEGRAM_LOGIN.md) | Session+Json, Telethon |
| [`ops/WP_OWNER_STEPS.md`](ops/WP_OWNER_STEPS.md) | WordPress-пульт на хосте (позже) |
| [`ops/WP_LOCAL_SKELETON.md`](ops/WP_LOCAL_SKELETON.md) | **Локальный WP** — скелет сайта без хоста |
| [`ops/wp-skeleton/`](ops/wp-skeleton/) | Тексты страниц для вставки в WP |
| [`ops/NEON_CURSOR.md`](ops/NEON_CURSOR.md) | Neon в Cursor (MCP) + `DATABASE_URL` |

---

## team/ — разработка

| Файл | Зачем |
|------|--------|
| [`team/TASKS.md`](team/TASKS.md) | Очередь Coder (только активное) |
| [`team/STATUS.md`](team/STATUS.md) | Статус и последняя сессия Coder |
| [`team/TZ.md`](team/TZ.md) | ТЗ фазы 0 (биржи + ИИ) |
| [`team/PRODUCT_VISION.md`](team/PRODUCT_VISION.md) | Большой продукт: TG, WP, Neon |
| [`team/VISION_SAAS_SITE.md`](team/VISION_SAAS_SITE.md) | Сайт с подпиской для фрилансеров (этапы) |
| [`team/RESEARCH_TGAIJOBS.md`](team/RESEARCH_TGAIJOBS.md) | Референс TgAiJobs — что позаимствовать |
| [`team/AI.md`](team/AI.md) | Промпт и модель ИИ |
| [`team/ARCHITECTURE.md`](team/ARCHITECTURE.md) | Схема модулей |
| [`team/TESTING.md`](team/TESTING.md) | Чеклист приёмки |
| [`team/LEAD.md`](team/LEAD.md) | Lead — только docs |
| [`team/SCALE.md`](team/SCALE.md) | Цикл большого проекта (20–50 задач) |
| `.cursor/rules/*.mdc` | Роли в Cursor (Project Rules) |
| [`team/SECURITY.md`](team/SECURITY.md) | Безопасность для владельца |
| [`team/HOW_TO_USE_CURSOR.md`](team/HOW_TO_USE_CURSOR.md) | Lead / Coder / Mechanic |

Архив сданных задач: [`team/archive/TASKS_HISTORY.md`](team/archive/TASKS_HISTORY.md).

**Новый проект:** [`../templates/cursor-universal/`](../templates/cursor-universal/) — роли + docs + бэкап.
