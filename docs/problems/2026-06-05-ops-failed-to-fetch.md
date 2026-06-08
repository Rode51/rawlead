# /ops/ «Сбросить баны» / «Проверить ссылки» → Failed to fetch

**Статус:** ✅ fix в коде · deploy `deploy-o121-w2b-vps.py` · owner smoke ⏸ · **2026-06-08**

## Симптом (владелец)

- На [`/ops/`](https://rawlead.ru/ops/) карточка **TG** — **«🔴 Сломалось»** (причина в UI неочевидна)
- **«Сбросить баны»** (прокси) → браузер **Failed to fetch**
- **«Проверить ссылки»** (delist) → тоже не работает

## Triage Lead (read-only код + prod smoke)

| # | Вероятная причина | Деталь |
|---|-------------------|--------|
| 1 | **WP timeout 20s на clear-bans** | O121-w2: `run_ops_control` после `clear-bans` делает `systemctl restart rawlead-radar` + bot-poll → **>20s**. WP `rawlead-api.php` `/ops/control`: timeout **20** для proxy (кроме `probe-all` 60s). cURL 28 → браузер **Failed to fetch**. |
| 2 | **Delist — theme/nginx timeout** | O122 hotfix: delist timeout **120s** в `rawlead-api.php`. Если на prod старая тема или nginx/php-fpm режет раньше — тот же симптом. |
| 3 | **TG «Сломалось»** — отдельно от кнопок | Карточка **Биржи → TG** = `exchange_health` level **red** (тишина >45 мин / последняя ошибка прокси). См. [`2026-06-05-tg-proxy-dead-kwork-hang.md`](2026-06-05-tg-proxy-dead-kwork-hang.md). Не баг кнопки — ingest/прокси. |
| 4 | **Вход** | Без `/cabinet/` + Telegram в **этом же браузере** — пустой пульт. Ключ `?key=` ≠ JWT; нужен `rl_access` cookie или `rawlead_access_token`. |

**Prod API жив:** `GET /wp-json/rawlead/v1/site-stats` → 200, `radar_online: true`.

## Fix (@coder § O121-w2b)

1. **`rawlead-api.php` `/ops/control` timeouts:**
   - `proxy` + `clear-bans` → **90s**
   - `proxy` + `switch` (если probe внутри) — оставить 60s probe-all
   - `radar`/`site`/`bots-*` **restart** → **90s** (systemctl + drain)
2. **Deploy:** скопировать `rawlead-api.php` на prod theme path (как O122-hotfix) + bump theme если нужно
3. **Тест:** mock slow control → WP REST не обрывает до 90s
4. **Опционально (лучше UX):** clear-bans — ответ **сразу**, restart radar/bot **в фоне** (thread/subprocess), чтобы UI не ждал

## Verify (@mechanic на VPS, read-only)

```bash
grep -A8 "ops/control" /var/www/.../rawlead-api.php   # timeout 90/120
systemctl is-active rawlead-api rawlead-radar rawlead-bot-poll
journalctl -u rawlead-api -n 30 --no-pager
sqlite3 /opt/rawlead/data/*.sqlite "SELECT key,value FROM settings WHERE key LIKE 'health_%tg%';"
```

## Workaround (владелец, SSH)

```bash
sudo systemctl restart rawlead-radar rawlead-bot-poll
# баны в SQLite/JSON — сброс через proxy_ops на VPS или дождаться w2b deploy
```

## Smoke после fix

1. `/cabinet/` → Telegram → `/ops/?key=…` → Ctrl+Shift+R
2. **Прокси → Сбросить баны** → зелёный статус (не Failed to fetch)
3. **Проверить ссылки** → сообщение delist (до 2 мин)
4. **Биржи → TG** — смотреть строку «что случилось»; если прокси — переключить слот TG Bot API
