# STATUS

Карта: **[`ROADMAP.md`](ROADMAP.md)** · владелец: **[`../FOR_YOU.md`](../FOR_YOU.md)**

---

## Сейчас

- **Карта проекта (Designer)** ✅ PNG [`design/rawlead/project-map-owner.png`](../design/rawlead/project-map-owner.png) (2026-05-24)
- **Пульт C** ✅ close/stop + логи по стрелке (2026-05-24)
- **Пульт D** ✅ ✕ без зависания — `destroy()` v2 (2026-05-24) · пересборка `rebuild-pult.bat`
- **TG карточка бота (§ E)** ✅ бюджет «по договорённости», `#id`, ссылка на пост (2026-05-24)
- **TG prompt-test (§ L)** ✅ Python в FILTERS, бюджет «по договоренности», без skip:budget (2026-05-24)
- **TG relay (§ H/M/N)** ✅ пересыл + карточка · dedup текстов · HTML-ссылки в разборе
- **Neon dedup § O** ✅ `content_hash` UNIQUE + ON CONFLICT · порядок SQLite→Neon
- **Пульт § P** ✅ лампа TG `ok` только при `ready=1` всех acc + свежий пульс
- **Пульт § R** ✅ при ▶ логи свёрнуты, без авто-разворота · `rebuild-pult.bat`
- **TG acc → /start (§ F)** ✅ auto `ensure_bot_started` при старте `tg_monitor` + `scripts/tg_bot_start.py --account all`
- **WP `/cabinet`** ⏳ в [`CODER_PROMPT.md`](CODER_PROMPT.md) § B — не сдан
- **TG unified join** ✅ · **proxy wait-loop** ✅ · **VPN** — выключать при радаре
- **WP Kadence child** ✅ (владелец + Designer 2026-05-23)
- **PRODUCT_VISION 0.4** — SaaS архитектура (Neon, API, rank) — docs 2026-05-23
- **GitHub** — push 2026-05-23
- **Волна 3** join — по лимитам

---

## Блокеры

- **Пульт «Нет связи с API»** — plugin-http IPC заблокирован; API живой, пульт не видит · Mechanic → [`2026-05-24-pult-no-api-connection.md`](../problems/2026-05-24-pult-no-api-connection.md)

- **§ I:** ✅ пульт работает (2026-05-24) · `kill_all_radar_control` не чистит системный Python — задача Mechanic открытая · [`2026-05-24-duplicate-python-processes.md`](../problems/2026-05-24-duplicate-python-processes.md)
- **§ H/M:** relay acc→бот→ты — **код § M**, ждёт приёмку владельца · [`2026-05-24-tg-forward-not-via-bot.md`](../problems/2026-05-24-tg-forward-not-via-bot.md)

---

## Приёмка WP + Design (2026-05-23)

| Проверка | Статус |
|----------|--------|
| REFERENCE E editorial light | ✅ |
| Bold type (Unbounded / Manrope) | ✅ Designer → Coder |
| Hero, поток, match %, 01·02·03, тарифы | ✅ child theme |
| Local `radarzakaz.local` | ✅ владелец |
| [`WP_KADENCE_INSTALL.md`](../ops/WP_KADENCE_INSTALL.md) | ✅ |

---

## Последний push (2026-05-23)

**Включено:** RawLead rebrand · WP `wordpress/rawlead-kadence-child/` · proxy_probe · filters/AI · docs · scripts WP install.

**Не в Git:** `.env`, `data/*.log`, sessions.

---

## Архив сессий

**TG § L (prompt-test):** `docs/ops/FILTERS.md` — python, python3, django, fastapi, flask; `budget.extract_budget_text_from_post` + `BUDGET_AGREED`; `tg_monitor` → бюджет из текста или «по договоренности»; `telegram_notify` / `ai_analyze` — единый fallback для TG. Тикет `problems/2026-05-24-tg-prompt-test-group.md`.

**TG бот: бюджет + ссылка (E):** `budget.extract_budget_text_from_post` — сумма из текста TG-поста; пусто → карточка `💰 по договорённости`; `📨 Сообщение #id`; ссылка и кнопка → `project.url` (`t.me/c/.../id`), fallback invite. FL/Kwork — «не указан» без регрессии. Тикет `problems/2026-05-24-tg-bot-budget-message-link.md`.

**TG acc → /start (F):** `scripts/tg_bot_start.py --account all`; auto ensure в `tg_main` до listen; флаг `data/.tg_bot_started_accN`. Тикет `problems/2026-05-24-tg-acc-bot-start.md`.

**TG relay § M (2026-05-24):** `tg_forward.py` — после Telethon→бот ok карточка ИИ **всегда** (`увед=1`); sync `relay_message_to_owner_chat` — 3× retry 0.75 с, при fail → `тг:relay:defer` (poll догонит). Без Telethon→бот — `увед=0`. Проверка: пульт ■→▶, пост в prompt-test → @FLPARSINGBOT: пересыл + «🤖 Разбор», лог `увед=1`.

**TG § N (2026-05-24):** dedup текста (`listing_dedup` + `listing_fingerprints`, `skip:dup_content`); карточка TG — HTML-ссылки чат (invite) + пост.

**§ O Neon dedup (2026-05-24):** `sql/001_neon_schema.sql` — `content_hash` + UNIQUE; `pg_storage.record_new_lead` → ON CONFLICT, `False` = дубль; `lead_pipeline` — hash → SQLite → Neon → `skip:dup_content`. Пустой hash — только `(source, external_id)`.

**§ P лампа TG (2026-05-24):** `status_tg_accN_ready=1` после handler + `get_me` (`tg_monitor`); сброс в `reset_tg_session_stats`; `tg_pult_lamp_state` — `ok` при всех ready + пульс ≤300с, иначе `warn` «подключение N/M».

**§ R пульт логи (2026-05-24):** `desktop/src/main.ts` — ▶ без авто-разворота; `pollStatus` не открывает логи; стрелка → `/ui-expanded`. Пересборка: `scripts\rebuild-pult.bat`.

**TG relay § H (2026-05-24, доработка):** `tg_forward.py` — Telethon `forward_messages` → @FLPARSINGBOT (8882739264), не в ЛС; `relay_message_to_owner_chat` (Bot API) → `TELEGRAM_CHAT_ID`; карточка ИИ только при успешной цепочке; `poll_commands` — резервный relay от allowlist; лог `tg:цепь` + `тг:relay:accN`. Проверка: `tg_bot_start.py --account all --force`, пульт ■→▶, пост в prompt-test → только чат @FLPARSINGBOT.

**Пульт ✕ hang (D v2):** `destroy()` + таймер 12 с; стоп без resize. **Пересборка:** `scripts\rebuild-pult.bat` (или `desktop\DEV_PULT` → tauri dev). Тикет `problems/2026-05-24-pult-close-hang.md`.

**Пульт close/stop + логи (C):** `desktop/src/main.ts` — ✕ и Alt+F4 → `POST /stop` затем close; ▶ — компактное окно, логи свёрнуты; разворот только `#btn-collapse`; `/ui-expanded` true только по стрелке. Тикет `problems/2026-05-24-pult-close-stop-logs.md`.

**Proxy wait-loop:** `src/proxy_probe.py` — бот жив при мёртвом прокси; тикет `problems/2026-05-23-proxy-exit-killed-bot.md`.

**Unified TG join:** acc1/2/3 в `tg_main`; метка acc в боте — принято 2026-05-23.

**Карта кода:** [`CODE_STRUCTURE.md`](CODE_STRUCTURE.md)
