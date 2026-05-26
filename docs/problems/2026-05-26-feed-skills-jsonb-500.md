# `/v1/feed` 500 при фильтре навыков (skills=)

**Дата:** 2026-05-26 · **Статус:** ✅ закрыто · принято владельцем 2026-05-26  
**Симптом:** после «Применить» в `/lenta/` лента падает; в логе uvicorn:

```
feed: operator does not exist: jsonb && jsonb
LINE ... AND lead_tags && $N::jsonb
```

**Где:** `src/api_server.py` → `_skills_sql()`

**Не ломает:** `GET /v1/feed` без `skills` (200), `/v1/skills/catalog` (200).

**Приёмка V10:** блокирует «Применить» навыки до фикса.

**Направление фикса:** пересечение тегов через `?|` / `jsonb_array_elements_text` + `= ANY(%s::text[])`, не `&&` с `json.dumps(skills)`.

---

_Из логов владельца · Lead Architect_
