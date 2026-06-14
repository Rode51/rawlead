# TASKS (активное)

**Снимок:** [`STATUS.md`](STATUS.md)

---

## Где мы

**Волна 1:** ingest/ops ✅ · **O215:** design polish (BrowserSync) **→ сейчас**  
**Волна 2:** **O209** ✅ theme **1.18.84** · deploy 2026-06-14  
**До ads:** Perf **после O215** · L2 **70%** · stress финал

---

## До soft ads (owner 2026-06-13)

| Волна | § | Кто |
|-------|---|-----|
| 1 TG | t2b · O207 · join | @coder |
| 2 Концепция | **O208** quiz-first UI/copy/воронка | @lead-product → @lead-designer → @coder |
| 3 Perf | lenta/home/quiz load | Design scope → @coder |
| 4 L2 | O200 regen **≥70%×4** | @coder |
| 5 Pre-ads | stress @50 · security | owner |
| 6 GTM | ads | ⏸ |

**Гейт ads:** O207 ok · L2 **70%**×4 · stress green.

---

## Шаги (hot)

| # | Что | Кто | Статус |
|---|-----|-----|--------|
| **43** | O203-HOTFIX + O199 | @coder | ✅ Lead local |
| **44** | Deploy **1.18.81** + VPS hotfix | owner | ✅ |
| **45** | Prod smoke | owner | ⚠️ filter ❌ |
| **46** | **O204** filter + msgs stats | @coder | ✅ Lead verify |
| **48** | **O205** t2+t5 spam+ops CSP | @coder | ✅ deploy |
| **49** | **O205** t1+t6+t7 fast ops+TG+banner | @coder | ✅ deploy |
| **50** | **O205** t10+t11+t13 deploy | Lead | ✅ 2026-06-13 |
| **51** | Owner smoke O205 (чеклист) | owner | **→ сейчас** |
| **52** | **O206** t1–t4 deploy | Lead | ✅ 2026-06-13 |
| **53** | Owner smoke test group | owner | ✅ мгновенно |
| **56** | **O206 t3c** watchdog zombie | @coder | ✅ Lead verify+deploy |
| **55** | **O206 t2b** sync chat_ids | @coder | ✅ Lead verify 2026-06-14 |
| **57** | **O207** TG funnel · history sample + replay | @coder | ✅ Lead verify 2026-06-14 |
| **58** | **O209** match-first UX+copy | @coder | ✅ Lead verify+deploy 2026-06-14 |
| **58b** | **FL-PROXY-STABILITY** + residential env | Lead | ✅ 2026-06-14 |
| **58d** | **O207b** TG filter tune (8 false blocks) | @coder | ✅ Lead verify 2026-06-14 |
| **58e** | **O207b** deploy radar + **O211** deploy API footer | @coder | ✅ Lead verify 2026-06-14 |
| **58f** | **O212** ops log spam + TG 🔴 false + «0 новых» UX | @coder | ✅ Lead verify 2026-06-14 |
| **58g** | **O213** Kwork pagination (page2-3) + filter scope | @coder | ✅ Lead verify 2026-06-14 |
| **58h** | **O213+O212 deploy** radar + API | @coder | ✅ Lead verify VPS 2026-06-14 |
| **58i** | **O214** ops truth: cycle_age fallback + residential badge | @coder | ✅ Lead verify VPS 2026-06-14 |
| **59** | **O215** WP design polish (BrowserSync local) | @designer + owner | **→ сейчас** |
| **60** | **Perf** lenta/home/quiz | @lead-designer → @coder | после O215 OK |
| **61** | **Stress** финал @50 VU | owner | **перед ads** |

---

## План O208 (owner 2026-06-13)

Quiz-first: UI/UX · тексты · воронка · **без ручного выбора навыков**.  
PM: `LEAD_PRODUCT_PROMPT` § O199 · Design: § O199-QUIZ-UX · `ROADMAP` § O208.

---

## План O207 (owner 2026-06-13)

**Цель:** понять, **есть ли заказы в группах** и **точно ли** их режет filter/L1 — не listen/handler.

1. Truth ladder + per-chat health в `/ops/tg`
2. Sample skip audit — owner метит «заказ / шум»
3. Filter lab — replay корпуса до деплоя правок
4. Golden posts в test group

Детали: [`ROADMAP.md`](../architect/ROADMAP.md) § **O207** · тикет [`tg-feed-volume`](../problems/2026-06-13-tg-feed-volume.md)

---

## Local smoke (перед VPS — обязательно)

```powershell
cd C:\Users\hramo\uisness
python -m pytest tests/test_o175_feed_inbox.py tests/test_o202_tg_spam_corpus.py tests/test_o171_ops_funnel.py -q
```

**WP UI (один раз):**
```powershell
.venv\Scripts\python.exe scripts\wp_link_theme_local.py --force
cd wordpress\rawlead-kadence-child
npm.cmd install
npm.cmd run dev
```
Если `npm` в PowerShell ругается на ExecutionPolicy — используй **`npm.cmd`**, не `npm`.

Браузер: `http://localhost:3000/lenta/` (прокси на `radarzakaz.local`).

**Кабинет локально:** junction ≠ вход. Нужны оба:
1. LocalWP **radarzakaz** → Start
2. API локально: `uvicorn` (см. `docs/ops/RUN.md` §5) + в `wp-config.php`: `RAWLEAD_API_URL` → prod **или** `http://127.0.0.1:18766`
3. Вход TG на `http://radarzakaz.local/cabinet/` — виджет на HTTP часто **не работает**; для UI-тестов ленты достаточно **prod API** + local WP.

**/ops/ локально не тестируется** — только `https://rawlead.ru/ops/` (пароль пульта, не кабинет TG).

**Проверить локально:** фильтр TG · спам · glow → **потом** `deploy-wp-theme-vps.py`.

**Радар/ops control** — только VPS; баннер «Перезапустить радар» сейчас **только скролл** → **Управление** → `Radar: перезапуск`.

### 1. Deploy (PowerShell, по порядку)

```powershell
cd C:\Users\hramo\uisness
python scripts/deploy-o190-tg-join-listen-vps.py
python scripts/deploy-wp-theme-vps.py
```

**Ожидай:**
- `o190_tg_join_listen_deploy_ok` + `active` (радар)
- theme **1.18.82** на сайте

**Если API 502 после deploy:** на VPS должен быть `tg_spam_corpus.py` — скрипт выше заливает его; `systemctl restart rawlead-api`.

---

### 2. Чеклист smoke

#### A. API (30 сек)
- [ ] `https://api.rawlead.ru/v1/feed?limit=1` → **200**, не 502
- [ ] Hard refresh `/lenta/` (Ctrl+F5) — новая версия CSS

#### B. `/ops/` → Telegram
- [ ] Колонки на русском: **Аккаунт · Состояние · Слушают · …**
- [ ] **acc1/acc2:** 🟢 или 🟡 (не 🔴) при **X · X · X** и без auth_error
- [x] **acc3:** 24/24 · лампы 🟢
- [ ] **Сообщения:** сессия + всего (после O204)
- [ ] Наведи на лампу/состояние — tooltip **причина** (`lamp_reason_ru`)
- [ ] Под таблицей: **«Очередь: N готово · …»**

#### C. `/lenta/` анон (инкогнито)
- [ ] Карточки грузятся
- [ ] TG-карточка (владелец) → **«Спам»** → «Учтём в фильтре» · карточка исчезла
- [ ] Ошибки спама: 403 → «Только владелец» · 404 → «Уже скрыт» (если повторный клик)
- [ ] **«Написать отклик»** → **карточка жёлто пульсирует** + полоска и пульс на кнопке

#### D. `/lenta/` залогинен (`/cabinet/` → Лента)
- [x] Карточки грузятся — **нет** «Не удалось загрузить»
- [x] **Нет** кнопки «Навыки» / ручного picker
- [x] «Написать отклик» → glow + toast черновика
- [ ] **Сортировка → Telegram → Применить** — только TG-карточки (**❌ O204**)
- [ ] TG → **«Спам»** → «Учтём в фильтре»

#### E. Опционально
- [ ] `python scripts/tg_spam_corpus_export.py` — count +1 после «Спам»

---

### 3. Отчёт Lead

Напиши: «smoke ок» или что красное (скрин + acc + URL). Lead закроет § в промпте.
