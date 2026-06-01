# Готовность к рекламе проекта RawLead

**Не про:** рекламу *на* сайте (TG-фильтр шума — `FILTERS.md`).  
**Про:** когда можно **привлекать пользователей** на rawlead.ru.

**Снимок:** [`STATUS.md`](../team/common/STATUS.md) · [`TASKS.md`](../team/common/TASKS.md) · [`ROADMAP.md`](../team/architect/ROADMAP.md)

---

## Статус gate (2026-05-30)

| Gate | Статус | Артефакт |
|------|--------|----------|
| UX mobile/desktop | **✅** O37c **18/19** · S6 owner **✅** | `preprod_ux_audit.json` |
| API HTTPS | **✅** O71 | health/feed/catalog **200** |
| k6 read load (~50 concurrent) | **✅** O71 · fail **0%** · p95 ~1.7 s | `data/preprod_k6_summary.json` |
| Shared draft matrix | **✅** **12/12** · `gemini-2.5-pro` | `data/preprod_ai_report.json` |
| Theme prod | **v1.11.15** | STATUS O70 |
| **Owner 5× draft глазами** | **⚠️ 9/10** · см. [`problems/2026-05-30-owner-draft-accept-9of10.md`](../problems/2026-05-30-owner-draft-accept-9of10.md) |
| **O72** prod audit (auto) | **✅ O72b** | `preprod_ai_prod_audit.json` |
| **O72c LLM judge + промпты** | **📋 перед рекламой** | § O72c |
| **O76 UX re-audit** | **📋 gate soft ads** | § O76 · re-run O37c |
| **Heatmap (Metrika / Clarity)** | **📋 backlog** | § O73 |
| Draft burst под нагрузкой | **не тестировали** | опционально перед большой кампанией |

**Infra gate закрыт.** Реклама проекта — после **ручной приёмки draft** + желательно **O72 baseline**.

---

## Чеклист владельца (5× «Написать отклик»)

На **prod** `/lenta/` под своим аккаунтом:

| # | Проверка | OK? |
|---|----------|-----|
| 1 | Черновик появляется за **&lt;30 с** (обычно ~20 с) | |
| 2 | Текст **без** цены/срока в теле · без «ИИ/Cursor/Gemini» | |
| 3 | **tools** на карточке **не пустые** (если заказ про инструменты) | |
| 4 | Текст **по делу** — не generic «готов выполнить» | |
| 5 | Повтор на **2–3 категориях** (dev / design / text) | |

Если **2+ провала** — не рекламируем · тикет `@coder` или `@mechanic`.

---

## O72 — Аналитика качества откликов ИИ

**Зачем:** понять, насколько корректно модель пишет **reply_draft** и **tools_required** на **реальных** лидах (не только fixtures).

**Coder:** [`CODER_PROMPT.md`](../team/architect/CODER_PROMPT.md) § **O72**

### Источники данных (Neon)

| Поле / таблица | Что даёт |
|----------------|----------|
| `leads.reply_draft` | кэш shared draft (O57) |
| `leads.tools_required` | JSON-массив инструментов L2 |
| L2 поля (`verdict`, `approach`, `time_for_client`, …) | контекст для judge |
| `leads.title`, `description`, `category`, `source_id` | вход для сверки |
| `user_lead_replies` (если есть правки) | drift «ИИ vs пользователь» |

### Автоматические метрики (скрипт)

1. **Выборка:** последние **N=100–200** лидов с непустым `reply_draft` · stratify по `category` + `source_id`.
2. **Повтор валидаторов** из `ai_analyze.py`: запретные слова, длина предложений, пустой draft при «Брать».
3. **tools_required:**
   - пустой массив при явных инструментах в описании (regex/heuristic);
   - инструмент **не из каталога** `/v1/skills/catalog`;
   - дубликаты / мусор.
4. **Сводка JSON** → `data/preprod_ai_prod_audit.json` + **markdown** для человека (как `preprod_ux_audit_human.md`).

### LLM-as-judge (опционально, фаза 2)

На подвыборке **20–30** лидов — второй проход (тот же `gemini-2.5-pro` или flash):

| Критерий | Шкала |
|----------|-------|
| Релевантность отклика ТЗ | 1–5 |
| Конкретность (шаги, не вода) | 1–5 |
| tools **соответствуют** задаче | да/нет/частично |
| Готов отправить клиенту as-is | да/нет |

**Accept O72:** отчёт сгенерирован · **≥85%** auto-pass · judge avg **≥3.5/5** · список top-10 fail cases для правок промпта.

### Когда перезапускать

- после смены `OPENROUTER_MODEL_SHARED_DRAFT`;
- после правок промпта L2;
- **перед** крупной рекламной кампанией;
- раз в **2–4 недели** на prod sample (не CI).

---

## O73 — Heatmap / поведение на сайте

**Проблема:** в продукте **нет** heatmap — не видим, куда кликают, где отваливаются.

| Вариант | Плюсы | Минусы |
|---------|-------|--------|
| **Yandex Metrika** | привычно RU · карты кликов · вебвизор | настройка счётчика в WP |
| **Microsoft Clarity** | бесплатно · записи сессий | GDPR/политика — проверить |

**Задача:** `@coder` или владелец — счётчик в child theme **до** старта рекламы · baseline 1–2 недели «органика».

**Не блокирует** первый soft-launch, но **нужно до масштабирования** трафика.

---

## Нагрузка и повторные прогоны

| Сценарий | Протестировано? | Действие |
|----------|-----------------|----------|
| ~50 concurrent **читателей** ленты/API | **✅** k6 O71 | повтор после крупного deploy API |
| **50× draft** одновременно | **❌** | опционально `preprod_k6` расширение или ручной burst перед большой рекламой |
| Playwright UX | **✅** 18/19 (O37c) | **O76 re-run** перед soft ads (theme v1.11.15 + O75) |

Runbook stress: [`PREPROD_STRESS_RUN.md`](PREPROD_STRESS_RUN.md)

---

## Порядок (сводка)

```
O71 ✅ → O72b ✅ → O75 ✅ → O72c judge → O76 UX re-audit → soft ads → O63 (parallel)
```

---

_Lead Architect · 2026-05-30_
