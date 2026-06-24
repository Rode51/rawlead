# RawLead — канон продукта (единый источник для PM / Design / QA)

**Назначение:** все лимиты, тарифы, потоки, тексты «как должно быть». PM проходит по разделам и сверяет с `/lenta/`, `/cabinet/`, `/pricing/`, FAQ, ботом — без противоречий в UX и логике.

**Обновляют:** `@lead-product` (содержание) · `@lead-architect` (технические факты из кода) · `@lead-designer` (UI-таблица).

**Не дублировать в чат** — правки только здесь + handoff в `LEAD_*_PROMPT`.

---

## 1. Тарифы и доступ

| Статус | Цена | Срок | Что даёт | Ограничения |
|--------|------|------|----------|-------------|
| **Anon** | 0 | — | `/lenta/` с задержкой ~15 мин | Нет черновиков, нет push, нет inbox |
| **Free (TG-login)** | 0 | — | Лента без задержки, match-фильтр | Нет Premium: черновики, push, слоты |
| **Trial** | **1 ₽** | **3 дня** | Полный Premium | **1× на `user_id` навсегда** |
| **Premium** | **790 ₽/мес** | 30 дн. | Черновики L2, push match, inbox, слоты | Автопродление **⏸** до O174d |
| **Owner** | — | — | Полный доступ без оплаты | `@rcnn43` |

**Owner 2026-06-12:** на **trial** должна быть кнопка **«Подключить Premium»** (790 ₽) — не блокировать «Уже есть Premium». → § **O185** t1.

**Отмена / автопродление:** после первых платящих (O174d) — красная «Отменить» + `YOOKASSA_SAVE_PAYMENT_METHOD=1`.

---

## 2. Оплата (ЮKassa) — цепочка

| Шаг | Где | Что происходит |
|-----|-----|----------------|
| 1 | `/cabinet/` | Клик trial / Premium → `POST /v1/me/subscription/checkout` |
| 2 | API | Создаёт платёж в ЮKassa, строка `yookassa_payments` **pending**, `metadata`: `user_id`, `kind` |
| 3 | Браузер | Redirect на `confirmation_url` ЮKassa |
| 4 | ЮKassa | Оплата карта/СБП |
| 5a | Webhook | `POST /v1/webhooks/yookassa` `payment.succeeded` → API **GET payment по id** в ЮKassa → `apply_payment_succeeded` |
| 5b | Return | `/cabinet/?pay=return` → `POST /v1/me/subscription/confirm` → ищет **pending в Neon** → **GET payment по id** в ЮKassa → если `succeeded` и webhook ещё не успел — activate |
| 6 | Neon | `subscriptions` trial/premium · `yookassa_payments.status=succeeded` |

**Идемпотентность:** atomic **claim** `pending→processing→succeeded` (O185 w1 ✅). Webhook ∥ confirm — второй поток no-op.

**Owner smoke ✅ 2026-06-12:** trial **1 ₽** · subscription **10 ₽** on trial (prod) · revert **790** · claim idempotent.

**Owner smoke pending:** none — pay path closed until O174d.

**Confirm vs pending:** в Neon ищется `status='pending'`; статус в ЮKassa на return обычно уже `succeeded` — confirm опирается на **GET YooKassa**, не на слово pending в шлюзе.

**Данные пользователя в ЮKassa:** сумма, idempotence key, return URL — **не** передаём email/телефон из Neon без необходимости.

**JWT:** вход TG Login → token **7 дней** · все `/v1/me/*` только с Bearer.

**Риски (аудит O185 t7):** включить `YOOKASSA_WEBHOOK_SECRET` на VPS · pytest webhook idempotency · smoke 790 ₽ · confirm не на каждый load ✅.

---

## 3. Match / совместимость

**Задумка owner 2026-06-12:** % = «насколько заказ закрывается навыками пользователя». Если в заказе **Python**, а у пользователя **Python + Java** → **100%**, не штраф за лишние навыки.

**Сейчас в коде (`rank.py` O185 w2):** % = matched lead tags / all lead tags · **лишние** навыки пользователя **не штрафуют** (Python+Java + заказ Python → **100%**).

**Фильтр min_match:** отсечка по этому % · не путать с L1 `ai_score`.

---

## 4. Навыки (**quiz-first · owner 2026-06-15**)

| Правило | Значение |
|---------|----------|
| **Источник профиля** | Квиз (import) + поведение в ленте · **без** ручного picker |
| **Лимит тегов** | **Нет** (снят max 12 — был только для manual UI) |
| Хранение | Neon `user_tags` + sync rev · meta `__quiz_niche:*` |
| Guest merge | После TG-login guest-теги сливаются |
| **Сохранённые навыки** | Neon `user_tags` · cabinet sort/min_match в sessionStorage |
| **«Сбросить фильтры»** | Сбрасывает source/category/sort · **не** трогает навыки → **O185 t5b ✅** |
| **Retake квиза** | Единственный способ **перезаписать** профиль целиком (import replace) |

~~Макс. тегов 12~~ · ~~«Сбросить навыки» на полоске~~ — **deprecated** с quiz-first (O208).

---

## 5. Push Telegram

| Условие | Деталь |
|---------|--------|
| Premium/trial | `push_enabled` + match ≥ порог |
| Бот | `@rawlead_bot` · нужен `/start` + `tg_chat_id` |
| Copy в ЛК | **Убрать** строку «Premium — оплата… Push — /start…» → § **O185** t2 |

---

## 6. Лента / ingest

| Источник | Статус prod |
|----------|-------------|
| FL, Kwork | ✅ основной поток |
| TG whitelist | ✅ |
| YouDo | **fix deployed 2026-06-12** — stealth + SPA detect + честный /ops/ · первый fetch после cooldown — smoke |

---

## 7. Retention Neon

| Что | Политика |
|-----|----------|
| `leads` | DELETE старше **2 дней** · `scripts/purge_old_leads.py` |
| Delisted | purge через **1 день** (env `DELIST_PURGE_DAYS`) |
| Users/tags/subs | **не трогаем** |
| Расписание VPS | systemd `rawlead-purge-leads.timer` **03:15 daily** |

**Owner 2026-06-12:** Neon ~**80%** — Lead: **не менять политику**, проверить что timer **enabled** и purge реально бежит (→ O185 t8 ops).

---

## 8. Безопасность (чеклист PM + QA)

- [ ] Все `/v1/me/*` без token → 401
- [ ] Checkout чужого `user_id` невозможен (JWT)
- [ ] Webhook без секрета / с подделкой → не активирует чужую подписку
- [ ] Confirm только свой pending payment
- [ ] Нет секретов в WP/JS (только public bot username)
- [ ] Pentest scope: auth, IDOR на draft/inbox, rate limit checkout — § **O186-SECURITY-AUDIT**

---

## 9. PM audit — страницы (пройтись и отметить)

| URL | Сверить с § |
|-----|-------------|
| `/` | тарифы, trial 1 ₽, без Stars/crypto |
| `/pricing/` | 790 ₽, trial, ЮKassa, legal footer |
| `/faq/` | оплата, trial 1×, без устаревших Stars |
| `/lenta/` | anon delay vs auth, match % |
| `/cabinet/` | подписка, навыки, push toggle, inbox |
| `/how/` | flow без противоречий |
| Footer | FIO + ИНН (O174a) |

**Handoff PM:** `@lead-product` § **PRODUCT-CANON-AUDIT** в `LEAD_PRODUCT_PROMPT.md`.

---

_Создан Lead Architect **2026-06-12** по запросу owner · дополнять по мере закрытия O185/O186._
