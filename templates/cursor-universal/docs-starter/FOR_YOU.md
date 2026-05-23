# Для тебя

| Вопрос | Файл |
|--------|------|
| **Что делать сейчас?** | Ниже «Твои шаги» |
| **Фазы** | [`ROADMAP.md`](ROADMAP.md) |
| **Запуск** | [`ops/RUN.md`](ops/RUN.md) |
| **Бэкап** | [`ops/BACKUP.md`](ops/BACKUP.md) |
| **Роли / Cursor** | `.cursor/rules/` (`@lead-architect` `@coder` `@mechanic` `@owner`) · [`team/SCALE.md`](team/SCALE.md) |

Lead = docs · Coder = код (**новый чат на задачу**) · Mechanic = поломки · **ты** = `.env`, запуск, бэкап.

---

## Твои шаги сейчас

1. _(Lead заполнит после первого планирования)_
2. Настрой бэкап: `scripts\backup.config.json` → `scripts\backup.bat`
3. Запуск по [`ops/RUN.md`](ops/RUN.md)

---

## Кому писать

| Нужно | Куда |
|-------|------|
| План, docs | **Lead** `@lead-architect` |
| Фича | **Coder** — если есть `team/CODER_PROMPT.md` |
| Поломка | **Mechanic** `@mechanic` + `problems/…` |

---

## Если сломалось

Lead → тикет в `problems/` → Mechanic. Не чини в чате Lead.
