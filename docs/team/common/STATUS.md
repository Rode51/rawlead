# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.12** · [`ROADMAP.md`](../architect/ROADMAP.md)

**Очередь:** [`TASKS.md`](TASKS.md)

> Hot ≤80 строк · детали → [`archive/STATUS_ARCHIVE.md`](../archive/STATUS_ARCHIVE.md)

---

## Сейчас prod (2026-06-12)

| Слой | Факт |
|------|------|
| **WP theme** | **1.18.75** O185 t5b-reset-btn |
| **VPS** | **4 GB / 2 vCPU** · swap 0 · radar **active** · `L1_MAX_WORKERS=2` |
| **Pay** | **✅ smoke 2026-06-12** trial 1 ₽ · ЮKassa · **790** restored · O174d ⏸ |
| **ИИ gate** | L2 send **71.8%** · L1 **83.1%** · L3 **92%** |
| **Feed env** | fl,kwork + **4× secondary** + **28× tg** (+ test_bots) |
| **YouDo ingest** | **✅ O190** subprocess · `fetch_end parsed=50` · `health:youdo ok` |
| **TG join** | O188 wave **28/127** · mechanism ✅ · ~10/h/account |
| **ads** | **⏸** owner — после stability + O186 |

**Judge freeze:** [`preprod_ai_prod_audit_judge_o72e_a_freeze.md`](../../data/preprod_ai_prod_audit_judge_o72e_a_freeze.md)

---

## Gaps / ⏳

| Зона | Статус |
|------|--------|
| **O191 YouDo proxy** | **→ @coder** · DC primary + RU residential fallback |
| **O193 FL subprocess** | owner **B** · после O191 · § O193-w |
| **O188 TG wave** | join ⏳ · 5 fail usernames · Neon 24h smoke |
| **O186 security** | pentest backlog · после O185 |
| **O171 /ops/** | rebuild ⏸ после O168 |
| **O133 TZ** | downloader ✅ deploy · smoke Kwork PDF owner |
| **HC fail URL** | `HEALTHCHECKS_SITE_FAIL_URL` — проверить на VPS |

---

## ✅ Недавно закрыто (индекс)

O190-t0j · O185 w1–w3/t5b/t6 · O174a/b/c · O182b · O182/O181/O180 delist · O178 feed sort · O176 trace · O175 inbox · O168 stress · O133 TZ batch · O160 ingest locks

Хронология O175–O190 → [`STATUS_ARCHIVE.md`](../archive/STATUS_ARCHIVE.md) § **2026-06-12**

---

_O190 **2026-06-12**: subprocess `youdo_fetch_worker` · t0j cycle gate · Lead verify · ingest DoD ✅ → **O191**_
