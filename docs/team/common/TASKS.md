# TASKS (активное)

**Снимок:** [`STATUS.md`](STATUS.md) · **Prod:** [`PROD_FACTS.md`](PROD_FACTS.md) · **Coder:** [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md)

---

## → Now (2026-06-22)

| Кто | Что |
|-----|-----|
| **owner** | **M1** — реклама запущена · первые визиты ~23.06 · smoke `/lenta/` |
| **@coder** (Cursor) | fallback · § **YOUDO-DETAIL** если >3 файлов |
| **MiMo `coder`** | **основной** кодинг по § `CODER_PROMPT` |
| **@lead-portfolio** | rode51.ru — только если owner хочет правки сайта |

**Закрыто:** § YOUDO-RESTORE-SNIPPETS ✅ · § BOT-NOTIFY-START ✅ · PRE-ADS-GATE G0–G10 ✅ · O280 ✅

---

## Очередь

| # | Что | Кто | Приоритет | Статус |
|---|-----|-----|-----------|--------|
| **YOUDO-DETAIL** | detail-fetch `/t{id}` — полное ТЗ, метрика `detail_ok_rate` | **MiMo coder** | **P0 M1** | § `CODER_PROMPT` |
| **ARTICLE** | demo inbox для статьи | **MiMo coder** | P1 | § `CODER_PROMPT` |
| **M1** | посевы + мониторинг конверсии | owner | **→ сейчас** | live |
| **P1–P6** | post-M1 tech (см. CODER_PROMPT) | @coder | backlog | backlog |
| **O39-docs** | TZ_API + schema docs | Lead | P2 | ⏳ |
| **A9–A11** | repo hygiene (scripts archive) | @coder | P3 | ⏳ |

**Готово (index):** O280-E2E · O283/O284 billing base · G6 L3 · G7b load · CABINET link · FEED-MULTI · rode51 P2 · O116 support · M1-bot.

---

## Аудит repo (2026-06-20)

Источник: [`AUDIT_REPORT_2026-06-20.md`](../../AUDIT_REPORT_2026-06-20.md) · **не блокер M1**.

| Приоритет | Статус |
|-----------|--------|
| A0–A8 Lead/Coder | ✅ |
| A9 O200 auto-tools | backlog |
| A10–A11 scripts archive | backlog |
| A13+ api_server split | после M1 |

---

## Probe

```powershell
python scripts/probe_prod_facts_vps.py --write
```
