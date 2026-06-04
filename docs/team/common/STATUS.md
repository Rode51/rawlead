# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.12** · [`ROADMAP.md`](../architect/ROADMAP.md)

**Очередь:** [`TASKS.md`](TASKS.md)

> Hot ≤80 строк.

---

## O109 ✅ Lead verify + VPS (2026-06-04)

**Theme:** **1.18.6** · `deploy-o109-bot-deeplink-vps.py` OK · curl `1.18.6`

**Симптом (владелец):** push Match 82% Kwork #3190279 — в `/lenta/` карточки нет; кнопка «Лента» вела в общую ленту.

**Причина:** O65 delist ложный `source_gone` — маркер `"404"` в HTML Kwork; push успел до скрытия.

**Fix (Coder, § O109):** убран `"404"` из `_KWORK_GONE_MARKERS` · grace **6 ч** после L1 · relist **234** kwork · bot «Лента» → `/lenta/?lead={id}` · scroll + pulse `.rl-lead-card--push-focus`.

**Verify:** lead **#11837** в feed API ✅ · `GET /wp-json/rawlead/v1/leads/11837` ✅ · tests **9/9**

**Процесс:** код в сессии до ужесточения `lead-no-code` — приёмка Lead retroactive · rules A+B+C **2026-06-04**

**Owner:** новый push → deep link; старый push — вручную [`/lenta/?lead=11837`](https://rawlead.ru/lenta/?lead=11837)

---

## O108-BC ✅ (2026-06-04)

**Theme:** **1.18.5** · TZ attachments B+C · TG **21** канал в `PUBLIC_FEED_SOURCES` · tests **31/31**

---

## PRE-RELEASE-AUDIT ✅ (2026-06-04)

**Theme:** **1.18.4** · BUG-1…5 + P1 · `/pricing/` · cabinet sub · notif 3 presets

---

### O114 ✅ Lead verify + VPS (2026-06-04)

**Coder:** `vacancy_filter.py` · pre-L1 в `analyze_lite` · post-L1 guard · L1 block VACANCY (O114) · `backfill_vacancy_hide.py`

**Тесты:** **24/24** unittest (vacancy + l3 + l1 complexity)

**VPS:** `deploy-o114-o115-vps.py` OK · `VACANCY (O114)` on prod

**Backfill:** **12** скрыто ✅ (#7049, #6943, #7240, …)

**Judge post-O114 (30 id, без regen):** combined **4.26** ✅ · send **56.7%** ❌ · `preprod_ai_prod_audit_judge_post_o114_30.md`

---

### O115 ⚠️ Lead verify частично (2026-06-04)

**Health:** tg **25 ingest / 24h** · **2 visible / 24h** · `tg_main` active on VPS · recent #12789

**Gaps:** `radar_site_tg.log` пуст/нет · judge pilot **только tg:%** не гоняли · top-3 feed API без tg (норм если L1 скрыл)

---

**Regen:** pool 30 since 2026-05-20 · догон **16/17** (fail **#7049** forbidden words) · **#6907** allow-cliche ok

**Judge:** combined **4.2** · send **63.3%** ❌ (&lt;70%) · `preprod_ai_prod_audit_judge_r8_30.md`

**Full 71:** ⏸ · промпт r8 на VPS ✅ · новые лиды ingest без regen

---

## O72e-L2-r7 ✅ pilot PASS (2026-06-04)

**Coder:** `l3_human_style.py` · tests **19/19** · pilot r7 **4.30/80%** · Full judge ⏸

---

## O114+O115 ✅ Coder (2026-06-04)

**O114:** `vacancy_filter.py` pre-L1 + L1 **VACANCY** block + `_finalize` override · `backfill_vacancy_hide.py` · tests **3/3** · dry-run 800 visible → **4** hits

**O115:** `o115_tg_feed_health.py` · Neon tg **24**/24h (2 visible) · judge hook `--source-like tg:%%` · deploy `deploy-o114-o115-vps.py`

**Lead:** VPS deploy + `backfill_vacancy_hide.py` (без `--dry-run`) · TG pilot judge 10 · Pay/SEO/UI — backlog «перед рекламой»

---

## Сейчас — **Фаза A: freeze done · r11 опционально**

| # | Задача | Статус |
|---|--------|--------|
| **O72e-A-freeze** | regen 52/55 + judge 71 | ✅ send **60.6%** · L1/L3 ✅ |
| **O72e-L2-r11** | #9843 TG wording, CRM depth… | **→ по ситуации** |
| **UI/UX pre-ads** | wireframes, copy | **→ @lead-architect** (параллельно) |
| **O114** | backfill **12** | ✅ |

**Gate:** L2 send **60.6%** (цель 70%) · combined **4.27** · L1 **83%** · L3 **92%**

**Judge freeze:** [`preprod_ai_prod_audit_judge_o72e_a_freeze.md`](../../data/preprod_ai_prod_audit_judge_o72e_a_freeze.md) · regen [`regen_o72e_a_freeze.json`](../../data/regen_o72e_a_freeze.json)

**Промпт r9+r10:** VPS ✅ · L2 — **можно гонять ingest/regen волнами** без блокировки UI.

**Owner параллельно:** UI/UX чат · pay smoke · stress — после send ≥70% или релиза.

**FL proxy ⏸:** монитор → **O110**

---

## Архив (детали)

O72e-L2 r3–r5 · O105 WP **1.18.3** · hotfix draft l3 (2026-06-03) · Judge прогоны — [`STATUS_ARCHIVE.md`](../archive/STATUS_ARCHIVE.md)

---

_Lead verify · 2026-06-04 · prod theme **1.18.6**_
