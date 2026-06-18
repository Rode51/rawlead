# Repo hygiene inventory (O251)

**Date:** 2026-06-15 · **Owner:** cleanup pass · **Coder:** Phase A+B

## Summary (RU)

| Паттерн | До | После | Действие |
|---------|-----|-------|----------|
| `git status --porcelain` строк | **394** | **231** | −163 (gitignore hides rest) |
| `scripts/_tmp_*.py` | 123 | **1** | gitignore + delete 122 |
| `.playwright-mcp/` | 83 | **0** | gitignore + delete dir |
| `audit_*.png` / `o105_*.png` / `rawlead_*.png` | 38 | **0** | gitignore + delete |
| Root junk (`127.0.0.1`, `=`) | 2 | **0** | delete |
| `data/preprod_*` | 80 on disk | 80 | **keep** (whitelist `.gitignore`) |
| `scripts/_*.py` (non-`_tmp_`) | 48 | 48 | keep local · not in scope |
| `src/` / `wordpress/` / `tests/` logic | — | — | **no changes** (O251) |

**Deploy dependency (never delete):** `scripts/_tmp_o170_delist_tg_ads.py` — uploaded by `scripts/deploy-o170-vps.py`.

---

## Detail table (EN)

| Pattern | Count (before) | Tracked | Action | Reason |
|---------|----------------|---------|--------|--------|
| `scripts/_tmp_*.py` | 123 | 0 untracked | **gitignore** + delete all except `_tmp_o170_delist_tg_ads.py` | Local VPS/ops probes; not prod imports |
| `scripts/_tmp_o170_delist_tg_ads.py` | 1 | untracked | **gitignore** + **keep on disk** | `deploy-o170-vps.py` uploads + runs on VPS |
| `scripts/_*.py` (48 non-tmp) | 48 | mixed | **keep** | Lead/coder smoke & diag; future optional gitignore |
| `.playwright-mcp/` | 83 (49 `.yml`, 21 `.log`, 13 `.png`) | untracked | **gitignore** + **delete** | MCP browser session dumps |
| `audit_*.png` (repo root) | 15 | untracked | **gitignore** + **delete** | Playwright UI audit screenshots |
| `o105_*.png` (repo root) | 11 | untracked | **gitignore** + **delete** | O105 smoke screenshots |
| `rawlead_*.png` (repo root) | 12 | untracked | **gitignore** + **delete** | Local WP audit screenshots |
| `127.0.0.1`, `=` (repo root) | 2 | untracked | **delete** | Accidental shell redirect artifacts |
| `app-icon-for-pc--*.png` | 1 | untracked | **keep** | Design asset; not in O251 ignore list |
| `data/preprod_*.json` / `*.md` | ~80 on disk, 37 `??` in status | whitelist `!data/preprod_*` | **keep policy** | Preprod judge/burst reports; owner may commit selectively |
| `data/quiz_*.json` | 4 whitelisted | untracked `??` | **keep** | Product quiz pool; `!data/quiz_*` in `.gitignore` |
| `data/*` (other runtime) | — | ignored | **keep policy** | `data/*` + explicit exceptions unchanged |
| `.cursorignore` | 1 | untracked `??` | **keep** | Cursor indexing; mirrors part of gitignore |
| `.pytest_cache/` | 7 files | — | **keep** (already standard ignore elsewhere) | Local pytest cache |
| `deploy-*.py`, `tg_queue_import.py` | tracked | tracked | **never touch** | Prod deploy paths |
| `docs/ops/TG_JOIN_QUEUE_*.csv` | tracked | tracked | **never touch** | TG join queue |
| `src/`, `wordpress/`, `tests/` | modified in working tree | — | **out of scope** | O251 = hygiene only |

---

## `_tmp_*.py` references (grep)

| Referenced in | File | Keep on disk? |
|---------------|------|---------------|
| `scripts/deploy-o170-vps.py` | `_tmp_o170_delist_tg_ads.py` | **YES** |
| `scripts/_tmp_draft_lead15146.py` | `_tmp_query_lead15146.py` | no (parent deleted) |
| `docs/team/common/STATUS.md` | `_tmp_o247b_smoke.py` | doc only |
| `docs/problems/2026-06-12-tg-authkey-duplicated.md` | `_tmp_tg_acc3_swap_239823951_vps.py` | doc only |
| `docs/team/archive/CODER_PROMPT_ARCHIVE.md` | `_tmp_o185_t1b_smoke_price.py` | archive only |
| `tests/` | — | none |
| `src/` | — | none |

No `_tmp_*.py` is imported by `src/` or `tests/`.

---

## `.gitignore` changes (Phase B)

Added:

```
.playwright-mcp/
audit_*.png
o105_*.png
rawlead_*.png
scripts/_tmp_*.py
```

Note: `.cursorignore` already had the PNG + `.playwright-mcp/` patterns (Cursor index only).

---

## Deleted paths (Phase B)

- Directory: `.playwright-mcp/` (83 files)
- Root PNGs: `audit_*.png` (15), `o105_*.png` (11), `rawlead_*.png` (12)
- Root junk: `127.0.0.1`, `=`
- `scripts/_tmp_*.py`: **122** files (all except `_tmp_o170_delist_tg_ads.py`)

**Not deleted:** `scripts/_tmp_o170_delist_tg_ads.py`, `deploy-*.py`, `data/preprod_*`, `data/quiz_*.json`, hot docs, `src/`, `wordpress/`.

---

## Verification

```bash
pytest tests/test_match_push_o250.py tests/test_tg_queue_import.py -q
# 8 passed (2026-06-15)
git status --porcelain | wc -l   # 231 vs 394 before
```

**Disk removed:** 245 files (83 `.playwright-mcp/` + 38 PNG + 2 root junk + 122 `_tmp_*.py`).
