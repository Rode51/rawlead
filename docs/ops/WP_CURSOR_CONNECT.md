# WordPress + Cursor (как «подключить» агента)

Радар **не** ходит в WP на этом шаге. Цель — чтобы **Cursor видел файлы сайта** и тексты из репо.

Скелет страниц: [`WP_LOCAL_SKELETON.md`](WP_LOCAL_SKELETON.md) §3 · тексты: [`../archive/wp-skeleton/`](../archive/wp-skeleton/).

---

## 1. Local уже стоит?

Если нет — [`WP_LOCAL_SKELETON.md`](WP_LOCAL_SKELETON.md) §1. **Твой сайт:** `radarzakaz` → `http://radarzakaz.local`

§2 у тебя ✅ — дальше §3 (страницы) и плагин ниже.

---

## 2. Добавить сайт в workspace Cursor

1. В **Local** → сайт → **Go to site folder** / «Папка сайта».
2. Обычный путь на Windows:
   - `C:\Users\<ты>\Local Sites\<имя-сайта>\app\public`
3. Cursor → **File → Add Folder to Workspace…** → выбери **`app\public`** (корень WordPress, где `wp-config.php`).

В чате можно писать: `@public/wp-content/...` и `@docs/archive/wp-skeleton/home.md`.

---

## 3. Плагин из репо (копия в Local)

В репозитории: [`wordpress/rawlead-landing/`](../../wordpress/rawlead-landing/).

Автоустановка (рекомендуется):

```powershell
.venv\Scripts\python.exe scripts\wp_skeleton_setup.py
```

Скрипт копирует плагин в `Local Sites\radarzakaz\...` и активирует через WP-CLI, если Local **запущен**.

WP Admin → **Плагины** → **RawLead Landing** → Активировать (создаёт 5 страниц + меню).

Плагин только подсказывает slug страниц и не трогает радар. Правки PHP — в репо, потом снова копируй или настрой symlink (опционально).

---

## 4. §3 — пять страниц

| Slug | Файл с текстом |
|------|----------------|
| `home` | [`../archive/wp-skeleton/home.md`](../archive/wp-skeleton/home.md) |
| `how` | [`../archive/wp-skeleton/how.md`](../archive/wp-skeleton/how.md) |
| `pricing` | [`../archive/wp-skeleton/pricing.md`](../archive/wp-skeleton/pricing.md) |
| `faq` | [`../archive/wp-skeleton/faq.md`](../archive/wp-skeleton/faq.md) |
| `contact` | [`../archive/wp-skeleton/contact.md`](../archive/wp-skeleton/contact.md) |

В чате: *«Собери блоки Gutenberg для home из wp-skeleton»* — вставишь в редактор.

Меню: Главная · Как работает · Тарифы · FAQ · Контакты.

---

## 5. REST (позже, не сейчас)

Когда понадобится API (фаза 3, [`TZ_WP.md`](../team/architect/TZ_WP.md)):

1. WP Admin → **Пользователи** → профиль → **Пароли приложений** → новый пароль.
2. В `.env` (не в Git):

```env
# WP_LOCAL_SITE_URL=http://fl-radar-demo.local
# WP_APP_USER=admin
# WP_APP_PASSWORD=xxxx xxxx xxxx
```

Проверка в браузере: `{URL}/wp-json/wp/v2/pages?per_page=1`

Код `src/` для WP — задача **@coder** по `TZ_WP.md`, не на шаге скелета.

---

## 6. Live dev O118 (CSS в реальном времени)

**Junction** (репо = Local, правки в Cursor сразу на сайте):

```powershell
cd C:\Users\hramo\uisness
.venv\Scripts\python.exe scripts\wp_link_theme_local.py --force
```

**BrowserSync** (прокси + inject CSS без F5):

```powershell
cd wordpress\rawlead-kadence-child
npm install   # один раз
npm run dev   # http://localhost:3000 → radarzakaz.local
```

Local: **radarzakaz** → Start. Браузер слева, Cursor справа. Деплой: `scripts/deploy-wp-theme-vps.py`.

Skill: [`.cursor/skills/rawlead-wp-live-dev/SKILL.md`](../../.cursor/skills/rawlead-wp-live-dev/SKILL.md)

---

## 7. Готово, когда

- [ ] Папка `app\public` в workspace Cursor.
- [ ] Плагин `rawlead-landing` активен.
- [ ] 5 страниц из меню открываются.
- [ ] Lead: «WP скелет локально готов».
