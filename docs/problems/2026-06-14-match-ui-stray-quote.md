# Match bar UI — stray `"` under progress bar (2026-06-14)

**Status:** ✅ closed 2026-06-14 · theme **1.19.02** · `lead_coverage_match` on API  
**Prod theme:** 1.19.01 · lenta + cabinet load after JS syntax hotfix ✅

## Symptom (owner screenshots)

- Under match progress bar: visible **`"`** (sometimes `.`) on its own line
- Feed and cabinet cards **look different** (padding/bar alignment); cabinet-only «ОТКЛИК ✓» badge is OK
- **Owner 2026-06-14:** remove **all** match band labels — bar only (overrides PM § A copy)

## Root cause (Lead verify read-only)

`renderMatchBreakdown` HTML string ends with orphan quote after `</div>`:

```javascript
// rawlead-feed.js ~2011 · rawlead-cabinet.js ~4175
'...>?</button></div>"'   // ← trailing " renders as text node
```

O220-JS-SYNTAX-HOTFIX fixed missing `'` on the string; **did not** remove the stray `"`.

## Fix (Coder)

1. Remove `renderMatchBreakdown` from card (no «?», no stray `"`)
2. Remove `.rl-match__label` — **bar only** on logged-in cards (owner decision)
3. Unify cabinet match markup with feed (`rl-match rl-match-bar`, `rl-row--match-tier`)
4. Bump theme · deploy · smoke: no text above bar · feed ≡ cabinet

## Related

- PM match formula rework: `lead_coverage_match` (not shipped — `priority_keyword_match` on prod is **wrong** vs PM § D)
- Canon: `LEAD_PRODUCT_PROMPT.md` § O220-MATCH-PM · owner OK 2026-06-14
