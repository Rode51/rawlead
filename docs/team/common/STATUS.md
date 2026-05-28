# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.11** · [`ROADMAP.md`](../architect/ROADMAP.md)

**Очередь:** [`TASKS.md`](TASKS.md) · решения владельца: [`OWNER_INTENT.md`](../architect/OWNER_INTENT.md)

---

## Сейчас (2026-05-28)

**Продукт:** [rawlead.ru](https://rawlead.ru) — лента, кабинет, API на VPS.

**Следующий шаг:** **владелец** — деплой E2 на VPS → **@coder E-polish B1** → stress после polish.

| Открыто | Кто | Где |
|---------|-----|-----|
| **VPS E2 deploy** | владелец | `DEPLOY_VPS.md` § E2/E2b |
| **E-polish B1** | @coder | `OWNER_INTENT` § B1 |
| **E-polish A1** — убрать «N лидов за 7 дней» | @coder | `OWNER_INTENT` § A1 |
| **E-polish C1** — mobile UX | @lead-designer → @coder | `OWNER_INTENT` § C1 |
| **P4b** — L2 `reply_draft` под профиль юзера | @coder + @lead-product | `TASKS.md` |
| **PRE-PROD-STRESS** S1–S6 | @coder → владелец | `PRE_PROD_GATE.md` · после polish |
| **3f** — ИИ «Написать отклик» + push | @coder | `CODER_PROMPT` § 3f-OWNER-BETA |

**Владельцу (ops, не код):** код E2 готов — деплой по `DEPLOY_VPS.md` § E2/E2b; затем `stop-radar-desktop-full.vbs`, оба ■.

---

## ✅ P5-E2-VPS (Coder 2026-05-28)

| | |
|--|--|
| **Сделано** | e2 legacy unit + runner; e4 пауза по профилю; e3/e5/e6 docs/импорт; `DEPLOY_VPS.md` E2b |
| **Файлы** | `deploy/run-radar-legacy.sh`, `deploy/systemd/rawlead-radar-legacy.service`, `src/storage.py`, `src/telegram_control.py`, `docs/ops/DEPLOY_VPS.md`, `.env.example` |
| **Как проверить (локально)** | pause split: legacy `/pause` не блокирует site (см. тест в storage); `radar_status` импорт `load_site_rollup_line` — без NameError |
| **Как проверить (VPS, владелец)** | `systemctl enable --now rawlead-radar rawlead-radar-legacy` · ПК stop full · `/lenta/` без Site ▶ · @FLPARSING `/pause` → Site log не замирает |

---

## ✅ Принято (код + Lead verify)

Сводка волны **2026-05-24 … 2026-05-28**. Детали приёмки — [`archive/TASKS_HISTORY.md`](../archive/TASKS_HISTORY.md).

| Блок | Суть |
|------|------|
| **Этап 0** | Радар ПК, legacy/site split, пульт, TG acc1–3 |
| **3b–3d** | Neon, API, WP `/lenta/` `/cabinet/` |
| **E0–E5** | PRE-LAUNCH A–D, REVOLUTION UI, copy c1–c4, canonical tags E2b |
| **3x** | Бадж «Горячий» (`is_hot` в API + WP) — **✅ принято владельцем** |
| **P5 E1** | API на VPS (`rawlead-api`, health ok) |
| **SITE-POLISH волна** | BACKLOG-CLEAR, FEED-FRESHNESS, DROP-FH, PULT-STATUS-LOGS, TG-FEED, FILTERS L2, SITE-LOG-ROLLUP, OWNER-UX-POLISH, NEON-AUDIT script |
| **Hotfix 28.05** | LEGACY-SELF-STOP (import), HOTFIX-POST-PULT, REPLAY-TG-FIX |
| **P5 E2 (код)** | `run-radar-legacy.sh`, `rawlead-radar-legacy.service`, пауза `radar_paused_site`/`radar_paused_legacy` |
| **Dogfood** | LEGACY-REPLY-DRAFT, STOP-STATUS-SPAM, CABINET-LOGIN-FALLBACK |
| **PRE-PROD** | Скрипты S1–S6 в repo — **прогон не начат** |

**Лог Site (Lead 2026-05-28):** FL/Kwork + TG в цикле; `конвейер:backlog≈108`; `site:сводка` есть.

---

## ЛК и подписка (честный статус)

| Есть | Ещё нет |
|------|---------|
| JWT, `/v1/me/*`, match %, L2 в раскрытии | Биллинг (§ 3h) |
| Вход TG + fallback | Gate «только paid → L2» |
| Схема `users` / `user_tags` SaaS-ready | Push агента на юзера (§ 3f) |
| `/v1/me/subscription` = заглушка `free` | |

---

## Блокеры (актуальные)

| Блокер | Кто |
|--------|-----|
| E2 на VPS не задеплоен — лента без Site ▶ на ПК | владелец · `DEPLOY_VPS.md` |
| B1 навыки «чужие на другом устройстве» (если репрод) | @coder E-polish |
| Пульт: sticky-скролл логов | код ✅ · `rebuild-pult.bat` — владелец |

Закрытые тикеты: [`docs/problems/`](../problems/) — не дублировать здесь.

---

## MVP acceptance (Plan B)

Сверка: [`LEAD_PRODUCT_PROMPT.md`](../product/LEAD_PRODUCT_PROMPT.md) § «Готово когда» — обновлять после **3f** и stress.

---

_Lead Architect · ревизия docs 2026-05-28_
