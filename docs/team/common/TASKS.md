# TASKS (активное)

**Снимок:** [`STATUS.md`](STATUS.md) · **карта:** [`ROADMAP.md`](../architect/ROADMAP.md)

**Фаза:** **Launch path** · prod theme **1.18.49**

---

## Где мы

**→ @owner:** `/ops/` **Сбросить баны** (после deploy) · Wave 2 sign-off ✅

**→ @coder:** фон — perf gate · O133 TZ (после ads)

---

## Шаги

| # | Что | Кто | Статус |
|---|-----|-----|--------|
| 1–11e | … · O139 | — | ✅ |
| **11f** | **O141-EXCHANGE-PARITY** | @coder + Lead deploy | ✅ **2026-06-08** |
| **12** | **O144-RFP-COMPLY** | @coder | ✅ код · deploy ⏸ |
| **12a** | **O145-FEED-CAT** | @coder | ✅ код · deploy ⏸ |
| **12b** | **Wave 2 rerun** | owner | **⚠️** J5 ✅ · J4 flake |
| **13** | **O146-DRAFT-CARD-UX** flip · pending · btn glow | @coder | ✅ код · accept ⏸ |
| **13a** | **O147-FEED-FLIP-MATCH** | @coder | ✅ deploy · **flip → O149** |
| **13c** | **O148-DRAFT-OR** warm · tools tz · btn 40s | @coder | ✅ deploy · owner smoke ⏸ |
| **13d** | **O149-NO-FLIP** inline expand | @coder | ✅ deploy · smoke → O150 |
| **13e** | **O150-DRAFT-UX-POLISH** | @coder + Lead | ✅ deploy ✅ |
| **13f** | **O151-OR-ACC2-UX** | @coder + Lead | ✅ deploy ✅ |
| **14a** | **O153-CARD-CHIPS** | @coder | **✅ Lead smoke** |
| **14a2** | **O154-GRID-NEIGHBOR** | @coder | **✅ Lead smoke** |
| **14b** | **O152-EXCHANGE-TRACE** | @coder | **deploy ✅** · owner `/ops/` ⏸ |
| **14c–e** | **O155–O157** HC · YouDo human · traffic | @coder + Lead | **deploy ✅** |
| **14f** | **O158-MATCH-UX** дубли push · шкала · ?lead= | @coder + Lead | **deploy ✅ 2026-06-08** |
| **14g** | **O121-w2b** `/ops/` clear-bans fetch | @coder + Lead | **✅ код · deploy ⏸ owner smoke** |
| **13b** | **Wave 2** journey 10/10 | owner | ⏸ после O147 |
| **14** | **ads + portfolio** | owner | **последним** |

---

## Owner checklist (Wave 2)

1. Premium → lead без draft → отклик **≤90s**
2. `/ops/` → FL row: `listing: 30 parsed · N fresh` (после O139 fresh>0 при новых)
3. Premium feed → sort **date** показывает все visible, не 10 cap
4. `preprod_draft_burst --max-leads 3`
5. `preprod_ux_journey` full → **10/10**
6. Опц. `OPENROUTER_HTTP_PROXY` если OR direct медленный

---

## ⏸ После ads

O113 · O123-w2 · O105-w2 · **O133** TZ downloader · **O142** split `ai_analyze` · **O143** split `api_server`

---

_O144 active **2026-06-08** · Wave 2 ⏸ до deploy_
