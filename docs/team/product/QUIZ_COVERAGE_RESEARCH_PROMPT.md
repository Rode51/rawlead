# Research: покрытие квиза vs каталог vs prod (промпт)

**Для:** `@mechanic` (основной исполнитель · Neon + crosswalk) · `@lead-product` (карточки после matrix) · owner (approve P0 signals)  
**Когда:** § **O221-QUIZ-COVERAGE** — после deploy v1, до quiz v2 / soft ads  
**Результат:** `data/quiz_coverage_matrix.csv` + `docs/team/product/QUIZ_COVERAGE_GAPS.md` + signal map v2  
**Канон:** [`SKILLS_TOOLS_CATALOG.md`](SKILLS_TOOLS_CATALOG.md) · [`LEAD_PRODUCT_PROMPT.md`](LEAD_PRODUCT_PROMPT.md) § O221-QUIZ-COVERAGE · `src/skills_catalog.py` `TIER_A_BY_NICHE`

---

## 1. Зачем (простыми словами)

Квиз — **измеритель профиля**. Если в квизе нет карточки под навык X, пользователь **никогда** не получит X в `user_tags` → match **0%** на лидах с X. Это не баг match.

v1 = **56** synthetic cards · **12** signals · **24** unique `skills_on_like`.  
Каталог Tier-A = **23** tags · prod лента = **50+** tags/нишу.

**Цель research:** построить **матрицу дыр** (каталог × prod × quiz v1) и правила v2, чтобы **ни одна частая ниша ленты** не оставалась неизмеряемой.

**Не цель:** написать 500 карточек «на всякий случай» · менять формулу match · трогать L1 промпт.

---

## 2. Источники данных

| # | Источник | Что взять |
|---|----------|-----------|
| s1 | Neon `leads` | `is_visible=true`, `category IN (dev,design,marketing,text)`, `lead_tags` frequency |
| s2 | `data/quiz_cards_v1.json` | `skills_on_like`, `signal`, `niche`, `card_type` |
| s3 | `src/skills_catalog.py` | `TIER_A_BY_NICHE`, `EXPAND_MAP`, `resolve_canonical_tag` |
| s4 | `docs/team/product/SKILLS_TOOLS_CATALOG.md` | Tier A/B, subheads, merge rules |
| s5 | Owner pain samples | скриншоты 0% match после квиза (optional) |

---

## 3. Шаги исполнителя

### Step A — Prod tag census (Neon)

SQL (adapt if schema differs):

```sql
SELECT category, tag, COUNT(*) AS cnt
FROM leads l,
LATERAL jsonb_array_elements_text(l.lead_tags) AS tag
WHERE l.is_visible = TRUE
  AND l.category IN ('dev','design','marketing','text')
GROUP BY 1, 2
ORDER BY 1, cnt DESC;
```

Export top tags per niche · compute **% of niche leads** per tag.

### Step B — Crosswalk matrix

For each `canonical_tag` (from catalog + top 30 prod tags/niche):

| column | meaning |
|--------|---------|
| `tag` | canonical id |
| `niche` | dev/design/marketing/text |
| `tier` | A/B/C from catalog |
| `prod_lead_cnt` | Neon count |
| `prod_pct_niche` | share within niche |
| `quiz_v1_skill` | Y if in any `skills_on_like` |
| `quiz_v1_signal` | signal id if mapped |
| `quiz_v1_card_count` | # cards teaching tag |
| `expand_reachable` | Y if parent Tier-A in quiz expands to tag |
| `gap_class` | **P0** ≥5% prod · **P1** Tier-A missing · **P2** long tail |

Write **`data/quiz_coverage_matrix.csv`**.

### Step C — Gap report

**`docs/team/product/QUIZ_COVERAGE_GAPS.md`:**

- Executive: N P0 gaps / niche
- Table: top 10 P0 tags/niche with example lead (id, title, tags)
- Quiz repetition analysis: cards per signal in v1 · why 20-card run repeats
- Recommended **signals v2** per niche (list for owner approve)

### Step D — Card budget + simulation spec

Propose:

- Min cards per P0 signal (anchor/trap/boundary counts)
- Total v2 target (~150–200)
- Simulation: 100 quiz paths → which tags imported → match vs 50 random leads (pseudo-code OK)

---

## 4. Gap classification rules

| Class | Rule | Action in v2 |
|-------|------|--------------|
| **P0** | `prod_pct_niche ≥ 5%` OR ≥30 visible leads | Must have ≥3 anchor cards + signal |
| **P1** | Tier-A in catalog, quiz_v1_skill=N | Must have ≥2 anchor cards |
| **P2** | Long tail · expandable via EXPAND_MAP from covered parent | Optional boundary/trap only |

---

## 5. Acceptance (research done)

- [ ] `quiz_coverage_matrix.csv` — all Tier-A rows present
- [ ] `QUIZ_COVERAGE_GAPS.md` — owner can read without code
- [ ] P0 list per niche — **≤15 tags/niche** prioritized (not infinite)
- [ ] Signal map v2 draft — owner approve before PM writes cards
- [ ] Handoff block in GAPS.md → `@lead-product` r6 pilot 40 cards

---

## 6. Handoff template

```
@lead-product
Mechanic § O221-QUIZ-COVERAGE research ✅
Read: docs/team/product/QUIZ_COVERAGE_GAPS.md
Matrix: data/quiz_coverage_matrix.csv
Next: pilot 40 cards (10/niche) on P0 gaps · then quiz_cards_v2.json
```

---

## 7. Запрещено

- Правки `src/`, `scripts/` (Mechanic = read-only analysis + docs/data artifacts only)
- Commit secrets · raw DATABASE_URL in docs
- «Починить match synonym» вместо quiz coverage — только если PM explicitly marks tag as expand-only
