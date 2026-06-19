# Draft «ИИ временно недоступен» — мёртвый OpenRouter proxy

**Дата:** 2026-06-19  
**Симптом:** сайт + TG · `ИИ временно недоступен — повторите` · lead **6830** / **6838**

## Причина

L2 draft ходит в OpenRouter **через proxy** (`OPENROUTER_HTTP_PROXY` в `.env.site`, 1 slot).

```
ProxyError: HTTPSConnectionPool(host='openrouter.ai'...): Unable to connect to proxy
```

**Direct** с VPS: `GET openrouter.ai/api/v1/models` → **200** ✅

Доп. баг: `_log_ai_failure` в `ai_analyze.py` — `if not errors` пропускает запись при **пустом** `ai_errors[]` → в UI только generic «ИИ временно недоступен».

## Fix P0 (ops)

1. ~~`.env.site` — убрать `OPENROUTER_HTTP_PROXY`~~ **owner 2026-06-19:** proxy **38.154.16.60:8000** поднят
2. Verify: `openrouter_via_proxy` **200** ✅ (Lead probe)
3. Owner: retry draft на ленте / TG

**Если всё ещё fail:** уже не ProxyError — смотреть `AiAnalyzeError` / пустой ответ модели → § O280-R11

## Fix P1 (code → @coder § O280-R11)

- `_log_ai_failure`: `if errors is None` вместо `if not errors`
- `_openrouter_chat`: при `ProxyError` → retry **direct** (как L1 fallback)

## Ref

`src/ai_analyze.py` `_openrouter_chat` · `analyze_shared_reply_draft` `use_draft_proxy=True`
