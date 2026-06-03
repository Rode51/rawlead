# O95 post-deploy: лента ⚙ · лимит 12 · sort · copy

**Дата:** 2026-06-02 · **Prod:** **1.16.4** · **Статус:** **✅ closed** (owner smoke OK)

**Owner smoke 2026-06-02 (повтор):** Save ⚙ → «0 навыков», нет match % · «Укажи навыки» на карточках.

---

## Симптомы (владелец)

| # | Симптом |
|---|---------|
| 1 | Hint «нажмите **Применить**», кнопка «**Сохранить**» |
| 2 | «Выбрано 12/12» + красный «Максимум 12» — при ровно 12 |
| 3 | Telethon в tray **дважды** (Telegram-боты + Парсинг) — путаница |
| 4 | L3 tray раздувается · плашки «скачут» при выборе |
| 5 | ⚙ на `/lenta/` → Сохранить → **0 навыков**, нет % совместимости |
| 6 | «по дате» клик — **ничего** (пока навыки только из ЛК — sort OK) |
| 7 | ⚙ на ленте ≠ ЛК · нет сквозной синхронизации |
| 8 | Тексты не объясняют anon/logged-in · кому платить |

---

## Корни (Lead, код)

| # | Корень | Файл |
|---|--------|------|
| 1 | Copy drift | `page-lenta.php` L108 · `rawlead-feed.js` L1266 |
| 2 | `skillTreeLimitEl.hidden = !atLimit` при `n >= 12` — баннер при **валидных** 12 | `rawlead-feed.js` ~1220 |
| 3 | `telethon` — L3 двух L1 (`telegram_bot_dev`, `web_scraping`) · tray рисует дубль | `skills_catalog.py` EXPAND · `renderFeedL3TrayHtml` |
| 4 | Tray без max-height · L1 row без min-height | `rawlead.css` §4.7 |
| 5 | Feed save: отдельный `persistTags` / tree vs cabinet `saveTags` · возможен silent fail / нет `updateCount` до reload | `rawlead-feed.js` · `rawlead-cabinet.js` |
| 6 | `setFeedSort('match')` блок при 0 tags · toggle «по дате»→match молча no-op | `rawlead-feed.js` ~997 |
| 7 | Два render skill-tree · нет shared module + cross-tab reload | feed + cabinet JS |
| 8 | PRE-LAUNCH-UX не обновлён под O95 | → @lead-product **O96-copy** |

---

## Acceptance O95-fix

| ID | Критерий |
|----|----------|
| AC-F1 | Hint = «…нажмите **Сохранить**» |
| AC-F2 | Красный лимит только при попытке **13-го**; при 12/12 — без ошибки |
| AC-F3 | Один chip `telethon` в tray (dedupe by tag) |
| AC-F4 | L1 row stable · tray `max-height` + scroll |
| AC-F5 | ⚙ lenta → Save → Neon → «N навыков» + match % на карточках |
| AC-F6 | Sort: 0 tags — только «по дате» (не кликабельно); с tags — toggle работает |
| AC-F7 | Save lenta ≡ save ЛК · reload tags на другой вкладке / `visibilitychange` |
| AC-F8 | Smoke: PUT tags с ленты → GET совпадает · feed `skills=` в запросе |

**Deploy:** bump **1.16.2**

---

## O95-fix-2 — owner smoke FAIL (2026-06-02)

**Симптом:** Save ⚙ · header «0 навыков» · карточки «Укажи навыки» · match % нет.

**Корень (Lead):**

| # | Проблема |
|---|----------|
| 1 | Logged-in лента грузит **`/rawlead/v1/feed`** (anon API), match только если JS `appliedTags` не пуст → **`/me/feed` не используется** |
| 2 | `loadTags`: при ошибке auth → `{tags:[]}` **молча** |
| 3 | O95-fix sync rev не гарантирует match, если feed endpoint не читает `user_tags` из Neon |

**Fix Coder:**

| # | Задача |
|---|--------|
| 1 | `functions.php`: `restMeFeed` → `/rawlead/v1/me/feed` |
| 2 | `loadMore`: if `isLoggedIn()` → **me/feed** (match из `user_tags` Neon) |
| 3 | `loadTags`: 401 → «войдите снова» / redirect cabinet; не маскировать пустым |
| 4 | `persistTags` success → `loadTags()` verify + `updateCount` |
| 5 | AC: Save с ленты → header N навыков + % на карточке; ЛК те же tags |

---

## O95-fix-3 — save после «Сбросить» (2026-06-02)

**Симптом:** Сбросить → выбрать навыки → Сохранить → окно закрывается мгновенно, «0 навыков», без загрузки.

**Корень:** после `persistTags([])` фоновый `loadTags()` **перезаписывал `draftTags`** в открытом модале → Save видел «не dirty» и просто закрывал. Плюс race: второй `persistTags` молча отбрасывался при `tagsLoading`.

**Fix:** `preserveDraft` в `loadTags` · очередь `tagsPersistQueue` · модал закрывается **после** успешного save · «Сбросить» всегда PUT `[]` в Neon.

**Deploy:** **1.16.3**

---

## O95-fix-4 — пустой профиль: лента + только «по дате» (2026-06-02)

**Ожидание владельца:** навыки сброшены → заказы **все равно видны**, sort **только по дате**.

**Корень:** `/me/feed` при пустых `user_tags` отфильтровывал все карточки (`keyword_match=0` → `_passes_min_match` false).

**Fix:** API — без профиля не фильтруем по match, force `sort=time` · JS — lock sort при 0 навыков.

**Deploy:** **1.16.4** (+ restart `rawlead-api`)

---

_Mechanic triage → Coder hotfix · Lead 2026-06-02_
