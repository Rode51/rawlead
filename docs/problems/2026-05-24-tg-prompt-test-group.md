# TG: группа prompt-test (5113) — «бот не собирает»

**Дата:** 2026-05-24  
**Статус:** open · triage Lead  
**Группа:** `prompt-test` · invite `https://t.me/+Z7HcnIAdSw9kY2U6` · `chat_id=5177575757` · acc1 · CSV wave 4 **done**

## Запрос владельца (2026-05-24, доп.)

- Ослабить **ключевые слова Python** (уровень 2 / FILTERS).
- **Нет бюджета в объявлении** → всё равно отправлять в ИИ.
- В карточке бюджет: **«по договоренности»** (не «не указан»).
- Задача Coder: `docs/team/architect/CODER_PROMPT.md` § **L**.

## Симптом (владелец)

Сообщения из тестовой группы не попадают в радар / бот не присылает карточку.

## Факты из repo (2026-05-24)

| Проверка | Результат |
|----------|-----------|
| `TG_JOIN_QUEUE.csv` | acc1, 5113, **done**, id `5177575757` |
| `data/telethon_chat_ids_acc1.txt` | `5177575757` **есть** |
| `data/radar.log` | listen включает `-5177575757` |
| `radar.log` 12:10:28 | **msg=46** из `chat=-5177575757` → **`skip:filter`** (сообщение **видели**) |

**Вывод Lead:** мониторинг группы **работает**. Частые «ложные» причины — см. ниже.

## Три причины (не баг)

1. **Пишешь с телефона acc1** — `message.out` в `tg_monitor.py` **молча игнорируется** (своих исходящих нет в логе).
2. **Текст не про заказ** — фильтр → `skip:filter` / `skip:ai:МИМО` (как msg 46).
3. **Дубли python** — 2× `tg_main` → `database is locked`, сообщения теряются · тикет [`2026-05-24-duplicate-python-processes.md`](2026-05-24-duplicate-python-processes.md).

## Самопроверка владельца (2 мин)

1. Запуск **только** `start-radar-desktop.vbs` → ▶.
2. PowerShell:
   ```powershell
   Get-CimInstance Win32_Process -Filter "name='python.exe'" | Where-Object { $_.CommandLine -match 'uisness' }
   ```
   → **≤ 2** процесса, оба `.venv`.
3. В группу пишет **другой** аккаунт / человек (не acc1).
4. Текст как заказ, напр.: «Нужен парсер на Python, бюджет 50 000 ₽, срок 2 недели».
5. Смотреть `data/radar.log` на строку `chat=-5177575757`.

## Задача Mechanic (если после п.1–5 всё ещё пусто)

| # | Готово когда |
|---|----------------|
| M1 | Подтверждено: один tg_main, chat в listen |
| M2 | Новое чужое сообщение → строка в `radar.log` (не обязательно в бот) |
| M3 | Если в логе есть, но не в боте — цепочка filter/AI/notify, причина в тикете |
| M4 | Если в логе нет при живом tg_main — peer_id / hot-reload / event handler |

**Файлы:** `src/tg_monitor.py`, `scripts/tg_main.py`, `data/radar.log`, `data/telethon_chat_ids_acc1.txt`

## Когда Coder (не Mechanic)

- Нужен **режим теста**: для `prompt-test` не применять filter / логировать свои `out` — **новая фича**, отдельный пункт в `CODER_PROMPT.md` от Lead.

## Кому писать

| Ситуация | Роль |
|----------|------|
| «Не понимаю, почему» после самопроверки | **Mechanic** + этот тикет |
| «Хочу, чтобы мои сообщения с acc1 тоже шли» | **Lead** → задача **Coder** |
| Дубли python / пульт | Mechanic или Coder по [`2026-05-24-duplicate-python-processes.md`](2026-05-24-duplicate-python-processes.md) |
