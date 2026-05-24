# WordPress: Kadence + RawLead child theme

Референс: [`../design/wp/REFERENCE.md`](../design/wp/REFERENCE.md)  
Child theme в репо: [`../../wordpress/rawlead-kadence-child/`](../../wordpress/rawlead-kadence-child/)

**Local сайт:** `C:\Users\hramo\Local Sites\radarzakaz\app\public` · URL: `http://radarzakaz.local`

---

## 1. Запусти Local

1. Открой **Local**.
2. Сайт **radarzakaz** → **Start** (зелёный статус).
3. Открой `http://radarzakaz.local` — должен открыться WP (не ошибка БД).

---

## 2. Плагин страниц (если ещё нет)

1. В репо:  
   ` .venv\Scripts\python.exe scripts\wp_skeleton_setup.py `
2. Или WP Admin → **Плагины** → активируй **RawLead Landing** (папка из `wordpress/rawlead-landing/`).
3. Проверь: **Страницы** — есть `home`, `how`, `pricing`, `faq`, `contact`; **Настройки → Чтение** — статическая главная «Главная».

---

## 3. Установи Kadence (родитель)

**Вариант A — скрипт (рекомендуется):**

```powershell
cd C:\Users\hramo\uisness
.venv\Scripts\python.exe scripts\wp_install_rawlead_theme.py
```

Скрипт: копирует child, ставит Kadence (`wp theme install` или скачивание zip, если у PHP нет SSL), активирует **RawLead Kadence Child**, назначает меню.

**Вариант B — вручную в админке:**

1. **Внешний вид → Темы → Добавить**.
2. Найди **Kadence** → **Установить** → **Активировать** (временно).
3. Скопируй папку `wordpress/rawlead-kadence-child` в  
   `...\radarzakaz\app\public\wp-content\themes\`.
4. **Внешний вид → Темы** → **RawLead Kadence Child** → **Активировать**.

---

## 4. Меню RawLead

1. **Внешний вид → Меню** (или Customize → Header → Navigation).
2. Меню **RawLead** должно содержать 5 страниц.
3. Назначь в расположение **Primary** / **Primary Navigation** (Kadence).
4. Сохрани.

---

## 5. Проверка главной

Открой `http://radarzakaz.local/`:

| Элемент | Ожидание |
|---------|----------|
| Фон | Белый, не дефолтный блог Twenty Twenty-Five |
| Hero | H1 «Лиды без шума», справа графика «поток», кнопки тарифы / как работает |
| Скролл | Lenis (плавная инерция, без snap); полоса прогресса; секции плавно появляются |
| Шрифты | Unbounded (заголовки) + Manrope (текст) |
| Внутренние | how / pricing / faq / contact — тот же header/footer и стиль, что главная |
| Поток | FL.ru · Kwork · Telegram → карточка лида 88% |
| Полоса | Тёмная цитата про «карточку в телефоне» |
| 01–02–03 | Три колонки с крупными цифрами |
| Тарифы | 3 колонки, средняя «Популярный» |
| Footer | Тёмный, ссылка Telegram @rcnn43 |

---

## 6. Внутренние страницы

Открой из меню **Как работает**, **Тарифы**, **FAQ**, **Контакты**:

- Шрифт **Inter**, те же pill-кнопки.
- Контакты: кнопка **Telegram @rcnn43**.
- Тарифы: три блока-карточки (из HTML плагина).

---

## 7. Mobile

1. DevTools → ширина **375px**.
2. Блок «поток»: источники и карточка лида **столбиком**, стрелка повёрнута вниз.

---

## 8. Если child не активируется

| Симптом | Действие |
|---------|----------|
| «Отсутствует родительская тема kadence» | Установи Kadence (шаг 3) |
| Белый экран | Local → logs; отключи последний плагин |
| Старая тема design-studio | Активируй RawLead Kadence Child |
| Меню пустое | Переактивируй RawLead Landing |

---

## 9. Редактирование

- Главная: правки в `wordpress/rawlead-kadence-child/template-parts/rawlead/` → снова `wp_install_rawlead_theme.py`.
- Тексты страниц how/pricing/…: `docs/archive/wp-skeleton/*.md` → `wp_skeleton_setup.py`

---

## 10. Не на этом шаге

- Оплата, WooCommerce, Neon, радар API.
- PNG Recraft как фон всей страницы.

---

_Инструкция для владельца · Coder 2026-05-23_
