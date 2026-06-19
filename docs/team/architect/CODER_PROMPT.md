# Coder — hot queue (active)

**→ Now:** **§ O283-MIMO** (остаток) · **O280-R10** admin link · owner smoke draft

---

## § O283-MIMO — MiMo audit (2026-06-19)

**Source:** [`2026-06-19-mimo-audit.md`](../../problems/2026-06-19-mimo-audit.md) · parsers: [`2026-06-19-mimo-parsers-fl.md`](../../problems/2026-06-19-mimo-parsers-fl.md)

| ID | Pri | Status | Fix |
|----|-----|--------|-----|
| **FL-LOOP** | P0 | ✅ code | `exchange_browser_fetch.py:717` · `exchange_proxy.py:1287` — `set_restart_source=not fl_listing_subprocess_enabled()` |
| **MOCK** | P0 | ✅ code | `lenta/page.tsx` — MOCK только localhost |
| **AI-CTX** | P0 | ✅ code | `_reply_validate_lead_ctx` → `ContextVar` |
| **R11** | P0 | ✅ code | `_log_ai_failure` · OpenRouter proxy → direct fallback |
| **CABINET** | P0 | ⏳ | pending draft API poll in cabinet |
| **NGINX** | P1 | ⏳ | security headers `deploy/nginx/rawlead.ru.conf` |
| **Favicon** | P1 | ✅ | `rawlead-next/app/icon.svg` — R on `#E8A020` |

**P1 backlog:** Kwork parsed-zero · proxy health-check · TG notify retry · Metrika Next

### DoD (остаток)

- Cabinet poll pending drafts · nginx headers · `npm run build` · deploy web + radar (FL fix)

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

## § O280-R10 — Next: ссылка `/ops/` (owner admin)

| Fix | File |
|-----|------|
| «Админка» при `can_ops_admin` | `rawlead-next/components/layout/Header.tsx` |

**DoD:** owner → `https://rawlead.ru/ops/` · build + deploy web

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
