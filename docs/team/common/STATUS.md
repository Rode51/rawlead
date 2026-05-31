# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.11** · [`ROADMAP.md`](../architect/ROADMAP.md)

**Очередь:** [`TASKS.md`](TASKS.md) · решения: [`OWNER_INTENT.md`](../architect/OWNER_INTENT.md) · **архив:** [`archive/STATUS_ARCHIVE.md`](../archive/STATUS_ARCHIVE.md)

> **Правило (~80 строк):** только «Сейчас» + активные задачи + сводка принятого. Детали сдачи → архив, не дублировать `CODER_PROMPT`.

---

## Сейчас (2026-05-30)

| | |
|--|--|
| **Theme prod** | **v1.11.15** |
| **API** | https://api.rawlead.ru **✅** · k6 fail **0%** · p95 ~1.7 s |
| **Draft** | `gemini-2.5-pro` · matrix **12/12** · shared cache O57 |
| **UX gate** | O37c **18/19** · S6 owner **✅** |
| **Owner draft** | **9/10 OK** ⚠️ · 1 завис · 1 разбор недоступен · [`problems/…`](../../problems/2026-05-30-owner-draft-accept-9of10.md) |
| **→ Coder** | **O75** — лента 7d · backlog O63/O74 |
| **O72b** | **✅** draft-only **97.8%** · tools **89.1%** · KNOWN_TOOLS · canonical **51** без изменений |
| **O72 фаза 1** | **✅ Lead verify** · combined **87%** после O72b |
| **Реклама** | **⏸ soft** — можно после O75 или параллельно |

**Отчёты:** `data/preprod_k6_summary.json` · `data/preprod_ai_report.json` · `data/preprod_ai_prod_audit.json` · `data/preprod_ux_audit_human.md`

---

## Активно

### O72 — AI draft quality audit

| | |
|--|--|
| **Цель** | качество `reply_draft` + `tools_required` на **реальных** лидах |
| **Фаза 1** | auto-metrics · tools vs catalog · JSON + human md |
| **Фаза 2** | LLM judge 20–30 samples (`--judge`) |
| **Accept** | ≥85% auto-pass · judge avg ≥3.5/5 |
| **Coder** | [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md) § **O72** |
| **Статус** | **✅ O72b** · draft-only **97.8%** · tools bucket **89.1%** · `tools:not_in_catalog` снят (KNOWN_TOOLS) |
| **Отчёт** | `data/preprod_ai_prod_audit.json` · `…_human.md` |

**O72b 2026-05-31:** разделены `draft_only_pass` / tools · whitelist `src/tools_catalog.py` (~30 имён) · synonyms skill-only (wordpress, html/css, aiogram 3, google ads) · re-audit prod.

---

## Prod gates (кратко)

| Gate | Статус |
|------|--------|
| O71 HTTPS + k6 + shared draft | **✅** |
| O70 cabinet overlay v1.11.15 | **✅** |
| O69 filters/sort v1.11.14 | **✅** |
| O64–O68 delist · legacy poll · status | **✅** |
| O38 Mechanic audit | **✅ NO-GO** → закрыто O59–O71 |
| PRE-PROD stress S1–S3 | **✅** |

---

## Принято (сводка)

| Период | Блоки |
|--------|-------|
| **2026-05-30** | O64–O71 · mobile UX · filters · pre-launch infra |
| **2026-05-29** | Wave-2 O52–O58 · PRE-STRESS O42–O51 · O38 · pipeline O39 · O32 status |
| **2026-05-28** | E0–E5 · P5 E2 VPS · 3f A/B · site polish · match push |

Детали по задачам → [`archive/STATUS_ARCHIVE.md`](../archive/STATUS_ARCHIVE.md) · волны → [`archive/TASKS_HISTORY.md`](../archive/TASKS_HISTORY.md)

---

## ЛК / подписка

| Есть | Ещё нет |
|------|---------|
| `/cabinet/` TG + fallback · JWT · навыки | L2 per-user (P4b) |
| `/lenta/` paid draft · shared cache | ЮKassa |
| Push TG · Stars · `tools_required` | Heatmap (O73) |
| `/v1/me/subscription` · pause | |

---

## Блокеры

| Блокер | Кто |
|--------|-----|
| Пульт: sticky-скролл логов | `rebuild-pult.bat` — владелец |

Тикеты: [`docs/problems/`](../../problems/) — не дублировать здесь.

---

_Lead Architect · hot snapshot · 2026-05-30_
