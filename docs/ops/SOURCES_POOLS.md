# Пулы источников

**Контур 1 (Дикий Запад, только владелец):** этот файл.  
**Контур 2 (SaaS, подписка):** [`SOURCES_SAAS.md`](SOURCES_SAAS.md) — отдельный whitelist.

**Секреты** — только в **`.env`** на ПК владельца.

---

## Telegram — три номера

Подробно (пути, прокси без паролей, шаблон `.env`): **[`TELEGRAM_ACCOUNTS.md`](TELEGRAM_ACCOUNTS.md)**

Кратко:

| key | Номер | Роль |
|-----|-------|------|
| acc1 | +66953964608 | ✅ MVP, `tg_main` |
| acc2 | +66967716330 | ✅ join волна 2 |
| acc3 | +351924778041 (`233333925_telethon`) | ✅ замена мёртвого + deploy |
| acc4 | +15092724173 (`234694761_telethon`) | ✅ запас |

~~+66985780470~~ — ❌ не авторизован, не использовать.

**4 рабочих из 5 файлов** — детали [`TELEGRAM_ACCOUNTS.md`](TELEGRAM_ACCOUNTS.md).

Очередь join: [`TG_JOIN_QUEUE.csv`](TG_JOIN_QUEUE.csv) · лимиты [`TG_JOIN_SCHEDULE.md`](TG_JOIN_SCHEDULE.md)

---

### Чаты MVP (acc1)

| Вкл | Название | Ссылка | chat_id |
|-----|----------|--------|---------|
| ☑ | ПОМОГАТОР | https://t.me/ipomogator | 3363793339 |
| ☑ | Фриланс, удалёнка | https://t.me/frilanc | 1127950512 |
| ☑ | WORK ON | https://t.me/workk_on | 1303819569 |
| ☑ | Удалёнщики | https://t.me/tgjob | 1333124183 |
| ☑ | Чат 1С | https://t.me/task_1C | 1434631241 |

Реестр имён/ссылок для бота: строки `done` в [`TG_JOIN_QUEUE.csv`](TG_JOIN_QUEUE.csv) (код: `load_chat_registry_from_queue`).

База каналов: [`TG_CHANNELS_BASE.md`](TG_CHANNELS_BASE.md)

---

## Биржи

| Источник | `.env` | URL (старт) |
|----------|--------|-------------|
| FL.ru | `FL_PROJECTS_URL` | `https://www.fl.ru/projects/?kind=1` — см. [`../archive/SOURCES.md`](../archive/SOURCES.md) |
| Kwork | `KWORK_PROJECTS_URL` | `https://kwork.ru/projects` |

Пагинация FL: до 3 страниц в `fl_parser.py`. Детали URL — архив [`SOURCES.md`](../archive/SOURCES.md).

---

## Уведомления

`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TG_PROXY_URL` — см. [`RUN.md`](RUN.md).
