# Hotfix: `/v1/feed` 500 после P1 (`PUBLIC_FEED_SOURCES`)

**Статус:** ✅ fixed 2026-05-26  
**Симптом:** WP `/lenta/` — «Не удалось загрузить ленту»; uvicorn: `the query has 4 placeholders but 8 parameters were passed`

**Причина:** `public_feed_source_sql()` отдавал `sources` как несколько params (`*feed_params` разворачивал `fl`,`kwork`,…), а SQL ждал **один** массив для `ANY(%s::text[])`.

**Фикс:** `src/public_feed.py` — `return " AND source = ANY(%s::text[])", [sources]`

**Проверка:** перезапуск uvicorn → `GET /v1/feed?limit=2` 200; Neon count ~64 лидов с `notified_at`.
