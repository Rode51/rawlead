# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.12** · [`ROADMAP.md`](../architect/ROADMAP.md)

**Очередь:** [`TASKS.md`](TASKS.md)

> Hot ≤80 строк.

---

## PRE-RELEASE-AUDIT ✅ Lead verify (2026-06-04)

**Theme:** **1.18.4** · deploy VPS ✅ · prod curl OK (BUG-1 CSS, footer bot, trust chip, slot-hint)

**Coder:** BUG-1–5 + P1-A–G · `/pricing/` visible · cabinet sub · notif 3 presets

**Замечание (не блокер):** P1-F — `.rl-live-preview` hide (не `.rl-hero__preview`; floats уже off @900px)

**Owner:** глаза `/pricing/` + ЛК premium · **→ E2E S6**

---

## Hotfix draft VPS ✅ (2026-06-03 ~13:00 UTC)

**Симптом:** баннер «ИИ временно недоступен — повторите» на `/lenta/` при «Написать отклик».

**Причина:** API crash `No module named 'l3_human_style'` — O72e-10 код задеплоен частично (WP/ingest), **`l3_human_style.py` не был на VPS**.

**Fix Lead:** upload `l3_human_style.py` + `ai_analyze.py` + `config.py` → restart `rawlead-api` · import OK.

**Проверка:** залогиниться → «Написать отклик» на карточке · лог `journalctl -u rawlead-api | grep lenta:draft`.

---

## Judge O72e-10 ✅ прогон · gate **L2 ❌** (2026-06-03 12:46 UTC)

**Артефакты:** `data/preprod_ai_prod_audit_judge.md` · `preprod_ai_prod_audit_human.md` · regen shared **61/61** · personal **30/30**

| Контур | Метрика | Порог | Итог |
|--------|---------|-------|------|
| **Auto O72** | draft-only | ≥95% | **95.8%** ✅ |
| | tools | — | **97.2%** ✅ |
| **L1** | понимание / usable | ≥70% | **84.5%** ✅ |
| | complexity | ≥70% | **85.9%** ✅ |
| **L2 shared** | combined | ≥4.0 | **4.16** ✅ |
| | send as-is | **≥70%** (vault) | **40.8%** ❌ → r2 |
| **L3 personal** | uniqueness | ≥3.0 | **3.28** ✅ |
| | send as-is | ≥50% | **80%** ✅ |
| | forbidden leak | 0% | **0%** ✅ |

**Vault:** L2 **≥70%** (новый gate) · **pilot 10 ids** → full 71. Coder: § O72e-L2-r2.

---

## O72e-L2-r2 ✅ Lead verify (2026-06-03)

**Сделано:** `Specificity-якоря по домену` · BAD/GOOD #8925/#10442/#9581/#9326 · gate **70%** в audit.

**Тест:** unittest **9/9 OK** · `test_shared_l2_specificity_domain_patterns`

**Deploy:** `l3_human_style.py` → VPS · `rawlead-api` restart

## O72e pilot judge ✅ прогон · gate **L2 ❌** (2026-06-03 ~13:32 UTC)

**Артефакт:** `data/preprod_ai_prod_audit_judge_pilot.md` · log `data/o99_judge_pilot.log`

| Метрика | Pilot 10 ids | Порог | Итог |
|---------|--------------|-------|------|
| L2 combined | **3.83** | ≥4.0 | ❌ |
| L2 send as-is | **40% (4/10)** | **≥70% (7/10)** | ❌ |

**send=True:** #8925 #9374 #9326 #10362 · **False:** #8772 #9831 #9843 #10442 #8752 #9581

## O72e-L2-r3 ✅ Lead verify (2026-06-03)

**Сделано:** «Глубина без простыни» · tools vs Описание · BAD/GOOD pilot 6 ids.

**Тест:** unittest **16/16** · deploy `deploy-o72e-l2-r3-vps.py` **r3_ok**

**Pilot r2:** 4/10 · **r3:** 6/10 (60%) · **r4:** 6/10 · **r5:** **7/10 (70%) send ✅** — `preprod_ai_prod_audit_judge_pilot_r5.md`

**r5 send=True:** #8925 #9843 #9581 #9831 #9374 #9326 #10362 · **False:** #8772 #10442 #8752

**r4→r5:** #10442 #9843 PASS (GAS) · #10362 #9581 восстановлены · combined **3.97** (<4.0) — script Accept L2 still ❌

**Regen r4:** 10/10 · **r5:** 4 ids (#10362 #8752 #8772 #9581) · deploy `l3_human_style.py` VPS

**Дальше:** full regen 71 + L2 judge (send gate OK) · или r6 на #8772/#8752 flip-flop tools

---

## O108-BC ✅ Lead verify + VPS (2026-06-04)

**Theme:** **1.18.5** · `deploy-o108-bc-vps.py` OK · curl `1.18.5` · `tz_attachments_ok` · deps docx/pypdf

**Prod env:** `PUBLIC_FEED_SOURCES` = fl,kwork,youdo,freelance_ru,freelancejob,pchyol + **21× tg:** (решение владельца) · TZ 8/2 MB

**Тесты:** unittest tz_attachments + l3 **31/31 OK**

---

## Сейчас (очередь)

| # | Задача | Кто | Статус |
|---|--------|-----|--------|
| **O108-BC** | Lead verify + VPS deploy | **Lead** | ✅ |
| **O72e full judge 71** | pilot send **7/10 ✅** → regen all + L2 judge | **owner** | |
| **E2E / vault** | | owner | L2 PASS |

---

## O105-WP-r3 + youdo-lite ✅ Lead verify (2026-06-03)

**WP r3:** anon TWO-SPEEDS → `/pricing/` · dedup delay (anon) · cabinet notif Premium/`/pay` · **1.18.3**

**YouDo:** `ctx.route` block image/font/media + tracker/tag.js · только ephemeral · FL не тронут

**Verify:** `_verify_o105_prod.py` **16/16 ALL OK** · unittest **13/13** · VPS `_abort_heavy_route` ✅

---

## Prod WP **1.18.3** · O105 wave ✅

| § | Deploy |
|---|--------|
| **O105-WP r1–r3** | `deploy-o105-wp-vps.py` |
| **youdo-playwright-lite** | `deploy-youdo-browser-vps.py` |

**Дальше:** pilot judge L2 → E2E → vault → O101 · O105-w1.

---

## O105-WP-r2 ✅ (2026-06-03)

FAQ/how/lenta/O106 collapsed — superseded **1.18.3**.

---

## Prod WP archive · 1.18.2

| § | Deploy | Verify |
|---|--------|--------|
| **O105-WP + r2** | `deploy-o105-wp-vps.py` | D1–D3·D7·FAQ/how/lenta·D4 card |
| **hotfix-youdo-playwright** | `deploy-youdo-browser-vps.py` | unittest **22 OK** |

**O105 prod:** `/` · `/pricing/` · `/cabinet/` · `/faq/` · `/how/` · `/lenta/` — 790 ₽ канон · collapsed card O106.

**Дальше:** pilot judge L2 → E2E → vault → O101 · O105-w1.

---

## Волна O105 — указатели (закрыта WP)

| Док | Статус |
|-----|--------|
| OWNER_INTENT § O101/O105/O106/O107 | ✅ решения |
| LEAD_PRODUCT § O105-COPY | ✅ PM |
| LEAD_DESIGN § O105-D | ✅ Design + Lead |
| CODER § hotfix + O105-WP + r2 | ✅ prod **1.18.2** |
| **P2 backlog** | FAQ 300→790 · anon strip · filter chips mobile |

---

## База (без изменений)

**O63-FIX · O72e-10 prompts · O104 · O99 · O97 · O96** — см. [`STATUS_ARCHIVE`](STATUS_ARCHIVE.md) или TASKS history.

_E2E:_ smoke 4/5 · FR.ru в ленте — владелец после judge.

---

_Lead verify + deploy · 2026-06-03_
