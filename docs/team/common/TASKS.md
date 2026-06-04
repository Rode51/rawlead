# TASKS (активное)

**Снимок:** [`STATUS.md`](STATUS.md)

**Решение владельца 2026-06-04:** **Фаза A** L2 send 60.6% — **релиз промпта ok**, r11 по ситуации · **UI/UX — параллельный чат @lead-architect** · stress после send ≥70%.

---

## Фаза A — ИИ gate (**freeze done, r11 опционально**)

| # | Задача | Кто | Статус |
|---|--------|-----|--------|
| **O72e-A-w1** | regen **21** + judge w1 | **Lead** | ✅ send **50%** FAIL |
| **O72e-L2-r9** | prompt send gate · tests 25/25 | **@coder** | ✅ |
| **O72e-L2-r10** | #12148 stack conflict · regen 1 | **Lead** | ✅ draft ok · judge rubric ⏸ |
| **O72e-A-freeze** | regen 52/55 + judge 71 | **Lead** | ✅ send **60.6%** ❌ |
| **O72e-L2-r11** | паттерны freeze FAIL → prompt | **@coder** | **→ по ситуации** |
| **O72e-A-w3** | judge **tg-only 10** · L1 spot-check | Lead | backlog |

**Gate freeze:** L2 combined ≥4.0 · send **≥70%** · L1 usable ≥70% · L3 smoke ✅

**Бюджет:** волны ~$4–6 · full 71 ~$2.5 · **не** regen 71 blind.

---

## Параллельно (**→ owner + @lead-architect**, не блокирует r11)

| # | Задача | Чат |
|---|--------|-----|
| **UI/UX pre-ads** | wireframes, copy, lenta/cabinet/pricing | **@lead-architect** + @lead-designer |
| **O105-w1** | pay prod smoke | owner |
| **O113-seo** | backlog | — |

---

## ⏸ После Фазы A

| # | Задача |
|---|--------|
| **Stress / vault** | стабильность |
| **O112-support** | FAB |
| **O107** | Trial |
| **E2E-UX финал** | polish перед ads |
| **Soft ads** | после freeze |

---

## ⏸ Ops фон

| # | Задача | Триггер |
|---|--------|---------|
| **O110-fl-proxy** | FL 403 | >2×/сутки |
| **O115-tg-feed** | tg ingest | ✅ 25/24h |

---

## Закрыто 2026-06-04

**O114-vacancy** ✅ · backfill **12** · judge post-O114 send **56.7%**

**O72e-L2-r8** ✅ · pilot r8 **80%** (10 regen)

**O109** ✅ · **O108-BC** ✅ · **PRE-RELEASE-AUDIT** ✅

---

_Lead · 2026-06-04 · Фаза A → stress → ads_
