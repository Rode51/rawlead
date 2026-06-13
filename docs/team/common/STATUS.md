# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.12** · [`ROADMAP.md`](../architect/ROADMAP.md)

**Очередь:** [`TASKS.md`](TASKS.md)

> Hot ≤80 строк · детали → [`archive/STATUS_ARCHIVE.md`](../archive/STATUS_ARCHIVE.md)

---

## Сейчас prod (2026-06-13)

| Слой | Факт |
|------|------|
| **WP theme** | **1.18.75** |
| **VPS** | **4 GB / 2 vCPU** · radar **active** · `L1_MAX_WORKERS=2` |
| **Pay** | **✅** trial 1 ₽ · **790** restored |
| **YouDo** | **✅ O190+O191+O194** · listing `parsed=50` · ingest+L1 restored · detail subprocess |
| **FL listing** | **✅ O193** subprocess · `parsed=30` · `health:fl ok` |
| **TG join** | O188 **28/127** |
| **ads** | **⏸** |

---

## Gaps / ⏳

| Зона | Статус |
|------|--------|
| **O195 TINDER-ONBOARD** | /quiz/ + scoring → @coder w1 |
| **O196 ASYNC-DRAFT** | instant отклик → @coder |
| **O188 TG wave** | join ⏳ radar auto · 5 fail usernames |
| **O186 security** | backlog |
| **O171 /ops/** | ⏸ |

---

## ✅ Недавно закрыто

O194-youdo-ingest · O193-fl-subprocess · O191-youdo-proxy · O190-t0j · O185 · O174 · O182* · O178 · O176 · O175

---

_O194 **Lead verify 2026-06-13 ~00:15 MSK**: approach **A** detail subprocess · `00:07` fetch → **29+** `pipeline:L1 youdo` · **0** asyncio · цикл YouDo-fetch **~6–10 мин** (50× detail+L1) — норма_

_O193 **Lead deploy+verify 2026-06-12 ~23:42**: `deploy-o193-fl-subprocess-vps.py` · `listing:fl parsed=30` · cycle **32–47s** на FL-only_

_O191 **2026-06-12**: DC+RU 26 slots · `slot=1/26`_
