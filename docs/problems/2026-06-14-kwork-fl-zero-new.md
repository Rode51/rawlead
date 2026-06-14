# Kwork / FL: 0 новых заказов несколько часов

**Date:** 2026-06-14  
**Owner:** «последний заказ от Kwork 6 часов назад, на Kwork есть заказы а у нас нет»  
**Triage:** Lead · Neon + log read-only

---

## Facts (VPS 2026-06-14 ~06:30 MSK)

| Source | Last Neon insert | MSK | 6h total/visible |
|--------|-----------------|-----|-----------------|
| **Kwork** | 2026-06-14 03:09 UTC | **06:09 MSK** | 2 / 1 |
| **FL** | 2026-06-13 21:30 UTC | **00:30 MSK** | ~0 |
| **YouDo** | 2026-06-14 05:37 UTC | 08:37 MSK | fresh |

**Kwork log:** `listing:kwork parsed=12 fresh=0` every cycle since 06:09 MSK.  
**BUT:** `pipeline:skip filter kwork:id=3196905` at 13:32 MSK = new item DID appear, got word-filtered.

---

## Root cause — Kwork: two problems stacked

### 1. Only one page fetched (12 items, MVP design)

`kwork_parser.py` line 170: `"""GET первая страница (без пагинации в MVP)."""`

We see top-12 from `KWORK_PROJECTS_URL`. Kwork has many more orders on page 2+. If new orders appear in a different category or below rank-12, **we never see them**.

### 2. Word filter blocks some new items that reach page 1

Today's kwork items that appeared fresh but were blocked:
- `kwork:id=3196826` (03:35 MSK) — filter
- `kwork:id=3196861` (05:03 MSK) — filter  
- `kwork:id=3196862` (05:15 MSK) — filter
- `kwork:id=3196905` (13:32 MSK) — filter

Filter is using words from `docs/ops/FILTERS.md` — these kwork orders have stop-word in title/snippet (e.g. design skill words, `вебинар`, etc).

**Owner repro (2026-06-14):**
- [3194789](https://kwork.ru/projects/3194789/view) «Сделать лендинг» — **already in Neon** 2026-06-10, visible ✅
- [3196704](https://kwork.ru/projects/3196704/view) «Парсинг сайтов» — **already in Neon** 2026-06-13 18:50 MSK, visible ✅
- Screenshot «Платформа для учебного центра» — **NOT in Neon** ← real parser gap
- Screenshot «Переписать промпт для Gemini» (3196630), «Поправить выгрузку фида» (3196662) — **in Neon**, visible ✅

**Owner confusion:** old orders still live on kwork.ru ≠ missing from RawLead. Check `/lenta/?source=kwork` scroll down (7-day window).

---

## Root cause — FL: low supply (expected Sunday)

FL `parsed=30 fresh=0` since 00:30 MSK Jun 14 (~13h).  
FL normally runs 3 pages. `fresh=0` = all 30 items already in DB.  
**Possible:** Sundays have low FL posting volume. Manual check: go to `FL_PROJECTS_URL` → see if there are items with new dates.

---

## Action needed

| # | Fix | Who | Priority |
|---|-----|-----|----------|
| 1 | **Kwork pagination:** fetch pages 2–3 in `kwork_parser.py` (same pattern as `fl_parser.py` 3 pages) | @coder | P1 |
| 2 | **Kwork URL review:** confirm `KWORK_PROJECTS_URL` in `.env` covers the right category (owner check) | owner | P0 manual |
| 3 | **Filter softening for Kwork:** some stop words that block design-adjacent orders should only apply to TG, not Kwork | @coder § in O213 | P1 |
| 4 | **FL Sunday baseline:** verify manually FL_PROJECTS_URL URL for today | owner | P2 |

**Not broken:** parsers running, proxy OK, Neon reachable. This is **scope/coverage** problem, not infrastructure.

---

## Neon sample (last 3 Kwork orders saved)

| id | MSK | visible | title |
|----|-----|---------|-------|
| 23701 | 06:09 Jun 14 | ✓ | Сео оптимизация на ВП |
| 23678 | 03:01 Jun 14 | ✗ | Упаковка игрушки |
| 23669 | 01:51 Jun 14 | ✓ | Рассылка мейл |
