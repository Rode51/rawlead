# O96-polish — карточка / кнопка навыков / FAQ (owner smoke FAIL)

**Дата:** 2026-06-02 · **Prod:** 1.17.0 · **Приоритет:** P0 (до O97)

## Симптомы (владелец)

1. «⚙ Изменить навыки» — не в стиле NEO, текст не влезает в плашку
2. Карточки разной высоты в свёрнутом виде (CTA / breakdown / badge)
3. Нет иконки категории на `/lenta/` (на главной в `flow.php` есть)
4. Нет «Сложность» — **ожидаемо без O97 API**, но UI должен быть готов
5. «Качество заказа: N» — **убрать** (решение владельца, override O96-Z3)
6. «ИДЕАЛЬНО ✦» лезет в строку совместимости — **перенести в head**, как `flow.php`
7. FAQ: убрать VPS, заменить на вопрос про бан

## Root cause

| # | Причина |
|---|---------|
| R1 | Coder сверстал match **row** (bar + label + badge inline), Design/home — **stack** + badge в **head-start** |
| R2 | Breakdown «Качество · Навыки» по PM-канону — владелец передумал |
| R3 | CTA-блок (`ОТКЛИК ✓` vs `Написать отклик` + note) без фикс-слота → разная высота |
| R4 | `item.category` может быть пустым → иконка не рисуется; на главе mock всегда есть |
| R5 | `difficulty` нет в API → row скрыта (**O97-code**) |

## Эталон карточки

**Канон:** `template-parts/rawlead/flow.php` + §4.8 (обновлён owner 2026-06-02)

```
┌─ [</>] corner ─────────────────── 👁 · time ─┐
│ ● Kwork    [ИДЕАЛЬНО ✦]  (badge в head)     │
│ Title                                        │
│ Бюджет: …                                    │
│ 73% Совместимость                            │
│ ▓▓▓▓▓▓▒▒▒  (bar под label)                   │
│ Навыки: 100%  (без «Качество заказа»)        │
│ Сложность: 🟡 Проект  (placeholder / O97)    │
│ tags…                                        │
│ [CTA slot fixed height]                      │
└──────────────────────────────────────────────┘
```

**Иконка категории:** absolute top-left карточки (owner), не терять при длинном title.

## Fix list → @coder § O96-polish

| # | Fix |
|---|-----|
| 1 | `.rl-feed-tags-edit` — NEO chip: border 2px #0A0A0A, shadow, padding 8px 12px, white-space nowrap |
| 2 | Карточка: HTML как `flow.php` — badge в head; match label **над** bar |
| 3 | Убрать «Качество заказа» из breakdown; оставить «Навыки: N%» или скрыть строку если 0 skills |
| 4 | Иконка категории: corner + fallback infer из `lead_tags` если `category` null |
| 5 | `.rl-feed-card__cta` min-height — все свёрнутые карточки одной высоты в grid |
| 6 | `rawlead-cabinet.js` — те же правки карточки |
| 7 | FAQ `marketing.php`: VPS → «Не получу ли бан на бирже?» + канон O96-Z10b |
| 8 | Bump **1.17.1** · deploy · smoke |

**Не в scope polish:** L1 `difficulty` data → **O97-code** (row UI уже есть).

## Acceptance

- [ ] Anon/logged: иконка категории видна на dev/design лидах
- [ ] ИДЕАЛЬНО не пересекает progress bar
- [ ] Grid: 4 карточки в ряд — одна высота (collapsed)
- [ ] Нет текста «Качество заказа»
- [ ] Кнопка навыков читается целиком
- [ ] FAQ без VPS, есть вопрос про бан
