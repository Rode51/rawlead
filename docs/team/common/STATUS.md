# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.12** · [`ROADMAP.md`](../architect/ROADMAP.md)

**Очередь:** [`TASKS.md`](TASKS.md)

> Hot ≤80 строк · детали → [`archive/STATUS_ARCHIVE.md`](../archive/STATUS_ARCHIVE.md)

---

## Снимок prod (2026-06-07)

| Контур | Факт |
|--------|------|
| **WP theme** | **1.18.35** · O131 perf boot + draft poll · deploy VPS ✅ |
| **ИИ gate** | L2 send **71.8%** ✅ · combined **4.28** · L1 **83.1%** · L3 **92%** |
| **VPS** | **2 GB RAM** ✅ owner upgrade **2026-06-08** · swap 0 · radar **0 OOM** post-reboot |
| **Бот prod** | @rawlead_bot · O120 TG failover · **O105 pay ✅** (WP 1.18.3+ · `premium_pay.py`) |
| **Админка** | `/ops/` w2 · **w2b** timeout 90s в коде ✅ · deploy/smoke owner |
| **TG acc2** | **6/6 done** · listen **6 чатов** на VPS ✅ · CSV v2 синхронизирован |
| **TG proxy acc1** | **45.152** мёртв (TLS) · **временно 38.154** (acc2 spare) · VPS ✅ local script |

**Judge freeze:** [`preprod_ai_prod_audit_judge_o72e_a_freeze.md`](../../data/preprod_ai_prod_audit_judge_o72e_a_freeze.md) · r12 [`…_r12.md`](../../data/preprod_ai_prod_audit_judge_o72e_a_r12.md)

---

## Закрыто недавно ✅

| § | Суть |
|---|------|
| **O117** | Kwork Playwright wall-clock **120s** → httpx fallback · на VPS |
| **O120** | TG Bot API proxy pool · auto-failover acc1→2→3 · на VPS |
| **O121-w0** | `/ops/` Bot restart |
| **O121-w0b** | секция **«Боты»** · per-bot restart · `deploy-o121-w0b-vps.py` |
| **O121-w0c** | `/ops/` restart 400 → detail в UI · sudo ctl · legacy TG drain · `deploy-o121-w0c-vps.py` |
| **O123-w1** | copy 10/ч · feed-strip · **1.18.16** |
| **O107** | Trial 3 дня · Neon 020 · TG push · **1.18.17** |
| **O122** | Delist + hotfix: trial deploy · WP 120s · limit 15 |
| **O121-w1** | прокси · probe/switch · `deploy-o121-w1-vps.py` |
| **O121-w2/b** | сброс банов · timeout **90s** · `deploy-o121-w2-vps.py` + `w2b` · VPS ✅ |
| **O121-w3-acc2** | acc2 join-bootstrap legacy filter · tests **6/6** · `deploy-o121-w3-acc2-vps.py` |
| **O116** | Z234+FEED+MKT+CABINET+b2+W4 · prod **1.18.11→1.18.15** |
| **O72e-regen-tail** | allowlist «ИИ» · regen **28/28** |
| **O109** | Kwork delist fix · bot deep link `/lenta/?lead=` |
| **O114** | vacancy filter · backfill **12** |
| **O124** | лента: accordion · flip · match-bar · free CTA · **1.18.18** prod |
| **O124-w2** | anon/free/premium polish · **1.18.34** prod ✅ |
| **O127-WP** | Filter Bar v2 + Lead Card v3 · **1.18.34** prod ✅ |
| **O126** | category filter API + backfill · prod ✅ |
| **O127-D** | Filter Bar v2 + Lead Card v3 · `feed-cabinet-mvp` §9 ✅ |
| **L2-tools-tune** | consulting/rhino guards · catalog post-process · tests **11/11** · VPS ✅ |
| **O125 L2 on-demand** | `TOOLS_BACKLOG_DRAIN=0` · tools+draft только по клику · VPS ✅ |
| **O128-L2-VOICE** | план по ТЗ B · smell/cliche · uniquify (A) план→шаги · tests **36/36** · VPS ✅ |
| **O110-B** | proxy hygiene: browser wipe · cooldown 5–15s · UA · VPS ✅ |
| **O131-PERF** | L2 · pooler · feed boot · API scan | ✅ deploy **2026-06-07** |
| **O129-W1** | UX anon/free/premium **24/24** · smoke **5/5** · load p95 **1846ms** · AI **96%** · S4 FL **4/4** |

---

## До soft ads — что осталось ⏳

**Порядок:** **UI ✅ → L2 ✅ → E2E → stress → ads**

| Шаг | Задача |
|-----|--------|
| 1–5d | pay · ops · O126 · O127 UI | ✅ |
| **5e** | **O128 L2 voice B** | ✅ |
| **6** | **Stress Wave 1** | ✅ **2026-06-07** · [`PREPROD_STRESS_RUN.md`](../../ops/PREPROD_STRESS_RUN.md) |
| **6b** | **O129 stress v2** | orchestrator ✅ · journey partial |
| **6c** | **O131-PERF** | ✅ deploy · load@20 p95 **2549 ms** ⏸ |
| 7 | **Wave 2 rerun** · sign-off · ads | **⏸** до **O132 deploy + 24h** |
| **7a** | **O132-STABILITY** | **deploy ✅** · 24h watch |
| **7b** | **O134-INGEST-SLA** — скорость ленты FL/Kwork | **код ✅ Lead verify** · **deploy ⏳** |

**Owner фон:** **45.152.197.25** — починить/заменить у провайдера (сейчас acc1+бот на **38.154** spare).

---

## O131-PERF ✅ deploy (2026-06-07)

**Deploy:** `deploy-o131-vps.py` — API (`api_server`, `match_push`, `ai_analyze`) + theme **1.18.35**  
**Pooler:** `check_neon_pooler.py` → **OK** (local `.env`)  
**Smoke:** feed **1818 ms** · 40 items · today_count **245**  
**Load@20×60s:** p95 **2549 ms** · 0% err — gate **<2s** ещё ⏸ (Neon latency / 1 vCPU)

**Owner next:** draft_burst · J5 · full stress v2

---

| § | Gap |
|---|-----|
| **L2-draft** | legacy drafts обновятся on-demand; #9909 ИИ-edge — опц. |
| **O115** | tg ingest ok (~25/24h) · judge pilot только tg — не гоняли |
| **O105-w1-r3** | только если снова 300⭐ / нет «Изменить способ» | ⏸ по симптому |
| **Perf** | load@20 p95 **2549 ms** post-O131 | rerun stress · app pool backlog |
| **O129-W2** | orchestrator ✅ · journey **9/10** | **⏸** Wave 2 |
| **O132** | deploy ✅ · MemoryMax · browser cleanup | 24h watch 0 oom-kill |
| **O134-INGEST-SLA** | deploy ✅ **2026-06-08** · fresh-only · /ops/ SLA | мониторинг ≤5m 24h |

---

## Архив

O116 детали · O72e волны · O108 · PRE-RELEASE-AUDIT — [`STATUS_ARCHIVE.md`](../archive/STATUS_ARCHIVE.md) § 2026-06-05

_O129-W2 verify fix **2026-06-07** · pytest **7/7** · owner: full без `--skip-*`_
