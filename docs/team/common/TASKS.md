# TASKS (активное)

**Снимок:** [`STATUS.md`](STATUS.md) · **Prod:** [`PROD_FACTS.md`](PROD_FACTS.md) · **Coder:** [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md)

---

## → Now (2026-06-23)

| Кто | Что |
|-----|-----|
| **owner** | smoke TG «Смотреть в ленте» — карточка **остаётся** раскрытой |
| **owner** | smoke `/lenta/` YouDo · квиз → cloud после ТЗ |
| **@lead-product** + **@lead-designer** | § **QUIZ-REDESIGN** ТЗ |

**Закрыто:** YOUDO-CLICK-PROXY ⏸ (IMAP-only) · YOUDO-IMAP deploy ✅

---

## Очередь

| # | Что | Кто | Приоритет | Статус |
|---|-----|-----|-----------|--------|
| **LENTA-DEEPLINK-RACE** | deep link flash → стабильный focus | — | P0 | ✅ deploy 2026-06-23 |
| **LENTA-LEAD-DEEPLINK** | TG «Смотреть в ленте» → карточка | — | P1 | ✅ deploy 2026-06-23 |
| **TG-DRAFT-BUTTONS** | TG кнопки в сообщении черновика | — | P1 | ✅ deploy 2026-06-23 |
| **NEXT-DRAFT-PLATFORM** | L2 черновик + link под биржу (Kwork t3203318) | — | **P1** | ✅ deploy 2026-06-23 |
| **NEXT-UI-HOTFIX** | FeedCard без «Свернуть» · Hero без CTA flash | — | **P1** | ✅ deploy 2026-06-23 |
| **YOUDO-IMAP-ONLY** | model B deploy | — | — | ✅ 2026-06-23 |
| **QUIZ-REDESIGN** | переделать квиз | product+design → **cloud** | **P1** | после YouDo |
| **YOUDO-IMAP** | timer deploy | — | — | ✅ 2026-06-22 |
| **YOUDO-CLICK-PROXY** | sticky click | — | — | ⏸ отменено 2026-06-23 |
| **YOUDO-SP-STABLE** | sticky human click | — | — | ✅ deploy (same bundle) |
| **YOUDO-SOURCE-GATE** | detail_ok gate | — | — | ✅ deploy 2026-06-22 |
| **YOUDO-AUDIT-P0** | dedup click-through | — | — | ✅ deploy |
| **FEED-HYGIENE** | МИМО filter · `--apply` VPS | — | — | ⏸ owner отмена 2026-06-24 |
| **YOUDO-AUDIT** | read-only аудит | **MiMo audit** | — | ✅ doc |
| **ARTICLE** | demo inbox для статьи | — | — | ⏸ owner отмена 2026-06-24 |
| **AUTH-LOGIN-PHONE** | телефон → код в TG | — | — | ⏸ owner отмена 2026-06-24 |
| **RETENTION-2D** | лента + purge 2 дня (было 7) | — | — | ✅ deploy 2026-06-24 |
| **AI-IMAP-REFRESH-L1** | invisible YouDo: не гонять L1 каждые 90 с если `has_l1` | — | — | ✅ deploy 2026-06-24 |
| **RULES-AUDIT-W1** | CODER_PROMPT+STATUS архив → hot ≤ лимитов | **Lead** | **✅ 2026-06-24** | hot 54/58 · bulk `*_W1_20260624_BULK.md` |
| **RULES-AUDIT-W2** | slim mimo · copy-paste · lead-no-code hotfix | **Lead** | **✅ 2026-06-24** | канон `mimo.mdc` § Копипаст |
| **RULES-AUDIT-W3** | react-best-practices off always-on | **owner** | **✅ 2026-06-24** | Agent decides (Cursor Rules) |
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
