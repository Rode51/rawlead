# TASKS (активное)

**Снимок:** [`STATUS.md`](STATUS.md) · **Prod:** [`PROD_FACTS.md`](PROD_FACTS.md) · **Roadmap:** [`ROADMAP.md`](../architect/ROADMAP.md)

---

## Где мы (2026-06-18)

**→ Now:** **O280** WP→Next до ads · O200 ⏸ · O271 ✅

---

## Очередь (hot)

| # | Что | Кто | Статус |
|---|-----|-----|--------|
| **0** | **O280** WP → Next UI `web/` | Claude Code + @coder | 🔴 **P0 owner** · [`WP_TO_NEXT_HANDOFF.md`](../architect/WP_TO_NEXT_HANDOFF.md) |
| **1** | **O200** L2 regen judge ≥70%×4 | @coder | ⏸ |
| **3** | **O237** Metrika goals UI | owner | ⏸ smoke отложен · код **1.19.20** ✅ prod |
| **4** | **M1** TG test ads (≤5k ₽) | @lead-marketing + owner | ⏳ после O218 + L2 |
| **5** | **Portfolio P0** skills + refs с нуля | @lead-portfolio + owner + Claude Code | ⏳ |
| — | **O262k** YouDo DC probe | @coder | ✅ servicepipe 1712b |
| — | **O252** TG content dedup | @coder | ✅ prod (Lead verify) |
| — | **O265** + **O265b** bot | @coder | ✅ prod **2026-06-17** |

---

## Закрыто недавно (где смотреть)

| Блок | Статус | Тесты / spec |
|------|--------|--------------|
| **O209** match-first UX/copy/quiz | ✅ theme 1.18.84 | [`wave-o209-match-brief.md`](../design/wp/wave-o209-match-brief.md) |
| **O217** quiz cards pack | ✅ | `tests/test_o217_quiz_cards.py` |
| **O197** adaptive quiz | ✅ | `tests/test_o197_quiz_adaptive.py` · `test_o195_quiz.py` |
| **O195** tags import + weight_delta | ✅ | `tests/test_o195_quiz.py` |
| **O220** feed draft instant | ✅ | `tests/test_o220_feed_draft.py` |
| **O225** match floors 20/10 | ✅ | `tests/test_o225_match_floors.py` |
| **O224** compatibility | ✅ | `tests/test_o224_compatibility.py` |
| **O250/O253** push UUID + JWT heal | ✅ prod | `tests/test_match_push_o250.py` · `test_o253_jwt_session_heal.py` |
| **Match push core** | ✅ | `tests/test_match_push.py` · `test_match_push_o50.py` · `test_match_f2.py` |
| **O261–O262d** YouDo parser recovery + list view | ✅ prod | `tests/test_o261_*` · `test_o262*` · `test_o262d_*` |
| **O109** push deeplink `?lead=` | ✅ | theme feed JS |

Архив закрытых § → [`CODER_PROMPT_ARCHIVE`](../architect/CODER_PROMPT_ARCHIVE.md)

---

## До рекламы (ROADMAP волны)

| Волна | Что | Статус |
|-------|-----|--------|
| **1 TG** | t2b sync · O207 funnel · join v4 ~304 | 🟡 фон |
| **2 Quiz** | O208/O217/O197 | ✅ большая часть |
| **3 Perf** | lenta/home/quiz load | ⏳ после design scope |
| **4 L2** | O200 regen 70%×4 | ⏳ |
| **5 Analytics** | O237 Metrika · O113 SEO | ⏸ owner smoke · код ✅ |
| **6 QA** | O218 Playwright | ✅ prod green |
| **7 GTM** | M1 ads · portfolio | ⏸ |

**Гейт GTM:** O218 green · O200 70%×4 · Metrika live · tier smoke ✅

---

## Probe (owner/Lead)

```powershell
cd C:\Users\hramo\uisness
python scripts/deploy-o258-playwright-probe-vps.py
python scripts/_lead_o261_o262_post_deploy.py grep   # YouDo trace
```
