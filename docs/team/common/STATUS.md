# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.12** · [`ROADMAP.md`](../architect/ROADMAP.md)

**→ Now:** M1 реклама live · **MiMo coder** = основной кодинг · § YOUDO-DETAIL P0 · § ARTICLE-DEMO-INBOX

**Prod UI:** `rawlead.ru` = **Next.js** (O280 cutover ✅ **2026-06-19**)

---

## Процесс кодинга (2026-06-22)

**MiMo `coder`** пишет код · **Lead** verify + deploy + commit. Канон: `.cursor/rules/mimo.mdc` · `.mimocode/MIMO_CODER.md`.

---

## YOUDO-RESTORE-SNIPPETS ✅ deploy (2026-06-22)

**Решение владельца:** вернуть YouDo с snippets пока ServicePipe не починен.

| | |
|---|---|
| **Env** | `YOUDO_DETAIL_MIN_CHARS=0` на VPS |
| **Restore** | `restore_youdo_visible_vps.py --apply` → **restored=4219** |
| **DB** | `youdo_visible=4219` · `youdo_hidden=1` |
| **API** | `GET /v1/feed?source=youdo` — лиды есть |
| **pytest** | `test_o281` + `test_o223` — **17 passed** |

**Smoke:** Ctrl+F5 `/lenta/` → «Фильтр» → **YouDo** → карточки появляются (snippet-тело, не full TZ).

---

## M1 + YouDo — риск для посетителей (2026-06-22)

**Реклама запущена** · первые визиты ~23.06.

| Источник | Для юзера | Риск |
|----------|-----------|------|
| FL · Kwork · TG | полное ТЗ · L1 · черновик | ✅ низкий |
| YouDo | карточки в ленте · **короткое описание** | ⚠️ средний — отклик менее точный |
| Фильтры | работают после hotfix 22.06 | ✅ |

**Mitigation:** snippet-режим deployed · **P0:** § YOUDO-DETAIL → **MiMo coder**.

**Probe 22.06:** listing `parsed=50` · `new=0` после 01:08 (дедуп) · antibot 1701b watch · [`2026-06-22-youdo-m1-day.md`](../problems/2026-06-22-youdo-m1-day.md)

---

## FEED-FILTER-TG-STUCK-v2 ✅ deploy (2026-06-22) + hotfix

Prefs **v3** · v2 migrate сбрасывает биржи · merge без server sources · race fix `filterGenerationRef`.

**Hotfix (Lead):** `FilterBar.handleSheetApply` / `handleDropdownApply` вызывали `onCategoriesChange` + `onSourcesChange` + `onSortChange` — каждый вызов `applyFilters` перезаписывал остальные с устаревшими значениями. Исправлено: `FilterBar` теперь принимает `onApplyFilters(FeedFilterState)` и делает **один** вызов для всех объединённых операций.

**Owner smoke:** Ctrl+F5 `/lenta/` → выбрать FL → список фильтруется · «Сбросить» → все биржи

---

## L1-TILDA-TAGS ✅ (2026-06-22)

YouDo t14881683: L1 угадывал `wordpress_dev` без «тильда» в коротком snippet.

| # | Сделано |
|---|---------|
| 1 | `sanitize_l1_cms_tags` — tilda/тильda/zero block → strip `wordpress_dev`, ensure `tilda_dev` |
| 2 | L1 prompt — явное правило Tilda ≠ WordPress (O47) |
| 3 | `enrich_youdo_l1_snippet` + detail carousel fallback в `fetch_project_page_html` |
| 4 | golden `tilda_turnkey` · `tilda_zero_block` |
| 5 | Deploy — `youdo_parser` + `g6` + `o230` · API active |
| 6 | **Follow-up:** `YOUDO_DETAIL_FETCH=1` · re-L1 `18311` → `['tilda_dev','ecommerce_dev','api_integration']` |
| 7 | `/lenta/` карточка #14881683 — теги `tilda dev` (без `wordpress_dev`) |

**Ограничение prod:** YouDo detail pages — ServicePipe на всех DC+RU слотах VPS (2026-06-22); re-L1 `18311` с TZ-fallback после неудачного detail fetch.

**pytest:** `tests/test_l1_tags_cms.py` — **4 passed**

**Как проверить:** `https://rawlead.ru/lenta/` → YouDo «Сделать сайт под ключ» → `tilda dev` · `https://youdo.com/t14881683`

**Скрипт one-shot:** `scripts/replay_l1_youdo_tilda_vps.py`

---

## FEED-QUIZ-POLISH ✅ deploy (2026-06-22)

Фильтры F5 · квиз Variant C (min 8 + signal coverage 4) · insufficient retry. Deploy Lead verify.

---

## PRE-ADS-GATE ✅ → M1 (2026-06-21)

| Шаг | Статус |
|-----|--------|
| G0–G7b · G-SEC · G8–G10 | ✅ |
| MiMo M0–M4 | ✅ P0=0 |
| Pre-M1 security M1+M2 | ✅ commit `786aede` |
| BOT-NOTIFY-START | ✅ deploy **2026-06-21** |
| CABINET-PARITY | ✅ **2026-06-21** |

Чеклист посевов: [`M1_SEEDING_CHECKLIST.md`](../marketing/M1_SEEDING_CHECKLIST.md)

---

## Недавно на prod

| Что | Когда |
|-----|-------|
| YOUDO-FULL-TZ-GATE O281 — gate + audit 521 hidden | 2026-06-22 |
| FEED-FILTER-TG-STUCK-v2 — prefs v3, TG reset fix | 2026-06-22 |
| FEED-QUIZ-POLISH — F5 фильтры + квиз depth + deploy | 2026-06-22 |
| BOT-NOTIFY-START — пинг владельцу на первый /start | 2026-06-21 |
| CABINET-PARITY — push Match без %, retake-кнопка | 2026-06-21 |
| Bearer-only `/v1/me/*` + CORS | 2026-06-21 |
| G7b deploy · ЛК «Читать на бирже» | 2026-06-21 |
| G6 L3 judge PASS · multi-filter · YouDo #8256 | 2026-06-20–21 |
| O280 Feed UX R1+R2 · E2E 24/24 | 2026-06-20 |
| rode51.ru P2 | 2026-06-21 |

Детали prod → [`PROD_FACTS.md`](PROD_FACTS.md) · артефакты → `data/preprod_*`

---

## Index (архив)

G2–G5 сдачи · draft_as_is-L2 · O116/M1-bot · MiMo отчёты → [`STATUS_ARCHIVE`](../archive/STATUS_ARCHIVE.md) · [`problems/`](../../problems/)
