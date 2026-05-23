# ТЗ — HTTP API (RawLead backend)

Версия: **0.1** · Lead · 2026-05-23

Связано: [`NEON_SCHEMA.md`](NEON_SCHEMA.md) · [`TZ_WP.md`](TZ_WP.md) · [`ARCHITECTURE.md`](ARCHITECTURE.md)

**Решение владельца:** сайт (WP) + подписки + Telegram-бот; **отдельного mobile app нет**.

---

## 1. Роль API

Единая точка между:

- **WordPress** (кабинет, теги, лента, оплата)
- **Neon** (лиды, пользователи)
- **Telegram-бот** (персональные дайджесты)
- **Рadar** (только ingest, не публичный)

```
[WP кабинет] ──REST──► [RawLead API] ◄── ingest ── [Рadar Python]
                            │
                            ▼
                       [Neon Postgres]
                            │
[TG Bot] ◄── poll/send ─────┘
```

---

## 2. MVP эндпоинты

| Method | Path | Кто | Действие |
|--------|------|-----|----------|
| `GET` | `/health` | мониторинг | ok + версия |
| `GET` | `/v1/feed` | WP (user JWT) | лиды, sorted by `final_rank`, limit, offset |
| `GET` | `/v1/leads/{id}` | WP | одна карточка + breakdown score |
| `PUT` | `/v1/me/tags` | WP | сохранить `user_tags[]` |
| `GET` | `/v1/me/tags` | WP | текущие теги |
| `GET` | `/v1/me/subscription` | WP | plan, active_until |
| `POST` | `/v1/internal/leads` | radar (API key) | upsert lead + ai_score + lead_tags |
| `GET` | `/v1/internal/digest` | bot (API key) | top-K leads per user where rank ≥ threshold |

**Не в MVP:** OAuth, webhooks оплаты, admin panel.

---

## 3. `GET /v1/feed`

**Query:** `limit` (default 20), `min_rank` (default 50), `since` (ISO datetime).

**Auth:** Bearer token (WP plugin выдаёт после login).

**Response (фрагмент):**

```json
{
  "items": [
    {
      "id": 123,
      "source": "tg:1204578088",
      "title": "...",
      "final_rank": 88,
      "ai_score": 92,
      "keyword_match": 82,
      "reasons": ["бюджет ок", "Python в тексте"],
      "url": "..."
    }
  ]
}
```

**Логика:** см. [`NEON_SCHEMA.md`](NEON_SCHEMA.md) §3.

---

## 4. Бот — персональная рассылка

| Сейчас (этап 0) | v1 SaaS |
|-----------------|---------|
| один `TELEGRAM_CHAT_ID` | `users.tg_chat_id` per подписчик |
| все лиды владельцу | digest: top-3 за 4 ч, `final_rank ≥ N` |
| | только `subscriptions.active_until > now()` |

Рadar **не** рассылает сам по 100 юзерам — **worker/cron** или цикл в `tg_main` extension вызывает `/v1/internal/digest` и `sendMessage` per user.

---

## 5. Безопасность

| Секрет | Где |
|--------|-----|
| `DATABASE_URL` | `.env` radar + API server |
| `RAWLEAD_API_KEY` | ingest + bot → internal routes |
| JWT secret WP↔API | WP plugin config, не Git |

Rate limit на `/v1/feed` — per user.

---

## 6. Деплой (этапы)

| Этап | Где API | Где radar |
|------|---------|-----------|
| Dev | localhost :18766 | ПК |
| v1 | тот же VPS что radar 24/7 | VPS |

Local WP (`radarzakaz.local`) → API на `localhost` или ngrok для отладки.

---

## 7. Очередь Coder

1. Расширить Neon schema ([`NEON_SCHEMA.md`](NEON_SCHEMA.md)).
2. `src/api/` или `scripts/rawlead_api.py` — FastAPI/Flask minimal.
3. Ingest из pipeline → `ai_score` + `lead_tags` в prompt ИИ.
4. WP plugin «кабинет» — REST client (фаза после API).

Приёмка: два тестовых user с разными тегами → разный порядок в `/v1/feed`.

---

_Coder — только по `CODER_PROMPT.md` от Lead._
