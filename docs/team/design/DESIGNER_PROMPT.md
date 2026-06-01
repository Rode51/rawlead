# Designer — **→ Сейчас:** **⏸** (D-O81 ✅ · D-O82b по запросу Lead)

**D-O81 ✅ 2026-06-01** — спека § O81-w1 в [`LEAD_DESIGN_PROMPT.md`](LEAD_DESIGN_PROMPT.md) · handoff **@coder**

| | |
|--|--|
| **Канон WP** | [`REFERENCE.md`](../../design/wp/REFERENCE.md) v5 |
| **Проблема** | `flow.php` — demo-карточка заказа; владелец хочет **понятную иллюстрацию** сути (N вкладок → 1 лента) |
| **Источники в copy** | FL · Kwork · TG · YouDo · Freelance.ru · FreelanceJob · Пчёл.нет |

## D-O81 — Deliverables

| # | Артефакт |
|---|----------|
| 1 | Макет/спека секции **Flow** (desktop + mobile) — **не** lead-card preview как главный элемент |
| 2 | Визуал: «10 вкладок → один поток RawLead» + chip источников |
| 3 | PNG или Figma → `docs/design/wp/` · правки `REFERENCE.md` §3.3 если нужно |
| 4 | Handoff `@lead-architect` → Coder § O63-w1 copy + WP |

**Не в scope:** парсеры (Coder O63) · правки `/lenta/`.

---

## § O82-w1 — Match breakdown на карточке (**→ @coder**, P1 · 2026-06-01)

**Спека:** [`feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) §3.1 · [`REFERENCE.md`](../../design/wp/REFERENCE.md) §4 (Match breakdown, Match label)

### Задача

Добавить строку breakdown под match-bar на карточке лида (`/lenta/` и live-preview на лендинге).

| ID | Что сделать | Файл |
|----|-------------|------|
| w1-1 | **Match row:** лейбл «Совместимость» при `skills_selected=true`; «Качество заказа» при `skills_selected=false` (`user_skills.length === 0`) | `rawlead-feed.js` |
| w1-2 | **Breakdown row** `.rl-match-breakdown`: одна строка под match-row; режим A: `Качество заказа: {ai_score} · Навыки: {keyword_match}%`; режим B: `Добавь навыки, чтобы увидеть совместимость →` (ghost link → trigger `[Навыки ▾]` / skills sheet) | `rawlead-feed.js` |
| w1-3 | **API check:** убедиться что `/v1/feed` возвращает `ai_score` и `keyword_match` раздельно (не только `final_rank`). Если нет — добавить поля в ответ | `api_server.py` |
| w1-4 | **Zero state bar:** когда `skills_selected=false` — bar width = `ai_score` (не `final_rank`); fill `#525252` | `rawlead-feed.js` |
| w1-5 | **ИДЕАЛЬНО ✦ mobile:** при `keyword_match=100 + ≥1 навык` — badge `ИДЕАЛЬНО ✦` появляется в match row **вместо** AI-чипа «Брать ✓»; НЕ в meta-строку | `rawlead-feed.js` |
| w1-6 | **Tooltip** на лейбле «Совместимость» (desktop): `title="Качество × 60% + Навыки × 40%"` | `rawlead-feed.js` |
| w1-7 | Стили: `.rl-match-breakdown` — Manrope 12px/400, `#525252`; mobile: 11px, 1 строка, `overflow: hidden; text-overflow: ellipsis; white-space: nowrap` | `rawlead.css` (или child-theme inline) |

### CSS

```css
.rl-match-breakdown {
  font: 400 12px/1.4 'Manrope', sans-serif;
  color: #525252;
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
@media (max-width: 767px) {
  .rl-match-breakdown { font-size: 11px; }
}
.rl-match-breakdown a {
  color: #525252;
  text-decoration: underline;
  text-underline-offset: 2px;
}
```

### Acceptance (O82)

- [ ] Режим A (навыки выбраны): строка «Качество заказа: N · Навыки: N%» видна на каждой карточке
- [ ] Режим B (нет навыков): «Добавь навыки…» — НЕ «0%» на карточке
- [ ] 100% match: «ИДЕАЛЬНО ✦» в match row, breakdown «Качество: N · Навыки: 100%» — нет конфликта на 390px
- [ ] Владелец: 3 карточки — «понятно, не обман»

---

## § O82-w1b — Match v2 (**→ @coder**, P0 · после **D-O82b**)

**Lead brief:** [`LEAD_DESIGN_PROMPT.md`](LEAD_DESIGN_PROMPT.md) § **D-O82b**

| ID | Что сделать |
|----|-------------|
| r1 | Убрать чипы «Брать ✓» / «Сомнительно» с карточки ленты |
| r2 | Label + bar = **только «Совместимость»** (`keyword_match`), не «Качество заказа» |
| r3 | CTA «Добавь навыки…» = **`!isLoggedIn() && !hasUserSkills()`** только |
| r4 | Breakdown = совпадение стека (по макету D-O82b), без `ai_score` в UI |
| r5 | Обновить U11 в `ux_audit.py` |

---

## Закрыто (индекс)

| Волна | Статус |
|-------|--------|
| WAVE-UX-MOBILE | ✅ |
| WAVE-2-CSS · O41 | ✅ |

Детали → [`archive/DESIGNER_PROMPT_ARCHIVE.md`](../archive/DESIGNER_PROMPT_ARCHIVE.md)

---

_Lead Designer · hot · 2026-06-01_
