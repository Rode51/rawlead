# Для тебя

## Cursor — прокси на ПК (2026-06-09)

**Зачем:** из РФ без прокси Cursor/модели часто дают region error. Прокси **только для Cursor на твоём ПК** — VPS и сайт работают сами.

### Как у нас устроено (простыми словами)

| Часть | Что делает |
|-------|------------|
| **`.env`** | `CURSOR_PROXY_ENABLED=1` — прокси включён · `CURSOR_PROXY_RELAY=1` — режим **relay** |
| **Relay** | Маленькая программа на ПК: Cursor ходит на `127.0.0.1:18777`, relay сам выбирает живой IP из пула |
| **Автосмена** | `CURSOR_PROXY_AUTO_FALLBACK=1` — перед включением проверяет TCP · relay каждые ~1 мин перепроверяет пул |
| **Если все мертвы** | `CURSOR_PROXY_DISABLE_IF_DEAD=1` — скрипт **выключает** прокси в Cursor (чтобы IDE не висел) |

**Сейчас на ПК:** Cursor → `http://127.0.0.1:18777` (relay). Пул из 5 IP в `CURSOR_PROXY_POOL_URLS` — relay берёт **первый живой** (часто один, остальные могут быть down — это норм, relay переключится).

---

### Быстрые команды (из корня `uisness`)

| Что нужно | Команда |
|-----------|---------|
| **Включить прокси + найти живой IP** | Двойной клик `scripts\cursor-proxy-recovery.bat` |
| **То же (короткий путь)** | `scripts\sync-cursor-proxy.bat` |
| **Только проверить, кто жив** | `.venv\Scripts\python.exe scripts\sync_cursor_proxy.py --probe-only` |
| **Проверить пул relay (5 IP)** | `.venv\Scripts\python.exe scripts\cursor_proxy_relay.py --probe-only` |
| **Выключить прокси в Cursor** | `.venv\Scripts\python.exe scripts\sync_cursor_proxy.py --off` |
| **Запустить/перезапустить relay** | Двойной клик `scripts\start-cursor-proxy-relay.bat` — **окно не закрывай** (можно свернуть) |

После **первого** включения relay или смены режима: **полностью выйди из Cursor** (File → Quit / Закрыть из трея), открой снова.  
При работе relay **перезапуск Cursor не нужен** — IP меняется сам.

---

### Пошагово: включить прокси обратно

1. Открой PowerShell или cmd в папке `uisness`.
2. Запусти: `scripts\start-cursor-proxy-relay.bat`  
   — должно появиться окно relay (или проверь, что порт `18777` слушается).
3. Запусти: `scripts\cursor-proxy-recovery.bat`  
   — в выводе ищи строку `OK` у одного из IP (не обязательно первый).
4. **Quit Cursor** полностью → открой снова.
5. Проверка: новый чат, любая модель — нет «region» / «not available in your region».

**Лог relay** (если что-то ломается): `data\cursor_proxy_relay.log` — там видно, на какой IP переключился и ошибки к `api2.cursor.sh`.

---

### Пошагово: временно **без** прокси

Когда нужно: отладка «это прокси или Cursor», или все IP мертвы и хочешь попробовать direct.

1. `.venv\Scripts\python.exe scripts\sync_cursor_proxy.py --off`
2. Quit Cursor → открой снова.
3. Окно relay можно закрыть.

Вернуть прокси — снова § «включить прокси обратно».

---

### Если «поломалось» — чеклист

| Симптом | Что сделать |
|---------|-------------|
| Region error / модели не грузятся | `cursor-proxy-recovery.bat` → relay запущен? → Quit Cursor |
| Скрипт пишет «все прокси недоступны → ВЫКЛЮЧЕН» | 4 из 5 IP могут быть down — relay всё равно работает, если **хотя бы один OK** в `--probe-only` |
| Cursor висит на запросах | Закрой relay, `--off`, Quit Cursor, снова recovery |
| Менял `.env` (новый IP) | Перезапусти relay (`start-cursor-proxy-relay.bat`) + `cursor-proxy-recovery.bat` |
| Не уверен, через прокси ли сейчас | `%APPDATA%\Cursor\User\settings.json` → `http.proxy` должен быть `http://127.0.0.1:18777` при relay |

**Не путать:** прокси Cursor **≠** прокси VPS (биржи/TG). Биржи на сервере — отдельные `EXCHANGE_*` / `/ops/`.

---

## Сейчас — stability ingest (2026-06-12)

| Шаг | Что |
|-----|-----|
| **YouDo ✅** | **O190** ingest на VPS · subprocess worker · `health:youdo ok` · **O191** — DC+RU прокси (Coder) |
| **Pay ✅** | Trial 1 ₽ smoke · prod **790 ₽** |
| **TG ⏳** | O188 wave4 join **~28/127** · acc1/2/3 только на VPS |
| **Дальше** | O191 → O193 FL subprocess · O186 security · **реклама ⏸** |

Детали: [`STATUS.md`](team/common/STATUS.md) · [`PRODUCT_CANON.md`](team/product/PRODUCT_CANON.md)

---

## Prod + O161 ops (фон)

| Шаг | Что |
|-----|-----|
| 1 | **O160 ingest** ✅ — радар с watchdog на VPS |
| 2 | **O161 `/ops/`** ✅ — пароль, лайв-лог, статусы бирж · https://rawlead.ru/ops/ |
| 3 | **Ingest 24h smoke** — смотреть, что лента не замирает >15 мин |
| 4 | **Perf @50** — после smoke |

**Пароль пульта:** `RAWLEAD_OPS_KEY` или `OPS_PASSWORD` в `.env` на VPS (не в git).

**Аккаунты FL/Kwork для ТЗ (O133):** `FL_TZ_EMAIL` / `KWORK_TZ_EMAIL` в локальном `.env` ✅ · на VPS — добавить в `/opt/rawlead/.env` когда Coder подключит downloader.

---

## L1 и очередь без разбора

| Что | Действие |
|-----|----------|
| Свежие без L1 (48 ч) | На VPS: `L1_BACKLOG_DRAIN=1` в `.env.site` — пачка L1 каждый цикл |
| Старый хвост (лишний OpenRouter) | `scripts/clear_l1_backlog.py --profile site --by-age --days-old 2 --apply` (сначала `--dry-run`) |
| Проверка | `/status` → «Без L1 (48 ч)»; лог `конвейер:L1=` |

---

## TG acc2 и join

- **Слушает** только чаты из `data/telethon_chat_ids_acc2.txt` (после join).
- **Волна 4 (2026-06-12):** 127 чатов подготовлены Lead → [`TG_JOIN_QUEUE_v3.csv`](docs/ops/TG_JOIN_QUEUE_v3.csv) · **@coder ещё не давали** · сейчас идёт **v2 backlog** acc3 (~4 join/час) · логи: `data/tg_join.log` на VPS
- **`TG_JOIN_IN_TG_MAIN=1`** обязателен на VPS (иначе join не крутится в radar).
- Старые ~25 чатов из `TG_JOIN_QUEUE.csv` — отдельно: `tg_sync_chat_ids.py --account acc2`.

---

## YouDo / O63 secondary (2026-06-03)

| source | Статус |
|--------|--------|
| **Freelance.ru** | ✅ **25 новых** на VPS после O63-FIX deploy — идут в L1 |
| **FreelanceJob** | ✅ 40 скачано · filter 6 — ожидаемо, см. `FILTERS_SITE.md` |
| **YouDo** | ✅ **node-proxy RU** (3 слота) · smoke **50 задач** · radar 24/7 · фикс: Chrome UA + antibot `noscript` + ephemeral browser |
| **Пчёл** | парсер ок · на листинге часто 0 новых (floor/dup) |

Deploy: `scripts/deploy-youdo-browser-vps.py` · диагностика: `scripts/_diag_secondary_logs_vps.py` → `data/_diag_secondary_logs.txt`.

---

## Gate (простыми словами)

- **Complexity L1:** 1 вечер · 2 проект · 3 система · **4 без норм ТЗ**
- **Judge:** насколько L1 угадал — **≥70% ok** или avg **≥3** из 4
- **L1 usable:** как O72e — **≥70%**

---

---

## Два бота (не путать)

| Бот | Зачем | Что приходит в ЛС |
|-----|--------|-------------------|
| **@FLPARSINGBOT** | Админ / dogfood | Карточки бирж под твои фильтры; **прокси** (бан, переключение, «осталось N/M»); `/status` с биржами и Neon consumer |
| **@rawlead_bot** | Продукт | Match подписчикам; **не** служебные алерты парсера |

**Прокси:** пуши только в чат **@FLPARSINGBOT** (не @rawlead_bot). Если видишь «FLPARSING · прокси» в чате RawLead — на VPS в `.env.legacy` был чужой токен; код теперь проверяет getMe. Проверка: `python scripts/verify-vps-bot-identity.py` → legacy=@FLPARSINGBOT, site=@rawlead_bot.

**TG Bot API failover (O120):** пул из `TG_PROXY_URL` + `TELETHON_PROXY_ACC1/2/3` (или явный `TG_PROXY_URLS`). При смерти слота бот сам переключается — **не нужно** править `.env`. В @FLPARSINGBOT придёт **`FLPARSING · TG Bot API прокси`**: какой слот забанен, причина (таймаут/прокси), на какой переключились, «свободно N из M». Опц. `TG_PROXY_DIRECT=1` — последний fallback direct с VPS. Состояние: `data/tg_proxy_pool.json`.

**Проверка:** `/status` в @FLPARSINGBOT → блоки FL (primary) и secondary.

## Биржи: датчики O104 ✅ на VPS

| Куда | Что |
|------|-----|
| **@FLPARSINGBOT** `/status` | 🟢🟡🔴 по каждой бирже + причина |
| **@FLPARSINGBOT** push | `🔴 YouDo · …` — max раз в 30 мин |
| **`/ops/`** | «Биржи и скорость» · lag минуты |
| **`radar_site.log`** | `health:youdo status=ok` |

**Regen/judge в консоли не ломает:** O104 на VPS (SQLite + log); regen/judge — Neon `reply_draft`, отдельный процесс.

## O99 ingest — **включено на VPS** (2026-06-03)

1. **FL/Kwork** — браузерный fetch + fallback httpx (`EXCHANGE_LISTING_BROWSER=1`).
2. **Лента** — только после L1; hot drain после FL/Kwork, до secondary.
3. **Secondary** — каждый 2-й цикл; свои прокси, не банят primary.
4. **L1:** 4 воркера, два OpenRouter-ключа (см. `.env.site`).
5. **Отдельно:** regen **текстов отклика** (`regen_shared_reply_drafts.py`) — **не** ingest; идёт в другом чате.

Канон: [`KAK_ETO_RABOTAET.md`](KAK_ETO_RABOTAET.md) · [`STATUS.md`](team/common/STATUS.md).

---

_Lead · 2026-06-12_
