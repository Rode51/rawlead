# Деплой на VPS — один сервер (WP + API + радар)

**Решение владельца 2026-05-28:** один VPS, домен **rawlead.ru**.

| Компонент | URL / порт |
|-----------|------------|
| WordPress | `https://rawlead.ru` — nginx :80/:443 |
| FastAPI (внутри) | `127.0.0.1:8000` — uvicorn, **не** открывать :8000 наружу |
| API наружу | `https://api.rawlead.ru` — nginx → :8000 |
| CORS | `https://rawlead.ru` (`RADAR_CORS_ORIGINS`) |

**IP, SSH, пароли, `.env`** — только у владельца в чате, **не в git**.

### Автодеплой E1 с ПК (Windows)

**Вариант A — пароль root (проще на Beget):** в `.env` (локально, не в git):

```env
VPS_SSH_HOST=62.113.103.231
VPS_SSH_USER=root
VPS_SSH_PASSWORD=пароль_из_письма_Beget
VPS_SSH_KEY=C:/Users/hramo/.ssh/id_rawlead_vps
```

Затем: `.venv\Scripts\pip install paramiko` и `.venv\Scripts\python scripts\deploy-vps-e1.py`

**Вариант B — SSH-ключ:** в панели Beget → Облако → терминал → `authorized_keys` (см. выше в чате) или ключ при создании VPS.

1. В `.env`: `VPS_SSH_HOST`, `VPS_SSH_USER`, `VPS_SSH_KEY`.
2. `scripts\deploy-vps-e1.py` — apt, clone, env, `rawlead-api`, nginx.

Связано: [`DEPLOY_BUDGET.md`](DEPLOY_BUDGET.md) · [`TELEGRAM_ACCOUNTS.md`](TELEGRAM_ACCOUNTS.md) · [`RUN.md`](RUN.md)

---

## Схема

```text
Посетитель → https://rawlead.ru (WP + тема rawlead-kadence-child)
                 ↓ wp_remote_get (127.0.0.1:8000 или api.rawlead.ru)
            FastAPI :8000 (systemd rawlead-api)
                 ↓
            Neon Postgres
                 ↑ ingest
            main.py + tg_main.py (systemd rawlead-radar, profile site)

ПК владельца (E2): Site ▶ и Legacy ▶ **выключить** — иначе дубли TG-сессий

E2b (решение владельца 2026-05-28): **dogfood на VPS** — `neon_legacy_consumer` + управление **@FLPARSINGBOT** (/status, /pause, кнопки). Site — отдельный unit + @rawlead_bot.
```

---

## 0. Подготовка VPS (Ubuntu 22.04+, 1 GB RAM)

```bash
sudo apt update && sudo apt install -y git python3 python3-venv python3-pip nginx certbot python3-certbot-nginx
sudo fallocate -l 1G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
sudo adduser --disabled-password --gecos "" rawlead
sudo usermod -aG www-data rawlead
```

DNS (у регистратора):

| Запись | Значение |
|--------|----------|
| `@` / `www` | A → IP VPS |
| `api` | A → IP VPS |

---

## 1. Клон и venv

```bash
sudo mkdir -p /opt/rawlead && sudo chown rawlead:rawlead /opt/rawlead
sudo -u rawlead git clone <URL_ПРИВАТНОГО_REPO> /opt/rawlead
cd /opt/rawlead
sudo -u rawlead python3 -m venv .venv
sudo -u rawlead .venv/bin/pip install -r requirements.txt
sudo -u rawlead .venv/bin/playwright install chromium
chmod +x deploy/run-radar-site.sh deploy/run-radar-legacy.sh
```

---

## 2. Секреты (scp с ПК, не коммитить)

Скопировать на VPS в `/opt/rawlead/`:

| Файл | Откуда |
|------|--------|
| `.env` | общие ключи: `DATABASE_URL`, Telethon, FL/Kwork, прокси |
| `.env.site` | `@rawlead_bot`, OpenRouter site, `RADAR_PROFILE=site` |
| `.env.legacy` | `@FLPARSINGBOT`, OpenRouter legacy, `RADAR_PROFILE=legacy` (E2b) |

**Прод `.env.site` (минимум):**

```env
RADAR_PROFILE=site
RADAR_CORS_ORIGINS=https://rawlead.ru
SITE_NOTIFY_OWNER=0
RADAR_EXCHANGES_ENABLED=1
RADAR_TG_ENABLED=1
```

Права: `chmod 600 .env .env.site .env.legacy`

### Карта прокси (5 IP, 2026-06-01)

**Решение владельца:** один пул оплаченных HTTP-прокси; часть закреплена за Telethon/Bot API, остальные — **ротация FL/Kwork** каждый цикл (~1 мин) + **failover** при 403/429/timeout (§ O79 Coder).

| IP | Роль | Переменные |
|----|------|------------|
| 45.152.197.25 | Bot API + acc1 | `TG_PROXY_URL`, `TELETHON_PROXY_ACC1` |
| 38.154.16.60 | acc2 + биржи (pool) | `TELETHON_PROXY_ACC2` · `FL_PROXY_URLS`, `KWORK_PROXY_URLS` |
| 168.90.199.99 | acc3 + биржи (pool) | `TELETHON_PROXY_ACC3` · `FL_PROXY_URLS`, `KWORK_PROXY_URLS` |
| 212.102.151.153 | биржи (pool) | `FL_PROXY_URLS`, `KWORK_PROXY_URLS` |
| 185.147.131.15 | биржи (pool) | то же |

**45.152 не класть в `FL_PROXY_URLS`** — там же Bot API и acc1.

### Страховка 2026-06-02 (O91)

| Рекомендация | Деталь |
|--------------|--------|
| **Докупить** | **+3–4** IPv4 HTTP **только** для `FL_PROXY_URLS` / `KWORK_PROXY_URLS` |
| **Страны** | RU ×2 · KZ или BY ×1 · DE/FI ×1 (fallback) |
| **Итого pool** | **7–8** IP (4 старых + 3–4 новых) |
| **Не нужно** | второй VPS-парсер · US-only pool |
| **Опц.** | 1× residential RU при постоянном 403 на FL |

После дописки env: `sudo systemctl restart rawlead-radar` · в логе `fetch:fl proxy=host:port` и (после O91) `exchange_proxy:alive=N/M`.

Пример **`.env` на VPS** (логины/пароли — из вашего блокнота, **не в git**):

```env
TG_PROXY_URL=http://45.152.197.25:8000:USER:PASS
TELETHON_PROXY_ACC1=http://45.152.197.25:8000:USER:PASS
TELETHON_PROXY_ACC2=http://38.154.16.60:8000:USER:PASS
TELETHON_PROXY_ACC3=http://168.90.199.99:8000:USER:PASS
FL_PROXY_URLS=http://212.102.151.153:8000:U:P,http://185.147.131.15:8000:U:P,http://38.154.16.60:8000:U:P,http://168.90.199.99:8000:U:P
KWORK_PROXY_URLS=http://212.102.151.153:8000:U:P,http://185.147.131.15:8000:U:P,http://38.154.16.60:8000:U:P,http://168.90.199.99:8000:U:P
TELETHON_PROXY_PROBE=1
```

После правки: `sudo systemctl restart rawlead-radar` · в `radar_site.log` — `fetch:fl proxy=212.102…` (host без пароля).

**ПК / Cursor:** те же `TG_*` / `TELETHON_*` в локальном `.env`; `FL_PROXY_URLS` на ПК **не нужны**, если Site ■ (парсинг только VPS).

---

С ПК скопировать **без git**:

```bash
scp user@pc:/path/to/+66953964608_telethon.session rawlead@vps:/opt/rawlead/data/sessions/
scp user@pc:/path/to/+66967716330_telethon.session rawlead@vps:/opt/rawlead/data/sessions/
# acc3/acc4 по docs/ops/TELEGRAM_ACCOUNTS.md
```

В `.env` на VPS — **Linux-пути**:

```env
TELETHON_SESSION_ACC1=/opt/rawlead/data/sessions/+66953964608_telethon
TELETHON_PROXY_ACC1=http://host:port:user:pass
TELETHON_SESSION_ACC2=/opt/rawlead/data/sessions/+66967716330_telethon
```

Также при необходимости: `data/projects.db`, `data/tg_join_state.json`, `data/telethon_chat_ids.txt`.

---

## 3. systemd

```bash
sudo cp /opt/rawlead/deploy/systemd/rawlead-api.service /etc/systemd/system/
sudo cp /opt/rawlead/deploy/systemd/rawlead-radar.service /etc/systemd/system/
sudo cp /opt/rawlead/deploy/systemd/rawlead-radar-legacy.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### E1 — только API (радар ещё на ПК)

```bash
sudo systemctl enable --now rawlead-api
sudo systemctl status rawlead-api
curl -s http://127.0.0.1:8000/health
```

`rawlead-radar` **не** включать — Site ▶ на ПК качает биржи в Neon.

### E2 — радар на VPS

1. На ПК: **остановить** Site (`stop-radar-desktop-full.bat` или пульт ■).
2. На VPS:

```bash
sudo systemctl enable --now rawlead-radar
sudo systemctl status rawlead-radar
tail -f /opt/rawlead/data/radar_site.log
```

**Важно:** два радара (ПК + VPS) = дубли TG и бан acc. После E2 — только VPS.

### E2b — Legacy dogfood на VPS (@FLPARSINGBOT)

**Уже в коде:** `neon_legacy_consumer.py` крутит `poll_commands` → `/status`, `/pause`, `/стоп`, кнопки панели; карточки из Neon → твой чат. **Не** парсит биржи (это Site `main`).

1. На VPS: `.env.legacy` (бот FLPARSING, `FILTERS_LEGACY`, свой OpenRouter, `RADAR_LOG_PATH=data/radar_legacy.log`).
2. `systemctl enable --now rawlead-radar-legacy` (unit: `deploy/systemd/rawlead-radar-legacy.service`, runner: `deploy/run-radar-legacy.sh`).
3. На ПК: **не** ▶ Legacy, **не** ▶ Site — `scripts\stop-radar-desktop-full.vbs`.

**Прод `.env.legacy` (минимум, без Telethon):**

```env
RADAR_PROFILE=legacy
RADAR_EXCHANGES_ENABLED=0
RADAR_TG_ENABLED=0
RADAR_LOG_PATH=data/radar_legacy.log
TELEGRAM_BOT_TOKEN=...FLPARSING...
TELEGRAM_CHAT_ID=...
TG_PROXY_URL=http://host:port:user:pass
AI_API_KEY=...legacy_openrouter...
FILTERS_MD_PATH=docs/ops/FILTERS_LEGACY.md
AI_MODE=legacy
POLL_INTERVAL_MINUTES=10
# Опционально: отдельный SQLite (иначе пауза раздельная по ключам radar_paused_legacy / radar_paused_site)
# SQLITE_PATH=data/projects_legacy.db
```

**Telethon на VPS — только для Site** (`rawlead-radar`). Legacy unit **не** нуждается в acc-сессиях, только Bot API.

| Unit | Процессы | Бот управления |
|------|----------|----------------|
| `rawlead-radar` | `main.py` + `tg_main.py` | @rawlead_bot (опц.) |
| `rawlead-radar-legacy` | `neon_legacy_consumer.py` | **@FLPARSINGBOT** — стоп/старт/статус |

**Пауза раздельно (e4):** `/pause` в @FLPARSINGBOT пишет `radar_paused_legacy`; Site читает `radar_paused_site` — общий ingest **не** гасится. Старый ключ `radar_paused` сбрасывается при первом /pause|/старт после обновления.

**E2 полный деплой (Site + Legacy на VPS):**

```bash
sudo systemctl enable --now rawlead-radar rawlead-radar-legacy
sudo systemctl status rawlead-radar rawlead-radar-legacy
tail -f /opt/rawlead/data/radar_site.log
tail -f /opt/rawlead/data/radar_legacy.log
```

---

## 4. nginx — API

```bash
sudo ln -sf /opt/rawlead/deploy/nginx/api.rawlead.ru.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d api.rawlead.ru
curl -s https://api.rawlead.ru/health
```

Альтернатива: [`deploy/Caddyfile`](../deploy/Caddyfile) (если API отдаёт Caddy, не nginx).

`:8000` снаружи **не** открывать в firewall — только 80/443.

---

## 5. WordPress + тема

WP на **том же VPS** (nginx vhost `rawlead.ru` — настраивает владелец / панель).

### wp-config.php

```php
define('RAWLEAD_API_URL', 'http://127.0.0.1:8000');
define('RAWLEAD_TG_BOT_USERNAME', 'rawlead_bot');
define('RAWLEAD_TG_BOT_ID', '8989158953'); // @rawlead_bot — OAuth fallback / Login Widget
```

WP на том же хосте — лучше `127.0.0.1:8000` (без лишнего TLS). Браузер ходит в WP REST same-origin; CORS нужен для `/docs` и отладки.

### Тема

```bash
cd /opt/rawlead
sudo rsync -a wordpress/rawlead-kadence-child/ /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/
# Kadence parent — через WP Admin → Themes → Install
sudo -u www-data wp theme activate rawlead-kadence-child --path=/var/www/rawlead.ru
```

Страницы `/lenta/`, `/cabinet/` — по [`TZ_WP.md`](../team/architect/TZ_WP.md).

### 5b. HTTPS — убрать «Не защищено» (**O18**)

Сайт на **http://** — браузер показывает красное «Не защищено». Нужен **Let's Encrypt** (certbot) на nginx.

**Условие:** DNS `rawlead.ru`, `www.rawlead.ru`, `api.rawlead.ru` → IP VPS (порт **443** открыт).

На VPS (SSH root):

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d rawlead.ru -d www.rawlead.ru -d api.rawlead.ru --redirect
sudo -u www-data wp option update siteurl 'https://rawlead.ru' --path=/var/www/rawlead.ru --allow-root
sudo -u www-data wp option update home 'https://rawlead.ru' --path=/var/www/rawlead.ru --allow-root
sudo nginx -t && sudo systemctl reload nginx
```

**Проверка:** `https://rawlead.ru/lenta/` — замок в адресной строке, без «Не защищено».

**Авто с ПК:** `python scripts/install-wp-vps.py` — certbot в конце, если DNS уже на VPS.

**После HTTPS:** BotFather `/setdomain` → `rawlead.ru` (Login Widget); в `.env.site` на VPS: `RADAR_CORS_ORIGINS=https://rawlead.ru`.

---

## 6. Приёмка (E1 + E2)

| # | Проверка | Ожидание |
|---|----------|----------|
| 1 | `https://api.rawlead.ru/health` | `{"status":"ok"}` |
| 2 | `https://rawlead.ru/lenta/` | карточки заказов |
| 3 | E2: ПК выключен, 30 мин | новый лид в Neon / боте |
| 4 | `systemctl status rawlead-api rawlead-radar` | active |
| 5 | `radar_site.log` | циклы FL/Kwork, `site:сводка` |
| 6 | E2b: `rawlead-radar-legacy` active | `radar_legacy.log` · `/status` в @FLPARSINGBOT отвечает |
| 7 | E2b: `/pause` в @FLPARSINGBOT | Site ingest продолжается (`radar_site.log` без `neon:пауза`-тишины на биржах) |

**Стоп-трафик:** пустая лента · API 5xx · CORS блок · два радара одновременно.

---

## 7. Обновление кода

```bash
cd /opt/rawlead
sudo -u rawlead git pull
sudo -u rawlead .venv/bin/pip install -r requirements.txt
sudo systemctl restart rawlead-api
sudo systemctl restart rawlead-radar   # только если E2
sudo systemctl restart rawlead-radar-legacy   # только если E2b
sudo rsync -a wordpress/rawlead-kadence-child/ /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/
```

---

## 8. ПК после E2

| Действие | Зачем |
|----------|-------|
| Не запускать Site ▶ 24/7 | дубли ingest + TG |
| **Не** ▶ Site / Legacy на ПК | только VPS systemd |
| @FLPARSINGBOT | стоп/статус/карточки dogfood (E2b) |
| @rawlead_bot poll | **только VPS** — иначе Bot API **409 Conflict** (два getUpdates на один токен) |
| Пульт Tauri | не нужен 24/7; опц. SSH + `journalctl` |
| `radarzakaz.local` | локальная вёрстка |

---

## 9. TG admin: пауза vs стоп (§ B3)

**@rawlead_bot** — кнопки ⏸/▶/🛑/ℹ **только** `TELEGRAM_CHAT_ID` (владелец). Подписчики: welcome без клавиатуры.

| Действие | Что делает |
|----------|------------|
| **⏸ Пауза** / `/pause` | мягкий флаг SQLite (`radar_paused_*`); systemd **active**, процессы живут |
| **▶ Старт** / `/старт` | снять паузу; если unit **inactive** — `systemctl start` через wrapper |
| **🛑 Стоп** / `/stop-radar` | **hard stop:** `systemctl stop rawlead-radar` или `rawlead-radar-legacy` |
| **ℹ Статус** | сводка + `systemctl is-active` |

Wrapper (без произвольного shell):

```bash
sudo /opt/rawlead/deploy/radar-ctl.sh {stop|start|status} {site|legacy}
```

Sudoers (один раз на VPS):

```bash
sudo cp /opt/rawlead/deploy/sudoers.d/rawlead-radar-ctl /etc/sudoers.d/rawlead-radar-ctl
sudo chmod 440 /etc/sudoers.d/rawlead-radar-ctl
sudo visudo -c
```

**@FLPARSINGBOT** (legacy) — отдельный токен; `/pause` там **не** гасит Site ingest (разные `.env` / units).

---

## 10. Retention purge (7d)

```bash
sudo cp /opt/rawlead/deploy/systemd/rawlead-purge-leads.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now rawlead-purge-leads.timer
```

---

_Coder § P5 · L3 · B3 · 2026-05-28 · без IP/секретов в git_
