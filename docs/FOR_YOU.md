# Для тебя

## Сейчас (2026-06-19)

| Что | Статус |
|-----|--------|
| **rawlead.ru** | ✅ **Next.js** на prod (`rawlead-next/out`) · не WP |
| **Локально** | `cd rawlead-next && npm run dev` → `:3001` |
| **Вход / лента** | аватар ✅ · **черновик ИИ** — мёртвый OpenRouter proxy → mechanic P0 |
| **Portfolio** | ✅ **https://rode51.ru** (P289) · код `portfolio/` · Lead: `@lead-portfolio` |
| **БД prod** | local Postgres (O271) · Neon только архив · O272 guard |
| **YouDo** | 🟡 camoufox · ops restart в `/ops/` |
| **→ smoke** | Ctrl+Shift+R → лента без счётчика → перелогин → фото · **админка:** https://rawlead.ru/ops/ (кнопка в header — после R10) |

**Prod snapshot:** [`team/common/PROD_FACTS.md`](team/common/PROD_FACTS.md) · **задачи:** [`team/common/TASKS.md`](team/common/TASKS.md)

**Кнопка restart:** `https://rawlead.ru/ops/` в **Chrome/YaBrowser** (не Cursor) → **Ctrl+Shift+R** → Биржи → YouDo → «Перезапустить источник» → toast «YouDo: сброс…». Тишина — напиши Lead.

**YouDo ingest отдельно:** даже ручной restart радара даёт `Connection closed` — это camoufox, не кнопка. Работает **@mechanic**.

---

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

## Claude Code — прокси + установка (2026-06-17)

**Тот же relay**, что Cursor: `127.0.0.1:18777` → пул из `.env`.

| Что | Команда |
|-----|---------|
| **Установить Claude Code через прокси** | Двойной клик `scripts\install-claude-code-via-proxy.bat` |
| **Прописать proxy навсегда** (Claude + npm) | `scripts\sync-claude-code-proxy.bat` |
| **Recovery** (probe + sync) | `scripts\claude-code-proxy-recovery.bat` |
| **Relay** (если не запущен) | `scripts\start-cursor-proxy-relay.bat` |
| **Ярлык на рабочем столе** | **`Claude START.lnk`** — relay + login с нуля · **`Claude Relay.lnk`** · **`Claude Code.lnk`** · **`Claude — вставить код.lnk`** |
| **Выключить proxy Claude Code** | `.venv\Scripts\python.exe scripts\sync_claude_code_proxy.py --off --npm` |
| **OAuth не проходит (403)** | **`scripts\claude-import-subscription.bat`** (подписка) · или `claude-auth-api-key.bat` (API key) |
| **Подписка, VPN только Dolphin** | § **Claude Code — подписка без VPN на ПК** ниже |
| **Диагностика tunnel** | `.venv\Scripts\python.exe scripts\probe_anthropic_relay.py` |

**Постоянный конфиг:** `%USERPROFILE%\.claude\settings.json` → `env.HTTP_PROXY` / `HTTPS_PROXY`.

**Ошибки (коротко):**

| Симптом | Что значит | Действие |
|---------|------------|----------|
| `CONNECT … 502` | relay жив, upstream proxy мёртв | `claude-code-proxy-recovery.bat` · пополни pool в `.env` |
| `HTTP 403` на probe | **норма** — api отвечает без ключа | продолжай login |
| `Login failed … 403` | OAuth exchange блокируется прокси | **`claude-import-subscription.bat`** — токен с другой сети |
| `Invalid code` | код одноразовый / другая сессия login | новый `claude auth login`, не перезапускай окно |
| `ECONNREFUSED` | relay не слушает 18777 | `start-cursor-proxy-relay.bat`, окно не закрывать |

**Порядок работы (OAuth):**
1. `start-cursor-proxy-relay.bat` — окно не закрывать
2. `install-claude-code-via-proxy.bat` — один раз
3. `claude auth login` — если ещё не залогинен
4. `claude` из нужной папки проекта

**Порядок работы (API key — если OAuth 403):**
1. relay как выше
2. `scripts\claude-auth-api-key.bat`
3. `claude` → approve key при первом запуске

### Claude Code — подписка без VPN на ПК (2026-06-17)

**Cursor не поможет:** логин Cursor ≠ логин Claude Code CLI. Через консоль Cursor авторизовать Claude Code нельзя.

**Почему Dolphin + login на этом ПК часто 403:** браузер в Dolphin ходит через прокси профиля, а CLI меняет код на токен через relay — Anthropic режет этот обмен с datacenter IP.

**Рабочий план для подписки Pro/Max:**

| Шаг | Где | Действие |
|-----|-----|----------|
| 1 | **Другая сеть** (мобильный интернет с телефона, друг, кафе) | `npm i -g @anthropic-ai/claude-code` → `claude setup-token` → логин в обычном браузере → **скопировать токен** |
| 2 | **Этот ПК** | `start-cursor-proxy-relay.bat` (окно не закрывать) |
| 3 | **Этот ПК** | `scripts\claude-import-subscription.bat` — вставить токен |
| 4 | **Этот ПК** | `claude` |

Токен живёт ~1 год · биллинг по **подписке**, не по API key.

---

## O220 — на prod ✅ (deploy 2026-06-14)

**Theme 1.19.00** · match + лента UX · API перезапущен.

| Шаг | Действие |
|-----|----------|
| **Smoke** | Ctrl+F5 `/lenta/` · Monica wipe → квиз → % на «своих» заказах |
| **L1 pilot** | Coder ✅ · **ты:** `--dry-run` → `--apply` → judge (см. ниже) |

---

## Сейчас — ingest (2026-06-15)

| Шаг | Что |
|-----|-----|
| **FL 🔴** | Нестабильно: `parsed=0` ↔ 30 · `pool_exhausted` · **O222** в `@coder` · Lead сбросил баны прокси |
| **Kwork 🟡** | `parsed=36 fresh=0` — парсер жив, **новых нет** (не «упал») |
| **YouDo 🟢** | `parsed=50` · но L1 путает перевозки с WordPress → **O223** |
| **TG 🟢** | acc1–3 connected |
| **Если FL снова 🔴** | `python scripts\clear-vps-proxy-bans.py` → подожди 5 мин → `/ops/` или `/status` в @FLPARSINGBOT |
| **Дальше** | **O222** deploy → **O223** → tier smoke → O218 → ads ⏸ |

Тикет: [`2026-06-15-parsers-fl-unstable.md`](problems/2026-06-15-parsers-fl-unstable.md)

**Нюанс:** цикл с полным YouDo-fetch (50 карточек + detail + L1) занимает **~6–10 мин** — это нормально, не «завис».

Детали: [`STATUS.md`](team/common/STATUS.md) · [`PRODUCT_CANON.md`](team/product/PRODUCT_CANON.md)

---

## Prod + O161 ops (фон)

| Шаг | Что |
|-----|-----|
| 1 | **O160 ingest** ✅ — радар с watchdog на VPS |
| 2 | **O161 `/ops/`** ✅ — пароль, лайв-лог, статусы бирж · https://rawlead.ru/ops/ |
| 3 | **Ingest 24h smoke** — смотреть, что лента не замирает >15 мин |
| 4 | **Perf @50** — после smoke |

**Пароль пульта:** `RAWLEAD_OPS_KEY` (или `OPS_PASSWORD`) в `/opt/rawlead/.env.site` на VPS · вход на https://rawlead.ru/ops/ · кнопка «Админка» в шапке · опционально `OPS_PASSWORD_HASH` (bcrypt).

**Аккаунты FL/Kwork для ТЗ (O133):** `FL_TZ_EMAIL` / `KWORK_TZ_EMAIL` в локальном `.env` ✅ · на VPS — добавить в `/opt/rawlead/.env` когда Coder подключит downloader.

---

## L1 и очередь без разбора

| Что | Действие |
|-----|----------|
| Свежие без L1 (48 ч) | На VPS: `L1_BACKLOG_DRAIN=1` в `.env.site` — пачка L1 каждый цикл |
| Старый хвост (лишний OpenRouter) | `scripts/clear_l1_backlog.py --profile site --by-age --days-old 2 --apply` (сначала `--dry-run`) |
| Проверка | `/status` → «Без L1 (48 ч)»; лог `конвейер:L1=` |

---

## TG join — волна 5 (2026-06-15)

| Что | Действие |
|-----|----------|
| **База** | ✅ `docs/ops/import/TG_FREELANCE_*.xlsx` (Lead copied 2026-06-15) |
| **Стратегия** | **> 5000 участников** (col B) · **305** net-new · ~**2 дня** join |
| **Фильтр** | Строго `Участники > 5000` · чаты **150** + каналы **179** = **329** проходят |
| **Импорт** | `@coder` § **O248-TG-WAVE5-IMPORT** |
| **Радар** | VPS: `TG_JOIN_IN_TG_MAIN=1` · лог `data/tg_join.log` |
| **Срок** | ~**2 дня** на **305** чатов/каналов (>5k участников) |
| **O247 toolbar** | § **O247b** — «осталось N откликов» (API deploy) |

Старый блок v2/v3 — ниже.

## TG acc2 и join (legacy note)

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

**FL tier-2 (2026-06-14):** в `/opt/rawlead/.env.site` — `FL_PROXY_URLS` (4 DC) + **`FL_PROXY_URLS_RESIDENTIAL`** (25 RU слотов из хвоста YouDo) ✅ Lead 2026-06-14. Патч повторно: `scripts/patch-vps-fl-residential-env.py`.

**Smoke O215 (сайт):** theme **1.19.12** · см. **чеклист tier smoke** ниже · **Canvas:** [tier-smoke-checklist](file:///C:/Users/hramo/.cursor/projects/c-Users-hramo-uisness/canvases/tier-smoke-checklist.canvas.tsx) (OK/FAIL + комментарии, сохраняется).

---

## Tier smoke — полный чеклист (все уровни доступа)

**Зачем:** после O215 убедиться, что UI/copy/гейты работают на **anon · trial · expired · premium · owner** (пауза подписки **снята с prod**).

**Prod billing (2026-06-15):** **обычная оплата** ЮKassa на `/pricing/` ✅ · **автооплата / auto-renew** убрана — в smoke **не** проверять.

**Тестовые аккаунты**

| Роль | Как |
|------|-----|
| **Anon** | Incognito · `https://rawlead.ru/lenta/` без входа |
| **First login / Trial** | **Monica Bates** (TG **8688264540**) — полный wipe в Neon (см. ниже) → auto trial 3 дня (**O219 ✅ prod**) · match/квиз — **O220 после deploy** |
| **Expired trial** | После Monica trial: `@lead-architect` или скрипт — `trial_used_at=now()`, `plan=free`, `active_until=null` |
| **Premium** | Твой owner TG **или** разовая оплата ЮKassa на `/pricing/` |
| ~~Paused premium~~ | **SKIP** — пауза подписки снята с prod |
| **Owner/beta** | Owner TG (`TELEGRAM_CHAT_ID`) |

**Перед каждым сценарием:** hard refresh или incognito · смотреть **desktop + mobile 390px**.

### 1. Anon (без JWT)

| # | Страница | Проверить |
|---|----------|-----------|
| A1 | `/lenta/` | flat лента · strip «~30 мин» · **нет** match-sort · **нет** черновиков |
| A2 | `/lenta/` карточка | match % / copy O215 · CTA «квиз / войти» |
| A3 | `/quiz/` | flow с нуля · кнопки «Да, близко» / «Не моё» |
| A4 | `/` home | hero · tier preview · pricing teaser |
| A5 | `/pricing/` | 790 ₽ · trial copy «3 дня бесплатно» |
| A6 | `/cabinet/` | редирект / gate anon |

### 2. Trial (Monica — первый вход после сброса)

| # | Проверить |
|---|-----------|
| T1 | TG-login → `plan=trial` · badge «Trial · N дн.» в ЛК/ленте |
| T2 | `/lenta/` **без** 30-мин задержки · персональная сортировка / match |
| T3 | Карточка → **черновик** (лимит **5/ч**) |
| T4 | `/quiz/` дополняет профиль · влияет на match |
| T5 | Push TG (если включены) — только paid/trial |

### 3. Expired trial (Monica после использования trial)

| # | Проверить |
|---|-----------|
| E1 | **Обязательный баннер** на `/lenta/` + `/cabinet/` (не dismiss) |
| E2 | Лента снова **flat + 30 мин** delay |
| E3 | Черновики **заблокированы** · inbox старый сохраняется |
| E4 | `/pricing/` CTA «Продлить» |

### 4. Premium (agent/pro, active)

| # | Проверить |
|---|-----------|
| P1 | Instant лента · match rank · filter bar (если включён) |
| P2 | Черновики 5/ч · generate OK |
| P3 | `/cabinet/` inbox · **разовая оплата** через `/pricing/` OK · **без** auto-renew UI |
| P4 | **SKIP** — пауза подписки снята |

### 5. Paused premium — **SKIP** (фича снята)

| # | Проверить |
|---|-----------|
| S1–S3 | Не актуально · owner 2026-06-15 |

### 6. Owner

| # | Проверить |
|---|-----------|
| O1 | Полный доступ без paywall |
| O2 | `/ops/` только owner |

### 7. Cross-cutting

| # | Проверить |
|---|-----------|
| X1 | Лексикон: **совпадение** · нет Tinder/«добавь навыки» |
| X2 | Theme **1.19.12** в view-source (query `ver=`) |
| X3 | API `/v1/quiz/start` 200 · `/v1/feed` delay по tier |
| X4 | TG bot `/status` · `/ops/` cycle_age зелёный |

**Monica — полный wipe (перед тестом auto-trial):** tg **8688264540** · `@lead-architect` / `@mechanic` — удалить из Neon (users, user_tags, subscriptions, auth_bot_sessions). **✅ wipe 2026-06-15** (user_id пересоздаётся при входе — не кэшировать старый id). После wipe — выйти из TG на сайте, incognito, войти снова как Monica → `plan=trial` · badge «Trial · 3 дн.».

**Удобнее:** открой Canvas [tier-smoke-checklist](file:///C:/Users/hramo/.cursor/projects/c-Users-hramo-uisness/canvases/tier-smoke-checklist.canvas.tsx) рядом с чатом — все 7 секций · галочки · FAIL-комментарии сохраняются.

**Симуляция expired trial (Monica):** после прохода trial — `@lead-architect` выставит `trial_used_at` + `plan=free`.

---

## Яндекс.Метрика — пошагово (2026-06-16)

**Counter ID:** `109860210` · **на prod уже стоит** (theme **1.19.20**, `/lenta/` → view-source → `ym(109860210)`).

**Тебе в интерфейсе Метрики** — создать цели и проверить воронку. Код сайта `reachGoal` уже шлёт события; без целей в UI отчёты пустые.

### Шаг 0 — браузер

- **YaBrowser или Chrome**, **AdBlock выключен** на rawlead.ru (иначе счётчик не грузится).
- **Не** проверяй в Cursor-browser — там часто режутся трекеры.
- `/ops/` и localhost — счётчик **намеренно выключен**.

**YaBrowser и нет `mc.yandex` в Network:**  
1. В Network фильтр **All** (не только Fetch/XHR) — `tag.js` идёт как **JS**.  
2. Если есть только `tag.js`, но **нет** `watch/` / `webvisor` — часто **заблокированы cookie** → визит не пишется, «онлайн» = 0.  
   Проверка в Console: `ym(109860210,'getClientID',id=>console.log(id))` — если пусто/timeout, это оно.  
   **Лечение:** Настройки → **Сайты → Cookie** → разрешить **сторонние cookie** (или исключение для rawlead.ru) → Ctrl+F5.  
3. Нейропротект «нет заблокированных трекеров» ≠ cookie разрешены — смотри п.2.

**Debug YaBrowser для Cursor MCP:** `scripts\start-yandex-debug.bat` → порт **9222** → см. `MCP_POOL.md` § Chrome DevTools MCP.

### Шаг 1 — счётчик жив?

1. [metrika.yandex.ru](https://metrika.yandex.ru/) → счётчик **109860210**.
2. Вкладка **«Посетители онлайн»** (или «Сейчас на сайте»).
3. В **другой вкладке** открой [rawlead.ru/lenta/](https://rawlead.ru/lenta/) → Ctrl+F5.
4. Через 10–30 сек в онлайне должен появиться **1 посетитель**. Нет — повтори без блокировщиков; проверь view-source: строка `ym(109860210`.

### Шаг 2 — три цели (обязательно)

**Настройки → Цели → Добавить цель** — тип **«JavaScript-событие»**, идентификатор **точно** как в таблице (регистр важен):

| Цель в UI (название любое) | Идентификатор | Когда срабатывает на сайте |
|----------------------------|---------------|----------------------------|
| Quiz complete | `rl_quiz_complete` | Дошёл до конца квиза (overlay на `/lenta/` или `/quiz/`) |
| Trial login | `rl_trial_login` | Первый вход в сессии с планом **trial** (TG-логин в кабинет) |
| Checkout start | `rl_checkout_start` | Клик «Оплатить» / старт checkout (тарифы или кабинет) |

Для каждой: условие — **совпадение идентификатора** (не URL, не клик по кнопке).

### Шаг 3 — smoke целей (15 мин)

| # | Действие | Ожидание |
|---|----------|----------|
| 1 | `/lenta/` → «Настроить ленту» → пройди квиз до финала | В Метрике → **Отчёты → Цели** → `rl_quiz_complete` (задержка до ~5 мин) |
| 2 | Incognito → TG-вход **новым** trial-пользователем (не Monica после wipe без trial) | `rl_trial_login` **1 раз за сессию** |
| 3 | Тарифы или кабинет → кнопка оплаты / checkout | `rl_checkout_start` |

**Быстрая проверка в DevTools (F12 → Console):** после загрузки `/lenta/` набери `typeof ym` → должно быть `"function"`. После квиза — без ошибок в консоли.

### Шаг 4 — что уже включено в коде (трогать не нужно)

webvisor · clickmap · trackLinks · accurateTrackBounce · ecommerce `dataLayer` (покупки в dataLayer — **позже**, когда подключим ecommerce-события).

### Шаг 5 — перед рекламой (позже)

- **O73:** карта кликов / heatmap — уже есть clickmap + webvisor.
- **Фильтр своих визитов:** в Метрике → **Настройки → Фильтры** → исключить свой IP **или** ждать O237b (opt-out owner/Monica в коде — в бэклоге).
- **Ads ⏸** до стабильных целей + L2 smoke (см. `TASKS.md`).

**Snippet в WP вручную не вставлять** — всё в теме `inc/yandex-metrika.php`.

---

**Удобнее:** Canvas [O207 TG labeling](file:///C:/Users/hramo/.cursor/projects/c-Users-hramo-uisness/canvases/o207-tg-labeling.canvas.tsx) — **выборка уже загружена** (120 постов acc1). Открой canvas → жми Заказ/Шум/Неясно.

**Важно:** команды ниже — только **SSH на VPS**, не вставлять в Canvas и не в PowerShell на ПК одной строкой.

Файл на ПК (если нужен): `data/tg_history_sample.json`

```bash
cd /opt/rawlead
.venv/bin/python scripts/tg_history_sample.py --account acc1 --max-chats 15 --per-chat 10
cp data/tg_history_sample.json data/tg_history_sample_labeled.json
# в labeled.json у каждой строки в rows[]: "owner_label": "vacancy" | "noise" | "unsure"
.venv/bin/python scripts/tg_filter_replay.py --in data/tg_history_sample_labeled.json
```

Baseline из лога (уже есть после deploy): `data/tg_funnel_audit_human.md` на VPS.  
Детали: [`docs/problems/2026-06-13-tg-feed-volume.md`](problems/2026-06-13-tg-feed-volume.md) § Owner labeling.

**Regen/judge в консоли не ломает:** O104 на VPS (SQLite + log); regen/judge — Neon `reply_draft`, отдельный процесс.

## O99 ingest — **включено на VPS** (2026-06-03)

1. **FL/Kwork** — браузерный fetch + fallback httpx (`EXCHANGE_LISTING_BROWSER=1`).
2. **Лента** — только после L1; hot drain после FL/Kwork, до secondary.
3. **Secondary** — каждый 2-й цикл; свои прокси, не банят primary.
4. **L1:** 4 воркера, два OpenRouter-ключа (см. `.env.site`).
5. **Отдельно:** regen **текстов отклика** (`regen_shared_reply_drafts.py`) — **не** ingest; идёт в другом чате.

Канон: [`KAK_ETO_RABOTAET.md`](KAK_ETO_RABOTAET.md) · [`STATUS.md`](team/common/STATUS.md).

---

## MiMo Code — пробный аудит репо (backlog)

**Что:** [MiMo Code](https://github.com/XiaomiMiMo/MiMo-Code) от Xiaomi — terminal-агент (как Claude Code), бесплатный канал MiMo-V2.5 на время. Запись от **12.06** — канон `OWNER_INTENT` § **MIMO-AUDIT**.

**Зачем:** второй «широкий» аудит (парсеры, ИИ, Next) — альтернатива прогону на Gemini 2M (O38).

**Когда:** после **O280 cutover** или на **копии** репо параллельно.

**Безопасно:** копия **без** `.env` и сессий · MiMo Auto = код уходит на Xiaomi · или Custom Provider → OpenRouter.

**Windows:** `npm install -g @mimo-ai/cli` · промпт старта — в `OWNER_INTENT` § MIMO-AUDIT · итог → `docs/problems/…-mimo-audit.md`.

**Посты завышают:** не «∞ контекст», а ~1M tokens; v0.1.x сырая; бенчмарки — от Xiaomi.

---

_Lead · 2026-06-12_
