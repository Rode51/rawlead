# 2026-06-05 — TG proxy мёртв + main.py завис на Kwork

## Симптом (владелец)

- Боты не отвечают на команды / push
- Парсеры не работают (нет новых лидов)

## Диагностика VPS (2026-06-05 ~12:00 IRK)

| Сервис | systemd |
|--------|---------|
| rawlead-api | active |
| rawlead-bot-poll | active |
| rawlead-radar | active |

### 1. Бот — `TG_PROXY_URL` не проксирует Telegram

- `api.telegram.org` **напрямую с VPS:** HTTP 302 за ~0.25с ✅
- Через `TG_PROXY_URL` (`45.152.197.25:8000`): TCP ok, HTTPS **ReadTimeout / ProxyError** ❌
- `rawlead-bot-poll`: **416× ProxyError** за 6 ч
- Лог: `тг:бот:ProxyError … getUpdates`

**Почему не переключился на acc2 автоматически:** Bot API — **один** `TG_PROXY_URL`; failover только у бирж (`exchange_proxy.py`). acc2/acc3 в env для Telethon, bot-poll **не перебирает**. TCP acc1 ok — HTTPS к Telegram timeout.

**→ @coder:** § **O120-tg-proxy-failover** в `CODER_PROMPT.md`

**Причина:** прокси-провайдер отдал TCP, но TLS-туннель до Telegram не работает (истёк / перегружен / заблокирован).

### 2. Парсеры — `main.py` завис 12+ ч на Kwork

- Последний полный цикл: **2026-06-05 03:01:55** (FL.ru ok → дальше тишина)
- `strace`: `epoll_wait` — процесс жив, цикл не идёт
- Вероятно: **Playwright / Cloudflare** на Kwork (`kwork_185.147.131.15:8000`) без таймаута

## Что сделано

```bash
# .env + .env.site (site profile перебивает .env!)
TG_PROXY_URL / TELETHON_PROXY_URL / TELETHON_PROXY_ACC1 → TELETHON_PROXY_ACC2 (38.154.16.60)
systemctl restart rawlead-bot-poll rawlead-radar
```

- **2026-06-05 12:08** — бот отвечает: `тг:команда:статус`, `стоп`, `старт` в journal
- Backup: `.env.bak-tg-proxy-acc2`, `.env.site.bak-acc2`

## Владельцу (срочно)

1. ~~**Прокси TG:** обновить `TG_PROXY_URL`~~ ✅ перекинуто на acc2
2. ~~`systemctl restart`~~ ✅
3. Проверить **ℹ Статус** в @rawlead_bot — **должен отвечать**
4. У провайдера: **45.152.197.25** — мёртв для TG; продлить/заменить если нужен отдельный acc1

**Backlog @coder:** ~~таймаут Kwork Playwright~~ ✅ · **O120** TG Bot API auto-failover · watchdog «Итого в бот» > N мин — опционально
- Опционально: Bot API direct с VPS когда `TG_PROXY_DIRECT=1` (VPS не RU residential)

## Файлы

- `src/config.py` — `TG_PROXY_URL`, `normalize_proxy_url`
- `src/kwork_parser.py` — Playwright listing
- `scripts/bot_poll_main.py`, `deploy/systemd/rawlead-bot-poll.service`
