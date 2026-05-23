# Расписание join в TG-чаты

**Цель:** три мониторинговых номера постепенно вступают в чаты из [`TG_JOIN_QUEUE.csv`](TG_JOIN_QUEUE.csv), без массового join за один раз.

---

## Распределение номеров

|key | Номер | Сессия | Роль в очереди
----|-------|--------|---------------
`acc1` | +66953964608 | `*_telethon.session` | MVP (5 чатов) + добор волны 2
`acc2` | +66967716330 | `+66967716330.session` | волна 2, IT/WP
`acc3` | +66985780470 | `+66985780470.session` | волна 2, WP + опционально

**Прокси:** у каждого номера **свой** IP ([`PRODUCT_VISION.md`](../team/PRODUCT_VISION.md)). Не гонять все три через один прокси.

---

## Лимиты (безопасный старт)

| Параметр | Значение | Зачем |
|----------|----------|--------|
| Join в час на **один** аккаунт | **4** | меньше FloodWait / ограничений |
| Пауза между join | **15–20 мин** (+ случайный разброс ±3 мин) | «как человек» |
| Join в сутки на аккаунт | **до 25** | потолок на первую неделю |
| При `FloodWait` | ждать `seconds` из ошибки, **не** увеличивать лимит | Telegram сам сказал паузу |
| Ночь 02:00–07:00 Irkutsk | **не join** | как у монитора |

Позже (волна 3+, ~100 чатов из Google Doc): не выше **5/час** и **30/сутки** без отдельного решения Lead.

---

## Очередь

Файл [`TG_JOIN_QUEUE.csv`](TG_JOIN_QUEUE.csv):

- `account` — `acc1` / `acc2` / `acc3`
- `status` — `pending` → `done` / `fail` / `skip`
- `chat_id` — заполняет Coder/скрипт после join (`tg_list_dialogs`)

Новые строки — из [`TG_CHANNELS_BASE.md`](TG_CHANNELS_BASE.md) и [Google Doc](https://docs.google.com/document/d/1KplF0v2eBr_o0ThbON17sRnfDqoMfiIkk_M3HkLtjfE/edit?usp=sharing). **Секция 7 — не добавлять.**

---

## Как запускать

```text
# Разовый прогон одного acc (до 4 join за час)
python scripts/tg_join_queue.py --account acc2

# Фон: один supervisor для acc2/acc3/acc4 (env TG_JOIN_DAEMON_ACCOUNTS)
python scripts/tg_join_daemon.py

# Windows — полный радар (3 окна)
scripts\start-radar-full.bat
```

Перед первым запуском acc2/acc3:

1. Конверт сессии: `python scripts/tg_convert_session.py PATH_TO_+66967716330`
2. В `.env` — пути и прокси ([`TELEGRAM_ACCOUNTS.md`](TELEGRAM_ACCOUNTS.md), [`RUN.md`](RUN.md))
3. Проверка: `TELETHON_SESSION_PATH=…acc2… python scripts/tg_list_dialogs.py`

---

## После join

1. Скрипт обновляет `TG_JOIN_QUEUE.csv` (`status`, `chat_id`).
2. Lead/Coder переносят `done` в [`SOURCES_POOLS.md`](SOURCES_POOLS.md) и [`TELEGRAM_CHATS.json`](TELEGRAM_CHATS.json).
3. Когда acc2/acc3 слушают чаты — отдельный `TELETHON_CHAT_IDS` или multi-session монитор (задача Coder, не в MVP).

---

## Владелец

1. Убедиться, что **acc2 и acc3** — `.session` на ПК + **2 отдельных прокси**.
2. Join: [`RUN.md`](RUN.md) § TG join queue.
3. После деплоя — один раз в день смотреть `data/tg_join.log` (или `radar.log`): `join:ok`, `join:fail`, `join:wait`.
