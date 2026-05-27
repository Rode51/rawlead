# Спам «📊 Статус радара» в Telegram после стопа

**Статус:** решено (Coder 2026-05-27 · приёмка владелец: спама нет)  
**Дата:** 2026-05-27  
**Симптом:** владелец нажал стоп / `stop-radar-desktop-full.vbs`, в @FLPARSINGBOT продолжают приходить сообщения «📊 Статус радара» (100+).

## Факты (Lead verify)

- Сообщение = `format_status_message()` → `telegram_control._handle_action(status)` → только кнопка **ℹ Статус** / `/status`.
- После «стопа» на ПК **живы** `neon_legacy_consumer.py` (×2: venv + Python311), `main.py`, `tg_main`, `radar_control` — `stop-radar-desktop-full.bat` вызывает `kill_all_radar_control`, но `_ALL_MATCH` в `process_guard.py` **не включает** `neon_legacy_consumer.py`.
- Consumer опрашивает бота в `_sleep_with_tg_poll` **каждые ~2 с** (`neon:tight-loop`).
- Экстренное гашение: kill всех `python*`, где CommandLine содержит `uisness` (см. `FOR_YOU.md`).

### Lead verify 2026-05-27 ~20:01 (повтор)

- Владелец стопал — **спам не прекратился**: снова поднялись **10** процессов (2× `radar_control` site+legacy, 2× `neon_legacy_consumer`, 2× `main`, 2× `tg_main`).
- Лог `radar_legacy.log`: **19:57** `neon:старт` — consumer **перезапустился** после «починки» Coder / повторного ▶ / ярлыка.
- **Общий баг offset:** `data/projects.db` → один ключ `tg_update_offset` для **обоих** ботов (@FLPARSINGBOT и @rawlead_bot). Site и Legacy **делят** cursor getUpdates → гонки и повторная обработка одних и тех же апдейтов (в т.ч. «ℹ Статус»).
- Оба профиля: один `TELEGRAM_CHAT_ID` (владелец) — ответы в один чат с разных ботов.

**Вероятная цепочка инцидента:** Coder чинил статус → полный стоп/падение → снова ▶ / VBS → **дубли** процессов + **сброс/рассинхрон offset** → очередь getUpdates отдаёт «Статус» снова и снова.

## Задачи @coder

| # | Готово когда |
|---|----------------|
| s1 | `kill_all_radar_control` + `stop-radar-desktop-full.bat` + `stop-radar.bat` убивают **`neon_legacy_consumer.py`** |
| s2 | `_ALL_MATCH` / `count_radar_workers` учитывают consumer (отдельная лампа «Neon» уже есть) |
| s3 | Не слать статус повторно на один и тот же `update_id`; **offset отдельно на bot token** (`tg_update_offset:<bot_id>`), не один на `projects.db` |
| s3b | После `sendMessage` статуса — **сразу** `set_tg_update_offset`; лог `тг:команда:статус update_id=…` |
| s4 | Опционально: не опрашивать getUpdates в `neon:tight-loop` чаще N с; или снять клавиатуру «ℹ Статус» после стопа |
| s5 | `FOR_YOU.md` / `DESKTOP_LAUNCH.md` — один канон полного стопа |

## Файлы

- `src/process_guard.py`
- `scripts/stop-radar-desktop-full.bat`
- `scripts/stop-radar.bat`
- `src/neon_legacy_consumer.py`
- `src/telegram_control.py`
- `src/bot_poll.py`

## Проверка

1. Legacy ▶ → в боте одно «Поехали» + ответ на один «Статус».
2. `stop-radar-desktop-full.vbs` → через 30 с **нет** python с `neon_legacy_consumer` / `main` / `tg_main`.
3. 2 мин в TG — **нет** новых «📊 Статус радара» без нажатия кнопки.
