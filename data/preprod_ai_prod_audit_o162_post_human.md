# O72 — AI prod audit (human)

- **Time:** 2026-06-09T08:15:14.801860+00:00
- **L2 sample (reply_draft):** 75 leads
- **Draft quality (L1+L2, без tools):** **97.3%** (✅ ≥95%) · 73/75 pass
- **Tools bucket (отдельно):** **92.0%** · 69/75 pass · KNOWN_TOOLS + canonical aliases
- **Combined auto-pass (draft+tools):** 90.7% (✅ ≥85%)
- **L1 empty bucket:** 0 leads · missing summary **0**
- **Merged rows:** 75
- **Profile:** site

> **O72b:** draft-only % — gate качества отклика (L1+L2); tools — отдельная строка (KNOWN_TOOLS whitelist + canonical aliases, без раздувания picker 51).

---

## Draft fail types (L1+L2)

- `L2:reply_draft`: **2**

## Tools fail types

- `tools:min_2_required`: **6**

## Top draft fail cases

- **#19244** [fl/dev] 'Проект внедрения ИИ в работу медицинской организации.'
  - fails: L2:reply_draft: запрещённые слова (ИИ/Cursor/…)
- **#9909** [kwork/text] 'Привлечь клиентов в ИИ-Бота в телеграмм'
  - fails: L2:reply_draft: запрещённые слова (ИИ/Cursor/…)

## Top tools fail cases

- **#19616** [kwork/design] 'Оперативно поменять телефон и лого на сайте на opencart'
  - fails: tools:min_2_required
- **#19506** [kwork/dev] 'Установить Unisite Board 4.11'
  - fails: tools:min_2_required
- **#19244** [fl/dev] 'Проект внедрения ИИ в работу медицинской организации.'
  - fails: tools:min_2_required
- **#19235** [kwork/design] 'Презентация агро проекта'
  - fails: tools:min_2_required
- **#19231** [kwork/marketing] 'Необходимо вывести сайт в топ поиска Яндекс и гугл'
  - fails: tools:min_2_required
- **#19229** [fl/dev] 'Разработать чертежи мебели по дизайн проекту'
  - fails: tools:min_2_required

## LLM judge (O72c)

- L2 scored: 39/39 · combined **4.33**/5 · send_as_is **64.1%** · ❌
- Подробно: `data/preprod_ai_prod_audit_judge.md`

## Owner lead_ids (root cause)

- **#10001**: auto_pass
- **#9901**: auto_pass
- **#9881**: auto_pass
- **#10442**: auto_pass
- **#10025**: auto_pass
- **#10019**: auto_pass
- **#9924**: auto_pass
- **#9911**: auto_pass
- **#9831**: auto_pass
- **#10749**: auto_pass
- **#10362**: auto_pass
- **#10291**: auto_pass
- **#10009**: auto_pass
- **#9885**: auto_pass
- **#12602**: auto_pass
- **#12148**: auto_pass
- **#11837**: auto_pass
- **#11353**: auto_pass
- **#11332**: auto_pass
- **#10143**: auto_pass
- **#10057**: auto_pass
- **#9928**: auto_pass
- **#9889**: auto_pass
- **#10479**: auto_pass
- **#9909**: L2:reply_draft: запрещённые слова (ИИ/Cursor/…)
- **#9905**: auto_pass
- **#9861**: auto_pass
- **#9847**: auto_pass
- **#9837**: auto_pass
- **#9875**: auto_pass
- **#9835**: auto_pass
- **#9913**: auto_pass
- **#9907**: auto_pass
- **#9891**: auto_pass
- **#9851**: auto_pass
- **#9849**: auto_pass
- **#9845**: auto_pass
- **#9843**: auto_pass
- **#9833**: auto_pass
