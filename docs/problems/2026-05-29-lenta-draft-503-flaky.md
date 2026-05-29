# Лента: второй черновик 503 (lead 7019)

**Дата:** 2026-05-29  
**Статус:** → @coder § **O56a** (async) + **O48** baseline · `CODER_PROMPT.md`  
**Контекст:** приёмка PRE-STRESS-PACK · `/lenta/` «Написать отkлик»

## Симптом

Первый черновик **OK** (lead **7051**, 200). Второй — **«Не удалось сгенерировать черновик»** (lead **7019**, **503** ×3).

Prod log:
```
POST /v1/me/leads/7051/draft → 200
POST /v1/me/leads/7019/draft → 503 (×3)
```

## Корень (Lead)

`me_lead_draft` → `analyze_premium()` вернул **None** (2 retry исчерпаны).  
**Не** race · **не** km=0 (теги `api_integration` + `wordpress_dev` = 100%).

**Проблема observability:** `analyze_premium(..., errors=...)` **не передаётся** в `api_server.py` → причина **не в логах**.

**Повтор Lead debug на VPS (2026-05-29):** L2 для 7019 **успешен** с первого вызова — **флаky** (OpenRouter / валидация JSON / money / reply_draft).

## Fix (Coder)

| # | Задача |
|---|--------|
| f1 | `me_lead_draft`: `errors=[]` → `logger.warning` при 503 |
| f2 | UI: «Повторить» + показать `detail` если API отдаёт (не только generic) |
| f3 | Опц.: 3-й retry только для on-demand draft |

## Не путать

- **tools_required** на карточке — стек **заказа** (L2), не «твои навыки»
- **100%** F2 = все **lead_tags** в профиле; L1 может ошибочно ставить `wordpress_dev` на Joomla
