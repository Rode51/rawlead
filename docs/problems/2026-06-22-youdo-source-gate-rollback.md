# YouDo SOURCE-GATE deploy — откат

**Дата deploy:** 2026-06-22 (Lead, после verify ✅)

## Что залили

| Файл | Зачем |
|------|--------|
| `src/lead_pipeline.py` | gate rev2: только `detail_ok` · `youdo_no_detail` |
| `src/youdo_parser.py` | dedup `list_project_ids` · click-through cache |
| `src/public_feed.py` | FEED-HYGIENE: скрыть `ai_verdict=МИМО` |
| `src/vacancy_filter.py` | маркеры физуслуг |
| `scripts/backfill_feed_hygiene_vps.py` | one-shot delist (не запускали без owner) |

**Сервисы:** `systemctl restart rawlead-radar rawlead-api`

## Быстрый откат (код)

На VPS, под root:

**Backup этого deploy:** `/opt/rawlead/data/backups/pre_source_gate_20260622-114840.tar.gz` (24K)

```bash
tar -xzf /opt/rawlead/data/backups/pre_source_gate_20260622-114840.tar.gz -C /
chown rawlead:rawlead /opt/rawlead/src/lead_pipeline.py /opt/rawlead/src/youdo_parser.py /opt/rawlead/src/public_feed.py /opt/rawlead/src/vacancy_filter.py
systemctl restart rawlead-radar rawlead-api
systemctl is-active rawlead-radar rawlead-api
```

## Откат click-through (без tar)

```bash
# в /opt/rawlead/.env.site
YOUDO_CLICK_DETAIL=0
systemctl restart rawlead-radar
```

## Откат ленты YouDo (вернуть сниппеты)

```bash
cd /opt/rawlead
sudo -u rawlead env RADAR_PROFILE=site PYTHONPATH=/opt/rawlead/src \
  .venv/bin/python scripts/restore_youdo_visible_vps.py --apply
```

Ожидание: `restored≈4200` visible YouDo (snippet mode).

## Откат браузер-профиля (если сессия убита)

**Не** `deploy-o268` (wipes profiles).

```bash
ls -la /opt/rawlead/data/backups/youdo_profile_pre_clickthrough_2026-06-22.tar.gz
# restore по playbook O268 / ops — только если sticky/antibot совсем мёртв
```

## Проверка после отката

```bash
grep -c youdo_no_detail /opt/rawlead/src/lead_pipeline.py   # 0 = старый код
grep 'fetch:youdo' /opt/rawlead/data/radar_site.log | tail -5
curl -sS 'https://rawlead.ru/v1/feed?source=youdo&limit=3' | head -c 400
```

## Диагностика «не попадает в ленту»

| Симптом в логе | Смысл |
|----------------|--------|
| `youdo:ingest done=0 new=0` | Листинг ок, **все 50 id уже в SQLite** — не баг deploy |
| `click_ok=0` | Click-through не достал detail (или нет new id) |
| `pipeline:skip youdo:… no_detail` | Source-gate: нет detail → не в ленту |
| `html_len=1701` + antibot | ServicePipe shell — ждать sticky/след. цикл |
| `parsed=0` | Парсер пустой — antibot/листинг |
