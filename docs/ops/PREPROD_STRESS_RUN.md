# PRE-PROD-STRESS — прогон перед трафиком

**Ворота:** [`docs/team/architect/PRE_PROD_GATE.md`](../team/architect/PRE_PROD_GATE.md) § S1–S6.

**Когда:** после § P5 (WP + API + Site на VPS), **и после** Design + PM copy + Coder финал (O21). DNS готов, рекламы нет.

---

## Слой 0 — UX-audit «ИИ-тестировщик» (S2, O21)

**Один прогон** перед stress — все страницы, клики, баги:

```powershell
.venv\Scripts\python.exe scripts\preprod_playwright\ux_audit.py --base-url https://rawlead.ru
```

Отчёты: `data/preprod_ux_audit.json` · `data/preprod_ux_audit.md` · скрины `data/preprod_ux_audit/`

| Что делает | Детали |
|------------|--------|
| Обход | `/`, `/lenta/`, `/cabinet/`, `/how/`, `/pricing/`, `/faq/`, `/contact/` |
| Клики | header, footer, CTA, навыки «Применить», pricing→ЛК |
| Ловит | 404/500, console errors, failed fetch, перекрытия на mobile 390px |
| ИИ (опц.) | LLM summary по JSON — «неудобно / баг / мёртвая кнопка» |

| PASS S2 | 0 critical findings; все footer URL 200 |

Debug: `--headed` · опц. `--llm` для markdown-отчёта

**Coder:** § PRE-PROD-UX-AUDIT в `CODER_PROMPT.md` (скрипт **→** после финала UI).

---

**Не гонять:** 1000+ premium OpenRouter. Нагрузка — **чтение** API/ленты.

### Переменные

| Переменная | Пример | Где |
|------------|--------|-----|
| `BASE_URL` | `https://rawlead.ru` | Playwright |
| `API_URL` | `https://api.rawlead.ru` | k6 / load |
| OpenRouter | `.env.site` на VPS или локально | матрица ИИ |

---

## Слой 1 — ИИ (S1)

**Локально или на VPS** (нужен ключ OpenRouter в `.env.site`):

```powershell
cd C:\Users\hramo\uisness
.venv\Scripts\python.exe scripts\preprod_ai_matrix.py --profile site --dry-run
.venv\Scripts\python.exe scripts\preprod_ai_matrix.py --profile site
```

Отчёт: `data/preprod_ai_report.json`

| Критерий S1 | PASS когда |
|-------------|------------|
| По каждой category (`dev`, `design`, `marketing`, `text`) | ≥3 фикстуры в отчёте |
| L1 | `task_summary` не пустой |
| L2 | `reply_draft` не пустой на «нормальном» лиде |
| Итог | `summary.s1_pass: true` |

Узкий прогон (экономия):

```powershell
.venv\Scripts\python.exe scripts\preprod_ai_matrix.py --profile site --category dev --limit 1
```

**Красные флаги:** массовые `errors` с `401`/`429`; пустой `reply_draft` на всех L2.

---

## Слой 2 — Сайт Playwright (S2, S5 частично)

**Только боевой/staging URL** (DNS готов):

```powershell
.venv\Scripts\python.exe scripts\preprod_playwright\smoke.py --base-url https://rawlead.ru
```

Отчёт: `data/preprod_playwright_report.json`

| Сценарий | Что проверяет |
|----------|----------------|
| `lenta_loads` | `/lenta/` без error banner |
| `multi_category` | chip «Дизайн» не ломает ленту |
| `skills_apply` | «Навыки ▾» → чип → «Применить» |
| `cabinet_login_stub` | `/cabinet/` — блок входа |
| `no_verdict_chips` | нет «Брать / Не брать / Сомнительно» на карточках |

| Критерий S2 | PASS когда |
|-------------|------------|
| Все 5 сценариев | `s2_pass: true` |

Debug с окном браузера: `--headed`

---

## Слой 3 — API нагрузка (S3)

### Вариант A — k6 (если установлен)

```powershell
k6 run -e API_URL=https://api.rawlead.ru -e VUS=50 -e DURATION=5m scripts/preprod_k6_feed.js
```

Сводка: stdout + `data/preprod_k6_summary.json`

### Вариант B — Python (без k6)

```powershell
.venv\Scripts\python.exe scripts\preprod_load_feed.py --api-url https://api.rawlead.ru --workers 50 --duration 300
```

Отчёт: `data/preprod_load_summary.json`

| Критерий S3 | PASS когда |
|-------------|------------|
| `GET /v1/feed?limit=20` p95 | **< 2000 ms** |
| Ошибки 5xx | **< 1%** запросов |
| Итог | `s3_pass: true` |

Эндпоинты в прогоне: `/health`, `/v1/feed?limit=20`, `/v1/skills/catalog` — **без** L1/L2.

**Красные флаги:** CORS на WP; 502 от nginx; p95 > 5 с при 20 VU.

---

## Слой 4 — Радар на VPS (S4)

**Владелец на VPS** (после E2 или Site ▶ на сервере):

1. `systemctl status rawlead-radar` — active
2. `tail -f /opt/rawlead/data/radar_site.log` — 2–4 цикла FL+Kwork
3. В футере цикла: `neon_insert` или `neon_replay` > 0 (или явная причина `0`)
4. Нет лавины `ai:http:401` / `429`

Записать в [`STATUS.md`](../team/common/STATUS.md) § PRE-PROD-STRESS одну строку baseline, напр.:

`цикл FL+Kwork ~N мин │ ИИ L1=M │ neon_insert=K`

---

## Ручная приёмка владельца (S5, S6)

| # | Действие | ~время |
|---|----------|--------|
| S5 | 15 мин на `https://rawlead.ru/lenta/` — 10 карточек осмысленные, без вердикт-чипов | 15 мин |
| S6 | `/cabinet/`: смена навыков → другой `reply_draft` на том же лиде (если L2 есть) | 10 мин |

Подписать в чат Lead: «S1–S6 зелёные» → «едем на прод».

---

## Порядок прогона

```
1. DNS + certbot + WP theme (владелец)
2. preprod_ai_matrix.py          → S1
3. preprod_playwright/smoke.py   → S2 (+ часть S5)
4. preprod_k6_feed.js или load   → S3
5. radar_site.log на VPS         → S4
6. глазами S5–S6                 → владелец
```

---

## Опционально: P5-E2 радар на VPS

См. [`DEPLOY_VPS.md`](DEPLOY_VPS.md) § E2 — **после** E1 и DNS. Перед слоем 4: стоп Site на ПК, один `rawlead-radar` на VPS.

---

## Файлы скриптов

| Путь | Роль |
|------|------|
| `scripts/preprod_fixtures.py` | 12 фикстур × 4 category |
| `scripts/preprod_ai_matrix.py` | S1 |
| `scripts/preprod_k6_feed.js` | S3 (k6) |
| `scripts/preprod_load_feed.py` | S3 (Python) |
| `scripts/preprod_playwright/smoke.py` | S2 |

Отчёты пишутся в `data/preprod_*.json` (gitignore ок).

---

_Lead / Coder · 2026-05-28_
