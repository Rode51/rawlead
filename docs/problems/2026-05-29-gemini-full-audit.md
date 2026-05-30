# Полный аудит + AI-логика — Gemini 2M (O38)

**Статус:** **✅ закрыт 2026-05-29** · **NO-GO O37** → **O59** P0 fixes  
**Дата:** 2026-05-29 · обновлено владельцем  
**Приоритет:** findings → **O59** → повтор go/no-go → **O37**

## Запрос владельца

1. Плотный построчный аудит всего проекта  
2. **Отдельно — вся ИИ-логика:** L1 tags, L2 draft, validation, false 100% match  
3. Findings → input для **stress-теста** (O37) с **очень сильным агентом**
4. **Docs drift (2026-05-29):** перепроверить документацию — расхождения с кодом/prod, устаревшие статусы, противоречия между канонами
5. **Product drift (2026-05-29):** `PRODUCT_VISION` **v0.11** vs **реальный MVP на prod** — что обещано, что уже есть, что «после MVP» ошибочно считается готовым (или наоборот)

## Scope @mechanic (обязательно)

### A — Код + ИИ

| Область | Что искать |
|---------|------------|
| **`src/ai_analyze.py`** | L1/L2 prompts · CMS rules · `_validate_*` · retry · shared draft prompt |
| **`src/rank.py` + L1 tags** | false positive 100% · Joomla/WP cases |
| **`src/draft_async.py` + `match_push.py`** | shared draft cache · lock · poll · TG path |
| **`src/lead_pipeline.py`** | когда L2 skip · no_reply_draft |
| **`api_server.py`** | draft GET/POST · 202 pending · 503 paths |
| **`match_push.py` + bot** | push format · callback draft |
| **Stress focus** | draft burst · 100 users 1 lead · concurrent L1 · OpenRouter limits |

### B — Документация (не переписывать — **отчёт drift**)

**Канон навигации:** [`DOCS_ARCHITECTURE.md`](../team/common/DOCS_ARCHITECTURE.md) · [`PROJECT_MAP.md`](../team/common/PROJECT_MAP.md)

| # | Проверить | Искать |
|---|-----------|--------|
| d1 | **STATUS ↔ TASKS ↔ ROADMAP ↔ OWNER_INTENT** | устаревшие «→ @coder» · дубли · противоречия порядка O38/O37 |
| d2 | **CODER_PROMPT** | § «→ Следующее» vs реальный prod · закрытые O52–O58 не висят как active |
| d3 | **Код ↔ docs** | env keys (`.env.example` vs `config.py`) · API routes (`TZ_API.md` vs `api_server.py`) · schema (`NEON_SCHEMA.md` vs `sql/`) |
| d4 | **ИИ-канон** | prompts в коде · shared draft · F2 match — одна формула везде (не product scope) |
| d5 | **FOR_YOU / RUN.md / ops** | шаги владельца vs prod (theme version, bot-poll, MATCH_PUSH, SHARED_DRAFT model) |
| d6 | **design/wp** | `REFERENCE.md` vs theme v1.10.9 (карточки, demo, cabinet) — только **P0** расхождения |
| d7 | **problems/** | открытые тикеты vs закрытые фиксы (O48 flaky draft → O56/O57/O58) |
| d8 | **Product drift** | [`PRODUCT_VISION.md`](../team/product/PRODUCT_VISION.md) **§0d** (5 acceptance) + §0c Directions B/C/D vs код/prod · `LEAD_PRODUCT_PROMPT` active vs built · «после MVP» vs уже в prod |

**Не делать:** массовый рерайт docs · правки `PRODUCT_VISION` / vision — только отчёт · новые `.md` без Lead · правки `archive/`

### d8 — Product drift (чеклист)

Сверить [`PRODUCT_VISION.md`](../team/product/PRODUCT_VISION.md) **v0.11** с кодом + prod (theme v1.10.9, VPS API/bot):

| § vision | Вопрос |
|----------|--------|
| **§0d #1–5** | Каждый пункт acceptance — **done / partial / missing** + evidence |
| **§0c Direction B** | `/feed` anon · ≥50 лидов/день · ИИ-модерация · шлак <30% |
| **§0c Direction C** | `/cabinet` match по тегам · регистрация · multi-user-ready |
| **§0c Direction D** | draft · рыночная цена · push TG · подписка vs «после MVP» |
| **§0a SaaS-ready** | `user_id` везде · нет хардкода владельца |
| **LEAD_PRODUCT_PROMPT** | активные инициативы vs уже в коде |

**Product drift P0** = блокирует stress/O37 или вводит владельца в заблуждение. **P1** = partial / docs устарели. **P2** = косметика.

**Кто чинит:** vision → **@lead-product** · ROADMAP/TASKS → **Lead** · код → **@coder** (P0).

## Формат

1. **AI P0/P1** — таблица: промпт/rule · баг · fix · test-кейс  
2. **Docs drift P0/P1/P2** — файл · строка/§ · «написано X» vs «в коде/prod Y» · кто чинит (Lead/Coder)  
3. **Product drift P0/P1/P2** — § vision · «обещано X» vs «prod Y» · done/partial/missing · кто чинит  
4. **Топ-10 общих** P0/P1 (код + docs + product)  
5. **Stress scenarios** — 8+ (в т.ч. 50× draft, 100× feed, **100 users 1 lead shared draft**)  
6. **Go/no-go O37**  

## Связь O37

Stress = **не только HTTP**, но **AI matrix** (preprod_ai_matrix или аналог) · Mechanic выдаёт чеклист → Coder фиксит P0 → потом O37.

## Артефакт

§ **Решение** ниже · P0 → [`CODER_PROMPT.md`](../team/architect/CODER_PROMPT.md) § **O59** · docs → Lead / @lead-designer

---

## Решение (@mechanic · 2026-05-29)

### Go/no-go O37

**NO-GO.** Stress до устранения P0 и синхронизации канона API/schema.

| Блокер | Почему |
|--------|--------|
| Flaky draft | Ядро MVP (§0d #3) нестабильно · O56/O57 смягчили, но OpenRouter/validation всё ещё дают fail |
| TZ_API / NEON_SCHEMA | Критически устарели — риск неверных stress-сценариев |
| Design canon | `feed-cabinet-mvp.md` ≠ `REFERENCE.md` (pre-wave-2 soft vs NEO) |

**После O59 + docs sync** — Lead повторяет go/no-go → O37.

---

### 1. AI P0/P1

| Pri | Проблема | Статус после O56–O58 | Fix |
|-----|----------|----------------------|-----|
| **P0** | Flaky draft · 503 на 2-м lead | async+shared **partial** · тикет [`2026-05-29-lenta-draft-503-flaky.md`](2026-05-29-lenta-draft-503-flaky.md) | **O59a** — логи `ai_errors` · poll `failed` · UI «Повторить» · тест |
| P1 | L1 false 100% (Joomla→wordpress_dev) | открыто | O59 backlog · stress matrix |
| P1 | ИИ-канон: F2 formula в docs vs rank.py | drift | Lead § AI.md сверка |

---

### 2. Docs drift

| Pri | Файл | Написано | Prod/код | Кто |
|-----|------|----------|----------|-----|
| **P0** | `TZ_API.md` v0.3g | 10 эндпоинтов | **20+** в `api_server.py` (draft GET/POST, auth, replies, admin, ops) | **Lead ✅ O39-docs** |
| **P0** | `NEON_SCHEMA.md` v0.3 | 4 таблицы | +`user_lead_replies`, `draft_jobs`, `lead_draft_jobs`, `match_push_log`, `admin_pageviews`, cols `reply_draft`… | **Lead ✅ O39-docs** |
| **P0** | `feed-cabinet-mvp` vs REFERENCE | pre-wave-2 soft spec | **NEO prod v1.10.9** | **✅ Lead D-O39** |
| P1 | `.env.example` vs `config.py` | в целом OK | `OPENROUTER_MODEL_SHARED_DRAFT` есть · опц. `RAWLEAD_OWNER_USER_ID` — добавить в O59b | Coder O59b |
| P1 | `FOR_YOU` / `STATUS` theme | расхождения версий | канон **v1.10.9** | Lead STATUS |
| P2 | `problems/` O48 flaky | открыт | закрыть после O59a | Lead |

---

### 3. Product drift (§0d acceptance)

| # | Vision | Статус | Evidence |
|---|--------|--------|----------|
| 1 | `/feed` ≥50/день · модерация | **partial** | лента live · метрики шлака не замерены |
| 2 | `/cabinet` match по тегам | **done** | `/v1/me/feed` + WP |
| 3 | Draft + push TG | **partial** | draft **flaky** · push OK |
| 4 | multi-user-ready | **partial** | `user_id` в API · `_OWNER_USER_ID` hardcode |
| 5 | docs → 2-й user за 1–2 дня | **partial** | TZ_API/schema drift мешает |

---

### 4. Stress scenarios (9 · не прогонялись)

1. 50× concurrent draft  
2. 100× concurrent feed  
3. 100 users · 1 lead shared draft  
4. Ingest flood 1000+ leads  
5. TG bot command spam  
6. API key rotation  
7. DB pool exhaustion  
8. Mixed load  
9. External AI/proxy failure  

→ input для **O37** после O59 go.

---

### 5. Топ-10 P0/P1 (сводка)

1. Flaky draft (**P0** code)  
2. TZ_API устарел (**P0** docs)  
3. NEON_SCHEMA устарел (**P0** docs)  
4. Design spec contradiction (**P0** design)  
5. Product §0d #3 partial (**P0** product)  
6. No stress results yet (**P1** process)  
7. L1 CMS false tags (**P1** AI)  
8. `_OWNER_USER_ID` hardcode (**P2** SaaS)  
9. problems/O48 open (**P2** hygiene)  
10. FOR_YOU order O38/O37 (**P2** docs)
