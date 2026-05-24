# WordPress-пульт — шаги для тебя

ТЗ для Coder: [`../team/architect/TZ_WP.md`](../team/architect/TZ_WP.md)

---

## Сколько денег

| Что | Цена |
|-----|------|
| **Supabase** | 0 ₽ (Free) |
| **Хостинг WP** | ~150–350 ₽/мес (акции «1 ₽ первый месяц» бывают) |
| **Домен .ru** | ~200–500 ₽/год **или 0 ₽** — поддомен хостера |
| **VPS** | **не нужен** на старте (радар на ПК) |

**Дешевле всего:** поддомен хостера + тариф «WordPress»/«Start» + Supabase Free.

---

## Шаг 1. База данных (облако или без него)

### A. **Neon** (вместо Supabase — рекомендуем)

**Лимит Supabase:** 2 проекта на аккаунт — у тебя уже занято. Neon — отдельный сервис, **0 ₽** на старт.

1. [console.neon.tech](https://console.neon.tech) → Sign up (Google/GitHub).
2. **Create project** → имя `fl-radar`, регион **EU** (ближе к РФ).
3. Dashboard → **Connection details** → вкладка **Python** или **Connection string**.
4. Скопируй строку вида:
   `postgresql://user:password@ep-….neon.tech/neondb?sslmode=require`
5. В `.env` проекта радара:
   ```
   DATABASE_URL=postgresql://…
   ```
   (одна строка, без кавычек; пароль со спецсимволами — Coder подскажет URL-encode при ошибке)
6. **Cursor + Neon (как Supabase MCP):** в корне проекта `npx neonctl@latest init` → перезапуск Cursor. Подробно: [`NEON_CURSOR.md`](NEON_CURSOR.md).
7. Напиши Lead/Coder: **«Neon готов»** (строку в чат **не** кидай).

**Как Supabase?** Для **радара (Python)** — да, та же роль: лиды и настройки в Postgres.  
Для **WordPress на shared-хостинге** — не REST «из коробки»; WP подключим через **маленький API** на ПК или позже VPS (Coder в `TZ_WP.md`).

### B. Совсем без облака (0 ₽)

Пульт WP **откладываем** или только витрина на хостинге. Лиды остаются в **SQLite на ПК** (`data/projects.db`) — радар уже так работает. Coder: расширить таблицы локально.

### C. Supabase снова доступен

Если проект на паузе — в dashboard **Restore** / новый проект на Free. Лимиты: [supabase.com/pricing](https://supabase.com/pricing).

---

## Шаг 2. Хостинг (сравни 2–3)

Искать: **«хостинг WordPress»**, тариф **Start / Блог / WordPress**.

| Провайдер (примеры РФ) | На что смотреть |
|------------------------|----------------|
| [Beget](https://beget.com) | Часто WP в 1 клик, акции |
| [Timeweb](https://timeweb.com) | То же |
| [Reg.ru](https://www.reg.ru) | Хостинг + домен пакетом |
| [Sprinthost](https://sprinthost.ru) | Недорогой старт |

**Минимум в тарифе:** PHP 8, MySQL, SSL Let's Encrypt, ≥1 ГБ.

**Не покупать пока:** VPS, «конструктор сайтов» вместо WP.

---

## Шаг 3. Установить WordPress

1. В панели хостинга → **Установить WordPress** на поддомен или домен.
2. Логин админа + **длинный пароль** (менеджер паролей).
3. Язык: русский.
4. Запиши **URL сайта**: `https://....`

---

## Шаг 4. Написать Lead

```
WP стоит: https://твой-url
Supabase: готов (ключи не в чат)
В MVP важно: лиды + вкл/выкл FL/Kwork
Домен: свой / поддомен хостера
```

---

## Шаг 5. Пока Coder не сделал плагин

- Радар по-прежнему: `python src/main.py` на ПК.
- Настройки — `docs/ops/FILTERS.md`, `.env`.
- Пульт в браузере появится после Coder.

---

## Параллельно (не отменяется)

- Список TG-чатов (Deep Research).
- Повторять [my.telegram.org/apps](https://my.telegram.org/apps) для API_ID.

---

_Вопросы по оплате хостинга — к Lead, не в общий чат с ключами._
