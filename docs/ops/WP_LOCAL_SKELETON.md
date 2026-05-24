# WordPress локально — скелет сайта (без хостинга)

Для **обучения WP** и черновика будущего SaaS. Радар на ПК **не требует** этого шага.

Видение продукта: [`../team/product/PRODUCT_VISION.md`](../team/product/PRODUCT_VISION.md).  
Тексты страниц: [`../archive/wp-skeleton/`](../archive/wp-skeleton/).

---

## 1. Установка (Windows, ~20 мин)

1. Скачай **[Local](https://localwp.com/)** (бесплатно).+
2. **+ Create a new site**
   - Name: `fl-radar-demo` (или любое)
   - Environment: **Preferred** (PHP 8.x)
   - Username/password admin — запиши в блокнот (не в Git).+
3. **Open site** → **WP Admin** (`/wp-admin`).
4. Язык: **Русский** (Настройки → Общие), если нужно.

Сайт откроется как `http://fl-radar-demo.local` (URL покажет Local).

---

## 2. Базовая настройка ✅ (владелец 2026-05-23)

| Шаг | Где в WP |
|-----|----------|
| Постоянные ссылки | Настройки → Постоянные → **Название записи** → Сохранить |
| Главная — статическая | Настройки → Чтение → **Статическая страница** → Главная: «Главная» |
| Меню | Внешний вид → Редактор / Меню (зависит от темы) |

**Тема:** встроенная **Twenty Twenty-Four** или **Twenty Twenty-Five** — достаточно для скелета. Позже — Kadence / Astra (бесплатные).

**Следующий шаг:** [`WP_CURSOR_CONNECT.md`](WP_CURSOR_CONNECT.md) (папка WP в Cursor + плагин) → § 3 — пять страниц из [`../archive/wp-skeleton/`](../archive/wp-skeleton/).

---

## 3. Какие страницы создать

Создай **Страницы** (не записи):

| Slug | Название | Контент |
|------|----------|---------|
| `home` | Главная | [`../archive/wp-skeleton/home.md`](../archive/wp-skeleton/home.md) |
| `how` | Как работает | [`../archive/wp-skeleton/how.md`](../archive/wp-skeleton/how.md) |
| `pricing` | Тарифы | [`../archive/wp-skeleton/pricing.md`](../archive/wp-skeleton/pricing.md) |
| `faq` | Вопросы | [`../archive/wp-skeleton/faq.md`](../archive/wp-skeleton/faq.md) |
| `contact` | Контакты | [`../archive/wp-skeleton/contact.md`](../archive/wp-skeleton/contact.md) |

В редакторе: вставь текст из `.md` (заголовки → блоки «Заголовок», списки → «Маркированный список»).

**Меню:** Главная · Как работает · Тарифы · FAQ · Контакты.

---

## 4. Плагины (по желанию, после скелета)

| Плагин | Зачем |
|--------|--------|
| **Contact Form 7** | Форма «Оставить заявку» на Контактах |
| **Yoast SEO** или **Rank Math** | Заголовки/описания страниц |
| **LiteSpeed Cache** | Только когда выложишь на хост (на Local не обязательно) |

**Не ставь пока:** WooCommerce, MemberPress — до этапа подписок.

---

## 5. Оформление (утверждённый референс)

**Источник правды:** [`../design/wp/REFERENCE.md`](../design/wp/REFERENCE.md) · скрин: [`../design/wp/bold-editorial-saas-full-page-landing-page-ui-mock.png`](../design/wp/bold-editorial-saas-full-page-landing-page-ui-mock.png)

| Шаг | Действие |
|-----|----------|
| 1 | Тема **Kadence** или **Astra** (светлая) |
| 2 | Цвета/шрифт **Inter** из REFERENCE §2 |
| 3 | Главная по §3 REFERENCE: hero, поток FL/Kwork/TG → лид, тёмная полоса, 01–02–03, тарифы |
| 4 | Остальные страницы — тот же язык (§4 REFERENCE) |

Не вставлять PNG Recraft как целый сайт — только блоки Gutenberg. Пульт Tauri остаётся **тёмным** (другой продукт).

---

## 6. Что не делать на этом шаге

- Платный хостинг.
- Подключение к Neon / радару.
- Подписки и оплата.

Это **этап B** в [`PRODUCT_VISION.md`](../team/product/PRODUCT_VISION.md).

---

## 7. Готово, когда

- [ ] 5 страниц открываются из меню.
- [ ] Главная объясняет «радар для фрилансеров» за 10 секунд.
- [ ] Тарифы — 2–3 карточки (можно «скоро»).
- [ ] Контакты — форма или ссылка на Telegram.

Напиши Lead: «WP скелет локально готов» — добавим в ROADMAP / портфолио.

---

## 8. Проблемы

| Симптом | Решение |
|---------|---------|
| Local не стартует | Перезапуск от админа; выкл. другие Apache/MySQL |
| Белый экран | Local → Site folder → logs; отключить последний плагин |
| Медленно | Норма на первом запуске |

Инциденты радара — [`../problems/`](../problems/), не путать с WP.
