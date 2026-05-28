# Деплой бюджетный — сайт и радар без включённого ПК

**Решение владельца 2026-05-25:** не туннель с ПК, а **прод 24/7** при минимальных расходах.

Связано: [`ROADMAP.md`](../team/architect/ROADMAP.md) · [`TASKS.md`](../team/common/TASKS.md) · [`WP_OWNER_STEPS.md`](../archive/WP_OWNER_STEPS.md) · [`TZ_WP.md`](../team/architect/TZ_WP.md)

---

## Сколько денег в месяц (ориентир РФ)

| Что | ₽/мес | Комментарий |
|-----|-------|-------------|
| **WordPress shared** | 150–350 | Beget / Timeweb / Reg — тариф «WordPress», SSL в панели |
| **VPS минимальный** | 200–450 | 1 vCPU, 1 GB RAM, Ubuntu 22.04 — **API + радар** на одной машине |
| **Neon Postgres** | **0** | уже есть `DATABASE_URL` |
| **Домен .ru** | ~25–40/мес | или **0** — поддомен хостера `site.beget.tech` |
| **Прокси** | по факту | только если FL режет IP VPS; не ScraperAPI |
| **Итого** | **~350–800 ₽/мес** | без пульта в облаке |

**Не покупаем:** второй VPS, Supabase, managed Kubernetes, ScraperAPI, отдельный сервер под TG.

---

## Что где живёт (схема)

```
Посетитель → https://сайт.ru (WP на shared)
                 ↓ fetch
            https://api.сайт.ru (VPS: uvicorn)
                 ↓
            Neon (лиды, users)
                 ↑ ingest
            VPS: tg_main + цикл FL/Kwork (systemd)
                 ↓
            Telegram Bot → тебе карточки

ПК владельца: опционально пульт Tauri (мониторинг), не обязателен 24/7
```

| Компонент | Где | ПК нужен? |
|-----------|-----|-----------|
| Лендинг, `/lenta/`, `/cabinet/` | Shared WP | нет |
| `api_server` | VPS | нет |
| Радар `tg_main` + FL/Kwork | **тот же VPS** | нет |
| База лидов | Neon | нет |
| Пульт Tauri | только у тебя | да, если смотришь статус |

---

## Покупки (владелец)

### 1. Shared-хостинг WP

- Тариф с PHP 8.2+, MySQL, Let's Encrypt.
- Установить WordPress, записать: `https://ТВОЙ-САЙТ.ru`, логин админки.

### 2. VPS (один на всё backend)

Минимум: **1 GB RAM**, Ubuntu 22.04, регион EU (ближе к Neon).

Примеры (сравни акции): Timeweb VPS Start, Beget VPS, Aeza/FirstVDS низкий тариф.

**Не брать** Windows VPS — дороже и лишнее.

### 3. DNS (бесплатно через хостера)

| Запись | Куда |
|--------|------|
| `@` или `www` | IP/shared WP (как в панели хостинга) |
| `api` | **A** → IP VPS |

Если домена нет: сайт на `xxx.beget.tech`, API на `api.xxx.beget.tech` или отдельный бесплатный поддомен у VPS-провайдера.

---

## Что делает @coder (§ P5)

| # | Артефакт |
|---|----------|
| 1 | `deploy/systemd/rawlead-api.service` — uvicorn `src.api_server:app` :18766 |
| 2 | `deploy/systemd/rawlead-radar.service` — `python scripts/tg_main.py` (или единый entry) |
| 3 | `deploy/Caddyfile` или nginx: `api.домен` → localhost:18766, авто-HTTPS |
| 4 | `docs/ops/DEPLOY_VPS.md` — пошагово: git clone, venv, `.env`, `systemctl enable --now` |
| 5 | Перенос Telethon: какие файлы из `data/` на VPS (сессии acc1–3) — **без** коммита в git |
| 6 | WP: опция `rawlead_api_base_url` = `https://api.домен` + CORS |

**Секреты:** только `.env` на VPS (scp), в git — `.env.example`.

---

## ПК после миграции

| Было | Станет |
|------|--------|
| `start-radar-desktop` / пульт ▶ | **выключить** автозапуск радара на ПК (дубли с VPS убьют TG) |
| Пульт Tauri | только смотреть статус, если Coder добавит `GET /health` / опционально SSH-туннель — не обязательно |
| Local `radarzakaz.local` | оставить для вёрстки |

---

## Этапы (чтобы не сломать за один раз)

| Этап | Результат |
|------|-----------|
| **E1** | VPS: только API + Neon → WP на хостинге, лента живая, радар ещё на ПК |
| **E2** | VPS: перенести радар + сессии TG, остановить радар на ПК |
| **E3** | P1 whitelist, P4 TG-login, P6 публичный git |

Сегодня цель: **минимум E1+E2**, чтобы с выключенным ПК работали сайт + новые лиды в бот.

---

## Риски бюджетного VPS

| Риск | Что делать |
|------|------------|
| FL банит IP дата-центра | прокси-пул § P2, не чаще 2 мин без нужды |
| 1 GB RAM мало | swap 1G; не поднимать desktop на VPS |
| Два радара (ПК + VPS) | после E2 — только VPS |

---

## Чеклист «ПК выключен — всё ок»

1. `https://сайт.ru/lenta/` — карточки грузятся  
2. `https://api.сайт.ru/health` — `{"status":"ok"}`  
3. Через 15–30 мин в боте — новый лид (если радар на VPS)  
4. `systemctl status rawlead-radar` на VPS — active  

---

_Lead · 2026-05-25 · бюджетный прод без ПК_
