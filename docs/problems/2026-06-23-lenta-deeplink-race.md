# LENTA deep link — flash then plain feed

**Дата:** 2026-06-23  
**Симптом (owner):** `/lenta/?lead=` сначала открывает карточку, через мгновение «обновляется» — остаётся голая лента.  
**Статус:** root cause ✅ · hotfix ✅ deploy 2026-06-23

## Root cause

Гонка эффектов в `rawlead-next/app/lenta/page.tsx`:

1. `useEffect([])` deep link — prepend `feedApi.lead` + scroll @600ms → **кратко видна карточка**.
2. `useEffect([prefsReady, auth.status, …])` → `loadFeed(true)`:
   - `setLoading(true)` → **скелетоны вместо ленты** (выглядит как refresh).
   - `setItems(data.items)` → **затирает** prepend лида.
3. `auth.status`: `pending` → `auth` → **второй** `loadFeed`.
4. `mergeFeedPrefsOnLogin` → смена sort/category → **третий** `loadFeed`.

`deepLinkRef` только блокирует `setExpandedId(null)`, но **не** сохраняет карточку в `items` и **не** refocus после load.

## Fix (coder)

Порт паттерна WP `focusLeadCard` **после** `loadFeed` complete:

| # | Что |
|---|-----|
| 1 | `parseFocusLeadId()` при init → `focusLeadIdRef` |
| 2 | `focusLeadPendingRef` до успешного focus |
| 3 | `applyFocusLead(leadId)` — merge в items если нет → `setExpandedId` → scroll+pulse после paint (`requestAnimationFrame` ×2) |
| 4 | В конце `loadFeed` reset: если `focusLeadPending` → `applyFocusLead` |
| 5 | Не `setLoading(true)` при deep-link **re**-fetch если items уже есть (опц.) |
| 6 | `auth pending→auth`: не дублировать load если первый уже ok и filters не менялись |
| 7 | После focus: `replaceState` убрать `?lead=` · `focusLeadPending=false` |

**Файлы:** `app/lenta/page.tsx` (+ опц. `lib/feed-deeplink.ts`)

**DoD:** TG «Смотреть в ленте» — карточка **остаётся** раскрытой, без flash skeleton.
