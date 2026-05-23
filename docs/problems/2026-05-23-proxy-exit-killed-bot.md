# 2026-05-23 — tg_main exit убивал бот после падения прокси

## Симптом

После переподключения прокси: TG красная в пульте, **ℹ Статус** в боте не отвечает, процессов `tg_main`/`main.py` нет.

## Причина

`proxy_probe.abort_proxy_unavailable` → `SystemExit(1)` при мёртвом прокси **до** или **после** обрыва сессии. Процесс `tg_main` завершался целиком (вместе с `bot_poll`). Пульт **не** перезапускает детей автоматически → красная лампа, бот молчит если упали оба процесса.

## Решение (Coder)

- `ProxyUnavailableError` вместо `SystemExit` в `require_proxy_live`
- `wait_active_monitor_proxies_live()` — ждём TCP прокси, алерт с cooldown, **процесс жив**
- `tg_main`: `_ensure_proxies_live` на старте и перед реконнектом; `bot_poll` / пульс работают во время ожидания

## Владельцу после инцидента

1. `scripts\stop-radar.bat`
2. Пульт **▶** (или `start-radar-full.bat`)
3. Проверить **ℹ Статус** в боте

## Файлы

- `src/proxy_probe.py`
- `scripts/tg_main.py`
