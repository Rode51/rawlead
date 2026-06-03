# O96 — аудит: Design §4.8–4.10 · §7.7 + PM Z1–Z13 vs код

**Дата:** 2026-06-02 · **Prod было:** 1.17.0 · **Локально:** 1.17.1 (polish, не на VPS)

## Вердикт

**Coder по O96-code выполнил ~60% канона.** Copy и strip — в основном ок. **Карточка и единый компонент — FAIL** на prod 1.17.0. Часть polish уже в репо (1.17.1), **не задеплоена**.

---

## §4.8 · §4.9 · §4.10 · §7.7 (Design)

| AC / пункт | Спека | Prod 1.17.0 | Локально 1.17.1 | Статус |
|------------|-------|-------------|-----------------|--------|
| §4.9 anon strip | над H1, copy Z2 | ✅ | ✅ | OK |
| §4.9 no card CTA | убрать с карточки | ✅ | ✅ | OK |
| §4.8 niche icon | corner + fallback | ❌ inline, часто скрыт | ✅ absolute + infer tags | **fix in 1.17.1** |
| §4.8 ИДЕАЛЬНО | head-start (`flow.php`) | ❌ в match-row | ✅ в head | **fix in 1.17.1** |
| §4.8 match layout | label **над** bar | ❌ row inline | ✅ stack | **fix in 1.17.1** |
| §4.8 breakdown | PM: «Навыки: N%» | ❌ «Качество · Навыки» | ✅ только навыки | **fix in 1.17.1** |
| §4.8 equal height | collapsed grid | ❌ CTA разный | ⚠️ min-height CTA, но `:empty` схлопывает | **ещё @coder** |
| §4.8 единая карточка | lenta=cabinet=home | ❌ lenta ≠ flow/live | ⚠️ lenta≈flow, live-preview без corner CSS | **ещё @coder** |
| §4.8 O97 row | UI под breakdown | ✅ скрыт без API | ✅ | OK до O97 |
| §4.10 Skill Tree hint | Z4 | ✅ | ✅ | OK |
| §4.10 strip «+» убрать | Z4 | ✅ | ✅ | OK |
| §7.7 mobile chips anon | horizontal scroll | ✅ CSS | ✅ | OK |
| §7.7 mobile logged chips | chips + sort | ⚠️ desktop rule hides cats for logged | ✅ mobile override | проверить smoke |

## PM O96-Z1–Z13 (выборка)

| Зона | Канон | Код | Статус |
|------|-------|-----|--------|
| Z1 title | Заказы под твой стек | ✅ functions.php | OK |
| Z1 features H2 | «Один поток…» в flow | flow ✅ · features.php **«Как устроено»** | ⚠️ мелочь |
| Z2 load more | Показать ещё | lenta ✅ · **cabinet «Ещё лиды»** | ❌ |
| Z2 TWO-SPEEDS | задержка 15 мин | ✅ JS | OK |
| Z3 skills btn | ⚙ Изменить навыки | ❌ серая, обрезка · **1.17.1 NEO chip** | fix 1.17.1 |
| Z5 cabinet anon sub | Nastroyish naviki… | ✅ | OK |
| Z8–Z9 pricing/how | copy pass | ✅ marketing.php | OK |
| Z10 FAQ ban | не VPS | ✅ marketing.php локально · **prod мог быть старый** | deploy |
| Z11 difficulty | badge UI | UI ✅ · data O97 | OK |

## Root cause (почему «всё не так»)

1. Coder **не взял эталон `flow.php`** — своя match-row в JS  
2. Lead **принял O96-code без owner smoke** карточки  
3. Design §4.8 wireframe и PM Z3 **расходились** (Качество заказа) — owner override 2026-06-02  
4. **1.17.1 не на VPS** — владелец видит 1.17.0  

## Остаток после deploy 1.17.1

| # | Fix | 1.17.2 |
|---|-----|--------|
| 1 | CTA placeholder always in DOM | ✅ |
| 2 | cabinet «Показать ещё» | ✅ |
| 3 | live-preview corner CSS | ✅ |
| 4 | features H2 Z1 | ✅ |

**O97:** `difficulty` в API — § O97-code.

**Prod:** **1.17.2** · deploy 2026-06-02 · **O96 closed**
