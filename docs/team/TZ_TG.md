# ТЗ — фаза 1: Telegram (только бесплатно)

Версия: **0.1** · Lead · 2026-05-20

**Решение владельца:** без платного софта (Prime и т.д.) и **без триалов**. Только **Telethon** в этом репозитории + уже купленные `.session`.

---

## 1. Цель

Слушать **3–5 (потом больше) чатов** с мониторинговых аккаунтов Session+Json → новые посты → фильтр → [ИИ] → **пересылка оригинала** в личку (Telethon) + **разбор ботом** (Bot API, как биржи). Ссылки `t.me/c/…` / `tg://user` в уведомлении **не используем** — открывается пересланное сообщение.

Вступление в чаты — **скриптом** `tg_join` по [`../ops/TG_JOIN_LINKS.txt`](../ops/TG_JOIN_LINKS.txt) (MVP из [`../ops/TG_CHANNELS_BASE.md`](../ops/TG_CHANNELS_BASE.md)), не платным GUI.

---

## 2. Ограничения

| Нельзя | Можно |
|--------|--------|
| Платный софт, триалы | Telethon (MIT), Python |
| Вход с телефона на купленные номера | `.session` + прокси |
| Хранить секреты в Git | `.env`, `*.session` в `.gitignore` |
| Автоспам в ЛС | Только чтение чатов + уведомление владельцу |

---

## 3. Конфиг `.env` (Coder)

| Переменная | Обязательно | Смысл |
|------------|-------------|--------|
| `TELEGRAM_API_ID` | да | my.telegram.org |
| `TELEGRAM_API_HASH` | да | |
| `TELETHON_PROXY_URL` | да | SOCKS5/HTTP; без прокси — **не старт** |
| `TELETHON_SESSION_PATH` | да | Путь без `.session`; позже список сессий |
| `TELETHON_CHAT_IDS` или файл | да | id чатов для listen (из SOURCES_POOLS) |
| `NIGHT_*` / Irkutsk | да | 02:00–07:00 — длинные паузы |

Бот для уведомлений — существующие `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TG_PROXY_URL`.

---

## 4. Модули (Coder)

| Модуль | Задача |
|--------|--------|
| `src/tg_client.py` | Telethon + прокси, connect, FloodWait |
| `scripts/tg_join.py` | Вступить по invite-ссылкам из файла/argv |
| `scripts/tg_list_dialogs.py` | Показать чаты и id (для заполнения SOURCES_POOLS) |
| `src/tg_monitor.py` | NewMessage → pipeline (filter → ai → notify) |
| `main.py` или отдельный `tg_main.py` | Режим: только TG / FL+TG |
| Supabase | Лиды + дедуп (не txt); миграция схемы |

**Фаза 1 MVP:** один `.session`, 3 чата, join-скрипт, монитор, ночь, Supabase минимум (lead row).

---

## 5. Владелец (до приёмки)

1. `TELEGRAM_API_ID` / `HASH` в `.env`.
2. Ссылки на чаты (invite) — список для `tg_join`.
3. Запуск: `python scripts/tg_join.py` → `python scripts/tg_list_dialogs.py` → вписать id в конфиг.
4. Запуск монитора (команда в `ops/RUN.md` после Coder).

---

## 6. Приёмка

- [x] `tg_join` вступает в тест-чат без SMS.
- [ ] Новый пост в чате → сообщение в бот владельцу ≤ 2 мин (днём) — **проверяет владелец**.
- [x] Ночью интервал выше дневного (reconnect 30s / 300s в `tg_main`).
- [x] Без прокси — понятная ошибка, exit 1.
- [ ] Дубль поста не шлётся дважды — **проверяет владелец** при живом `tg_main`.

---

## 7. Позже (не MVP)

- 3 сессии параллельно; WordPress; аналитика.

См. [`PRODUCT_VISION.md`](PRODUCT_VISION.md).
