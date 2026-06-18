# INCIDENT: api.rawlead.ru 502 — feed + cabinet login dead

**When:** 2026-06-13 (owner smoke after O201/O190/O202 deploy batch)

## Symptoms

- `/lenta/` anon: «Не удалось загрузить»
- `/cabinet/`: «Не удалось открыть Telegram…» (bot-session via WP → API)
- Lead probe:
  - `https://api.rawlead.ru/v1/feed?limit=1` → **502 Bad Gateway**
  - `https://api.rawlead.ru/v1/quiz/start` → **502**
  - `https://rawlead.ru/wp-json/rawlead/v1/feed?limit=1` → **500**

## Likely cause

`deploy-o201-ops500-vps.py` uploaded `api_server.py` with:

```python
from src.tg_spam_corpus import fetch_corpus_summary, mark_tg_lead_spam
```

If `tg_spam_corpus.py` was **not** on VPS before `systemctl restart rawlead-api` → **ImportError** → unit failed → nginx 502.

## Fix (owner / @coder)

**1. Upload missing module + restart API:**

```powershell
cd C:\Users\hramo\uisness
python -c "import sys; from pathlib import Path; sys.path.insert(0,'scripts'); import deploy_vps_ssh as s; r=Path('.'); s.upload(r/'src/tg_spam_corpus.py','/opt/rawlead/src/tg_spam_corpus.py'); s.run('chown rawlead:rawlead /opt/rawlead/src/tg_spam_corpus.py && systemctl restart rawlead-api && sleep 4 && systemctl is-active rawlead-api && journalctl -u rawlead-api -n 15 --no-pager')"
```

**2. Verify:** feed returns 200:

```powershell
python -c "import urllib.request; print(urllib.request.urlopen('https://api.rawlead.ru/v1/feed?limit=1', timeout=20).status)"
```

**3. If still down:** `journalctl -u rawlead-api -n 80` on VPS — paste traceback to Mechanic.

## Do not

- Debug O199 feed UI until API is **active**
- Full redeploy radar unless needed

## Follow-up

- `@coder`: one-shot `scripts/deploy-o202-api-vps.py` (tg_spam_corpus + api restart guard)
- Deploy docs: always upload `tg_spam_corpus.py` **before** api_server restart
