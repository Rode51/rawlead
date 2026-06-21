# O72 — AI prod audit (human)

- **Time:** 2026-06-20T18:24:22.731518+00:00
- **L2 sample (reply_draft):** 117 leads
- **Draft quality (L1+L2, без tools):** **94.9%** (❌ <95%) · 111/117 pass
- **Tools bucket (отдельно):** **71.8%** · 84/117 pass · KNOWN_TOOLS + canonical aliases
- **Combined auto-pass (draft+tools):** 66.7% (❌ <85%)
- **L1 empty bucket:** 0 leads · missing summary **0**
- **Merged rows:** 117
- **Profile:** site

> **O72b:** draft-only % — gate качества отклика (L1+L2); tools — отдельная строка (KNOWN_TOOLS whitelist + canonical aliases, без раздувания picker 51).

---

## Draft fail types (L1+L2)

- `L2:reply_draft`: **6**

## Tools fail types

- `tools:empty_but_desc_hints`: **20**
- `tools:min_2_required`: **13**

## Top draft fail cases

- **#3355** [youdo/text] 'Избавиться от следов ИИ в курсовой работе'
  - fails: L2:reply_draft: запрещённые слова (ИИ/Cursor/…)
- **#3209** [kwork/design] 'ИИ видео - погоня'
  - fails: L2:reply_draft: запрещённые слова (ИИ/Cursor/…)
- **#3123** [kwork/design] 'Дизайн карточек для МП при помощи ИИ'
  - fails: L2:reply_draft: запрещённые слова (ИИ/Cursor/…)
- **#902** [fl/text] 'Нужно написать сценарий пилотное шоу на 20 минут.'
  - fails: L2:reply_draft: запрещённые слова (ИИ/Cursor/…)
- **#666** [tg:-1001400175014/text] '**Копирайтер, опыт работы с косметологами |  |  |**'
  - fails: L2:reply_draft: запрещённые слова (ИИ/Cursor/…)
- **#624** [fl/text] 'Редактура перевода книги на английский язык (для Amazon)'
  - fails: L2:reply_draft: запрещённые слова (ИИ/Cursor/…)

## Top tools fail cases

- **#13221** [kwork/dev] 'Яндекс карты'
  - fails: tools:min_2_required
- **#12878** [kwork/dev] 'Объединение сайтов и стратегия продвижения'
  - fails: tools:min_2_required
- **#12582** [kwork/dev] 'Доработки'
  - fails: tools:min_2_required
- **#12474** [youdo/marketing] 'Смм специалист'
  - fails: tools:min_2_required
- **#12437** [fl/dev] 'Доработать сайт на вордпресс по ТЗ'
  - fails: tools:min_2_required
- **#12086** [kwork/text] 'Вступительный SEO текст для магазина POD систем'
  - fails: tools:min_2_required
- **#11846** [kwork/marketing] 'Вывести Telegram-бота в ТОП поиска'
  - fails: tools:min_2_required
- **#11141** [youdo/design] 'Оформить презентацию'
  - fails: tools:min_2_required
- **#11105** [kwork/dev] 'Поправить сайт на мод х'
  - fails: tools:min_2_required
- **#9998** [youdo/text] 'Заполнить карточки товара на сайте'
  - fails: tools:min_2_required
