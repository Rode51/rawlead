# OpenRouter ~$10/день — triage 2026-06-23

**Симптом:** владелец видит ~$10/сутки на OpenRouter, подозрение на лишние вызовы ИИ.

**Probe:** `scripts/_probe_ai_spend_vps.py` (SSH VPS, 2026-06-24 UTC).  
**Update 2026-06-24:** владелец прав — L2/L3 вызывались; `stage=l2_http` в journal **не индикатор** (см. § Logging blind spot). OpenRouter dashboard: **$10.97 = DeepSeek V3 (L1)**, не черновики.

---

## Logging blind spot (почему `stage=l2_http` = 0 — ложный ноль)

На prod в `journalctl -u rawlead-api` попадают в основном **uvicorn access** строки (`POST /v1/me/leads/…/draft`).  
`logger.info` из `ai_analyze` / `match_push` / `draft_trace` (**в т.ч. `stage=l2_http`**) в journal **не видны**:

| Проверка (7d) | Результат |
|---------------|-----------|
| `grep db:` / `openrouter:proxy` (startup) | **0** |
| `grep trace stage=` (draft_trace) | **0** |
| `grep stage=l2_http` | **0** |
| `POST …/draft` (access log) | **266** |

В коде есть комментарий и попытка фикса (`api_server.py` startup: root INFO + loggers `ai_analyze`, `draft_trace`…), но на VPS **app-логи в journal не доходят** — только access.

**Где смотреть реальные черновики:**

```bash
journalctl -u rawlead-api --since '7 days ago' | grep 'POST /v1/me/leads/.*/draft'
journalctl -u rawlead-bot-poll --since '7 days ago' | grep tg:draft
```

**Факты за 7d (access + bot):**

| HTTP | Кол-во |
|------|--------|
| `202 Accepted` (async draft start) | **96** |
| `200 OK` (draft ready sync) | **22** |
| `404` | **35** |
| `429` (rate limit) | **113** |
| TG `tg:draft:*` (bot journal) | **120** строк |

Владелец **лично** бился в API (IP `84.244.14.99` / `31.76.254.1`): лиды 19676, 22213, 23597, 24681, 25461… — `202`/`200`.  
Недавние `POST …/24823/draft` → **404** (лид не найден / не тот id).

**Вывод:** черновики **были**; grep по `stage=l2_http` давал **ложный 0** из-за logging gap.

---

## OpenRouter dashboard (скрин владельца, 2026-06-23)

| Модель | $/день (23 июн) | Роль в RawLead |
|--------|-----------------|----------------|
| **DeepSeek V3** | **$10.97** | L1 `OPENROUTER_MODEL_SUMMARY=deepseek/deepseek-chat` |
| **Gemini 2.5 Pro** | **$0.30** | L2/L3 shared draft (ваши клики «Отклик») |
| Claude / Flash | мало в этот день | ранние июньские пики = audit/stress |

**$10/день сейчас = L1 (DeepSeek), не черновики.** Черновики в этот день на графике ~30 центов.

---

## Факты prod (последние 24h, journal + radar_site.log)

| Метрика | Значение | Что значит |
|---------|----------|------------|
| `pipeline:L1` (journal) | **607** | hot-path L1 после ingest (FL/Kwork/TG/YouDo IMAP) |
| `openrouter`/`analyze_lite` (journal radar) | **712** | строки с упоминанием OpenRouter/L1 (вкл. ретраи) |
| `конвейер:L1` (journal) | **10** строк | backlog drain; в хвосте лога обычно **1–3 L1/цикл**, не полные 40 |
| `stage=l2_http` / `stage=l3_http` (api journal) | **0** | **не смотреть** — app logger не в journal; см. access log выше |
| `tg:draft:callback` | **6** | кнопка «Отклик» в боте |
| `/health` `draft_ok`/`draft_fail` | **0/0** | счётчик в памяти API (сброс после restart) |
| YouDo IMAP | ~каждые 90s, `discovered=5–8` | в хвосте лога **440× `new_id=`** на ~8000 строк |

**Env prod (site):**

- `L1_BACKLOG_DRAIN=1` · `L1_BATCH_PER_CYCLE=40` · `L1_MAX_WORKERS=2`
- `OPENROUTER_MODEL_SUMMARY=deepseek/deepseek-chat` (L1)
- `OPENROUTER_MODEL_SHARED_DRAFT` / `PREMIUM` = **google/gemini-2.5-pro** (L2/L3)
- `TOOLS_BACKLOG_DRAIN=0` ✅

**Итог по prod:** основной расход **сейчас** — **L1 DeepSeek** (сотни–тысячи вызовов/сутки, YouDo IMAP + backlog). **L2/L3** идут по клику, на графике **копейки/день** vs **~$11 DeepSeek**.

---

## IMAP refresh loop (подтверждено 2026-06-24) — главный burn L1

**Вопрос владельца:** жрёт ли вся почта? одна вакансия 50 раз каждые 90 с?

| | Факт |
|---|------|
| **Вся почта?** | **Нет.** Только папка `YOUDO_IMAP_FOLDER` (prod: `INBOX/Newsletters`) + IMAP search `FROM "youdo"` + проверка From в коде. Личная переписка **не читается**. |
| **Каждые 90 с?** | **Да**, timer `rawlead-youdo-imap` (~90 с). Каждый цикл: заново **скачать последние N писем** (`YOUDO_IMAP_FETCH_LAST=30`, не 50). Почту **не отправляет** — только IMAP read. |
| **50 раз одна вакансия за цикл?** | **Нет в одном цикле.** Из ~30 писем парсятся id; типичный цикл: `discovered=30`, `skip_exists=22`, `refresh_invisible=4`, `new=0–4`. |
| **Та же вакансия снова и снова?** | **Да — баг/дыра.** Видимые в ленте → `skip_exists` (L1 нет). **Invisible** → `refresh_invisible` **каждый цикл** → снова ingest → **снова L1**. |

**Доказательство (prod log), лид `14890747`:**

| Метрика | Значение |
|---------|----------|
| `refresh_invisible=14890747` | **325** |
| `pipeline:L1 youdo:id=14890747` | **325** (всегда `visible=0`) |
| интервал | ~каждые **90 с** (11:12 → 11:13 → 11:15 → 11:16 → 11:18) |

**Почему в коде:** `lead_imap_dedup_skip` пропускает только `is_visible=true`. Invisible снова идут в `process_new_listing`; poller каждый раз делает `clear_neon_dup_synced` → ветка `neon_replay` → **L1 снова**, даже если verdict уже есть.

**Оценка burn:** 4 «застрявших» invisible × ~960 циклов/сутки ≈ **~3800 L1/день** только с IMAP refresh (порядок величины; плюс backlog drain для других id).

**Быстрый ops (владелец):** `L1_BACKLOG_DRAIN=0` режет второй канал; IMAP loop — **нужен код** (skip L1 если `has_l1`, или не refresh invisible с verdict).

---

Journal считает в основном **строки радара** (`pipeline:L1`), не каждый HTTP к OpenRouter. Возможные множители:

- **2× retry** в `analyze_lite`
- **backlog drain** + **IMAP** (много новых YouDo)
- **длинный snippet** (письмо YouDo 300+ символов в prompt)
- **тот же ключ** с локальной машины (preprod L1 judge)

Сверка: OpenRouter Activity → фильтр **deepseek** → requests/day.

## Где в коде вызывается OpenRouter

| Слой | Модель (prod) | Когда | Риск $ |
|------|---------------|-------|--------|
| **L1** `analyze_lite` | deepseek | каждый новый лид + **backlog drain** до 40/цикл | средний (объём) |
| **L1 backlog** `drain_l1_backlog` | deepseek | invisible YouDo без verdict (**до 20 YouDo + остальное**) | **лишнее**, если лид не станет visible |
| **L2** shared draft | gemini-2.5-pro, до **4** попыток | клик «Написать отклик» / TG «Отклик» / cold lead | **высокий** за вызов |
| **L3** uniquify | premium, до **6** попыток | 2-й и далее пользователь на том же лиде | **высокий** |
| **warm** `warm_shared_lead_draft` | gemini pro | `POST …/draft/warm` | высокий (если дергают) |
| **tools backlog** | L2-ish | `TOOLS_BACKLOG_DRAIN=1` | выкл. на prod |

---

## Локальные скрипты (тот же ключ в `.env` / `.env.site`)

| Скрипт | Риск |
|--------|------|
| `preprod_stress_v2.py` | `draft_burst` до **20× L2/L3** на **https://api.rawlead.ru** |
| `preprod_ai_prod_audit.py --judge` | сотни LLM-judge (L1/L2/L3) |
| `preprod_playwright/ux_audit.py` | vision LLM + draft на карточках |
| `preprod_ai_matrix.py` | L1 + full draft pipeline |
| `preprod_playwright/ux_journey.py` | `generate_draft_on_card` |

В репо: stress **2026-06-21** (`draft_burst` 20 leads), ux_audit **2026-06-20**. Если $10 именно **сегодня** — сверить **OpenRouter Activity** по времени.

Канон: [`PREPROD_STRESS_RUN.md`](../ops/PREPROD_STRESS_RUN.md) — «**Не гонять: 1000+ premium OpenRouter**».

---

## Что сделать владельцу (5 мин)

1. **OpenRouter → Activity** за проблемный день: фильтр по модели (`gemini-2.5-pro` vs `deepseek`).  
2. Если pro/judge — это **не радар**, а **preprod** или редкие черновики.  
3. Если deepseek тысячи вызовов — смотреть **YouDo IMAP** (`journalctl -u rawlead-youdo-imap`) и **L1 backlog**.  
4. Временно снизить burn (ops, без кода): в `.env.site` на VPS  
   - `L1_BACKLOG_DRAIN=0` — stop drain invisible хвоста;  
   - или `L1_BATCH_PER_CYCLE=10`;  
   затем `systemctl restart rawlead-radar`.  
5. Для preprod — **отдельный** OpenRouter key с лимитом $/day.

---

## Рекомендация Coder (следующий спринт)

- **P0 logging:** app `logger.info` → journal (uvicorn `log_config` или `StandardOutput=journal` + единый handler); иначе triage слепой.
- Счётчики L1/L2/L3 в `/health` (persistent).
- Не гонять L1 в `drain_l1_backlog` для YouDo `is_visible=false` без перспективы detail.
- Guard: preprod → prod draft только с `PREPROD_ALLOW_PROD_DRAFT=1`.

**Маршрут:** § `AI-SPEND-GUARDS` в `CODER_PROMPT.md` · verify Lead.
