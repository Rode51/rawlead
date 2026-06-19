# TASKS (активное)

**Снимок:** [`STATUS.md`](STATUS.md) · **Prod:** [`PROD_FACTS.md`](PROD_FACTS.md) · **Coder:** [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md)

---

## → Now (2026-06-19)

**O283-MIMO** deploy (FL loop + MOCK + AI ctx) · **O280-R10** admin link · owner **draft smoke** · **O39-docs** (Lead)

---

## Очередь

| # | Что | Кто | Статус |
|---|-----|-----|--------|
| **1** | **O283-MIMO** MiMo fixes (FL/MOCK/AI/favicon) | @coder | 🟡 code ✅ · deploy pending |
| **2** | **O280-R11** draft proxy | @coder | ✅ code · smoke draft |
| **3** | **O280-R10** `/ops/` link Next | @coder | ⏳ |
| **4** | **O280-R11** CABINET draft poll | @coder | ⏳ backlog O283 |
| **5** | **O39-docs** TZ_API + NEON_SCHEMA | Lead | ⏳ |
| **6** | **O280-E2E-NEXT** prod matrix | @coder | ⏳ after smoke |
| **7** | **M1** TG ads | @lead-marketing | ⏳ gate |
| — | O280 cutover · P289 rode51 · O272 · O269 | — | ✅ |

---

## Закрыто / архив

O200 · O217–O225 · O250/O253 · O261–O262 · O281 · O282 → [`CODER_PROMPT_ARCHIVE`](../architect/CODER_PROMPT_ARCHIVE.md) · [`TASKS_HISTORY`](archive/TASKS_HISTORY.md)

**Гейт GTM:** O218 ✅ · O200 ✅ · O280 cutover ✅ · draft smoke · E2E · M1

---

## Probe

```powershell
python scripts/probe_prod_facts_vps.py --write
python scripts/probe_parsers_health_vps.py  # on VPS log path
```
