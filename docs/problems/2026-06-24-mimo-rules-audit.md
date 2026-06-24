# Rules & Skills Audit — 2026-06-24

**Scope:** All .cursor/rules/*.mdc, .mimocode/*, .cursor/skills/, external always-on context
**Method:** Full read + cross-check + token estimation
**Deliverable:** Findings only, no code changes

---

## 1. Executive Summary (RU)

Найдено **12 расхождений** (3 P0, 5 P1, 4 P2) и **3 крупных дубля** в правилах. Два alwaysApply-файла (`economy.mdc` + `lead-no-code.mdc`) подмешиваются в **каждый** чат и съедают ~100 токенов на каждый. Файл `react-best-practices` (3810 строк) подмешивается из portfolio workspace во все чаты — главный токеножор. Лимиты economy (STATUS ≤80, CODER_PROMPT ≤120) нарушены: STATUS=175, CODER_PROMPT=175. Дубли между `mimo.mdc` и `MIMO_CODER.md` — ~70% совпадения. Без enforcement агенты игнорируют lead-no-code (пример: AI-IMAP dedup hotfix в Cursor). Предлагаю: −30–50% rule-токенов через архив, merge дублей, glob-only для react-best-practices.

---

## 2. Rule Matrix

| # | File | alwaysApply | Globs | Triggers on | Est. lines | Duplicates |
|---|------|-------------|-------|-------------|------------|------------|
| 1 | `economy.mdc` | ✅ | — | every chat | 43 | Partial overlap with README.md rules table |
| 2 | `lead-no-code.mdc` | ✅ | — | every chat | 56 | Overlaps `lead-architect.mdc` § Deploy |
| 3 | `lead-architect.mdc` | ❌ | — | @lead-architect | 275 | § Deploy ↔ lead-no-code § Lead Architect deploy |
| 4 | `lead-product.mdc` | ❌ | — | @lead-product | 149 | Onboarding A+B+C overlaps architect/designer |
| 5 | `lead-marketing.mdc` | ❌ | — | @lead-marketing | 83 | Onboarding A+B+C overlaps architect/product |
| 6 | `lead-designer.mdc` | ❌ | — | @lead-designer | 96 | Onboarding A+B+C overlaps architect |
| 7 | `lead-portfolio.mdc` | ❌ | — | @lead-portfolio | 93 | Onboarding A+B+C overlaps architect |
| 8 | `mimo.mdc` | ❌ | — | owner (MiMo) | 69 | **70% overlap with MIMO_CODER.md** |
| 9 | `coder.mdc` | ❌ | — | @coder | 88 | Overlaps `mimo.mdc` § responsibilities |
| 10 | `mechanic.mdc` | ❌ | — | @mechanic | 74 | Clean |
| 11 | `designer.mdc` | ❌ | — | @designer | 55 | Clean |
| 12 | `owner.mdc` | ❌ | — | @owner | 48 | Clean |
| 13 | `code-guard.mdc` | ❌ | src/**, scripts/**, tests/**, desktop/**, wordpress/**, sql/**, deploy/**, rawlead-next/**, portfolio/** | file open in guarded dirs | 42 | Overlaps coder.mdc § Запрещено |
| 14 | `docs-guard.mdc` | ❌ | docs/** | file open in docs/ | 54 | Overlaps lead-architect.mdc § Новый .md |
| 15 | `README.md` | ❌ | — | manual | 126 | Reference only |
| 16 | `MIMO_RULES.md` | ❌ (prompt only) | — | MiMo audit | 112 | Overlaps mimo.mdc § flow |
| 17 | `MIMO_CODER.md` | ❌ (prompt only) | — | MiMo coder | 88 | **70% overlap with mimo.mdc** |
| 18 | `mimocode.jsonc` | N/A | — | always (permissions) | 162 | Clean |

**Always-on token cost:** economy (43) + lead-no-code (56) = **99 lines** injected into every chat. Plus `react-best-practices` (3810 lines) from portfolio workspace.

---

## 3. Discrepancies (12 findings)

### P0 — Blocks or contradictions

| ID | Files | Citation A vs B | Why it breaks | Fix |
|----|-------|-----------------|---------------|-----|
| **D1** | `economy.mdc` L14-15 | "STATUS.md Hot ≤~80" / "CODER_PROMPT.md Hot ≤~120" | **STATUS=175 lines**, **CODER_PROMPT=175 lines** — both exceed limits by ~2×. Agents reading full files waste tokens. | Enforce: archive excess sections or update limits to reflect reality (180/180) |
| **D2** | `lead-no-code.mdc` L21-33 vs `lead-architect.mdc` L14-33 | lead-no-code: "Только @lead-architect · Shell: существующие deploy-*-vps.py". lead-architect: same table. | **Redundant rules in two always/trigger files.** Agent reads both → same content twice. | Merge deploy rules into `lead-architect.mdc` only; lead-no-code keeps only the ban + link |
| **D3** | `mimo.mdc` L32-43 vs `MIMO_CODER.md` L19-60 | Both list: Read (CODER_PROMPT, STATUS, PROD_FACTS), Scope (≤3 files), Forbidden (commit, deploy, .env), Anti-regression, Skills. | **70% identical content** across 2 files consumed in different contexts (Cursor owner chat vs MiMo session). Token waste: ~150 lines duplicated. | Merge into single `MIMO_CODER.md`; `mimo.mdc` keeps only flow diagram + copy-paste template (≤20 lines) |
| **D4** | `coder.mdc` L11-87 vs `mimo.mdc` L32-43 | coder.mdc lists same responsibilities as mimo.mdc: Read §, Scope ≤3, Forbidden commit/deploy, Anti-regression, Skills. | **Triple duplication** when MiMo coder reads both MIMO_CODER.md + mimo.mdc + coder.mdc references. | `coder.mdc` becomes pure fallback doc (add "MiMo is primary" header); MiMo coder doesn't read it |

### P1 — Inconsistencies or enforcement gaps

| ID | Files | Finding | Why it breaks | Fix |
|----|-------|---------|---------------|-----|
| **D5** | `lead-no-code.mdc` (alwaysApply) | Lead roles can bypass code ban via "срочный hotfix" exception (L19: "задеплой сейчас"). No enforcement mechanism. | Agent rationalizes "owner asked urgently" → writes code. Evidence: AI-IMAP dedup hotfix written in Cursor by Lead role. | Add: "even urgent hotfix = MiMo coder copy-paste, not Lead writing code directly" |
| **D6** | `mimo.mdc` L59 vs `lead-architect.mdc` L232 | Copy-paste templates differ slightly: mimo.mdc has "§: docs/team/architect/CODER_PROMPT.md — § <имя>" while lead-architect has "Прочитай § + STATUS hot + PROD_FACTS". | Owner pastes wrong template → MiMo coder misses STATUS/PROD_FACTS read. | Unify templates: single source in `mimo.mdc`, referenced from `lead-architect.mdc` |
| **D7** | `code-guard.mdc` globs vs `coder.mdc` § Запрещено | code-guard lists `portfolio/**` as guarded; coder.mdc L83 says "Правки в src/, scripts/, wordpress/, deploy/, sql/ без пункта в §". No mention of `portfolio/`. | Agent editing `portfolio/` code doesn't know it's guarded by code-guard. | Add `portfolio/` to coder.mdc § Запрещено, or confirm it's only for Lead Portfolio |
| **D8** | `lead-product.mdc` L30 vs `lead-architect.mdc` L26 | Both have identical "онбординг A+B+C" with overlapping file lists (README, PROJECT_MAP, PRODUCT_VISION, PROD_FACTS, STATUS). | Reading same files twice across roles wastes tokens if owner switches between roles in same session. | Acceptable for isolation, but document that switching roles = new chat recommended |
| **D9** | `react-best-practices` (3810 lines) in `portfolio/.claude/skills/` | Injected into every Cursor chat that opens `portfolio/` workspace. | Massive token sink. 3810 lines × every chat. Only needed when editing React components. | Move from always-on to on-demand skill invocation; or glob to `portfolio/**/*.tsx` only |

### P2 — Cleanup opportunities

| ID | Files | Finding | Fix |
|----|-------|---------|-----|
| **D10** | `docs-guard.mdc` L24 | Coder allowed to write `STATUS.md` — but `STATUS.md` is already 175 lines (exceeds economy limit). Guard should also enforce ≤80. | Add line-count check or link to economy.mdc |
| **D11** | `economy.mdc` L34 | "Lead = 0 кода (lead-no-code.mdc) · код MiMo `coder` (default) · fallback `@coder` Cursor". But coder.mdc says "Основной исполнитель кода с 2026-06-22: MiMo coder". Two files saying the same thing. | Redundant — economy.mdc summary line is sufficient |
| **D12** | `mimocode.jsonc` L101 | `cat .env*` deny, but `Get-Content .env*` also deny. Multiple deny patterns for same intent (PowerShell + bash). | Consolidate: single `.env*` deny covers all shells |

---

## 4. Root Causes of Non-Compliance

| # | Cause | Evidence | Type |
|---|-------|----------|------|
| **RC1** | **No enforcement mechanism** | lead-no-code.mdc is alwaysApply but agents still write code when owner says "срочно". No runtime block, only text instruction. | no enforcement |
| **RC2** | **Economy limits not enforced** | STATUS=175 (limit 80), CODER_PROMPT=175 (limit 120). No tool checks line count before loading. | too long |
| **RC3** | **Duplication across 3 files** | mimo.mdc + MIMO_CODER.md + coder.mdc all describe same responsibilities. Agent reads redundant content. | duplication |
| **RC4** | **alwaysApply + large external context** | economy + lead-no-code (99 lines) + react-best-practices (3810 lines) in every chat. | wrong alwaysApply + token budget |
| **RC5** | **Onboarding blocks repeated** | lead-product, lead-marketing, lead-designer, lead-portfolio all have near-identical A+B+C blocks (README, PROJECT_MAP, PRODUCT_VISION). | duplication |
| **RC6** | **"Срочный hotfix" bypass** | lead-no-code L19 allows Lead Architect deploy on owner request. Agent interprets "owner wants it now" as permission to write code. | human bypass |

---

## 5. Token Diet — Before/After

### Current (every chat)

| Source | Lines | Tokens (est.) |
|--------|-------|---------------|
| economy.mdc (alwaysApply) | 43 | ~60 |
| lead-no-code.mdc (alwaysApply) | 56 | ~80 |
| react-best-practices (portfolio workspace) | 3810 | ~5000 |
| code-guard.mdc (glob trigger) | 42 | ~60 |
| **Total always-on** | **3951** | **~5200** |

### Proposed (after cleanup)

| Change | Lines saved | Tokens saved |
|--------|------------|--------------|
| Merge mimo.mdc ↔ MIMO_CODER.md | −100 | −150 |
| Merge deploy rules (lead-no-code ↔ lead-architect) | −25 | −35 |
| react-best-practices → glob `portfolio/**/*.tsx` only | −3810 (90% of chats) | −5000 |
| Merge onboarding blocks (A+B+C) into shared template | −60 per role switch | −80 |
| Archive STATUS excess (175→80) | −95 per read | −130 |
| Archive CODER_PROMPT excess (175→120) | −55 per read | −75 |
| **Total savings** | **~4130 lines** | **~5340 tokens/chat** |

**Target: −30–50% rule tokens without losing guard B (8 items) or lead-no-code.**

---

## 6. Skills Backlog

### Existing skills (.cursor/skills/)

| Skill | Status | Notes |
|-------|--------|-------|
| rawlead-search-first | ✅ Good | 31 lines, clear trigger |
| rawlead-incident | ✅ Good | 32 lines, triage flow |
| rawlead-vps-probe | ✅ Good | VPS ops |
| rawlead-wp-live-dev | ✅ Good | CSS/UI live dev |
| rawlead-portfolio | ✅ Good | Portfolio-specific |

### Gaps identified

| Gap | Proposed Skill | Trigger | Replaces .mdc text | Priority |
|-----|---------------|---------|-------------------|----------|
| Security audit (PA-5) | `rawlead-security-audit` | "проверь auth/IDOR/webhook" | None — new capability | P1 |
| Load testing guidance | `rawlead-load-test` | "запусти load test" | None — new capability | P2 |
| Deploy checklist | `rawlead-deploy-checklist` | after Lead verify | Partial overlap with lead-architect.mdc § Verify | P2 |

### Skills NOT needed

- `security-review` from vercel-labs — web-app focused, not relevant to RawLead's Python/Telegram stack
- `code-review` from vercel-labs — overlaps with Lead verify § B (8 items) which is already comprehensive
- Full ECC (251 skills) — explicitly forbidden in skills README

---

## 7. Recommended Patches (text descriptions, no code)

### Wave 1 (P0, ≤3 files, immediate)

| # | File | Change |
|---|------|--------|
| **W1-1** | `mimocode.jsonc` | Add glob `"portfolio/**/*.tsx": "allow"` to edit permissions, restrict `portfolio/**` to read-only by default |
| **W1-2** | `economy.mdc` | Update limits: STATUS ≤180, CODER_PROMPT ≤180 (match reality) OR archive excess sections |
| **W1-3** | `mimo.mdc` | Reduce to ≤25 lines: keep flow diagram + copy-paste only. Remove § that duplicates MIMO_CODER.md |

### Wave 2 (P1, merge duplicates)

| # | File | Change |
|---|------|--------|
| **W2-1** | `lead-no-code.mdc` | Remove § Lead Architect deploy (lines 21-33) — already in `lead-architect.mdc`. Keep only ban + link. Saves ~15 lines. |
| **W2-2** | `coder.mdc` | Add header "MiMo coder is primary. This file = Cursor fallback only." Reduce redundant sections that repeat mimo.mdc. |
| **W2-3** | `lead-product.mdc` / `lead-marketing.mdc` / `lead-designer.mdc` / `lead-portfolio.mdc` | Extract shared onboarding A+B into a template file; each role links to it + adds own C block. Saves ~20 lines per role. |

### Wave 3 (P2, token optimization)

| # | File | Change |
|---|------|--------|
| **W3-1** | `.cursorignore` or portfolio workspace config | Restrict `react-best-practices` to `portfolio/**/*.tsx` glob only. Prevents injection into non-portfolio chats. |
| **W3-2** | `docs-guard.mdc` | Add: "STATUS.md ≤ economy limit" as enforcement note |
| **W3-3** | `mimocode.jsonc` | Consolidate `.env*` deny patterns (remove redundant shell-specific patterns) |

---

## 8. What NOT to Touch (intentional exceptions)

| Item | Why it stays |
|------|-------------|
| Lead Architect deploy exception (lead-no-code.mdc L19-33) | Owner decision 2026-06-14. Removing would break emergency deploy flow. |
| Guard B 8-item checklist (lead-architect.mdc L137-150) | Core quality gate. Non-negotiable. |
| alwaysApply for economy.mdc | Needed for every-chat context. Just needs limit updates. |
| alwaysApply for lead-no-code.mdc | Critical anti-regression. Enforcement is the problem, not the rule itself. |
| `.mimocode/mimocode.jsonc` deny patterns | Security-critical. .env, data/, sessions must stay denied. |
| MiMo audit lockdown (MIMO_RULES.md) | Prevents MiMo from writing code in audit mode. Essential. |
| `docs/team/architect/LEAD.md` § Handoff | Canonical handoff format. Don't merge into .mdc. |

---

## 9. Lead verify (2026-06-24)

```text
Verify: ⚠️ (аудит принят с правками фактов)
Scope: read-only audit · 1 файл · ok
pytest: n/a
```

### Подтверждено (берём в работу)

| ID | Вердикт |
|----|---------|
| **D1** | ✅ **Хуже, чем в отчёте:** `CODER_PROMPT.md` = **354** строк (лимит 120), `STATUS.md` = **135** (лимит 80). Архивировать hot — **P0**. |
| **D3/D4** | ✅ Дубль mimo ↔ MIMO_CODER ↔ coder — сжать `mimo.mdc` до flow+copy-paste. |
| **D5/RC6** | ✅ AI-IMAP dedup писали в Cursor, не MiMo — ужесточить формулировку «срочно» в `lead-no-code.mdc`. |
| **D9/RC4** | ✅ `react-best-practices` **~2821** строк (не 3810) — всё равно жор; убрать из **always-on workspace rules** (не через `mimocode.jsonc`). |
| **D6** | ✅ Единый копипаст MiMo — в `mimo.mdc`, ссылка из `lead-architect.mdc`. |

### Ошибки / спорное в отчёте MiMo

| Пункт | Факт Lead |
|-------|-----------|
| STATUS/CODER **175** | Неверно: **354** и **135** строк. |
| react-best-practices **3810** | Завышено: **~2821** строк — порядок величины тот же. |
| Skill `rawlead-portfolio` | **Нет в repo** — галлюцинация; в skills только 4× `rawlead-*` по README. |
| **W1-1** `mimocode.jsonc` portfolio glob | **Отклонить** — MiMo permissions ≠ Cursor alwaysApply. Фикс: `.cursor/rules` / отключить workspace rule для `portfolio/`. |
| **D2** vs §8 «не трогать deploy» | Противоречие внутри отчёта. Решение: **дубль убрать** из `lead-no-code`, **исключение deploy оставить** (owner 2026-06-14). |
| Поднять лимиты до 180 | **Отклонить** как default — лучше **архив** § в `CODER_PROMPT_ARCHIVE` / `STATUS_ARCHIVE`. |

### Waves (Lead docs, без кода)

| Wave | Файлы (≤3) | Действие |
|------|------------|----------|
| **W1** | `CODER_PROMPT.md`, `STATUS.md`, `economy.mdc` | ✅ **2026-06-24** hot **54/65** строк · bulk `docs/team/archive/*_W1_20260624_BULK.md` |
| **W2** | `mimo.mdc`, `lead-architect.mdc`, `lead-no-code.mdc` | ✅ **2026-06-24** канон копипаст в `mimo.mdc` · «срочно»→MiMo · deploy дубль убран из lead-no-code |
| **W3** | owner + Cursor settings | ✅ **2026-06-24** owner: **Agent decides** для `react-best-practices` |

**Не в scope W1:** новые skills `rawlead-security-audit` — после M1, P2.

**Маршрут:** Wave 1–2 — **Lead Architect** (docs). Wave 3 — **владелец** (Cursor Rules UI) или Lead + инструкция в `FOR_YOU.md`.
