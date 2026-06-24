# Миграция Neon → Postgres на VPS (O271)

**Статус:** ✅ **prod на VPS** (2026-06-19) · **локальный** `.env.site` с `*.neon.tech` — заменить (§ `PREPROD_ACCOUNTS` 1b).

**Зачем:** Neon Free — `compute time quota exceeded` · оплата из РФ недоступна · Postgres на том же VPS = localhost, без квоты.

---

## Что переносим

| Данные | Метод |
|--------|--------|
| Вся схема + данные | `pg_dump` → `pg_restore` (если старый Neon пускает) |
| `users`, `subscriptions`, `leads`, drafts | внутри dump |
| SQLite на VPS | не трогаем · backfill опционально после |

**Не в git:** `DATABASE_URL`, дампы (`/opt/rawlead/data/neon_pre_migration_*.dump`).

---

## Rollback

1. В `.env.site` вернуть старый `DATABASE_URL` (Neon).
2. `systemctl restart rawlead-api rawlead-radar`.
3. Локальный Postgres можно остановить: `systemctl stop postgresql`.

Сохранить копию строки Neon **до** правки (owner local, не в repo).

---

## Шаги (VPS)

```bash
# 1. Пауза ingest
systemctl stop rawlead-radar rawlead-api

# 2. Дамп (пока Neon отвечает)
cd /opt/rawlead
sudo -u rawlead bash -c 'set -a; source .env.site; set +a; \
  pg_dump "$DATABASE_URL" -Fc -f data/neon_pre_migration.dump'

# 3. Postgres
apt-get update && apt-get install -y postgresql postgresql-client

# 4. БД (пароль — owner, не в git)
sudo -u postgres psql -c "CREATE USER rawlead WITH PASSWORD '...';"
sudo -u postgres psql -c "CREATE DATABASE rawlead OWNER rawlead;"

# 5. Restore
sudo -u rawlead pg_restore -d postgresql://rawlead:...@127.0.0.1/rawlead \
  --no-owner --no-acl data/neon_pre_migration.dump

# 6. .env.site — DATABASE_URL=postgresql://rawlead:...@127.0.0.1:5432/rawlead?sslmode=disable

# 7. Старт
systemctl start rawlead-api rawlead-radar
systemctl enable rawlead-purge-leads.timer

# 8. Smoke
curl -sS http://127.0.0.1:8000/health
# лента, логин TG, подписка
```

---

## После миграции (@coder)

- `scripts/probe_neon_storage.py` → `probe_pg_storage.py`
- Бэкап timer: `pg_dump` daily в `/opt/rawlead/data/backups/`
- `PROD_FACTS.md` — `DATABASE_URL` = local

---

_Lead · 2026-06-18 · O271_
