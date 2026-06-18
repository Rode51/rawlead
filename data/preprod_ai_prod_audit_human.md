# O72 — AI prod audit (human)

- **Time:** 2026-06-14T14:40:29.156392+00:00
- **L2 sample (reply_draft):** 85 leads
- **Draft quality (L1+L2, без tools):** **97.6%** (✅ ≥95%) · 83/85 pass
- **Tools bucket (отдельно):** **82.4%** · 70/85 pass · KNOWN_TOOLS + canonical aliases
- **Combined auto-pass (draft+tools):** 81.2% (❌ <85%)
- **L1 empty bucket:** 0 leads · missing summary **0**
- **Merged rows:** 123
- **Profile:** site

> **O72b:** draft-only % — gate качества отклика (L1+L2); tools — отдельная строка (KNOWN_TOOLS whitelist + canonical aliases, без раздувания picker 51).

---

## Draft fail types (L1+L2)

- `L2:empty_reply_draft`: **38**
- `L2:reply_draft`: **2**

## Tools fail types

- `tools:empty_but_desc_hints`: **10**
- `tools:min_2_required`: **5**

## Top draft fail cases

- **#23100** [fl/design] 'Создать через ии презентацию компании'
  - fails: L2:reply_draft: запрещённые слова (ИИ/Cursor/…)
- **#19244** [fl/dev] 'Проект внедрения ИИ в работу медицинской организации.'
  - fails: L2:reply_draft: запрещённые слова (ИИ/Cursor/…)

## Top tools fail cases

- **#23249** [kwork/design] 'Разработка UX/UI-кейса интернет-магазина'
  - fails: tools:min_2_required
- **#23174** [fl/marketing] 'Необходимо сопостоставить около 20 тыс записей из трех файлов'
  - fails: tools:empty_but_desc_hints:excel
- **#23173** [fl/design] 'Обработка фотографий в ФШ'
  - fails: tools:empty_but_desc_hints:photoshop
- **#23165** [kwork/marketing] 'АИ ИИ агент'
  - fails: tools:empty_but_desc_hints:google_sheets_api,telegram_bot_dev
- **#23156** [kwork/dev] 'Исправление ошибок сайта wordpress'
  - fails: tools:empty_but_desc_hints:telegram_bot_dev,wordpress_dev
- **#23153** [kwork/dev] 'Виджет для стрима'
  - fails: tools:empty_but_desc_hints:figma
- **#23101** [kwork/dev] 'Создать парсер телегpaмм'
  - fails: tools:empty_but_desc_hints:google_apps_script,mysql,python,telegram_bot_dev,web_scraping
- **#23100** [fl/design] 'Создать через ии презентацию компании'
  - fails: tools:empty_but_desc_hints:powerpoint
- **#23063** [kwork/dev] 'Наполнение и редактирование сайтов'
  - fails: tools:empty_but_desc_hints:seo,wordpress_dev
- **#23014** [kwork/dev] 'Необходим калькулятор для сайта'
  - fails: tools:empty_but_desc_hints:wordpress_dev

## LLM judge (O72c)

- L2 scored: 40/40 · combined **4.2**/5 · send_as_is **75.0%** · ✅
- Подробно: `data/preprod_ai_prod_audit_judge.md`

## Owner lead_ids (root cause)

- **#24723**: L2:empty_reply_draft
- **#24706**: L2:empty_reply_draft
- **#24626**: L2:empty_reply_draft
- **#24590**: L2:empty_reply_draft
- **#24578**: L2:empty_reply_draft
- **#24396**: L2:empty_reply_draft
- **#24394**: L2:empty_reply_draft
- **#24393**: L2:empty_reply_draft
- **#24339**: L2:empty_reply_draft
- **#24202**: L2:empty_reply_draft
- **#24824**: L2:empty_reply_draft
- **#24779**: L2:empty_reply_draft
- **#24777**: L2:empty_reply_draft
- **#24776**: L2:empty_reply_draft
- **#24775**: L2:empty_reply_draft
- **#24768**: L2:empty_reply_draft
- **#24721**: L2:empty_reply_draft
- **#24718**: L2:empty_reply_draft
- **#24717**: L2:empty_reply_draft
- **#24709**: L2:empty_reply_draft
- **#24778**: L2:empty_reply_draft
- **#24767**: L2:empty_reply_draft
- **#24722**: L2:empty_reply_draft
- **#24719**: L2:empty_reply_draft
- **#24647**: L2:empty_reply_draft
- **#24638**: L2:empty_reply_draft
- **#24627**: L2:empty_reply_draft
- **#24592**: L2:empty_reply_draft
- **#24580**: L2:empty_reply_draft
- **#24536**: L2:empty_reply_draft
- **#24818**: L2:empty_reply_draft
- **#24770**: L2:empty_reply_draft
- **#24708**: L2:empty_reply_draft
- **#24653**: L2:empty_reply_draft
- **#24545**: auto_pass
- **#24541**: auto_pass
- **#24539**: L2:empty_reply_draft
- **#24294**: L2:empty_reply_draft
- **#24201**: L2:empty_reply_draft
- **#23959**: L2:empty_reply_draft
