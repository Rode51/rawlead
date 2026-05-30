# Mobile UX — review владельца (2026-05-30)

**Статус:** **✅ код v1.11.4** · local test → deploy → re-run O37c

**Контекст:** O37c audit 1/5 · скрин владельца `/lenta/` 390px · audit U3/U8 sheet broken.

## Findings (владелец)

| ID | Проблема | Где |
|----|----------|-----|
| **M1** | Карточки **не влезают** — обрезаны справа, тяжёлые рамки | `/lenta/` · `/cabinet/` |
| **M2** | Header: «Как устроено» **пересекается** с плашкой категорий | sticky stack |
| **M3** | Фильтры **неудобные** — нужно **одно выпадающее окно** (sheet) | лента |
| **M4** | **Полная пересборка** mobile UI/UX feed + ЛК | 390×844 |

**Референс карточек:** как на **главной** (live preview hero), не desktop-grid на узком экране.

## Связь с audit

| Audit | Owner |
|-------|-------|
| W1 sheet hidden | M3 |
| W2 tap outside | M4 |
| W3 cabinet modal | M4 (ЛК) |

## Артефакты

- Скрин владельца (Cursor assets 2026-05-30)
- `data/preprod_ux_audit/U*_mobile_*.png`
