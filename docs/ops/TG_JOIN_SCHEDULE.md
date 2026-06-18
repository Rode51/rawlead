# Расписание join в TG-чаты

**Цель:** три мониторинговых номера постепенно вступают в чаты из [`TG_JOIN_QUEUE.csv`](TG_JOIN_QUEUE.csv), без массового join за один раз.

---

## Распределение номеров

|key | Номер | Сессия | Роль в очереди
----|-------|--------|---------------
`acc1` | +66953964608 | `*_telethon.session` | MVP (5 чатов) + добор волны 2
`acc2` | +66967716330 | `+66967716330.session` | волна 2, IT/WP
`acc3` | +66985780470 | `+66985780470.session` | волна 2, WP + опционально

**Прокси:** у каждого номера **свой** IP ([`PRODUCT_VISION.md`](../team/product/PRODUCT_VISION.md)). Не гонять все три через один прокси.

---

## Лимиты

| Параметр | Значение | Зачем |
|----------|----------|--------|
| Join в час на **один** аккаунт | **10** (owner **2026-06-12**, wave 4) | было 4 · см. § O188 |
| Пауза между join | **5–7 мин** (`TG_JOIN_MIN_DELAY_SEC=300`) | ~10/час на acc |
| Join в сутки на аккаунт | **до 80** (`TG_JOIN_MAX_PER_DAY`) | 127 чатов ÷ 3 acc ≈ 43 each |
| При `FloodWait` | ждать `seconds` из ошибки, **не** увеличивать лимит | Telegram сам сказал паузу |
| Ночь 02:00–07:00 Irkutsk | **не join** | как у монитора |

Позже (после недели без FloodWait): Lead может поднять до **5/час** и **30/сутки** через `.env` — **сейчас не менять**.

---

## Волна 5 (2026-06-15, owner Excel)

| Что | Деталь |
|-----|--------|
| Источник | `Фриланс Чаты 1500.xlsx` + `Фриланс Каналы 2000.xlsx` → repo `docs/ops/import/` |
| Уникальных ссылок | **4421** · после фильтра **>5000 участников** → **329** (150 чатов + 179 каналов) |
| Net-new в v4 | **305** (24 уже в v1–v3) |
| Очередь | **`TG_JOIN_QUEUE_v4.csv`** · wave **5** · round-robin acc1/acc2/acc3 |
| Фильтр | col **B «Участники»** > **5000** (owner 2026-06-15) |
| Join порядок | v2 backlog → v3 (127) → **v4 (305)** · multi-queue в `tg_join_runner` |
| Импорт v4 | `python scripts/tg_queue_import.py --from-xlsx --dry-run` → без `--dry-run` пишет `TG_JOIN_QUEUE_v4.csv` |
| Срок | **~2 дня** при 80 join/сутки × 3 acc |

---

## Волна 3 (2026-05-23, решение владельца)

| Что | Деталь |
|-----|--------|
| Очередь | Все каналы из Google Doc → `TG_JOIN_QUEUE.csv` как **`pending`** |
| Распределение | **acc1 / acc2 / acc3** round-robin (~⅓ на номер) |
| Исключения | Секция 7 Doc + [`TG_JOIN_BLOCKLIST.txt`](TG_JOIN_BLOCKLIST.txt) |
| Срок | ~**3–7 дней** на ~150 чатов при лимитах 25/сутки × 3 acc |
| Запуск | Пульт ▶ или `start-radar-full.bat` — join не идёт без радара |
| Импорт | [`TG_CHANNELS_EXPORT.txt`](TG_CHANNELS_EXPORT.txt) → `python scripts/tg_queue_import.py` (см. [`RUN.md`](RUN.md)) |

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

# Join в фоне — внутри tg_main (TG_JOIN_IN_TG_MAIN=1), не отдельный процесс
# acc2 без chat_ids: join-bootstrap в tg_monitor (очередь TG_JOIN_QUEUE_v2.csv)
# Нельзя: TG_JOIN_IN_TG_MAIN=1 + tg_join_queue.py параллельно с radar (database locked)

# Windows — полный радар (2 окна: биржи + TG)
scripts\start-radar-full.bat
```

Перед первым запуском acc2/acc3:

1. Конверт сессии: `python scripts/tg_convert_session.py PATH_TO_+66967716330`
2. В `.env` — пути и прокси ([`TELEGRAM_ACCOUNTS.md`](TELEGRAM_ACCOUNTS.md), [`RUN.md`](RUN.md))
3. Проверка: `TELETHON_SESSION_PATH=…acc2… python scripts/tg_list_dialogs.py`

---

## После join

1. Скрипт обновляет `TG_JOIN_QUEUE.csv` (`status`, `chat_id`).
2. Lead/Coder переносят `done` в [`SOURCES_POOLS.md`](SOURCES_POOLS.md); в CSV уже есть `name`, `link`, `chat_id` — отдельный JSON не нужен.
3. Когда acc2/acc3 слушают чаты — отдельный `TELETHON_CHAT_IDS` или multi-session монитор (задача Coder, не в MVP).

---

## Владелец

1. Убедиться, что **acc2 и acc3** — `.session` на ПК + **2 отдельных прокси**.
2. Join: [`RUN.md`](RUN.md) § TG join queue.
3. После деплоя — один раз в день смотреть `data/tg_join.log` (или `radar.log`): `join:ok`, `join:fail`, `join:wait`.
