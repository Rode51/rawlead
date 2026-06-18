# TASKS — архив

Краткие записи после сдачи Coder (Lead).

---

## 2026-06-16 — TASKS hot slim

**Перенесено из hot:** шаги **#43–#96** (O203–O251) · планы O207/O208 · чеклист smoke O204/O205 (deploy 1.18.82, filter TG, glow).

**Новый hot:** [`TASKS.md`](../common/TASKS.md) — только #1–5 (O254 deploy · O252 · O237 · O200-L2 · smoke).

**Закрытые треки (index):** O220 quiz/match batch · O221 adaptive 130 cards · O222 FL hard reset · O223 YouDo L1 · O224–O227 match UX · O230–O231 inbox · O236–O246 perf · O247–O248 TG · O249–O251 hygiene · O250 push chain ✅ prod.

**Старый smoke O205** (filter TG, acc3, API 502) — устарел; актуальный local smoke → `TASKS.md` § Local smoke.

---

## 2026-06-15 — O221-QUIZ-ADAPTIVE + PM r7

**Закрыто:** `quiz_cards_v2.json` 130 · loader 186 · `test_quiz_coverage.py` · VPS DEPLOY OK · pytest 64/64 ✅ Lead verify+deploy.

---

## 2026-06-14 — O206 t2b sync chat_ids

**Закрыто:** merge 3 queue CSV → listen file · acc1 72/70 peers · audit ok:true ✅ Lead verify+deploy.

---

## 2026-06-14 — O211 ops truth metrics

**Закрыто:** footer `сегодня/24ч` · YouDo soft lamp · pytest 15/15 ✅ Lead verify. Deploy API ⏳.

---

## 2026-06-14 — FL-PROXY-STABILITY deploy

**Закрыто:** tier-2 proxy code on VPS · pytest 25/25 · smoke `alive=4/4` ✅ Lead.

**Owner tail:** `FL_PROXY_URLS_RESIDENTIAL` in `.env.site`.

---

## 2026-06-14 — O209 match-first WP

**Закрыто:** O209 P0 quiz rebuild + P1 copy/tier strips · theme **1.18.84** · Lead verify+deploy ✅.

**Next:** волна 1 t2b/O207 · FL tier-2 (отдельный чат) · волна 3 perf.

---

## 2026-06-13 — O190-auto + O203 + O202-proxy + glow

**Закрыто:** O190-auto · O203 ops RU · O202 spam WP proxy · draft glow · acc3 VPS diag ✅ Coder.

**Deploy ⏳ owner:** o190 script + wp theme 1.18.80.

**Next:** O199 logged-in lenta.

---

## 2026-06-13 — O202 spam corpus + O200 r2 код

**Закрыто:** O202-TG-SPAM-CORPUS ✅ Lead verify · pytest 11/11 · deploy ⏳.

**Параллель:** O200-L2 r2 playbooks ✅ код · judge re-pilot ⏳.

**Не сдано:** O190-AUTO-ALLOWLIST-LISTEN — filter всё ещё allowlist∩CSV.

---

## 2026-06-13 — O201 ops500 + O190 TG chain

**Закрыто:** O201-OPS-500 (`load_config`, degraded funnel) · O190-TG-JOIN-LISTEN-CHAIN (allowlist expand, peers ladder, chain logs) · pytest 24/24 · deploy ⏳ owner.

**Hot:** CODER_PROMPT → O199 · L2 parallel untouched.

---

## 2026-06-12 — O190 ingest DoD + hot slim

**Закрыто:** O190-t0j YouDo ingest · Lead verify VPS · `fetch_end parsed=50`.

**Hot:** CODER_PROMPT **~85** строк · STATUS **~55** · TASKS slim · O191 active.

**Урок:** Lead push только `docs/**` пока Coder на O191 — без конфликта с `src/`.

---

## 2026-06-05 — Docs sync + infra hot closed

**Закрыто:** O117-deploy · O120-deploy · O121-w0 · O116 full · O72e gate.

**Hot Coder:** O105-w1-r3 verify → O107 trial → O122 delist.

**Урок:** STATUS был 236 строк и противоречил TASKS (O117 «→ сейчас» при ✅). Lead slim + ROADMAP дата 2026-06-05.

---


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
