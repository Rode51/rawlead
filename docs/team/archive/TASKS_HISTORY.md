# TASKS — архив

Краткие записи после сдачи Coder (Lead).

---

## 2026-06-04 — O109 ✅ + Lead rules A+B+C

**Сделано:** Kwork delist false-positive · bot «Лента» → `/lenta/?lead={id}` · theme **1.18.6** · STATUS/TASKS hot slim · `lead-no-code` + wordpress ban.

**Урок:** Lead не кодит даже после conversation summary — только docs + `@coder`.

---

## 2026-06-03 — Lead slim CODER_PROMPT hot (40 строк)

**Было:** hot ~225 строк — O104 + O72e-10 DoD дублировали «✅ принято».

**Сделано:** DoD → [`CODER_PROMPT_ARCHIVE.md`](CODER_PROMPT_ARCHIVE.md) · hot — таблица сводка · правила Lead в `lead-architect.mdc` § зоны.

**Урок:** Lead не пишет `LEAD_PRODUCT_PROMPT` copy — только `OWNER_INTENT` + «→ @lead-product» в TASKS.

---

**Закрыто:** O81-w1c · O88 · O85/O86/O78 · O72e-6 · O72e-7 r4 · O82-w2 · O63-w2.

**O72e:** 3× quick-test (send 20→40→60%) · **PASS** на 5 якорях (`152154Z`: 4.07/60%/80%) · full judge ⏳ владелец.

**Следом:** O89 uniquify (OWNER_INTENT § O89) · GTM после full PASS.

**Docs:** STATUS/TASKS/ROADMAP/FOR_YOU — один снимок, без дублей закрытых треков.

---

## 2026-05-30 — Cursor Team Kit v1.0 + DESIGNER slim

**Kit:** `docs/team/templates/cursor-team-kit/` — rules + docs-skeleton + `bootstrap.ps1` для других repo.

**DESIGNER_PROMPT** ~1900 → **~35 hot** + `DESIGNER_PROMPT_ARCHIVE.md`.

**`.gitignore`:** `!.cursor/rules/**` — правила в git.

---

**CODER_PROMPT** ~4500 строк → **~130 hot** + [`CODER_PROMPT_ARCHIVE.md`](CODER_PROMPT_ARCHIVE.md).

**Правила `.mdc`:** `economy` § бюджет · `coder` — § шапки only · `code-guard` + `wordpress/` · `docs-guard` — anti-bloat.

---

## 2026-05-30 — Lead: STATUS slim + STATUS_ARCHIVE

**STATUS** снова раздулся (~1280 строк, ~60 KB) → **~80 строк hot** + [`STATUS_ARCHIVE.md`](STATUS_ARCHIVE.md) (~1200 строк холодного архива).

**Правило:** агенты читают только hot STATUS; архив — по явному запросу или grep по задаче (O71, O37c, …).

**Hot содержит:** Сейчас · активное (O72) · prod gates · сводка принятого · блокеры.

---

## 2026-05-28 — Lead: ревизия docs, волна SITE-POLISH принята

**STATUS** урезан (~80 строк): один снимок «Сейчас» + таблица принятых блоков; детальные § BACKLOG-CLEAR … 3x убраны из STATUS (не дублировать ТЗ).

**TASKS** — только активная очередь (P5-E2 → E-polish → 3f → stress).

**Принято в коде (Lead verify):** E0–E5, 3x HOT-BADGE, BACKLOG-CLEAR, FEED-FRESHNESS, DROP-FH, PULT-STATUS-LOGS, TG-FEED, FILTERS L2, LEGACY-SELF-STOP, HOTFIX-POST-PULT, PRE-PROD scripts, P5 E1 API.

**Открыто:** P5-E2-VPS, E-polish B1/A1/C1, P4b, 3f, stress.

**Архив:** [`PORTFOLIO_SPRINT.md`](PORTFOLIO_SPRINT.md) (устарел, 2026-05-25) перенесён из `architect/`.

---

## 2026-05-24 — Lead Architect: vision v0.9 принят, docs cleanup

- Product: ставка **A → B** · [`PRODUCT_VISION.md`](../PRODUCT_VISION.md) v0.9 · [`LEAD_PRODUCT_PROMPT.md`](../LEAD_PRODUCT_PROMPT.md)
- `ROADMAP.md` фазы 3b–3h · `LEAD_DESIGN_PROMPT` (/feed, /cabinet) · `CODER_PROMPT` → **3b Neon**
- `STATUS`/`TASKS`/`FOR_YOU` без дублей · `SOURCES_SAAS` → [`archive/SOURCES_SAAS.md`](../../archive/SOURCES_SAAS.md)
- Снято: Coder § B demo `/cabinet`, `contour` в NEON_SCHEMA (→ `is_visible`)

---

## 2026-05-23 — Lead: два контура owner / saas + монетизация

- [`PRODUCT_VISION.md`](../PRODUCT_VISION.md) §0c–0d · [`SOURCES_SAAS.md`](../../ops/SOURCES_SAAS.md)

---

## 2026-05-23 — Lead: PRODUCT_VISION 0.4 + Neon/API/WP TZ

- Внутренний язык match; наружу «совместимость»
- Сайт + подписки + бот (без app)
- [`NEON_SCHEMA.md`](../NEON_SCHEMA.md) · [`TZ_API.md`](../TZ_API.md) · [`TZ_WP.md`](../TZ_WP.md) v0.2

---

## 2026-05-23 — WP Kadence child + Design REFERENCE E (принято)

- `wordpress/rawlead-kadence-child/` · Manrope + Unbounded · hero / поток / match %
- `scripts/wp_install_rawlead_theme.py` · `docs/ops/WP_KADENCE_INSTALL.md`
- Designer: [`design/wp/REFERENCE.md`](../design/wp/REFERENCE.md)

---

## 2026-05-23 — Proxy fail-closed + wait-loop (Mechanic/Coder)

- `src/proxy_probe.py` — не kill tg_main при мёртвом прокси; бот жив
- `docs/problems/2026-05-23-proxy-exit-killed-bot.md`

---

## 2026-05-23 — Coder: unified TG join + acc labels in bot (принято владельцем)

- Join acc1/2/3 в `tg_main`; убран child join из пульта
- Метка `accN · чат` в пересылке/разборе
- [`CODE_STRUCTURE.md`](../CODE_STRUCTURE.md) · `tg_queue_import.py` · 73 pending CSV

---

## 2026-05-23 — Coder: волна 3 TG join queue

- `scripts/tg_queue_import.py` — 73 pending, round-robin acc1/2/3 (25/24/24)
- `TG_JOIN_QUEUE.csv` wave=3 · 14 `done` без изменений

---

## 2026-05-23 — Владелец: пульт v2 принят

- Приёмка: play/stop, —/✕, логи, вкладка «Статус», `start-radar-desktop.vbs`
- [`STATUS.md`](../STATUS.md) · [`TASKS.md`](../TASKS.md)

---

## 2026-05-23 — Coder: пульт regression (кнопки, window perms)

- `capabilities/default.json` — minimize/close/set-size/dragging
- `main.ts` — plugin-http, status-banner, blockDragOnClick
- Тикет: `problems/2026-05-23-pult-buttons-regression.md`

---

## 2026-05-23 — Coder: пульт v2 Tauri (принято Lead)

- `scripts/radar_control.py`, `desktop/` (Tauri 2 + CSS v2), `start-radar-desktop.bat`
- PyQt6 deprecated · см. [`DESKTOP_LAUNCH.md`](../../ops/DESKTOP_LAUNCH.md)

---

## 2026-05-23 — Designer: пульт v2 (ЮБуст / Tauri brief)

- [`DESIGN_BRIEF.md`](../DESIGN_BRIEF.md) v2, [`DESIGN_SYSTEM.md`](../DESIGN_SYSTEM.md), canvas `fl-radar-pult-v2`
- Lead → [`CODER_PROMPT.md`](../CODER_PROMPT.md)

---

## 2026-05-20 — Coder: UI пульта по DESIGN_BRIEF (принято Lead)

- `scripts/radar_desktop.py` — ops-dashboard, лампы green/red/gray, токены, размеры 480×320 / 880×620
- `docs/ops/DESKTOP_LAUNCH.md` — описание ламп
- Дизайн: [`DESIGN_BRIEF.md`](../DESIGN_BRIEF.md)

---

## 2026-05-23 — Coder: пульт управления (принято Lead)

- `scripts/radar_desktop.py` — Старт/Стоп 3 процессов без cmd, логи, статус
- Архитектура: [`ARCHITECTURE.md`](../ARCHITECTURE.md) § процессы на ПК

---

## 2026-05-23 — Coder: статус номеров в боте (принято Lead)

- Кнопка **ℹ Статус** / `/status`: FL/Kwork + acc1/2/3 (чаты, сообщения, новые, в бот, ошибки)
- `src/radar_status.py`, правки `telegram_control.py`, `tg_monitor.py`, `main.py`, `tg_main.py`

---

## 2026-05-23 — Coder: multi-session TG (принято Lead)

- Один `tg_main`: acc1+acc2+acc3; `telethon_chat_ids_accN.txt`; `TELETHON_MONITOR_ACCOUNTS`
- `tg_sync_chat_ids.py --account all`; join → `join:listen:add` для monitor-аккаунтов
- Владелец: `.env` + sync + тест JS Jobs (acc2)

---

## 2026-05-23 — Coder: join supervisor (принято Lead)

- Один `tg_join_daemon.py` для acc2/acc3/acc4; registry; 3 окна в `start-radar-full.bat`

---

## 2026-05-23 — Coder: авто-join в чаты (принято Lead)

- `src/tg_join_runner.py` — `run_join_tick(account, client=…)`
- acc1 join в `tg_monitor` + `listen+` без рестарта; acc1 в CLI запрещён
- acc2/acc3 — 2 окна `--daemon`; `start-radar-full.bat`
- Следующий шаг: один `tg_join_daemon` (бэклог)

---

## 2026-05-24 — Coder: пульт ✕=стоп + логи по стрелке (принято Lead)

- `desktop/src/main.ts` — `stopRadarCore`, `onCloseRequested`, логи collapsed при ▶
- Тикет: `problems/2026-05-24-pult-close-stop-logs.md`

---

## 2026-05-23 — Coder: авто `telethon_chat_ids.txt` (принято Lead)

- append после join acc1; `tg_sync_chat_ids.py`; `.env` → файл id

---

## 2026-05-23 — Coder: TG accounts + join queue (принято Lead)

- `--account acc1|acc2|acc3`, `tg_join_lib.py`, `tg_join_queue.py`, CSV, `data/tg_join.log`
- `acc4` — бэклог

---

_Старые записи MVP/TG-кнопки — в истории чатов / бэкапе docs при необходимости._
