# Coder — hot queue (active)

**→ Now:** § **O191-YOUDO-PROXY-MIX** · § **O188** wave (no code unless stuck) · **O186** backlog

**O190:** ✅ Lead verify **2026-06-12** · ingest DoD closed · chronicle → [`CODER_PROMPT_ARCHIVE.md`](../archive/CODER_PROMPT_ARCHIVE.md) · **O193** FL subprocess after O191

**Archive:** [`CODER_PROMPT_ARCHIVE.md`](../archive/CODER_PROMPT_ARCHIVE.md)

---

## § O191-YOUDO-PROXY-MIX (owner **2026-06-12** — § O191-w)

**Context:** O190 ingest ✅ · `fetch_end parsed=50` · `health:youdo ok` · subprocess worker stable · prod `YOUDO_PROXY_URLS` = residential RU (node-proxy).

**Goal:** **DC proxy primary** · **residential RU fallback** on slot retry · **do not** slow listing (`fetch_every_n` unchanged) · shared node-proxy traffic — slot count ≠ GB savings.

**Steps:**
- `t1` — owner/ops: prepend **DC slot(s)** to `YOUDO_PROXY_URLS` in `/opt/rawlead/.env.site` (keep RU slots after) · document order in deploy script comment only (no secrets in git)
- `t2` — smoke subprocess worker with DC slot: `smoke_youdo_t6c_vps.py` or worker CLI · log `html_len` + `parsed>=50`
- `t3` — radar 1–2 cycles · gate: `fetch_end parsed>=50` · `health:youdo ok` · no new asyncio/cycle abort
- `t4` — rollback = restore RU-only order one env line

**Do not:** merge YouDo pool with FL/Kwork · cut slot count for “savings” · raise `YOUDO_FETCH_EVERY_N`

**DoD:** DC-first order on VPS · smoke + radar `parsed>=50` · failover to RU visible in trace when DC antibot/refused

**Files:** `scripts/patch-vps-youdo-proxy-env.py` or new `deploy-o191-youdo-proxy-vps.py` · `scripts/smoke_youdo_t6c_vps.py` · `src/exchange_proxy.py` (only if slot order logic needs code)

---

## § O188-TG-JOIN-WAVE4 (owner **2026-06-12** — wave ⏳)

**Facts (Lead verify):** v3 **`28 done` / `94 pending` / `5 fail`** · **`61`** `тг:join:` in log · round-robin acc1/2/3 ✅ · ~10/h/account · mechanism ✅

**Goal:** join **127** channels · rate **10/h/account** · per-acc logs in `radar_site.log` + `tg_join.log`

**Inputs:** [`TG_CHANNELS_OWNER_2026-06-12.txt`](../../ops/TG_CHANNELS_OWNER_2026-06-12.txt) · [`TG_JOIN_QUEUE_v3.csv`](../../ops/TG_JOIN_QUEUE_v3.csv)

**Env (VPS `.env.site`):** `TG_JOIN_QUEUE_CSV` · `TG_JOIN_MAX_PER_HOUR=10` · `TG_JOIN_IN_TG_MAIN=1` · `TELETHON_MONITOR_ACCOUNTS=acc1,acc2,acc3`

**Rules:** merge VPS CSV on deploy (preserve `done`+`chat_id`) · **never** blind overwrite · **no** parallel `tg_join_queue.py` CLI (database locked)

**DoD (wave):** v3 progress · `grep 'тг:join:acc' radar_site.log` · 3 acc ready · TG Neon 24h smoke

**Files:** `src/tg_join_runner.py` · `scripts/tg_join_queue.py` · deploy env only unless stuck

---

## § O190-YOUDO-CAMOUFOX ✅ closed (Lead **2026-06-12**)

| Milestone | Result |
|-----------|--------|
| t0i subprocess | `youdo_fetch_worker.py` · listing **50 cards** · no asyncio |
| t0j cycle gate | `_safe_close_browser_contexts` · `_commit_youdo_fetch_gate` · `YOUDO_DELIST_MAX_PER_CYCLE=10` |
| Ingest DoD | **22:46** `fetch_end parsed=50` · `health:youdo ok` · cycle **~50s** |
| Deploy | `deploy-o190-t0e-vps.py` · pytest delist **22/22** |

Full t0a–t0j chronicle · abandoned async paths → [`CODER_PROMPT_ARCHIVE.md`](../archive/CODER_PROMPT_ARCHIVE.md) · [`problems/2026-06-12-youdo-antibot-permanent.md`](../../problems/2026-06-12-youdo-antibot-permanent.md)

**Next owner backlog (not hot until Lead opens):** **O193** FL listing subprocess worker (§ O193-w)

---

## § O186-SECURITY-AUDIT (**→ backlog**, after O185 ✅)

Pentest JWT/IDOR/webhook/draft — deliver `docs/problems/…-security-audit.md`

---

## § O174d-PAY-POST-USERS (**⏸ backlog**)

Cancel UI + autopay — after first paying users.

---

## Closed ✅ (hot index)

O190 · O189 · O185-t5b · O185-w3/w2/w1 · O174c/b · O182b · O182/O181/O180 · O178 · O176 · O175 · O174a · O168 → `CODER_PROMPT_ARCHIVE.md`

## Background

O171 · O173 · L2 judge · [`PRODUCT_CANON.md`](../product/PRODUCT_CANON.md)
