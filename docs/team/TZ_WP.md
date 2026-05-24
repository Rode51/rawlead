# ТЗ — WordPress (маркетинг + кабинет + подписки)

Версия: **0.2** · Lead · 2026-05-23

**Решение владельца:** **сайт с подписками** + Telegram-бот; **mobile app нет**.

Связано: [`PRODUCT_VISION.md`](PRODUCT_VISION.md) · [`NEON_SCHEMA.md`](NEON_SCHEMA.md) · [`TZ_API.md`](TZ_API.md)

---

## 1. Две роли WP

| Роль | Статус | Что |
|------|--------|-----|
| **Маркетинг** | ✅ MVP | Kadence child, REFERENCE E — [`WP_KADENCE_INSTALL.md`](../ops/WP_KADENCE_INSTALL.md) |
| **Кабинет (SaaS)** | → фаза 3b | теги, лента, подписка |

WP **не** парсит FL/TG. WP **не** подключается к Neon Postgres напрямую (shared-хостинг).

---

## 2. Архитектура v1

```
[Посетитель] → WP маркетинг (лендинг, тарифы)
[Подписчик]  → WP кабинет (логин, теги, лента)
                    ↓ HTTPS + JWT
              [RawLead API] ←→ [Neon]
                    ↑
              [Рadar Python] ingest
                    ↓
              [TG Bot] digest per user
```

База лидов — **Neon**. База WP — **MySQL** хостера (только WP users, WooCommerce, плагины).

---

## 3. MVP кабинета (после API)

| Экран | Действие |
|-------|----------|
| Регистрация / вход | стандартный WP или Members |
| **Мои теги** | чекбоксы/поля: Python, FastAPI, парсеры… → `PUT /v1/me/tags` |
| **Лента** | `GET /v1/feed` — карточки с **final_rank** и breakdown |
| **Подписка** | plan free/pro; `active_until` (v0 — ручной флаг или WooCommerce) |
| **Telegram** | привязка `tg_chat_id` для digest |

**Не в MVP кабинета:** свайп-UI, графики аналитики, админка радара.

---

## 4. Плагин / тема

| Вариант | Lead |
|---------|------|
| Child theme `rawlead-kadence-child` + page template «Кабинет» | предпочтительно |
| Отдельный плагин `rawlead-cabinet` | если логика разрастается |

REST-клиент к API: Bearer из сессии WP (HMAC plugin ↔ API).

---

## 5. Подписки

| Этап | Как |
|------|-----|
| v0 | Lead/Coder: поле `plan` в Neon вручную |
| v1 | WooCommerce Subscriptions или ЮKassa webhook → API `PATCH /v1/me/subscription` |

Тарифы на странице [`pricing`](../archive/wp-skeleton/pricing.md) — тексты в архиве скелета.

---

## 6. Бот для подписчиков

| Этап 0 | v1 SaaS |
|--------|---------|
| один chat_id владельца | `users.tg_chat_id` |
| все уведомления | digest top-3, `final_rank ≥ N` |

Бот **не** читает Neon сам — только **API** ([`TZ_API.md`](TZ_API.md) §4).

---

## 7. Хостинг (без изменений)

Shared WP **150–350 ₽/мес** + Neon Free. Рadar/API позже на VPS. См. старый § «Хостинг» в git history при необходимости.

Local: `radarzakaz.local` — учёба, [`WP_LOCAL_SKELETON.md`](../ops/WP_LOCAL_SKELETON.md).

---

## 8. Очередь (Lead → Coder)

| # | Задача | Зависимость |
|---|--------|-------------|
| 1 | Neon schema v1 | [`NEON_SCHEMA.md`](NEON_SCHEMA.md) |
| 2 | RawLead API | [`TZ_API.md`](TZ_API.md) |
| 3 | Ingest: `ai_score` + `lead_tags` в pipeline | API key |
| 4 | WP кабинет (теги + лента) | API на staging |
| 5 | Бот multi-user digest | API + subscriptions |

**Не ждёт:** доработка маркетинговой темы (Designer).

---

## 9. Приёмка кабинета

- [ ] Два тестовых пользователя, разные теги → **разный порядок** в ленте.
- [ ] На карточке видны `ai_score`, `keyword_match`, `final_rank`.
- [ ] Подписчик с истёкшей подпиской не получает digest в боте.
- [ ] Секреты API/Neon не в Git.

---

_Lead 2026-05-23 · Supabase в тексте устарел → Neon._
