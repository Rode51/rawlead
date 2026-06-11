# TASKS (активное)

**Снимок:** [`STATUS.md`](STATUS.md) · **бэклог:** [`OWNER_INTENT.md`](../architect/OWNER_INTENT.md)

**Решение owner 2026-06-09:** **ads ⏸** · сначала TG smoke + UI + stress/L2

---

## Где мы

**→ @coder:** § **O174b-YOOKASSA** prep ⏸ keys · YouDo ingest monitor (US proxy + antibot)

**→ @owner:** после deploy — Ctrl+F5 `/lenta/` · меньше битых ссылок

---

## Шаги (hot)

| # | Что | Кто | Статус |
|---|-----|-----|--------|
| **15a** | **O165-TG-TEST-GROUP** join 3 acc + feed | **owner post** → Lead Neon | **→ smoke** join+feed ✅ |
| **15b** | **O170-TG-L1-FILTER** | Lead | ✅ deploy |
| **15c** | **O166-HOME-MATCH-BAR** главная полоски | Lead | ✅ deploy **1.18.51** |
| **15d** | **O167-SORT-SOURCE** биржи в dropdown | Lead | ✅ deploy **1.18.52** |
| **15e** | **O168-PRE-ADS-GATES** | Lead | ✅ load **1462ms** · L2 **80%** judge **2026-06-10** |
| **16a** | **O174a-FOOTER-LEGAL** FIO + ИНН | @coder | ✅ owner **2026-06-10** |
| **16b** | **O174b-YOOKASSA** prep → keys → pay | @coder + PM + Design | **⏸** ЮKassa на проверке |
| **17** | **O175-FEED-INBOX** + **O175b** | @coder | ✅ **2026-06-11** theme **1.18.55** |
| **18** | **O176-YOUDO-TRACE** | @coder | ✅ trace on VPS **2026-06-11** |
| **24** | **O182b-YOUDO-IMPORT** | ✅ **2026-06-11** · import hotfix · deploy VPS · pytest **43/43** |
| **23** | **O182-DELIST-INPROGRESS** | ✅ **2026-06-11** · #16149 `source_gone` · pytest **21/21** |
| **22** | **O181-DELIST-CLOSED** | ✅ **2026-06-11** · #16797 · purge apply **306+964** rows |
| **21** | **O180-DELIST-WEB** | ✅ smoke **2026-06-11** · #17048 · backlog drain ongoing |
| **19** | **O177/O179 YouDo** ingest | Lead | ✅ deploy · listing OK |
| **20** | **O178-FEED-SOURCE-SORT** filter+banner | @coder | ✅ deploy **1.18.56** **2026-06-11** |
| **15f** | **YouDo Playwright thread** | Mechanic | код ✅ · **deploy VPS ⏳** |
| **15g** | **O171-OPS-ADMIN-REBUILD** `/ops/` + FLPARSING | @coder | **⏸ после O168** |
| **15h** | **O172-OPS-GREEN-RED** runbook | @coder | **⏸ после O171** |
| **15i** | **O173-DRAFT-WAIT-UX** stream B + 2-й юзер C | @coder + Design | **⏸ после O168** · O160-w ❌ |
| **14** | **ads + portfolio** | owner | **→ после O174 smoke оплаты** |

Закрыто O131–O164 → см. [`STATUS.md`](STATUS.md)

---

## Owner checklist (O165 smoke)

1. ~~Join 3 acc~~ ✅ `5177575757` · peer в feed
2. Написать **тестовую вакансию** в группу (как реальный заказ, не CV/promo)
3. Сообщить Lead — проверим Neon + `/lenta/?source=tg`

---

_O168 active **2026-06-09** · O167 deploy ✅ · O165 smoke ждёт пост owner_
