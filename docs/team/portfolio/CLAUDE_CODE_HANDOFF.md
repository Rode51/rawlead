# Claude Code — handoff (Rode51 portfolio)

**Кто запускает:** владелец в терминале. **Кто пишет промпты:** `@lead-portfolio` (EN). **Lead Portfolio не правит** файлы в `portfolio/`.

**Legacy ❌:** P288 · terracotta · spiral · PNG в `docs/design/portfolio/refs/`.

---

## § bootstrap — установка skills (P0)

Скопировать в **новую сессию Claude Code** из корня репо `uisness`:

```text
Bootstrap Rode51 portfolio — skills only, no page UI yet.

Context:
- Personal site for brand Rode51 (Nikita), target labs.rawlead.ru, static Next.js later.
- RawLead is a case study only; facts in docs/team/common/PORTFOLIO.md — do not invent features.
- Owner decision 2026-06-18: completely fresh visual direction. Do NOT use docs/design/portfolio/refs/*.png or any P288/terracotta/spiral canon.

Task 1 — Install Claude Code skills (review SKILL.md + any scripts/ for safety before running):

A) frontend-design
   Source: https://github.com/anthropics/skills — copy skills/frontend-design to:
   - User: ~/.claude/skills/frontend-design/
   OR project (preferred for team): portfolio/.claude/skills/frontend-design/

B) ui-ux-pro-max
   Source: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
   Run from repo root after portfolio/ exists:
   uipro init --ai claude
   Do NOT run design-system search until owner approves refs in docs/design/portfolio/README.md.

C) web-design-guidelines (quality gate)
   Source: https://github.com/vercel-labs/agent-skills — skills/web-design-guidelines/

D) react-best-practices (Next.js static export)
   Same repo: skills/react-best-practices/

Optional later: Impeccable (https://impeccable.style/) — only if frontend-design outputs feel generic.

Task 2 — Create portfolio/ scaffold ONLY (no Hero/UI sections):
- Next.js 14 App Router, output: 'export', TypeScript, Tailwind
- portfolio/CLAUDE.md with:
  - Read LEAD_PORTFOLIO_PROMPT.md § → Now only
  - Desktop-first 1440–1920 (premium); mobile must not break — not the layout driver
  - Skills: frontend-design + ui-ux-pro-max + web-design-guidelines on polish passes
  - Never copy rawlead.ru NEO-brutalist UI
  - Do not read superseded PNG refs

Task 3 — Report:
- List installed skill paths
- Confirm no page components beyond placeholder
- Wait for owner + @lead-portfolio ref table before any design-system --persist or Hero work

Rules:
- Do not touch src/, wordpress/, scripts/ outside portfolio/
- Do not commit secrets
- Ask before installing any skill not listed above
```

---

## § design-system — после refs (P0.4)

```text
Read docs/design/portfolio/README.md — approved ref table only.

Run ui-ux-pro-max design system search for Rode51 portfolio:
- Keywords from LEAD_PORTFOLIO_PROMPT.md mood § (owner-approved)
- --design-system -p "Rode51" --persist
- Align with frontend-design skill (distinctive type, not Inter/Roboto default stack)

Output: short markdown summary of chosen direction (palette words, type pairing, motion level).
Do not build Hero until @lead-portfolio confirms summary in chat.
```

---

## § polish-v1 — full page audit (P2)

**Когда:** P1 секции собраны, owner «всё, polish».

```text
/clear

Read portfolio/CLAUDE.md § P2 polish goals.

Task: POLISH PASS ONLY — do not redesign structure or rewrite copy.

1. Audit all sections at desktop 1440: spacing rhythm, type scale, amber discipline.
2. Fix inconsistencies (padding px-6 vs px-10, section gaps).
3. prefers-reduced-motion: ScrambleTitle, Typewriter, Ticker, ping badge.
4. Delete dead files: Cases.tsx, CaseSection.tsx, ProductResult.tsx, CursorGlow.tsx, any *.tmp.*
5. Run web-design-guidelines on changed files.
6. npm run build — must pass.

Report: bullet list of changes. No new sections. Stop for owner screenshot.
```

---

## § hero-v1 — static only (P1)

```text
Section: Hero only. Static everywhere — no WebGL, no R3F, no Three.js in v1.

Read: portfolio/CLAUDE.md, docs/design/portfolio/README.md, docs/team/portfolio/LEAD_PORTFOLIO_PROMPT.md
Brand: Rode51 · CTA Telegram @rcnn43 · Owner is PC/full-stack dev — site must feel premium on desktop first.

Build:
- One strong typographic/editorial hero per approved mood — optimize for 1440px+ (wide type, grid, whitespace)
- Responsive down to 390px without broken layout; do not cripple desktop for mobile
- prefers-reduced-motion safe
- LCP-friendly (no heavy JS in v1)

After build:
- Run web-design-guidelines pass on changed files
- List files changed; owner will 1440px smoke test (+ quick 390px sanity)
```

---

## § polish-pass (repeat per section)

```text
Polish pass on [SECTION NAME] only — no new features.

Order: spacing/hierarchy → typography → motion (CSS only, subtle) → web-design-guidelines audit → perf (bundle/size notes).

Do not refactor unrelated sections.
```
