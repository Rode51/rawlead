# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.11** · [`ROADMAP.md`](../architect/ROADMAP.md)

**Очередь:** [`TASKS.md`](TASKS.md) · решения владельца: [`OWNER_INTENT.md`](../architect/OWNER_INTENT.md)

---

## Сейчас (2026-05-28)

**Продукт:** [rawlead.ru](https://rawlead.ru) — лента, кабинет, API на VPS. Site-радар на ПК → Neon (до **P5-E2**).

**Следующий шаг:** **@coder** § **P5-E2-VPS** (радары на сервер, ПК не 24/7) → **E-polish** (B1/A1/C1) → **3f** → **PRE-PROD-STRESS** → трафик.

**Stress отложен** до polish + VPS (решение O1).

| Открыто | Кто | Где ТЗ |
|---------|-----|--------|
| **P5-E2-VPS** — Site+Legacy на VPS, стоп радаров на ПК | @coder | `CODER_PROMPT` § P5-E2-VPS · `DEPLOY_VPS.md` |
| **E-polish B1** — навыки персонально на user_id | @coder | `OWNER_INTENT` § B1 |
| **E-polish A1** — убрать «N лидов за 7 дней» | @coder | `OWNER_INTENT` § A1 |
| **E-polish C1** — mobile UX | @lead-designer → @coder | `OWNER_INTENT` § C1 |
| **P4b** — L2 `reply_draft` под профиль юзера | @coder + @lead-product | `TASKS.md` |
| **PRE-PROD-STRESS** S1–S6 | @coder → владелец | `PRE_PROD_GATE.md` · после polish |
| **3f** — ИИ «Написать отклик» + push | @coder | `CODER_PROMPT` § 3f-OWNER-BETA |

**Владельцу (ops, не код):** пока нет E2 на VPS — держать **Site ▶** на ПК; после E2 — `stop-radar-desktop-full.vbs`, оба ■.

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
| Радар только на ПК — лента на проде без Site ▶ | **P5-E2-VPS** @coder |
| B1 навыки «чужие на другом устройстве» (если репрод) | @coder E-polish |
| Пульт: sticky-скролл логов | код ✅ · `rebuild-pult.bat` — владелец |

Закрытые тикеты: [`docs/problems/`](../problems/) — не дублировать здесь.

---

## MVP acceptance (Plan B)

Сверка: [`LEAD_PRODUCT_PROMPT.md`](../product/LEAD_PRODUCT_PROMPT.md) § «Готово когда» — обновлять после **3f** и stress.

---

_Lead Architect · ревизия docs 2026-05-28_
