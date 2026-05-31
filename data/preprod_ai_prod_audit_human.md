# O72 — AI prod audit (human)

- **Time:** 2026-05-31T05:59:57.736830+00:00
- **L2 sample (reply_draft):** 46 leads
- **Draft quality (L1+L2, без tools):** **97.8%** (✅ ≥95%) · 45/46 pass
- **Tools bucket (отдельно):** **89.1%** · 41/46 pass · KNOWN_TOOLS + canonical aliases
- **Combined auto-pass (draft+tools):** 87.0% (✅ ≥85%)
- **L1 empty bucket:** 25 leads · missing summary **25**
- **Merged rows:** 71
- **Profile:** site

> **O72b:** draft-only % — gate качества отклика (L1+L2); tools — отдельная строка (KNOWN_TOOLS whitelist + canonical aliases, без раздувания picker 51).

---

## Draft fail types (L1+L2)

- `L2:reply_draft`: **1**

## Tools fail types

- `tools:empty_but_desc_hints`: **5**

## Top draft fail cases

- **#7051** [kwork/design] 'Заменить Google recaptcha &mdash; на Yandex SmartCaptcha'
  - fails: L2:reply_draft: запрещённое начало «Готов…»

## Top tools fail cases

- **#7546** [fl/dev] 'Починить прежний скрипт отправщик файлов эксель в Телеграм и на почту.'
  - fails: tools:empty_but_desc_hints:telegram_bot_dev
- **#7218** [kwork/dev] 'WP Настройка главных страниц мобильной и версии для ПК'
  - fails: tools:empty_but_desc_hints:wordpress_dev
- **#6661** [kwork/dev] 'Сделать логику отправки товара после оплаты wordpress'
  - fails: tools:empty_but_desc_hints:python,wordpress_dev
- **#6655** [kwork/design] 'Оповещения wordpress, удалить лишние плагины, бекап'
  - fails: tools:empty_but_desc_hints:wordpress_dev
- **#6381** [fl/dev] 'Telegram-бот: персональный график ухода за волосами + PDF-протокол (Python)'
  - fails: tools:empty_but_desc_hints:python,telegram_bot_dev
