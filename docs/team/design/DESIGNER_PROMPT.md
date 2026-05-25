# Designer — активная задача

**Дата:** 2026-05-25 · от Lead Designer (согласовано с владельцем)  
**Спека:** [`docs/design/wp/feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) — главный документ  
**Токены:** [`DESIGN_SYSTEM.md`](DESIGN_SYSTEM.md) § WordPress v2  
**Анимации:** [`docs/design/wp/REFERENCE.md`](../../design/wp/REFERENCE.md) § 6  
**Роль:** [`DESIGNER.md`](DESIGNER.md)

---

## Задачи (приоритет сверху вниз)

### 1. Анимации на лендинге (главная страница)

Файл: `wordpress/rawlead-kadence-child/assets/css/rawlead.css` + inline `<script>` в footer или отдельный `assets/js/animations.js`

| Что | Где | Спека |
|-----|-----|-------|
| Scroll-reveal (fade + translateY) | все `.rl-reveal` секции | REFERENCE §6.1 |
| Stagger карточек | `.rl-flow`, `.rl-features`, `.audience` | REFERENCE §6.2 |
| Hover карточки (lift + shadow) | `.rl-lead-card`, `.rl-price-card` | REFERENCE §6.3 |
| Match-bar fill on scroll | `.rl-match__fill` | REFERENCE §6.4 |
| Micro-press кнопок | `.rl-btn` | REFERENCE §6.5 |
| Сборка кубиков источников | `.rl-flow__sources .rl-source-cube` | REFERENCE §6.6 |
| IntersectionObserver | один общий скрипт | REFERENCE §6.7 |

### 2. Исправить цвета источников

Файл: `wordpress/rawlead-kadence-child/assets/css/rawlead.css`

```css
/* БЫЛО */
--color-source-fl: #2563eb;
--color-source-tg: #0ea5e9;

/* СТАЛО */
--color-source-fl: #00A65A;   /* FL.ru бренд-зелёный */
--color-source-tg: #0088CC;   /* Telegram официальный */
```

### 3. Обновить тарифный блок (pricing)

Файл: `wordpress/rawlead-kadence-child/template-parts/rawlead/pricing-preview.php`

Убрать три карточки (Старт/Про/Команда). Поставить **одну карточку**:
- Название: **ИИ-агент**
- Цена: **от 300 ₽/мес**
- Список: Match по тегам · Рыночная цена · Черновик отклика · Push в TG
- Badge: «Скоро» (серый, правый верхний угол)
- CTA: «Ранний доступ» → `/contact`

### 4. Добавить «Лента» в навигацию

Файл: `wordpress/rawlead-kadence-child/template-parts/rawlead/header.php`

Пункт «Лента» → `/feed`, между «Главная» и «Как работает».  
CTA в шапке: текст «Попробовать →» вместо «Тарифы» / «Ранний доступ».

### 5. Пульт — пульсация лампы

Файл: `desktop/src/styles/pult.css`

Добавить keyframe `lamp-pulse` для `.lamp__dot--ok` — спека в [`feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) § 6.1.

---

## Не делать

- PHP-шаблоны `/feed` и `/cabinet` — это Coder (после 3b/3c API)
- Правки `src/`, `scripts/` — только пульт CSS
- Новые `.md` файлы — не нужны
- Логику JS (API-запросы, IntersectionObserver кроме анимаций) — Coder

---

## Сдача — ✅ принято Lead 2026-05-25

| § | В коде |
|---|--------|
| 1–5 | `rawlead.css`, `rawlead-scroll.js`, `flow.php`, `pricing-preview.php`, `header.php` |
| 6 | `pult.css` — `lamp-pulse` |

Handoff: [`DESIGN_BRIEF.md`](DESIGN_BRIEF.md) §195. Внедрение: Coder § W (по промпту Lead). **Designer-роль закрыта.**
