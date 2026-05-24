# TG: acc шлёт в ЛС владельца, а не через @FLPARSINGBOT

**Дата:** 2026-05-24  
**Статус:** открыт — § H в коде, **приёмка нет** · **§ I** решено Mechanic (2026-05-24), нужна приёмка владельца + § H  
**После:** § F (`tg_bot_start.py`) — приёмка не пройдена полностью

---

## Симптом (владелец)

Acc1/2/3 пересылают посты **напрямую в личку** (как от номера acc), а не через цепочку **acc → @FLPARSINGBOT → ты в чате с ботом**.

**Уточнение владельца (2026-05-24):** у бота **нет proxy нет логики** принимать пересылки от acc — бот умеет только **отправлять карточки ИИ** (`sendMessage`) и **команды владельца** (`/pause`, кнопки). Когда acc пишет боту — **бот молчит и не пересылает**.

---

## Корневая причина (архитектура)

| Компонент | Сейчас |
|-----------|--------|
| `telegram_control.py` | `getUpdates` → только `TELEGRAM_CHAT_ID` (ты) + только **text** команд |
| acc → бот | Telethon `forward_messages` в `tg_forward.py` |
| бот → ты | `relay_forward_to_owner_chat` (sync `forwardMessage`) — **хрупко**, не «живой» приёмник |
| **Нет** | whitelist acc user_id · обработка входящих от acc в poll · auto-register нового acc |

**Целевая цепочка:**

```
Группа → acc (Telethon) → forward @FLPARSINGBOT
       → бот (getUpdates) видит msg от allowlisted user_id → forwardMessage → TELEGRAM_CHAT_ID
       → карточка ИИ (sendMessage) в тот же чат
```

---

## Факты из лога (`data/radar.log`)

| Дата | Строка | Смысл |
|------|--------|--------|
| 05-23 | `tg:forward:ValueError: Could not find the input entity for PeerUser(user_id=1342741103)` | acc **не видит бота** в Telethon — forward на numeric id падает |
| 05-24 14:17 | `acc1 chat=-5177575757 msg=61 увед=1 ош=-` | одно уведомление **без ошибки** в логе |
| 05-24 | флаги `data/.tg_bot_started_*` | **только acc1** — acc2/acc3 **нет** |
| 05-24 15:26–15:36 | `радар:старт` + `цикл:старт` **парами** (15:26:35+39, 15:28:00+01, 15:34:10+11, 15:36:55+56) | **2× main.py** — два цикла FL/Kwork |
| 05-24 15:28+ | `acc1 … msg=112/115/118 увед=1 ош=-` | карточка без `tg:цепь` / `тг:relay` в логе → **старый tg_main** или relay не дошёл |
| 05-24 | в `radar.log` **нет** строк `tg:цепь`, `acc-to-bot-v4`, `тг:relay` | код § H **не крутится** в живом процессе **или** getUpdates съедает второй процесс |

**Снимок процессов (Lead 2026-05-24):** 3× python: **2×** `src/main.py` + **1×** `tg_main.py` — норма **2** (main + tg_main).

---

## Вероятные причины

1. **`forward_messages(bot_id)` по числовому id** без `get_entity('FLPARSINGBOT')` — классика Telethon (см. ошибки PeerUser).
2. **`relay_forward_to_owner_chat` не проверяется** — в `tg_forward.py` relay может упасть, а функция всё равно `return True`; владелец видит только карточку Bot API или старое поведение.
3. **acc2/acc3** — нет `/start` (нет флага), forward блокируется или не тот acc.
4. **Путаница UX:** итог **всегда** в чате с @FLPARSINGBOT (`TELEGRAM_CHAT_ID` = твой id в личке с ботом). Заголовок пересылки может показывать **источник acc** — это не «левый» ЛС, если чат = @FLPARSINGBOT.

---

## Ожидание (Coder § H — **блокер**, после § G частично)

| # | Готово когда |
|---|----------------|
| H1 | **`data/tg_relay_allowlist.json`** (не Git): `{acc → user_id}` — **авто** при `tg_bot_start` / старте `tg_main` (`get_me` каждой сессии из `TELETHON_MONITOR_ACCOUNTS`) |
| H2 | Новый acc в `.env` → после `tg_bot_start --account accN` **сам** попадает в allowlist |
| H3 | **`telegram_control.poll_commands`**: входящие **не только от владельца** — если `from.id` в allowlist → `forwardMessage` в `TELEGRAM_CHAT_ID` (forward **и** обычные msg, не только `text`) |
| H4 | Чужие user_id — **игнор** (без пересылки) |
| H5 | `forward_listing_to_owner`: acc → бот (Telethon); relay владельцу — **через poll H3** или sync с проверкой; карточка ИИ **после** успешной пересылки оригинала |
| H6 | Лог: `тг:relay:accN:msg=…` / ошибки в `radar.log` |

**Файлы:** `src/telegram_control.py`, `src/tg_bot_start.py` (register), новый `src/tg_relay_allowlist.py` (или helper), `src/tg_forward.py`, `src/lead_pipeline.py`, `scripts/tg_main.py`, `docs/ops/TELEGRAM_ACCOUNTS.md`

---

## Ожидание (§ I — **блокер перед приёмкой § H**)

**Владелец:** весь радар **только** пульт (`start-radar-desktop.vbs` → ▶ / ■). Не `start-radar-full.bat`, не `python tg_main` из консоли.

| # | Готово когда |
|---|----------------|
| I1 | После пульт ■ — **0** python uisness (или только `radar_control.py` до ▶) |
| I2 | После ▶ — **ровно 2** процесса: `src/main.py` + `scripts/tg_main.py`, оба `.venv` |
| I3 | Повторный ▶ **не** плодит второй `main.py` (`process_guard` + `radar_control`) |
| I4 | В `radar.log` при дубле — явная строка `радар:дубль:…` (Mechanic/Coder) |
| I5 | Один consumer `getUpdates` на бота — нет гонки main vs tg_main за offset |

**Тикет дублей:** [`2026-05-24-duplicate-python-processes.md`](2026-05-24-duplicate-python-processes.md) — **решено** Mechanic.

**Кто:** **@coder** — приёмка § H после чистого § I (один main + один tg_main).

---

## Ожидание (Coder § G — частично сдано)

| # | Готово когда |
|---|----------------|
| G1 | Перед `forward_messages` — **`await client.get_entity(bot_username)`**, не только `resolve_bot_user_id()` |
| G2 | `relay_forward_to_owner_chat` — если fail → **ошибка в log**, `forward_listing_to_owner` → `False` |
| G3 | `tg_bot_start --account all` — флаги **acc1/2/3**; в логе `тг:бот_start:accN:ok` |
| G4 | Успешный пост → в чате **@FLPARSINGBOT**: переслан оригинал + карточка; **нет** отдельного чата с +66 номером |

**Файлы:** `src/tg_forward.py`, `src/tg_bot_start.py`, опционально `src/tg_monitor.py`

---

## Владелец — проверка

1. Пульт ■ → ▶ (перезапуск tg_main после фикса).
2. `.venv\Scripts\python.exe scripts/tg_bot_start.py --account all --force`
3. Тестовый пост в prompt-test **не с acc1**.
4. Смотреть **только чат @FLPARSINGBOT** — не список «Личные» от +66.

---

## Приёмка

- В `radar.log` нет `Could not find the input entity for PeerUser`
- `увед=1` → пересыл + карточка в @FLPARSINGBOT
- Три флага `.tg_bot_started_acc1/2/3`

---

## Решение § G (частично — недостаточно для приёмки)

| Критерий | Что сделано |
|----------|-------------|
| G1 | `forward_listing_to_owner`: `get_entity(@bot)` → `forward_messages` |
| G2 | `relay_forward_to_owner_chat` fail → log + `False` |
| G3 | `resolve_bot_start_accounts("all")` → acc1/2/3 |

## Решение § H (Coder 2026-05-24) — **не принято**

Код в repo есть; **в `radar.log` нет** trace `tg:цепь` / `тг:relay` → живой процесс не тот билд **или** § I мешает relay.

## Решение § I (Mechanic 2026-05-24)

См. [`2026-05-24-duplicate-python-processes.md`](2026-05-24-duplicate-python-processes.md): lock `main`, идемпотентный `/start`, `радар:дубль` в логе, wait перед spawn.

## Приёмка § H (после § I)

1. Пульт ■ → подождать 5 с → ▶ **один раз**.
2. `tg_bot_start.py --account all --force`
3. Тест в prompt-test → в `radar.log` строка с `tg:цепь:1/3` … `тг:relay:acc1:msg=…` и `увед=1`.
4. В Telegram — **только** чат @FLPARSINGBOT (оригинал + карточка).
5. В процессах — **ровно 2** python uisness (main + tg_main), без пар `радар:старт` в логе.

---
- `src/tg_forward.py`
- `src/tg_bot_start.py`
- `src/lead_pipeline.py` — карточка только после успешного forward+relay
- `scripts/tg_bot_start.py` (help `--account all`)

## Изменённые файлы (§ H)

- `src/tg_relay_allowlist.py` (новый)
- `src/telegram_control.py` — poll relay + `relay_message_to_owner_chat`
- `src/tg_forward.py` — общий relay, dedup
- `src/tg_bot_start.py` — register allowlist
- `scripts/tg_main.py` — refresh allowlist на старте, лог relay

## Диагностика (владелец: «acc шлёт в личку»)

| Вопрос | Ответ |
|--------|--------|
| `.env` `TELEGRAM_CHAT_ID=1342741103` | **Норма** — это твой user id для Bot API (чат с @FLPARSINGBOT), **не** цель Telethon |
| id бота (getMe) | `8882739264` — **другой** номер; в `.env` не путать с `TELEGRAM_CHAT_ID` |
| Старый баг в логе | `PeerUser(user_id=1342741103)` — acc пытался `forward_messages` **на тебя**, не на бота |
| Почему «увед=1» при ошибке | Карточка ИИ шла через Bot API даже если пересылка падала — исправлено: без forward нет `увед` |
| Отдельный чат +66 | Старые успешные forward на твой id **или** перезапуск tg_main не был после фикса § G |
| Внутри @FLPARSINGBOT | Заголовок «переслано от +66…» — **норма**; смотри имя чата сверху = бот |

## Как проверить

1. Пульт ■ → ▶ (перезапуск tg_main).
2. `.venv\Scripts\python.exe scripts/tg_bot_start.py --account all --force`
3. Убедиться: `data/.tg_bot_started_acc1`, `_acc2`, `_acc3`.
4. Тестовый пост в prompt-test **не с acc1**.
5. В `data/radar.log`: нет `PeerUser`; при `увед=1` — пересыл + карточка в чате @FLPARSINGBOT.

---

## Диагностика § M (2026-05-24) — пересыл есть, разбор ИИ нет

**Симптом:** в @FLPARSINGBOT приходит **пересланный пост**, но **нет карточки** с блоком «🤖 Разбор».

**Лог (`data/radar.log`, prompt-test msg=134/136):**

```
увед=0 … tg:цепь:2/3 telethon→бот ok …
тг:relay:forwardMessage HTTP 400 … message to forward not found … тг:relay:acc1:fail msg=135
(+2 с) tg:цепь:acc=acc1 BotAPI forwardMessage … msg_id=431 … тг:relay:acc1:msg=431
```

| Шаг | Что происходит |
|-----|----------------|
| Telethon acc→бот | ✅ ok |
| Sync `forwardMessage` сразу после Telethon | ❌ 400 — бот ещё не видит msg (id Telethon ≠ id Bot API / гонка) |
| `forward_listing_to_owner` → `False` | ❌ **`send_listing_notification` не вызывается** → нет карточки ИИ |
| Poll через ~2 с | ✅ relay `msg_id=431` — владелец видит **только пересыл** |

**Корень:** § H завязал `увед=1` на **sync relay**; poll догоняет пересыл, но карточка уже заблокирована.

**Ожидание (Coder § M):**

| # | Готово когда |
|---|--------------|
| M1 | После Telethon→бот ok — **карточка ИИ уходит** (`увед=1`), даже если sync relay ждёт poll |
| M2 | Sync relay: retry 2–3× с паузой 0.5–1 с **или** id из getUpdates, не слепой `fwd_msg.id` |
| M3 | В логе при успехе: `увед=1` + `тг:relay:accN:msg=…` (sync или poll) + карточка с «🤖 Разбор» |
| M4 | Нет регрессии: без Telethon→бот — по-прежнему `увед=0` |

**Файлы:** `src/tg_forward.py`, `src/lead_pipeline.py` (при необходимости), `src/telegram_control.py`

**Тикет:** этот файл § M · промпт: `docs/team/CODER_PROMPT.md` § M
