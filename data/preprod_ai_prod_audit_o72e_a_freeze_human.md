# O72 — AI prod audit (human)

- **Time:** 2026-06-04T14:04:30.962809+00:00
- **L2 sample (reply_draft):** 71 leads
- **Draft quality (L1+L2, без tools):** **100.0%** (✅ ≥95%) · 71/71 pass
- **Tools bucket (отдельно):** **97.2%** · 69/71 pass · KNOWN_TOOLS + canonical aliases
- **Combined auto-pass (draft+tools):** 97.2% (✅ ≥85%)
- **L1 empty bucket:** 0 leads · missing summary **0**
- **Merged rows:** 71
- **Profile:** site

> **O72b:** draft-only % — gate качества отклика (L1+L2); tools — отдельная строка (KNOWN_TOOLS whitelist + canonical aliases, без раздувания picker 51).

---

## Draft fail types (L1+L2)

- _(none)_

## Tools fail types

- `tools:min_2_required`: **2**

## Top draft fail cases


## Top tools fail cases

- **#8812** [kwork/marketing] 'Помощь в работе с блогерами'
  - fails: tools:min_2_required
- **#8782** [kwork/dev] 'SEO оптимизация сайта'
  - fails: tools:min_2_required

## LLM judge (O72c)

- L2 scored: 71/71 · combined **4.27**/5 · send_as_is **60.6%** · ❌
- Подробно: `data/preprod_ai_prod_audit_judge.md`
