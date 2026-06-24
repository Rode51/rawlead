# STATUS — bulk из hot pre-W1 (2026-06-24)

Полные блоки, снятые RULES-AUDIT-W1. Актуальный hot: [`STATUS.md`](../common/STATUS.md).

---

## LENTA deep link — ✅ deploy (2026-06-23)

**Fix:** merge lead в `loadFeed` · expand сохраняется · scroll после load  
**⚠️** возможен краткий skeleton при `auth` reload — smoke TG

## LENTA-DEEPLINK-RACE — ✅ closed

**Next:** `?lead=` → `deepLinkRef` · `feedApi.lead` prepend · expand+scroll+pulse · build+deploy ok  
**Smoke:** TG «Смотреть в ленте» → карточка в ленте

---

## TG-DRAFT-COPY-HOTFIX — ✅ deploy (2026-06-23)

**Fix:** `copy_text: {"text": ...}` + лимит 256 · pytest `test_o265` **15 passed** · prod active

## INCIDENT — TG draft sendMessage 400 — ✅ closed

**Bot:** после «Отклик» — **Скопировать текст** + **На Kwork/FL ↗**  
**pytest verify:** `test_o265` 14 passed · **prod:** `match_push.py` + `rawlead-api`/`bot-poll` active

## NEXT-UI + NEXT-DRAFT — ✅ deploy (2026-06-23)

**Web:** Hero anti-flicker · FeedCard «Открыть на Kwork» · без «Свернуть»  
**Backend:** L2 platform playbooks · `match_push` source/url  
**pytest verify:** `test_o280` 2 passed · `test_o135`+`test_o220` 28 passed

## TG-DRAFT-BUTTONS — ✅ verify (2026-06-23)

**Задача:** в @rawlead_bot после «Отклик» — inline **Скопировать текст** + **На биржу ↗** — **код ✅** · deploy ⏳

---

## QUIZ-REDESIGN — ✅ deploy (2026-06-23)

**Claude Code:** `quiz_cards_v1` (56) + `v2` (130) — тексты упрощены · `skills_on_like` без изменений  
**Deploy:** `deploy-o217-quiz-vps.py` · `rawlead-api` **active** · smoke `quiz_source=synthetic` · merged **186**  
**pytest verify:** 68 passed (Lead) · **⚠️** 23 title >70 симв. (косметика)

**model B:** last 30 + PG dedup · listing/browser **off** · backup `pre_youdo_imap_b_20260623-065533`  
**verify:** pytest 50 passed · **prod:** `listing_skip` · IMAP 30 tasks/poll · timer active  
**Watch:** oneshot ingest >2 мин → `systemctl kill rawlead-youdo-imap.service`

## YOUDO — ⏸ listing backup

CLICK-PROXY / click-through **отменено** при IMAP-only.

## YOUDO-IMAP-ONLY — ✅ deploy (2026-06-23)

**pytest:** 44 passed · **backup:** `pre_click_retry_20260622-141501.tar.gz` · **radar** active

| Watch 24h | |
|-----------|--|
| `pending=N` в `fetch:youdo outcome` | retry-очередь |
| `stage=click_summary retry>0` | повторные клики идут |
| `click_detail outcome=ok` | detail пробит |

## YOUDO-SP-STABLE — verify частично (2026-06-22)

**pytest:** `test_o269` + `test_youdo_human` — **25 passed**

| ✅ | ❌ gaps |
|----|---------|
| hover+jitter · go_back · click IPC · `click_ok=` trace | `click_summary` · cache hit/miss log · debug HTML write · ingest lag doc · IPC pytest |

**Deploy:** не делали · owner «задеплой» → worker + 3× `src/*` · radar restart · watch `click_ok>0`

---

## YOUDO-SOURCE-GATE — ✅ deploy (2026-06-22)

| | |
|---|---|
| **Backup** | `pre_source_gate_20260622-114840.tar.gz` |
| **Откат** | [`2026-06-22-youdo-source-gate-rollback.md`](../../problems/2026-06-22-youdo-source-gate-rollback.md) |
| **Диагноз логов** | радар **жив** (`parsed=50`) · **new=0** (все id уже в базе) · последний insert ~11:17 UTC |
| **backfill snippets** | ❌ owner **нет** — старые ~4219 snippet-YouDo **остаются** в ленте · gate только на **новые** ingest |

---

## YOUDO-CLICK-DETAIL ✅ deploy (2026-06-22)

| | |
|---|---|
| **Код** | click-through detail в sticky Camoufox · fallback `goto` · trace `stage=click_detail` |
| **Env** | `YOUDO_CLICK_DETAIL=1` · `YOUDO_CLICK_DETAIL_MAX=10` |
| **pytest** | `test_o269` + `test_youdo_human` — **45 passed** |
| **Deploy** | 4 файла на VPS · `rawlead-radar` + `rawlead-api` **active** |
| **Watch** | `youdo:ingest new=0` → traces когда появятся новые id · antibot streak после restart — мониторить |

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

**Probe 22.06:** listing `parsed=50` · `new=0` после 01:08 (дедуп) · antibot 1701b watch · [`2026-06-22-youdo-m1-day.md`](../../problems/2026-06-22-youdo-m1-day.md)

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

## Недавно на prod (pre-W1 snapshot)

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
