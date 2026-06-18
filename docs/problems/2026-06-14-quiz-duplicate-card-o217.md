# 2026-06-14 — квиз: одна карточка 4× подряд (O217 JSON ids)

**Severity:** P1 UX  
**Reported:** owner 2026-06-14 (retake «Пройти ещё раз», amoCRM ↔ Google Sheets)

## Symptom

При перепрохождении теста одна и та же карточка (amoCRM ↔ Google Sheets) показывается **4 раза подряд** на «Берем»/«Мимо».

## Root cause (Lead verify)

O217 JSON pack uses **string** `card_id` (e.g. `qc_dev_api_01`).

`quiz_next_response` builds `shown_ids` with **`int(raw)` only** — non-numeric ids are **silently dropped**:

```python
# src/quiz_adaptive.py ~566-571
shown_ids: list[int] = []
for raw in card_ids:
    try:
        shown_ids.append(int(raw))
    except (TypeError, ValueError):
        continue  # ← all JSON ids skipped
```

→ `_query_card_json(..., shown_str=[])` every `/quiz/next` → **same first card**.

Client sends history correctly (`card_id: String(currentCard.card_id)` in `rawlead-quiz.js`).

## Fix (@coder)

| File | Change |
|------|--------|
| `src/quiz_adaptive.py` | Track **shown as strings** from history; pass to JSON path; keep int exclude for Neon fallback |
| `tests/test_o217_quiz_cards.py` | POST `/v1/quiz/next` with 2+ history entries using `qc_dev_api_01` → **different** `card_id` |

Deploy: **API** (`quiz_adaptive.py`) + restart `rawlead-api` — theme not required.

## Related UX (separate)

Result screen category bars misaligned — § **O220-QUIZ-BAR-ALIGN** in `CODER_PROMPT.md`.
