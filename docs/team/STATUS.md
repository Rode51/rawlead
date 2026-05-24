# STATUS

Карта: **[`ROADMAP.md`](ROADMAP.md)** · владелец: **[`../FOR_YOU.md`](../FOR_YOU.md)**

---

## Сейчас

- **Карта проекта (Designer)** ✅ PNG [`design/rawlead/project-map-owner.png`](../design/rawlead/project-map-owner.png) (2026-05-24)
- **Пульт C** ✅ close/stop + логи по стрелке (2026-05-24)
- **Пульт D** ✅ ✕ без зависания — `destroy()` v2 (2026-05-24) · пересборка `rebuild-pult.bat`
- **TG карточка бота (§ E)** ✅ бюджет «по договорённости», `#id`, ссылка на пост (2026-05-24)
- **TG relay (§ H)** ⚠️ код в repo, **приёмка нет** — в логе нет `tg:цепь` · **2× main.py** § I · [`2026-05-24-tg-forward-not-via-bot.md`](../problems/2026-05-24-tg-forward-not-via-bot.md)
- **TG acc → /start (§ F)** ⚠️ частично · [`2026-05-24-tg-acc-bot-start.md`](../problems/2026-05-24-tg-acc-bot-start.md)
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
- **§ H:** relay в ЛС — после § I · [`2026-05-24-tg-forward-not-via-bot.md`](../problems/2026-05-24-tg-forward-not-via-bot.md) → **@coder**

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

**TG бот: бюджет + ссылка (E):** `budget.extract_budget_text_from_post` — сумма из текста TG-поста; пусто → карточка `💰 по договорённости`; `📨 Сообщение #id`; ссылка и кнопка → `project.url` (`t.me/c/.../id`), fallback invite. FL/Kwork — «не указан» без регрессии. Тикет `problems/2026-05-24-tg-bot-budget-message-link.md`.

**TG acc → /start (F):** `scripts/tg_bot_start.py --account all`; auto ensure в `tg_main` до listen; флаг `data/.tg_bot_started_accN`. Тикет `problems/2026-05-24-tg-acc-bot-start.md`.

**TG relay § H (2026-05-24):** `data/tg_relay_allowlist.json` + `poll_commands` (allowlisted `from.id`) + sync relay после Telethon forward; dedup; лог `тг:relay:accN`. Проверка: `tg_bot_start.py --account all --force`, пульт ■→▶, пост в prompt-test не с acc1, только чат @FLPARSINGBOT. Тикет `problems/2026-05-24-tg-forward-not-via-bot.md`.

**Пульт ✕ hang (D v2):** `destroy()` + таймер 12 с; стоп без resize. **Пересборка:** `scripts\rebuild-pult.bat` (или `desktop\DEV_PULT` → tauri dev). Тикет `problems/2026-05-24-pult-close-hang.md`.

**Пульт close/stop + логи (C):** `desktop/src/main.ts` — ✕ и Alt+F4 → `POST /stop` затем close; ▶ — компактное окно, логи свёрнуты; разворот только `#btn-collapse`; `/ui-expanded` true только по стрелке. Тикет `problems/2026-05-24-pult-close-stop-logs.md`.

**Proxy wait-loop:** `src/proxy_probe.py` — бот жив при мёртвом прокси; тикет `problems/2026-05-23-proxy-exit-killed-bot.md`.

**Unified TG join:** acc1/2/3 в `tg_main`; метка acc в боте — принято 2026-05-23.

**Карта кода:** [`CODE_STRUCTURE.md`](CODE_STRUCTURE.md)
