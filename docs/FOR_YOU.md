# Для тебя

## Что сейчас важно (2 минуты)

| # | Действие |
|---|----------|
| 1 | **O72e закрыт:** PASS `075032Z` (`combined 4.10`, `send 61.9%`, `L1 87.0%`) |
| 2 | **Закрыто:** `O90+O91` (lag + watchdog + proxy health) |
| 3 | **Закрыто:** `O89` (уникальный отклик per-user) |
| 4 | **Interim:** O92 в `/cabinet/` (deploy `1.11.30`) — **не финал**, в ленту не тащим |
| 5 | **✅ O93** deploy `1.12.0` — проверь `/cabinet/` + `/lenta/` (Разработка → 2 блока) |
| 6 | **Сейчас:** E2E UX прогон → потом O92b / ads |

---

## Быстрые ссылки

| Вопрос | Где смотреть |
|--------|--------------|
| Текущий статус | [`team/common/STATUS.md`](team/common/STATUS.md) |
| Активные задачи | [`team/common/TASKS.md`](team/common/TASKS.md) |
| ТЗ для Coder | [`team/architect/CODER_PROMPT.md`](team/architect/CODER_PROMPT.md) |
| Решения владельца | [`team/architect/OWNER_INTENT.md`](team/architect/OWNER_INTENT.md) |
| Запуск/ops | [`ops/RUN.md`](ops/RUN.md), [`ops/DEPLOY_VPS.md`](ops/DEPLOY_VPS.md) |

---

## Прокси (кратко)

- Для бирж: только `FL_PROXY_URLS` / `KWORK_PROXY_URLS`
- Не смешивать с `TG_PROXY_URL` / `TELETHON_PROXY_*`
- Цель пула: `7-8` IP (текущие + `+3..4` новых)

---

## Если ИИ «недоступен»

- L1 обычно продолжает работать
- L2 может временно падать из-за OpenRouter
- Действие: повторить через 1-2 мин и проверить баланс OpenRouter в `.env.site`

---

## Безопасность и Git

- Не коммитить: `.env*`, `*.session`, `*credentials*`, `mcp.pool.json`
- Перед коммитом: `git status`

---

## История и подробные инструкции

Длинная история, старые runbook и разборы перенесены в рабочие документы:

- [`team/archive/STATUS_ARCHIVE.md`](team/archive/STATUS_ARCHIVE.md)
- [`team/archive/CODER_PROMPT_ARCHIVE.md`](team/archive/CODER_PROMPT_ARCHIVE.md)
- [`ops/DESKTOP_LAUNCH.md`](ops/DESKTOP_LAUNCH.md)
- [`KAK_ETO_RABOTAET.md`](KAK_ETO_RABOTAET.md)
