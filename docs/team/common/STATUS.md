# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.11** · [`ROADMAP.md`](../architect/ROADMAP.md)

**Очередь:** [`TASKS.md`](TASKS.md) · решения владельца: [`OWNER_INTENT.md`](../architect/OWNER_INTENT.md)

---

## ✅ L1 + L2 — вход ЛК prod + страницы сайта (**✅ Lead verify 2026-05-28**)

| | |
|--|--|
| **L1** | `canMountTelegramWidget()` + allowlist rawlead.ru; `rawlead_cabinet_login_url()`; fallback `return_to` prod; 127.0.0.1 только local |
| **L2** | hero CTA лента+ЛК; pricing Stars; plugin `rawlead-landing` + `wp-vps-skeleton-pages.py` |
| **Lead verify** | `marketing.php`, `functions.php` v1.7.7, `page-cabinet.php`, `rawlead-cabinet.js` — без hard-block prod |
| **Деплой (владелец)** | `deploy-wp-theme-vps.py` + `wp-vps-skeleton-pages.py` · BotFather `/setdomain` → rawlead.ru |

---

## ✅ E-polish D1 — навыки + шапка (**Coder 2026-05-28**)

| | |
|--|--|
| **Сделано** | закрытие навыков по клику вне; sticky footer «Применить»; header: Лента+Тарифы; CTA «Вход в ЛК» / «Кабинет» |
| **Файлы** | `template-parts/rawlead/header.php`, `page-lenta.php`, `assets/css/rawlead.css`, `assets/js/rawlead-feed.js` |
| **Как проверить** | § LENTA-HEADER-UX приёмка 1–4; деплой theme **v1.7.6+** (`functions.php` bump + `scripts/deploy-wp-theme-vps.py`) |

---

## ✅ E-polish B1 — навыки per user_id (**✅ Lead + владелец 2026-05-28**)

| | |
|--|--|
| **Сделано** | гость → `localStorage`; JWT → Neon `user_tags`; REST без owner #1; theme **v1.7.5** на VPS |
| **Lead verify** | `rawlead-api.php`: GET tags без Bearer → `[]`; PUT → 401; `/me/feed` → 401; `rawlead-feed.js`: guest не шлёт PUT |
| **Файлы** | `inc/rawlead-api.php`, `assets/js/rawlead-feed.js`, `functions.php` |

---

## Сейчас (2026-05-28)

**Следующий шаг:** деплой v1.7.7 на VPS (ты) → **@coder B3** → A1 → **3f**.

| Открыто | Кто | Где |
|---------|-----|-----|
| **Деплой L1/L2/D1** | владелец | `deploy-wp-theme-vps.py` + `wp-vps-skeleton-pages.py` · BotFather domain |
| **E-polish B3** | @coder | admin-only TG · § BOT-OWNER-CONTROLS |
| **E-polish A1** | @coder | убрать «N лидов за 7 дней» |
| **E-polish C1** — mobile UX | @lead-designer → @coder | `OWNER_INTENT` § C1 |
| **P4b** — L2 `reply_draft` под профиль юзера | @coder + @lead-product | `TASKS.md` |
| **PRE-PROD-STRESS** S1–S6 | @coder → владелец | `PRE_PROD_GATE.md` · после polish |
| **3f** — ИИ «Написать отклик» + push | @coder | `CODER_PROMPT` § 3f-OWNER-BETA |

**Владельцу:** Site/Legacy ■ на ПК — **не включать**; радар 24/7 только VPS systemd.

---

## ✅ P5-E2-VPS deploy (Lead ops 2026-05-28)

| | |
|--|--|
| **Сделано** | sync кода на `/opt/rawlead`; `.env` + `.env.site` + `.env.legacy`; Telethon-сессии acc1–3; `rawlead-radar` + `rawlead-radar-legacy` **active**; ПК `stop-radar-desktop-full.vbs` |
| **Скрипты** | `scripts/finish-vps-e2.py`, `scripts/check-vps-e2.py`, `prep-vps-env.ps1` (+ `.env.legacy`) |
| **Проверка** | `main.py` + `tg_main` на VPS; `/v1/feed` — свежий FL-лид `2026-05-28`; TG acc1/acc3 **ready**; `http://rawlead.ru/lenta/` → 200 (nginx :80) |
| **Заметки** | acc3 = `233333925_telethon.session` (не +66985780470); CRLF в `.sh` — `sed` в finish-e2; Legacy consumer ok |

---

## ✅ P5-E2-VPS (Coder 2026-05-28)

| | |
|--|--|
| **Сделано** | e2 legacy unit + runner; e4 пауза по профилю; e3/e5/e6 docs/импорт; `DEPLOY_VPS.md` E2b |
| **Файлы** | `deploy/run-radar-legacy.sh`, `deploy/systemd/rawlead-radar-legacy.service`, `src/storage.py`, `src/telegram_control.py`, `docs/ops/DEPLOY_VPS.md`, `.env.example` |

---

## ✅ Принято (код + Lead verify)

Сводка волны **2026-05-24 … 2026-05-28**. Детали — [`archive/TASKS_HISTORY.md`](../archive/TASKS_HISTORY.md).

| Блок | Суть |
|------|------|
| **Этап 0** | Радар ПК, legacy/site split, пульт, TG acc1–3 |
| **3b–3d** | Neon, API, WP `/lenta/` `/cabinet/` |
| **E0–E5** | PRE-LAUNCH A–D, REVOLUTION UI, copy c1–c4, canonical tags E2b |
| **3x** | Бадж «Горячий» — **✅** |
| **P5 E1** | API на VPS (`rawlead-api`, health ok) |
| **P5 E2** | код + **деплой VPS** — Site+Legacy systemd |
| **E-polish B1** | навыки per user_id (guest localStorage + JWT Neon) — **✅** |
| **SITE-POLISH волна** | BACKLOG-CLEAR, FEED-FRESHNESS, … NEON-AUDIT |
| **Dogfood** | LEGACY-REPLY-DRAFT, STOP-STATUS-SPAM, CABINET-LOGIN-FALLBACK |
| **PRE-PROD** | Скрипты S1–S6 — **прогон не начат** |

**Лента:** ingest на VPS, интервал Site **1 мин** (`.env.site`). Прокси acc1–3 на месте.

---

## ЛК и подписка (честный статус)

**Лестница (канон O6):** polish (D1–A1) → **§ 3f фаза A** (ЛК + L2 без денег) → **фаза B** (экран тарифа) → **фаза C / касса** (590–990 ₽).

| Есть сейчас | Ещё нет (очередь) |
|-------------|-------------------|
| `/cabinet/`, вход TG + fallback | Gate «L2 только paid» |
| JWT, навыки per user (B1 ✅) | Push match в TG подписчику (3f-A4) |
| `/v1/me/feed`, match %, L2 в раскрытии | L2 персонально под профиль (P4b) |
| Таблица `subscriptions` в Neon | Реальный `/v1/me/subscription` (не заглушка `free`) |
| @rawlead_bot в коде | Оплата **Telegram Stars** (O12) — после L1 + 3f-A |
| | Страница тарифа, статус, пауза подписки (3f-B) |
| | Биллинг webhook → `is_active=true` |

**ТЗ:** [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md) § **3f-OWNER-BETA** (фазы A→B→C).

---

## Блокеры (актуальные)

| Блокер | Кто |
|--------|-----|
| Пульт: sticky-скролл логов | код ✅ · `rebuild-pult.bat` — владелец |
| SSL :443 на VPS (если нужен прямой HTTPS) | владелец · certbot |

Закрытые тикеты: [`docs/problems/`](../problems/) — не дублировать здесь.

---

## MVP acceptance (Plan B)

Сверка: [`LEAD_PRODUCT_PROMPT.md`](../product/LEAD_PRODUCT_PROMPT.md) § «Готово когда» — после **3f** и stress.

---

_Lead Architect · ревизия docs 2026-05-28_

### B1 verify (владелец, ~3 мин)

1. **Гость `/lenta/`:** инкognito → навыки → «Применить» → Network: **нет** `PUT …/me/tags`; перезагрузка — навыки на месте (localStorage).
2. **Два гостя:** другой браузер — **другие** навыки (не owner #1).
3. **ЛК:** `/cabinet/` → TG-вход → навыки → `PUT …/me/tags` **200** + `Authorization: Bearer`.
4. **Кросс-девайс:** тот же TG на телефоне и ПК → `/cabinet/` — **одинаковые** навыки после reload.
5. **Лента залогинен:** после входа в ЛК открыть `/lenta/` — подтянулись навыки из Neon (тот же JWT).
