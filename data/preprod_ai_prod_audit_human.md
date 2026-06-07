# O72 — AI prod audit (human)

- **Time:** 2026-06-07T13:32:30.013111+00:00
- **L2 sample (reply_draft):** 50 leads
- **Draft quality (L1+L2, без tools):** **96.0%** (✅ ≥95%) · 48/50 pass
- **Tools bucket (отдельно):** **96.0%** · 48/50 pass · KNOWN_TOOLS + canonical aliases
- **Combined auto-pass (draft+tools):** 92.0% (✅ ≥85%)
- **L1 empty bucket:** 0 leads · missing summary **0**
- **Merged rows:** 50
- **Profile:** site

> **O72b:** draft-only % — gate качества отклика (L1+L2); tools — отдельная строка (KNOWN_TOOLS whitelist + canonical aliases, без раздувания picker 51).

---

## Draft fail types (L1+L2)

- `L2:reply_draft`: **2**

## Tools fail types

- `tools:min_2_required`: **2**

## Top draft fail cases

- **#9909** [kwork/text] 'Привлечь клиентов в ИИ-Бота в телеграмм'
  - fails: L2:reply_draft: запрещённые слова (ИИ/Cursor/…)
- **#8694** [fl/design] 'Разработка логотипа для кофейни КОРЖ + готовый брендбук'
  - fails: L2:reply_draft: обязательное начало «Здравствуйте»

## Top tools fail cases

- **#8812** [kwork/marketing] 'Помощь в работе с блогерами'
  - fails: tools:min_2_required
- **#8782** [kwork/marketing] 'SEO оптимизация сайта'
  - fails: tools:min_2_required
