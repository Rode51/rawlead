# Coder — hot queue (active)

**→ Now:** owner smoke draft (R11) · verify admin `/ops/` · P1 backlog

---

## § O283-MIMO — MiMo audit (2026-06-19) ✅ deployed

**Source:** [`2026-06-19-mimo-audit.md`](../../problems/2026-06-19-mimo-audit.md) · parsers: [`2026-06-19-mimo-parsers-fl.md`](../../problems/2026-06-19-mimo-parsers-fl.md)

| ID | Pri | Status | Fix |
|----|-----|--------|-----|
| **FL-LOOP** | P0 | ✅ prod | `exchange_browser_fetch.py` · `exchange_proxy.py` |
| **MOCK** | P0 | ✅ prod | `lenta/page.tsx` — localhost only |
| **AI-CTX** | P0 | ✅ prod | `ContextVar` in `ai_analyze.py` |
| **R11** | P0 | ✅ prod | proxy → direct fallback |
| **CABINET** | P0 | ✅ prod | pending draft poll |
| **NGINX** | P1 | ✅ prod | security headers |
| **Favicon** | P1 | ✅ prod | R on `#E8A020` |

**Deploy:** `deploy-o283-mimo-fixes-vps.py` · `deploy-web-rawlead-vps.py` (2026-06-19)

**P1 backlog:** Kwork parsed-zero · proxy health-check · TG notify retry · Metrika Next

---

## § O280-R11 — draft OpenRouter proxy (2026-06-19)

**Incident:** [`draft-openrouter-proxy-dead.md`](../../problems/2026-06-19-draft-openrouter-proxy-dead.md)

| # | Status |
|---|--------|
| A1 `_log_ai_failure` | ✅ |
| A2 proxy → direct fallback | ✅ |
| A3 unset dead proxy on VPS | ops owner/mechanic |

**DoD:** draft lead → 200 + ≥80 chars · smoke site + TG

---

## § O280-R10 — Next: ссылка `/ops/` (owner admin) ✅ prod

| Fix | File |
|-----|------|
| «Админка» при `can_ops_admin` | `rawlead-next/components/layout/Header.tsx` |

**DoD:** owner → `https://rawlead.ru/ops/` · verify logged in

---

## Index — shipped (detail → archive)

| § | Note |
|---|------|
| O280-R9/R9b | лента · avatar |
| O272 | Neon guard |
| O280 cutover | Next prod |
| O281/O282 | TG delete · weights |
| MIMO-AUDIT | ✅ triaged |

**Полные спеки закрытых §** → [`CODER_PROMPT_ARCHIVE.md`](../archive/CODER_PROMPT_ARCHIVE.md) · [`STATUS_ARCHIVE.md`](../archive/STATUS_ARCHIVE.md)
