# ИИ draft недоступен (intermittent) — 2026-05-30

**Симптом:** «Не удалось сгенерировать черновик» / «ИИ временно недоступен — повторите» на `/lenta/`.

**Prod (Lead VPS 2026-05-30 ~15:44 UTC):**

- `journalctl -u rawlead-api`: `lenta:draft:7578:fail` ×2
- Следом: draft **7592**, **7588** — **200 OK** (intermittent, не total outage)
- Site L1: `pipeline:L1 fl:id=5507351 visible=1` — **lite работает**

**Разделение:**

| Слой | Статус |
|------|--------|
| L1 (лenta, tags) | OK |
| L2 draft (OpenRouter full) | Fail на части запросов |

**Coder:** § **O67** в `CODER_PROMPT.md`.

**Mechanic если ключ OK:** OpenRouter 429, model id, timeout в `draft_async.py`.

**Ops владельцу:** проверить `OPENROUTER_API_KEY` в `.env.site` · баланс OpenRouter.
