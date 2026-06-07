# Pre-prod UX audit (O37c)

- **URL:** https://rawlead.ru
- **Time:** 2026-06-07T12:09:18.036766+00:00
- **Browser:** chromium+token
- **Auth:** True
- **PASS:** False
- **Critical:** 4

## Scenarios

| ID | Viewport | Title | Pass | ms | Error |
|----|----------|-------|------|-----|-------|
| U1 | desktop | Header + footer links | ✅ | 7004 | — |
| U2 | desktop | Лента: категория + навыки | ✅ | 10106 | — |
| U3 | desktop | Сортировка + закрытие | ✅ | 6967 | — |
| U4 | desktop | Expand + tap outside | ✅ | 8756 | — |
| U10b | desktop | Draft×5 tools audit | ❌ | 100312 | U10b: only 0/3 drafts OK (AI fail on other cards) |
| U11 | desktop | Match breakdown | ✅ | 8017 | — |
| U12 | desktop | Tools auth-only | ❌ | 100196 | U12: premium — no «Инструменты» after draft |
| U5 | desktop | Draft + инструменты | ✅ | 10839 | — |
| U6 | desktop | FAB support modal | ✅ | 6148 | — |
| U7 | desktop | ЛК: навыки + inbox | ✅ | 12639 | — |
| U9 | desktop | Marketing CTA | ✅ | 448 | — |
| U10 | desktop | Console + network | ✅ | 63 | — |
| U1 | mobile | Header + footer links | ✅ | 6620 | — |
| U2 | mobile | Лента: категория + навыки | ✅ | 11349 | — |
| U3 | mobile | Сортировка + закрытие | ✅ | 8512 | — |
| U4 | mobile | Expand + tap outside | ✅ | 8621 | — |
| U11 | mobile | Match breakdown | ✅ | 7996 | — |
| U12 | mobile | Tools auth-only | ❌ | 8847 | U12: premium — no «Инструменты» after draft |
| U5 | mobile | Draft + инструменты | ✅ | 8769 | — |
| U6 | mobile | FAB support modal | ✅ | 6030 | — |
| U7 | mobile | ЛК: навыки + inbox | ❌ | 11618 | cabinet skills modal did not close on overlay tap |
| U8 | mobile | Mobile bottom sheet | ✅ | 11381 | — |
| U9 | mobile | Marketing CTA | ✅ | 419 | — |
| U10 | mobile | Console + network | ✅ | 66 | — |

## Findings

- **critical** [U10b/desktop] Draft×5 tools audit: U10b: only 0/3 drafts OK (AI fail on other cards)
- **critical** [U12/desktop] Tools auth-only: U12: premium — no «Инструменты» after draft
- **critical** [U12/mobile] Tools auth-only: U12: premium — no «Инструменты» after draft
- **critical** [U7/mobile] ЛК: навыки + inbox: cabinet skills modal did not close on overlay tap

## Human review

См. `data/preprod_ux_audit_human.md` — LLM-слой (не авто-rating).

