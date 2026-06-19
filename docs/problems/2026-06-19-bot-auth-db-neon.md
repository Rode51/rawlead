# bot Start — нет ответа, login 401 (Neon DB в bot-poll)

**Дата:** 2026-06-19  
**Симптом:** ПК + QR · Start в @rawlead_bot · **тишина в боте** · сайт «Ждём подтверждение…» → 401  
**Не фронт:** API создаёт `auth_bot_sessions` в local Postgres · poll ок

## Root cause (VPS probe)

`rawlead-bot-poll` при `/start auth_*` вызывает `authorize_bot_auth_session` → **`DATABASE_URL` у процесса = Neon** (quota exceeded), не `127.0.0.1:5432/rawlead`.

Лог:

- `radar_site.log`: `bot_auth:fail db error`
- `journalctl -u rawlead-bot-poll`: `authorize_bot_auth_session: ... ep-patient-dust-apq8gv3s-pooler ... exceeded the compute time quota`
- API: `GET /v1/auth/bot-complete?auth=...` → **401** `awaiting bot authorization`
- `auth_bot_sessions`: `authorized_at IS NULL` на свежих сессиях

При `ok=False` бот **не шлёт** сообщение пользователю → «никакой реакции».

## Fix

| Шаг | Кто | Действие |
|-----|-----|----------|
| 1 | Lead/owner | `systemctl restart rawlead-bot-poll` ✅ 2026-06-19 |
| 2 | @coder | **§ O272-NEON-GUARD** — единый `require_database_url()` + запрет neon на site · см. [`2026-06-19-neon-db-audit.md`](2026-06-19-neon-db-audit.md) |
| 3 | @coder | `_handle_bot_auth_start`: при fail — `sendMessage` с RU-текстом (не молчать) |
| 4 | owner | Smoke: QR → Start → «✓ Вход подтверждён» + header `@nick` |

## Verify

```bash
journalctl -u rawlead-bot-poll --since '5 min ago' | grep -E 'bot_auth:ok|bot_auth:fail'
grep bot_auth /opt/rawlead/data/radar_site.log | tail -5
```

Ожидание: `bot_auth:ok` · в БД `authorized_at` NOT NULL · API bot-complete **200**.
