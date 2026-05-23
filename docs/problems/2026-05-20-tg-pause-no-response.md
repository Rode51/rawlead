# TG: пауза «тупит» / не отвечает на команды



**Статус:** решено (2026-05-20)



## Симптом

`/pause`, `/status` — тишина или ответ через **10+ минут**. Радар иногда **не запущен**, команды копятся в `getUpdates`.



## Ожидалось

Ответ **до ~30 сек**, пауза без FL/Kwork/ИИ (`docs/ops/RUN.md` §9).



## Фактически

- `poll_commands` вызывался **раз в цикл** → между опросами `sleep(POLL_INTERVAL_MINUTES)`.

- В очереди Telegram висели `/pause`, `/status` с верным `chat_id`, пока радар не работал.



## Контекст

2026-05-20, Windows. **Lead ошибочно правил `src/`** — дальше только **Mechanic**.



## Задача Mechanic

1. **`src/main.py`:** между циклами опрос `getUpdates` **каждые ~30 сек** (не один раз на 10 мин). Проверить/допилить `_sleep_with_tg_poll` или аналог.

2. **`src/telegram_control.py`:** успешная команда → строка в `radar.log` (`tg:cmd:…`), ошибки `tg:control:…`.

3. Не ломать паузу в SQLite (`radar_paused`).



### Как проверить

1. `python src/main.py` — не закрывать.

2. `/status` → ответ **≤30 сек**.

3. `/pause` → `cycle_paused` в логе, нет `cards_fl=` 5+ мин.



---



## Решение (заполняет Mechanic)



**Статус:** решено (2026-05-20)  

**Дата:** 2026-05-20



### Причина



1. **`_sleep_with_tg_poll`** сначала делал `sleep(30)`, и только потом `getUpdates` (и не опрашивал после последнего куска) — между командами могло проходить до **~POLL_INTERVAL** без опроса.

2. Во время **`run_cycle`** (FL/Kwork, ИИ) **`poll_commands` не вызывался** — `/status` и `/pause` ждали конца цикла (минуты).



### Что сделано



- **`_TG_POLL_INTERVAL_SEC = 30`** — единый интервал опроса.

- **`_sleep_with_tg_poll`:** в цикле **сначала** `getUpdates`, затем `sleep` до следующего 30 с (пока не истечёт пауза между циклами / `POLL_INTERVAL`).

- **`_tg_poll_if_due`:** во время `run_cycle` опрос не реже чем раз в 30 с (между карточками в `_process_listings`, после fetch FL/Kwork).

- **`telegram_control.py`:** без изменений логики — успех уже пишет `tg:cmd:pause|status|resume`, сбои — `tg:control:…`; **`radar_paused` в SQLite** не трогали.



### Изменённые файлы



- `src/main.py`

- `docs/problems/2026-05-20-tg-pause-no-response.md` (этот тикет)



### Как проверить



1. Из корня репозитория: `python src/main.py` (не закрывать).

2. В Telegram боту из `.env`: **`/status`** — ответ в чат **в течение ~30 сек**; в `data/radar.log` строка вида `… tg:cmd:status`.

3. **`/pause`** — ответ «Радар на паузе…»; в логе `tg:cmd:pause` и затем `cycle_paused` (без `cards_fl=` несколько минут подряд).

4. **`/resume`** — снова циклы с `cards_fl=` / `cycle_start`; `tg:cmd:resume` в логе.


