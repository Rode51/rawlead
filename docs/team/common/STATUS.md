# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.12** · [`ROADMAP.md`](../architect/ROADMAP.md)

**Очередь:** [`TASKS.md`](TASKS.md) · **Coder:** [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md)

**Next:** **M1 wave 1** посевы · CSP/HSTS nginx (post-M1)

**Pre-M1 security hotfix ✅ (2026-06-21 @coder):** M2 owner fallback убран · M1 `RADAR_CORS_ORIGINS` на VPS · prod `GET /v1/me/feed` без Bearer → **401** · G0 **32 passed**, 1 skipped

**MiMo ✅ (2026-06-21):** [`2026-06-21-mimo-pre-m1-security.md`](../problems/2026-06-21-mimo-pre-m1-security.md) · [`2026-06-21-mimo-post-g7b-load.md`](../problems/2026-06-21-mimo-post-g7b-load.md) · **P0=0**

**Принято владельцем (2026-06-21):** G7b deploy + ЛК ссылка ✅

**Deploy ✅ (2026-06-21 Lead):** `deploy-l2-stack-vps.py` + `deploy-web-rawlead-vps.py` · commits `3e12011`+`2af72a1`

**G7b full ✅:** stress **09:52Z** PASS · **prod** API+Next залиты

**CABINET-EXCHANGE-LINK ✅:** «Читать на бирже ↗» в ЛК · **prod** Next

**G6 ✅ (2026-06-21):** `preprod_ai_prod_audit_judge.md` **Accept L3: ✅ PASS** · 2026-06-20T18:24Z · uniq **3.04** · combined **4.19** · send **68%** · leak **0%** · L3 v4 `l3_opener_too_similar` + deploy VPS

**YOUDO-T14878013 ✅ (2026-06-21):** lead #8256 delist `youdo_detail_mismatch` · `lead_pipeline` — всегда fetch YouDo detail · [`problems/2026-06-20-youdo-t14878013-mismatch.md`](../problems/2026-06-20-youdo-t14878013-mismatch.md)

**FEED-MULTI-FILTER ✅ (2026-06-21):** multi category/source · **deploy Next ✅** prod verify

**G4-fix ✅ (2026-06-20):** desktop J1–J9,J5,J6,J8,J11 **10/10** · mobile J10 **1/1** · gate `preprod_ux_journey.json` **11/11** · `j5_draft_ok: true` · `critical_count: 0` · harness J5 = n16 parity (no reload между drafts)

**draft_as_is-L2 ✅ (Lead 2026-06-20):** avg **4.0** · vendor-lock **0** · ux_audit **0 critical 24/24** · G0 pytest ✅

---

## PRE-ADS-GATE ✅ (2026-06-21 Lead sign-off → M1)

| Шаг | Прогон | Кто | Статус |
|-----|--------|-----|--------|
| G0 | pytest smoke | @coder | ✅ **32 passed**, 1 skipped (2026-06-21 pre-M1 security) |
| G1 | Next E2E 24/24 | @coder | ✅ **24/24** (2026-06-20 · n5/n17 draftable lead id) |
| G2 | Playwright smoke 5/5 | @coder | ✅ **5/5** `s2_pass` (2026-06-20 · Next selectors) |
| G3 | UX audit 0 critical | @coder | ✅ **0 critical** · U1–U12 **24/24** (2026-06-20) |
| G4 | UX journey J1–J11 | @coder | ✅ **11/11** · `j5_draft_ok` · 0 critical (2026-06-20 · desktop+mobile gate) |
| G5 | AI matrix S1 | @coder | ✅ **12/12** · `s1_pass` (2026-06-20) |
| G6 | L3 judge uniquify | @coder | ✅ **PASS** uniq 3.04 (2026-06-21) |
| G7a | Load quick smoke | @coder | ✅ tier+tz+load (2026-06-21) |
| G7b | Load **full** 50 VU + draft×20 | @coder | ✅ deploy **2026-06-21** Lead |
| G-SEC | Security regression | @coder + owner | ✅ S-1 + **S-2 owner** |
| M0–M4 | **MiMo** audit + skills | owner | **M0–M1** ✅ · **M2+M4** ✅ **2026-06-21** |
| G8 | Radar 2–4 цикла | owner | ✅ owner **2026-06-21** |
| G9 | S5–S6-b ручная | owner | ✅ owner **2026-06-21** |
| G10 | anon квиз→TG→% | owner | ✅ owner **2026-06-21** |

§ команды → [`CODER_PROMPT`](../architect/CODER_PROMPT.md) · runbook → [`PREPROD_STRESS_RUN.md`](../../ops/PREPROD_STRESS_RUN.md)

**G4 сдача (Lead ✅ 2026-06-20):** `ux_journey.py` Next dual-path · desktop J1–J9,J5,J6,J8,J11 + mobile J10 · `data/preprod_ux_journey.json` **11/11** · `j5_draft_ok: true` · leads 13353+13221 · 0 critical

**G3 сдача:** `scripts/preprod_playwright/ux_audit.py` — Next/WP dual-path (`next_ui`) · benign 404/Metrika console · артефакты `data/preprod_ux_audit.json` + `data/preprod_ux_audit_human.md`

**draft_as_is-L2 сдача (2026-06-20):** `src/ai_analyze.py` (`_shared_reply_system` · `_build_shared_reply_user` · `_shared_draft_send_ready_reason` · tool aliases · fail on last send_ready) · `src/l3_human_style.py` · deploy `scripts/deploy-o200-l2-vps.py` · `ux_audit.py --base-url https://rawlead.ru` (без `--skip-llm`) → avg **4.0** · vendor-lock **0** · **24/24** · critical **0**

**G2 сдача:** `scripts/preprod_playwright/smoke.py` — dual Next/WP селекторы · артефакт `data/preprod_playwright_report.json`

**Sign-off M1:** все G0–G10 ✅ → Lead → посевы

## O280 Feed UX ✅ (owner accept 2026-06-20)

| | |
|---|---|
| **R1** | «открыть ссылку» · жёлтый **Отклик ✓** · draft при раскрытии · выделение текста |
| **R2** | Квота **справа** над «Кабинет →»: `Осталось N откликов` · при лимите `· лимит обновится через M мин` |
| **Deploy** | `deploy-web-rawlead-vps.py` · owner smoke ✅ |

Файлы: `LoginPanel.tsx` · `lenta/page.tsx` · `FeedCard.tsx` · `globals.css`

## O116 Support ✅ · M1-bot ✅ · PRE-ADS W1 ✅ (2026-06-20)

FAB↔TG↔reply в боте · bot ▶️ Старт + UTM · API pool + webhook digest + draft feed gate.

---

## Index (детали в архиве / PROD_FACTS)

| Блок | Где |
|------|-----|
| O280-E2E gate | `data/preprod_next_e2e_human.md` |
| O200 L2 judge | `data/preprod_o200_judge_human.md` |
| Portfolio rode51 P2 | [`PROD_FACTS`](PROD_FACTS.md) |
| Billing O283/O284 | archive · PROD_FACTS |
| Repo audit A7–A12 | [`TASKS`](TASKS.md) § аудит |
