# O72 — AI prod audit (human)

- **Time:** 2026-06-03T13:32:05.330267+00:00
- **L2 sample (reply_draft):** 72 leads
- **Draft quality (L1+L2, без tools):** **95.8%** (✅ ≥95%) · 69/72 pass
- **Tools bucket (отдельно):** **97.2%** · 70/72 pass · KNOWN_TOOLS + canonical aliases
- **Combined auto-pass (draft+tools):** 93.1% (✅ ≥85%)
- **L1 empty bucket:** 0 leads · missing summary **0**
- **Merged rows:** 72
- **Profile:** site

> **O72b:** draft-only % — gate качества отклика (L1+L2); tools — отдельная строка (KNOWN_TOOLS whitelist + canonical aliases, без раздувания picker 51).

---

## Draft fail types (L1+L2)

- `L2:reply_draft`: **3**

## Tools fail types

- `tools:min_2_required`: **2**

## Top draft fail cases

- **#8734** [kwork/dev] 'Нужно настроить почтовый сервер MailWizz'
  - fails: L2:reply_draft: обязательное начало «Здравствуйте»
- **#8720** [kwork/marketing] 'Парсинг email кадровых агенств'
  - fails: L2:reply_draft: обязательное начало «Здравствуйте»
- **#8702** [kwork/dev] 'Установка и доработка WordPress-темы ресторана'
  - fails: L2:reply_draft: обязательное начало «Здравствуйте»

## Top tools fail cases

- **#8812** [kwork/marketing] 'Помощь в работе с блогерами'
  - fails: tools:min_2_required
- **#8782** [kwork/dev] 'SEO оптимизация сайта'
  - fails: tools:min_2_required

## LLM judge (O72c)

- L2 scored: 10/10 · combined **3.83**/5 · send_as_is **40.0%** · ❌
- Подробно: `data/preprod_ai_prod_audit_judge.md`

## Owner lead_ids (root cause)

- **#8925**: auto_pass
- **#10442**: auto_pass
- **#9843**: auto_pass
- **#8752**: auto_pass
- **#9581**: auto_pass
- **#8772**: auto_pass
- **#9831**: auto_pass
- **#9374**: auto_pass
- **#9326**: auto_pass
- **#10362**: auto_pass
