# 2026-06-18 — Neon compute quota exceeded

**Статус:** 🔴 open · ingest/L2 regen blocked

---

## Симптом

- `purge_old_leads.py --dry-run` на VPS → `ERROR: Your account or project has exceeded the compute time quota`
- O200 `regen_shared_reply_drafts` — SSL/quota fail
- Owner: «Neon недоступен, память кончилась»

## Факты

| Проверка | Результат |
|----------|-----------|
| Autocleanup timer | ✅ `rawlead-purge-leads.timer` **active** |
| Last purge | **2026-06-18 03:15** — **607** rows >7d + **92** delisted |
| Root error | **Compute time quota** (Neon billing), не отсутствие скрипта purge |

## Owner unblock

1. [console.neon.tech](https://console.neon.tech) → проект → **Billing / Usage**
2. Upgrade plan **или** дождаться monthly reset квоты
3. Если лимит **storage** — SQL Editor → проверить размер; удалить старые branches

## После восстановления Neon

```bash
cd /opt/rawlead
sudo -u rawlead env PYTHONPATH=/opt/rawlead/src .venv/bin/python scripts/purge_old_leads.py --apply
systemctl restart rawlead-api rawlead-radar   # если останавливали
```

## Coder

§ **O270-NEON-QUOTA-RETENTION** in `CODER_PROMPT.md` — probe storage · circuit breaker · ops visibility.
