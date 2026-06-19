# Аудит: обращения к Neon после O271 (local Postgres)

**Дата:** 2026-06-19  
**Триггер:** login fail — `bot-poll` → Neon (quota), API → local  
**Канон:** [`PROD_FACTS.md`](../team/common/PROD_FACTS.md) · O271 · `DATABASE_URL` = **127.0.0.1** · Neon только `NEON_DATABASE_URL` (архив)

---

## Вывод

| Уровень | Что |
|---------|-----|
| **P0** | `bot_auth.py` и часть путей читают `os.getenv("DATABASE_URL")` **без** `load_radar_env()` и **без** запрета Neon на site |
| **P1** | O271 меняет только `.env.site`; корневой `.env` может **всё ещё** содержать Neon `DATABASE_URL` → риск при stale process / неверном порядке env |
| **P2** | Deploy/mechanic-скрипты с fallback `NEON_DATABASE_URL` |
| **OK** | Большинство `src/*` через `load_config().database_url` после `load_radar_env()` |
| **Legacy** | `neon_legacy_consumer.py` + `rawlead-radar-legacy` — отдельный профиль, не site prod |

**Site prod не должен открывать TCP к `*.neon.tech` — никогда.**

---

## P0 — runtime `src/` (критично)

| Файл | Проблема | Риск |
|------|----------|------|
| `src/bot_auth.py` | `_db_url()` = голый `os.getenv("DATABASE_URL")` | **Инцидент login** · bot-poll без reload env |
| `src/api_server.py` | `_db_url()` = голый `os.getenv` | Смягчено: `load_radar_env()` при import L158 |
| `src/owner_admin.py` | L1066, L1959: `os.environ.get("DATABASE_URL")` | Ops UI / restart paths без guard |
| `src/tg_client.py` | `load_dotenv(.env)` без site override | Косвенно, не auth |

**Безопасный паттерн (единый):**

```python
from config import load_radar_env, require_database_url

def connect():
    url = require_database_url()  # load_radar_env + load_config + site≠neon assert
    with psycopg.connect(url) as conn: ...
```

---

## P1 — конфиг VPS / systemd

| Файл | Проблема |
|------|----------|
| `deploy/systemd/rawlead-*.service` | `EnvironmentFile=.env` **затем** `.env.site` — site должен **всегда** задавать local `DATABASE_URL` |
| `scripts/migrate_neon_to_vps_postgres.py` | `cutover_env()` пишет только в `.env.site` |
| Корневой `/opt/rawlead/.env` | Может остаться старый `DATABASE_URL=…neon.tech…` |

**Ops (owner/Lead после O272):**

1. В `.env` **убрать** `DATABASE_URL` (или закомментировать) · Neon только `NEON_DATABASE_URL`
2. В `.env.site` единственный `DATABASE_URL=127.0.0.1:5432/rawlead`
3. `systemctl restart rawlead-api rawlead-bot-poll rawlead-radar` после правки
4. Probe: `db_kind=local` у **всех** трёх unit (см. O272)

---

## P2 — скрипты с Neon fallback (убрать на site)

| Скрипт | Строка / паттерн |
|--------|------------------|
| `scripts/_mechanic_o262e_feed_probe_vps.py` | `DATABASE_URL or NEON_DATABASE_URL` |
| `scripts/_mechanic_o262e_triage_vps.py` | то же |
| `scripts/_diag_secondary_logs_vps.py` | `NEON_DATABASE_URL or DATABASE_URL` |
| `scripts/deploy-o174b-vps.py` | `${DATABASE_URL:-$NEON_DATABASE_URL}` |
| `scripts/deploy-o185-vps.py` | grep `NEON_DATABASE_URL` fallback |
| `scripts/deploy-o107-vps.py` | `${DATABASE_URL:-$NEON_DATABASE_URL}` |

**Правило:** site-скрипты — только `DATABASE_URL` после `load_dotenv(.env.site, override=True)`; при neon host → **fail fast**.

---

## OK — уже через `cfg.database_url`

`match_push.py`, `draft_async.py`, `trial_subscription.py`, `telegram_control` (upsert via cfg), большинство API через `load_config()`.

---

## Legacy (не трогать site)

| Компонент | Назначение |
|-----------|------------|
| `src/neon_legacy_consumer.py` | `RADAR_PROFILE=legacy` · dogfood FLPARSINGBOT |
| `rawlead-radar-legacy.service` | Отдельный unit |
| `NEON_DATABASE_URL` в `.env.site` | Backup / миграция / ручной dump |

---

## Задача кода → **§ O272** в `CODER_PROMPT.md`

1. `require_database_url()` + `assert_site_not_neon()` в `config.py`
2. Заменить `_db_url()` в `bot_auth.py`, `api_server.py`; audit `owner_admin.py`
3. Startup log: `db: local|neon|unset` (без секретов) в api, bot_poll_main, main
4. `tests/test_o272_neon_guard.py`
5. `probe_prod_facts_vps.py` — fail/warn если site unit → neon
6. Scrub helper в migrate или ops-doc для root `.env`
7. Убрать Neon fallback из P2 скриптов

---

## Verify после O272

```bash
# на VPS — ни одна site-служба не должна показывать neon
for u in rawlead-api rawlead-bot-poll rawlead-radar; do
  PID=$(systemctl show $u -p MainPID --value)
  tr '\0' '\n' < /proc/$PID/environ | grep DATABASE_URL | grep -i neon && echo "FAIL $u"
done
journalctl -u rawlead-bot-poll --since '1h ago' | grep -i neon && echo FAIL || echo OK
```

Ожидание: пусто · login `bot_auth:ok` · API и bot одна local DB.
