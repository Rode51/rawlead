# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.11** · [`ROADMAP.md`](../architect/ROADMAP.md)

**Очередь:** [`TASKS.md`](TASKS.md) · решения владельца: [`OWNER_INTENT.md`](../architect/OWNER_INTENT.md)

---

## ✅ MATCH-PUSH-V2 O30 — backend (**Lead verify ✅ 2026-05-28**)

| | |
|--|--|
| **sql/010** | `push_min_match` DEFAULT 60 · `push_enabled` DEFAULT TRUE — **Neon ✅** |
| **match_push.py** | top-3 **убран** · всем paid при `km >= push_min_match` · `push_enabled` |
| **API** | `GET/PATCH /v1/me/notification-settings` (30–100) |
| **VPS** | API restart · `match_push.py` без TOP_K |
| **⚠️ UI gap** | `rawlead-api.php` — **нет** REST proxy → `/cabinet/` блок «Уведомления» **404** |
| **Fix** | § **MATCH-PUSH-V2-WP-PROXY** → @coder · theme bump **v1.7.24** |

---

## ✅ HOTFIX UX wave — v1.7.23 (**Lead verify ✅ 2026-05-28**)

| | |
|--|--|
| **#20 DRAFT-403** | `barPct = keyword_match` · кнопка только `km > 0` · 403 → «Нет пересечения…» |
| **#21 CABINET-SKILLS** | `pickerNiche = null` · full catalog · все 4 группы в модалке |
| **#22 FEED-SORT-DD** | `mousedown` закрывает `.rl-filter-sort-dd` |
| **Theme** | **v1.7.23** |
| **Деплoy** | **✅ Lead ops** — prod rawlead.ru |

---

## ✅ TAGS-V0.3 + b3 + OWNER-BETA — (**Lead verify ✅ 2026-05-28**)

| | |
|--|--|
| **TAGS t3-1…t3-7** | 51 canonical · PUT/GET max 6 · merge v0.2→v0.3 · picker **«Ещё навыки»** · чипы 4+«+N» · L1 smoke warn |
| **t3-2b** | `openai`/`gpt` → `llm_integration` |
| **OWNER-BETA-GRANT** | `_grant_owner_beta_if_match` при TG-login |
| **b3-HOTFIX** | `status`: inactive/failed = ok · ▶ → `start` если ≠ active |
| **Lead verify** | py_compile ok · 51 tags · 7-й tag → 6 · theme **v1.7.19** |
| **Деплoy** | theme + API restart на VPS — **→ владелец/Lead ops** |

**Открыто:** SITE-ACCEPT-GATE a2 + a5–a6 (TG-login владельца с VPN).

---

## ✅ PRE-DESIGN-BLOCKERS O27–O29 (**Lead verify ✅ 2026-05-28**)

| | |
|--|--|
| **O27** | `POST …/draft` → `analyze_premium` · `tools_required` в Neon + ответ API · feed/cabinet «Инструменты» |
| **O28** | `/start` → `upsert_subscriber_chat_id` · `push_match_for_lead` после L1 · dedupe `match_push_log` · env `MATCH_PUSH=1` |
| **O29** | `sendInvoice` XTR · `pre_checkout_query` · `successful_payment` → `plan=agent` · `stars_available` в API · UI `/pay` + кабинет |
| **Lead verify** | py_compile ok · draft 403 free / tools в `renderExpandedBody` · push top-K=3 paid/owner · Stars `activate_subscription` |
| **Theme** | **v1.7.22** (O25b + blockers) |
| **Деплoy** | **✅ Lead ops 2026-05-28** — Neon `009` · env `MATCH_PUSH=1` `STARS_ENABLED=1` · theme + API/bot/radar restart · smoke 5/5 |

---

## ✅ FEED-CARD-UX O25–O26 + O25b (**Lead verify ✅ 2026-05-28**)

| | |
|--|--|
| **O25/O25b** | `feed_social.py`: fresh instant 1–3 · 15m/60m растут с age · delayed bonus · eye SVG + count (без «просмотров») |
| **O26** | perfect-match badge + green bar |
| **Smoke** | fresh 1 / delayed 2 · 15m 21/35 · 60m 29/41 (lead_id=42) |
| **Theme** | **v1.7.22** |

---

## ✅ CABINET-INBOX-O23 — лента vs inbox (**Lead verify ✅ 2026-05-28**)

| | |
|--|--|
| **Модель** | `/lenta/` — единственная lenta; anon + free TG → delay 15 мин, без «Написать отклик»; paid/beta → instant + кнопка |
| **Inbox** | `user_lead_replies` · `GET/DELETE /v1/me/replies` · `/cabinet/` = профиль + inbox |
| **L2** | `analyze_premium` on-demand через `POST …/draft` (O27) |
| **Lead verify** | o23-1…7 · API `feed_delayed:true` · theme **v1.7.15** на prod |
| **Деплoy VPS** | **✅ Lead** — `deploy-l3-vps.py` · Neon `008` · API restart |
| **Владельцу** | § **SITE-ACCEPT-GATE** a1–a9 |

**Открыто:** SITE-ACCEPT-GATE a1–a9.

---

## ✅ L1 + L2 — вход ЛК prod + страницы сайта (**✅ Lead verify 2026-05-28**)

| | |
|--|--|
| **L1** | `canMountTelegramWidget()` + allowlist rawlead.ru; hotfix **v1.7.8** — рекурсия `tg_login_bot_id`↔`fallback_url` → 500 на `/cabinet/` |
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

## ✅ L3 — навыки picker + retention 7d + L3-FIX (**Lead verify ✅ 2026-05-28**)

| | |
|--|--|
| **L3-FIX** | API `?mode=full` → static L1 pool (Tier A+B); ЛК `?mode=full&limit=200`; modal **сверху**; theme **v1.7.10** |
| **TG login RU** | widget fail → redirect; VPN hint; popup timeout 8s; `#tgAuthResult` hash; `RAWLEAD_TG_BOT_ID` в install + DEPLOY_VPS |
| **Retention** | feed/me/feed 7d; `purge_old_leads.py` + systemd timer |
| **Lead verify** | `api_server.py` L518–581, `rawlead-cabinet.js` L156–219/1423, `rawlead.css` L2425–2456 — ок |
| **Деплoy VPS** | **✅ Coder 2026-05-28** — `deploy-l3-vps.py`: theme **v1.7.10**, API `mode=full`, `RAWLEAD_TG_BOT_ID=8989158953`, units **active** |
| **Владельцу** | BotFather `/setdomain` → `rawlead.ru` · приёмка 🛑/▶ в @rawlead_bot |

**⚠️ Вход TG из РФ:** без VPN redirect на `oauth.telegram.org` тоже не откроется — VPN обязателен.

---

## ✅ E-polish B3 — owner-only TG controls (**Coder 2026-05-28**)

| | |
|--|--|
| **Сделано** | `is_radar_admin()`; admin-клавиатура ⏸/▶/🛑/ℹ только владельцу; подписчикам welcome + `remove_keyboard`; `/stop-radar` + 🛑 → `systemctl stop` через `deploy/radar-ctl.sh`; ▶ поднимает unit если inactive |
| **Файлы** | `src/telegram_control.py`, `deploy/radar-ctl.sh`, `deploy/sudoers.d/rawlead-radar-ctl`, `docs/ops/DEPLOY_VPS.md` §9–10 |
| **Как проверить** | § BOT-OWNER-CONTROLS приёмка 1–4; **на VPS** — 🛑 → `systemctl is-active rawlead-radar` = inactive; ▶ → active |
| **Деплой VPS** | **✅** с L3 (`deploy-l3-vps.py`: `radar-ctl.sh`, sudoers, CRLF fix `deploy/*.sh`) |
| **Hotfix 2026-05-28** | `bot_poll.py` fcntl; offset до 🛑; **`rawlead-bot-poll.service`**; ack «✓ Принято»; статус — явная строка ingest (🛑/⏸/▶) |
| **b3-HOTFIX** | **✅ Coder** — см. блок **b3-HOTFIX** выше · Lead verify VPS pending |
| **Радар VPS** | **✅ active** (Lead restart 2026-05-28) · TG acc1+acc3 **ready** · acc2 skip (нет chat_ids) · `bot_start` entity — некритично |

---

## ✅ LK-UX-POLISH + A1 + 3f-A (**Lead verify ✅ 2026-05-28**)

| | |
|--|--|
| **LK-UX** | merge guest-навыков; avatar в шапке; user bar + «Выйти»; @rawlead_bot hint |
| **A1** | «N лидов · по совместимости» |
| **3f-A2** | expand + copy (**⚠️** L2 on-demand нет — только готовый `reply_draft` в Neon) |
| **Lead verify** | `mergeGuestSkillsAfterAuth`, `header.php`, `page-cabinet.php`, v**1.7.11** |
| **Деплой** | `deploy-wp-theme-vps.py` + restart API |

---

## ✅ 3f-B — тариф/статус подписки (**Lead verify ✅ 2026-05-28**)

| | |
|--|--|
| **Сделано** | `GET /v1/me/subscription` из Neon; `POST …/pause` (days/resume); блок «Подписка» в ЛК; `/pricing/` 590 ₽ + Stars soon; `sql/007_subscriptions_status.sql` |
| **Lead verify** | `api_server.py` L765–931 · `rawlead-api.php` REST proxy · `page-cabinet.php` + `rawlead-cabinet.js` subscription UI · `rawlead.css` · v**1.7.13** |
| **Stars** | live при `STARS_ENABLED=1` — см. блок **O27–O29** |
| **Beta owner** | `plan=owner` → status **beta**, `can_pause=false` ✅ |
| **Деплoy** | Neon: `007_subscriptions_status.sql` · `deploy-wp-theme-vps.py` · `systemctl restart rawlead-api` |
| **Не в 3f-B** | NEO-BRUTALIST CSS (MATCH_PUSH/Stars — **O27–O29 ✅**) |

---

## ✅ LK-FEED-FILTERS (O22) + SFW sfw-8 / sfw-3…7 (**Lead verify ✅ 2026-05-28**)

| | |
|--|--|
| **O22** | sort match\|time + sessionStorage; min_match 30–100; `_passes_min_match`; карточка `keyword_match` % |
| **sfw-8** | `POST /v1/me/leads/{id}/draft` + «Генерируем…» в ЛК |
| **sfw-3…7** | how/faq/contact/pricing; footer; FAQ `<details>`; contact stub |
| **Lead verify** | `api_server.py` · `page-cabinet.php` · `rawlead-cabinet.js` · v**1.7.14** |
| **⚠️** | `reply_draft` в `leads` — один на лид (полный P4b per-user позже) |
| **Деплoy** | theme + API на VPS · Lead ops |

---

## ⚠️ Pivot O23 (2026-05-28) — лента vs inbox

**Решение владельца:** `/cabinet/` **не** дублирует ленту. Inbox откликов + профиль. «Написать отkлик» на **`/lenta/`** (paid). ТЗ: § **CABINET-INBOX-O23**.

**Код v1.7.14** (match-лента в ЛК) — **legacy до O23**.

---

## Сейчас (2026-05-28)

**O30 ✅ + v1.7.24 prod.** Дальше: **SITE-ACCEPT-GATE** (ты) → Design/PM.

| Волна | Кто | Статус |
|-------|-----|--------|
| **Hotfix UX #20–22** | @coder | **✅** · **v1.7.23** prod |
| **O30 MATCH-PUSH-V2** | @coder | **✅** Lead verify · **v1.7.24** prod |
| **Приёмка** | **владелец** | § **SITE-ACCEPT-GATE** a2, a5–a6 |
| **E-polish C1** — mobile UX | @lead-designer → @coder | `OWNER_INTENT` § C1 |
| **P4b** — L2 `reply_draft` под профиль юзера | @coder + @lead-product | `TASKS.md` |
| **PRE-PROD-STRESS** | S1–S6 | @coder → владелец | **после** Design + PM + Coder финал (O21) |
| **O11 / 3r** две скорости ленты | @coder | **⏸** · copy/UI в Product+Design docs |

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

**Лестница (канон O6):** polish (D1–A1) → **§ 3f фаза A** ✅ → **фаза B** ✅ → **фаза C / касса** (590–990 ₽).

| Есть сейчас | Ещё нет (очередь) |
|-------------|-------------------|
| `/cabinet/`, вход TG + fallback | Gate «L2 только paid» |
| JWT, навыки per user (B1 ✅) | L2 персонально под профиль (P4b full) |
| `/v1/me/feed`, match %, sort, min_match, L2 on-demand | PRE-PROD stress S1–S6 |
| `/v1/me/subscription` — реальные поля Neon | ЮKassa / несколько тарифов |
| Push match TG (O28) · Stars оплата (O29) · `tools_required` (O27) | NEO-BRUTALIST CSS |
| Таблица `subscriptions` + `is_active` / `paused_until` | |
| Блок «Подписка» + `/pricing/` Stars live при `STARS_ENABLED=1` | |

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

