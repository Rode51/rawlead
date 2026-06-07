# @FLPARSINGBOT не отвечает + жёлтые биржи на /ops/

**Статус:** решено

## Симптом (владелец 2026-06-05 ~09:22 UTC)

- **@FLPARSINGBOT** («flparser») **не отвечает** на команды (/status и т.д.)
- На `/ops/` «проблемы с парсерами»: часть бирж 🟡 «Давно не видели» (YouDo, Freelance.ru, Freelancejob, Pchel.net)
- Скрин пульта: FL.ru 🟢 «Работает» (~2 мин), Kwork 🟢 (~14 мин), TG 🟢 (~11 мин); Radar «Сканирует заказы»; bot-poll **active**

## Ожидалось

- `/status` в @FLPARSINGBOT отвечает в течение секунд
- Site radar (`rawlead-radar`) крутит циклы FL/Kwork/TG
- Legacy consumer (`rawlead-radar-legacy`) шлёт dogfood-карточки и **poll'ит команды FLPARSING** (`neon_legacy_consumer.py` → `try_poll_commands`)

## Гипотезы (Lead triage)

| # | Что | Почему |
|---|-----|--------|
| 1 | **`rawlead-radar-legacy` dead/stuck** | Команды FLPARSING **не** в `rawlead-bot-poll` (только @rawlead_bot). Legacy = отдельный unit |
| 2 | **Kwork hang** (повтор 2026-06-05 утра) | В hint Radar аномальный `p95 … 140702m` для kwork — возможен зависший Playwright в **site** radar |
| 3 | **TG proxy** | acc1 `45.152.197.25` мёртв — если снова откатили env или O120 pool не сработал для legacy token |
| 4 | 🟡 secondary | YouDo/Freelance.* могут быть **нормой** если `PUBLIC_FEED_SOURCES` не включает их или нет свежих лидов — **не P0** если FL+Kwork+TG зелёные |

## Gap продукта

`/ops/` **Radar: перезапуск** → только `rawlead-radar` (site). **`rawlead-radar-legacy` не перезапускается** (`owner_admin.py` `_run_systemctl` whitelist). Владелец без SSH не может поднять FLPARSING.

→ backlog: O121-w1 «Legacy: перезапуск» в `/ops/` или restart обоих radar в одной кнопке.

## Диагностика VPS (Mechanic)

```bash
systemctl is-active rawlead-radar rawlead-radar-legacy rawlead-api rawlead-bot-poll
journalctl -u rawlead-radar-legacy -n 40 --no-pager
journalctl -u rawlead-radar -n 20 --no-pager
tail -40 /opt/rawlead/data/radar_site.log
tail -30 /opt/rawlead/data/radar_legacy.log
grep -E 'ProxyError|timeout|fetch_error|health:' /opt/rawlead/data/radar_site.log | tail -25
grep TG_PROXY /opt/rawlead/.env.site /opt/rawlead/.env.legacy | head -6
ps aux | grep main.py
```

## Срочно владельцу (SSH)

```bash
sudo systemctl restart rawlead-radar-legacy
sudo systemctl restart rawlead-radar rawlead-bot-poll
sudo systemctl status rawlead-radar-legacy --no-pager
```

Проверка: `/status` в @FLPARSINGBOT · обновить `/ops/` (Ctrl+Shift+R)

С `/ops/` (без SSH): **Radar: перезапуск** + **Bot: перезапуск** — помогает site/@rawlead_bot, **не legacy**.

## Связанные тикеты

- [`2026-06-05-tg-proxy-dead-kwork-hang.md`](2026-06-05-tg-proxy-dead-kwork-hang.md) — acc1 proxy + Kwork hang (O117/O120 закрыты в коде; проверить деплой на VPS)

## Файлы

- `deploy/systemd/rawlead-radar-legacy.service`
- `src/neon_legacy_consumer.py` — poll FLPARSING
- `src/owner_admin.py` — ops control whitelist
- `deploy/radar-ctl.sh` — `legacy` profile

---

## Решение (Mechanic)

**Статус:** решено · **2026-06-05**

### Причина

1. **`rawlead-radar-legacy` жив, но FLPARSING «глухой»:** poll getUpdates шёл через `try_poll_commands`, но **`neon_legacy_consumer` не писал строки в `radar_legacy.log`** — ProxyError/команды не видны; отладка вслепую.
2. **`.env.legacy` остался на acc1** (`45.152.197.25`): `fix_tg_proxy_acc2_vps.py` правил только `.env` + `.env.site`; legacy Bot API ходил через мёртвый primary proxy (O120 pool не спасал старый процесс с Jun04).
3. **Gap `/ops/`:** «Radar: перезапуск» → только `rawlead-radar`; владелец без SSH не мог поднять FLPARSING.

🟡 YouDo/Freelance.* — secondary (site radar зелёный, не P0).

### Что сделано

| # | Изменение |
|---|-----------|
| 1 | `neon_legacy_consumer.py` — лог poll как в `main.py` (`тг:бот:` / `тг:команда:`) |
| 2 | `owner_admin.py` — Radar restart → **site + legacy**; карточка «Бот»: `legacy: active/inactive` |
| 3 | `fix_tg_proxy_acc2_vps.py` — добавлен `.env.legacy` + restart legacy |
| 4 | VPS deploy `scripts/deploy-flparsing-hotfix-vps.py`: patch `.env.legacy` TG→acc2, restart all radar units |

### Изменённые файлы

- `src/neon_legacy_consumer.py`
- `src/owner_admin.py`
- `scripts/fix_tg_proxy_acc2_vps.py`
- `scripts/deploy-flparsing-hotfix-vps.py` (deploy)

### Как проверить

1. `/status` в @FLPARSINGBOT — ответ за секунды
2. `/ops/` Ctrl+Shift+R — карточка «Бот»: `bot-poll: active · legacy: active`
3. «Radar: перезапуск» — оба unit active (без SSH)
4. `tail -f /opt/rawlead/data/radar_legacy.log` — после команды видно `тг:команда:статус`

### VPS (Mechanic 2026-06-05)

- `systemctl is-active` — все **active** после deploy
- `.env.legacy` TG_PROXY_URL → acc2
- `neon:старт` в log после restart

### Доп. (2026-06-05 ~06:32 UTC) — «всё ещё не отвечает»

**Причина:** deploy `systemctl restart rawlead-radar-legacy` → legacy поднялся с рабочим proxy → **съел queued `/stop`** из Telegram → `radar-ctl.sh stop legacy` → unit **inactive**. Новые `/status` некому poll'ить.

**Сделано:** `systemctl start rawlead-radar-legacy` — в log `тг:команда:статус`, бот отвечает.

**Код:** `_restart_radar_units()` — sleep 8s + recovery start если legacy dead; ops restart снимает паузу SQLite; legacy `ensure_bot_polling_mode` на старте.
