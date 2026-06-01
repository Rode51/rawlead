# O72 — AI prod audit (human)

- **Time:** 2026-06-01T10:22:53.771651+00:00
- **L2 sample (reply_draft):** 22 leads
- **Draft quality (L1+L2, без tools):** **100.0%** (✅ ≥95%) · 22/22 pass
- **Tools bucket (отдельно):** **27.3%** · 6/22 pass · KNOWN_TOOLS + canonical aliases
- **Combined auto-pass (draft+tools):** 27.3% (❌ <85%)
- **L1 empty bucket:** 0 leads · missing summary **0**
- **Merged rows:** 22
- **Profile:** site

> **O72b:** draft-only % — gate качества отклика (L1+L2); tools — отдельная строка (KNOWN_TOOLS whitelist + canonical aliases, без раздувания picker 51).

---

## Draft fail types (L1+L2)

- _(none)_

## Tools fail types

- `tools:not_in_catalog`: **14**
- `tools:vendor_lock`: **2**
- `tools:min_2_required`: **2**

## Top draft fail cases


## Top tools fail cases

- **#8764** [kwork/dev] 'Консультация по Авито'
  - fails: tools:min_2_required, tools:not_in_catalog:avito
- **#8752** [kwork/design] 'Платформа для учебного центра'
  - fails: tools:vendor_lock:telethon,neon, tools:not_in_catalog:aiogram_3
- **#8925** [fl/dev] 'Скрипты из Google-таблиц перестали работать. Нужно адаптировать сценарии к новой'
  - fails: tools:not_in_catalog:google_sheets
- **#8902** [kwork/dev] 'Сделать футажи'
  - fails: tools:not_in_catalog:after_effects,cinema_4d
- **#8812** [kwork/dev] 'Помощь в работе с блогерами'
  - fails: tools:min_2_required
- **#8794** [kwork/design] 'Ускорьте сайт WP-Elementor'
  - fails: tools:not_in_catalog:elementor
- **#8788** [kwork/design] 'Есть сайт на неткате'
  - fails: tools:not_in_catalog:netcat
- **#8782** [kwork/marketing] 'SEO оптимизация сайта'
  - fails: tools:not_in_catalog:robots_txt,sitemap_xml
- **#8776** [kwork/design] 'Улучшить скорость работы сайта Elementor, WC, Tutor'
  - fails: tools:not_in_catalog:elementor,woocommerce,tutor_lms,pagespeed_insights,wp_rocket
- **#8774** [kwork/design] 'Разместить на саите каталог автопитера'
  - fails: tools:vendor_lock:telethon,neon

## LLM judge (O72c)

- L2 scored: 22/22 · combined **4.03**/5 · send_as_is **31.8%** · ❌
- Подробно: `data/preprod_ai_prod_audit_judge.md`
