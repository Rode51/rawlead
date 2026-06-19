# RawLead Product UI — Claude Code Context

**Target:** `https://rawlead.ru` · **Package:** `rawlead-next/` · **Track:** O280 WP→Next  
**Backend:** `https://api.rawlead.ru` — **do not modify** `src/`

> Legacy docs may say `web/` — **this folder is `rawlead-next/`** (owner decision 2026-06-19).

---

## Read order (before any UI code)

1. [`docs/migration/PAGES_INVENTORY.md`](../docs/migration/PAGES_INVENTORY.md) — **what to build** (prod strings verified 2026-06-19)
2. [`docs/migration/O280_AS_BUILT.md`](../docs/migration/O280_AS_BUILT.md) — **what is already done** (Lead verify)
3. [`docs/migration/API_CONTRACTS.md`](../docs/migration/API_CONTRACTS.md) — **how data flows**
4. [`docs/design/wp/feed-cabinet-mvp.md`](../docs/design/wp/feed-cabinet-mvp.md) — **UX behavior only** §0 + §0.1
5. [`docs/team/architect/WP_TO_NEXT_HANDOFF.md`](../docs/team/architect/WP_TO_NEXT_HANDOFF.md) — phases + copy-paste prompts
6. **Reference only:** `wordpress/rawlead-kadence-child/assets/js/rawlead-{feed,cabinet,quiz,pricing}.js`

**Не в bootstrap:** дизайн-промпты, `DESIGN_TOKENS.md`, NEO/палитра.

---

## Stack (fixed)

| Tool | Version / rule |
|------|----------------|
| Next.js | **14** App Router |
| TypeScript | yes |
| Tailwind CSS | yes |
| Export | `output: 'export'` in `next.config.mjs` |
| API | `fetch` → `https://api.rawlead.ru/v1/*` |
| Auth storage | `localStorage` key `rawlead_access_token` |
| Dev port | **3001** (`npm run dev`) |

---

## Hard constraints

### Touch only

- ✅ `rawlead-next/**`
- ✅ read `wordpress/**`, `docs/**`, `tests/**`

### Never modify

- ❌ `src/` · ❌ `wordpress/` · ❌ `portfolio/` · ❌ `scripts/` deploy · ❌ secrets

### Product rules

- Quiz-first · no manual skill tree primary UX
- O272: `rawlead-tags-imported` after quiz import
- JWT rotation: `X-Rawlead-Access-Token`
- Copy: `PAGES_INVENTORY` prod snapshot

---

## Phases

| Phase | Goal | Status |
|-------|------|--------|
| **0** | scaffold + api + smoke lenta | **✅ done** |
| **1** | full `/lenta/` + auth + quiz | **✅ done** |
| **1b** | lenta polish (mobile filter + source filter + skeleton fix) | **✅ done** |
| **2** | `/cabinet/` — anon gate + inbox + subscription | **🟡** · gaps: skills/trial/dev mocks → `O280_AS_BUILT` § Prod-канон |
| **3** | `/pricing/` + deploy script + cutover | **→ NEXT** |

---

## As-built map (Claude session 4 · 2026-06-19)

| Route | Status | Components / notes |
|-------|--------|-------------------|
| `/` | **✅ done** | AnnouncementBar · Header · Hero · LivePreview · FlowSection · Features · PricingPreview · Footer |
| `/lenta/` | **✅ COMPLETE** | FilterBar · FilterSheet · FeedCard · MatchBar · AnonStrip · LoginModal · QuizOverlay · load more |
| `/cabinet/` | **🟡 Phase 2** | anon+QR ✅ · subscription **починить** (no skills, no trial btn, auto trial) · inbox ✅ |
| `/pricing/` | **❌** | → 404 · Phase 3 |
| `/quiz/` | **❌** | → QuizOverlay from lenta/#quiz |

**`/lenta/` — всё что сделано (не трогать):**
- `lib/auth-context.tsx` — AuthProvider · feedTier (`pending` → `anon`) · 3s timeout на auth init
- `lib/api.ts` — GET-запросы без Content-Type (no CORS preflight для anon) · JWT rotation
- `lib/utils.ts` — timeAgo · SOURCE_LABEL · SOURCE_COLOR · NICHE_ICON · DIFFICULTY_BADGES
- `components/Providers.tsx` — AuthProvider + SmoothScroll
- `components/feed/FeedCard.tsx` — card collapsed/expanded · hover lift · stagger animation
- `components/feed/MatchBar.tsx` — tier-aware: anon locked / quiz-locked / % match
- `components/feed/FilterBar.tsx` — desktop: категории + sort · mobile: «☰ Фильтр» trigger + active pill
- `components/feed/FilterSheet.tsx` — mobile bottom sheet · **категории + биржи + сортировка** · draft mode · «Применить» / «Сбросить»
- `components/feed/AnonStrip.tsx` — «Заказы с задержкой 30 мин.»
- `components/feed/LoginModal.tsx` — bot-session flow · JWT save
- `components/feed/QuizOverlay.tsx` — start · like/skip · import · rawlead-tags-imported
- `app/lenta/page.tsx` — skeleton только по `loading` (не по auth.status) · 5s fetch timeout · source + category + sort state

**Биржи в FilterSheet (все 7 как на prod WP):**
`fl` FL.ru · `kwork` Kwork · `youdo` YouDo · `tg` Telegram · `freelance_ru` Freelance.ru · `freelancejob` FreelanceJob · `pchyol` Пчёл.нет

**8/8 дизайн-критериев ✅** (neo-brutalist · Unbounded display · 5 цветов · hierarchy · motion cubic-bezier · mobile sheet ≠ desktop · semantic HTML · WCAG)

**`/cabinet/` — MVP (gaps vs prod — read `O280_AS_BUILT.md` § Prod parity):**

| Что есть | Чего нет vs prod |
|----------|------------------|
| anon gate · bot login poll · inbox accordion · copy/delete | QR login block · user bar · **Уведомления** |
| skills chips · subscription CTA · `?dev=free\|paid` | copy «черновики» · **RawLead Premium** title · inline skills layout · load more |

- `app/cabinet/page.tsx` · `components/cabinet/InboxCard.tsx`
- **Reference:** `page-cabinet.php` · `rawlead-cabinet.js` — **не** упрощённая трёхкарточная вёрстка как финал

**Next session:** cabinet **prod parity** P0 + `/pricing/` phase 3. Do NOT rebuild home/lenta.

---

## API quick reference

- `GET /v1/feed` · `GET /v1/public/site-stats`
- Auth: `POST /v1/auth/bot-session` → `GET /v1/auth/bot-complete`
- Quiz: `GET /v1/quiz/start` · `POST /v1/quiz/next` · `POST /v1/me/tags/import`
- Draft / inbox / pay — see `lib/api.ts` · [`API_CONTRACTS.md`](../docs/migration/API_CONTRACTS.md)

---

## `/cabinet/` prod canon (read before editing cabinet)

**Source:** `O280_AS_BUILT.md` § Prod-канон · `page-cabinet.php` · `rawlead-cabinet.js` O219

| ❌ Не строить | ✅ Строить |
|--------------|-----------|
| Блок «Твои навыки» / chips тегов | User bar · Premium · Уведомления · Inbox |
| Badge «Бесплатно» для нового юзера | Badge Trial / Premium после 1-го входа |
| Кнопка «Активировать Trial» | Trial **авто** при login (`_try_auto_start_trial_on_login`) |
| `?dev=free` как референс UI | Реальный JWT или мок **trial-by-default** |
| Skill-tree modal | Retake: ссылка «Пройти тест заново» → `/lenta/#quiz` |

**Подписка после входа:** H2 «RawLead Premium» · detail «Premium активен до …» · цена скрыта пока trial active · CTA pay только expired / no access.

---

## Verify before saying «done»

- [ ] `npm run build` passes
- [ ] No edits outside `rawlead-next/`
- [ ] Update `O280_AS_BUILT.md` + this § As-built
- [ ] Report blockers (CORS, 404 routes)

---

_RawLead O280 · Lead verify 2026-06-19_
