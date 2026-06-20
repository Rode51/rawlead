# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.12** · [`ROADMAP.md`](../architect/ROADMAP.md)

**Очередь:** [`TASKS.md`](TASKS.md) · **Coder:** [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md)

**Next:** **M1 wave 1** · owner smoke · UX-audit rerun (Next) · **portfolio P2** deploy после commit

---

## Portfolio (rode51.ru)

| | |
|---|---|
| **Prod** | https://rode51.ru — **P1** (Hero→Process) ✅ |
| **Локально** | P2 WIP: WhyMe, FAQ, `/en`, polish — **не задеплоено** |
| **Канон** | [`LEAD_PORTFOLIO_PROMPT.md`](../portfolio/LEAD_PORTFOLIO_PROMPT.md) |

## O200 L2 judge ✅ (2026-06-18)

| | |
|---|---|
| **Прогон** | `data/preprod_o200_judge.json` + `_human.md` · 79 лидов · judge Claude Sonnet 4 |
| **Owner bar** | send ≥70% × 4 категории — **PASS** (80–90% по cat) |
| **Auto vault** | draft 92.4% (порог 95%) · tools auto 60.8% — **не блокер** · backlog tools extraction |

---

## O280-E2E-NEXT ✅ (2026-06-20)

| | |
|---|---|
| **Harness** | `scripts/preprod_playwright/next_e2e.py` n1–n25 · `tests/test_o280_next_e2e.py` |
| **Prod gate** | `data/preprod_next_e2e.json` + `preprod_next_e2e_human.md` |
| **Gate run** | **24/24** (2026-06-20 04:14 UTC) |
| **Draft fix** | API `POST /v1/me/draft/quota/reset` (preprod user) · harness reset before n5/n16/n17 · deploy `deploy-o280-draft-quota-reset-vps.py` |
| **Как проверить** | `.venv\Scripts\python.exe scripts\preprod_playwright\next_e2e.py --base-url https://rawlead.ru --gate-all` · `pytest tests/test_o280_next_e2e.py -q` |

---

## Billing + DB (Lead verify 2026-06-19)

| | |
|---|---|
| **Prod DB** | `.env.site` → `127.0.0.1:5432/rawlead` · Neon только `NEON_DATABASE_URL` |
| **ЮKassa keys** | в `.env.site` ✅ |
| **Smoke price** | `PAY_PREMIUM_RUB=790` ✅ (owner smoke 5 ₽ завершён 2026-06-19) |
| **Next** | O285 no trial checkout · O284 billing CTA ✅ |


---

## Draft — proxy (2026-06-19)

Owner поднял **38.154.16.60:8000** · probe: OR через proxy **200** ✅ · **→ retry** черновик на ленте/TG

---

## Index

| Блок | Где |
|------|-----|
| O280 R9–R9b | archive § 2026-06-19 |
| R10 admin | `CODER_PROMPT` § O280-R10 |
