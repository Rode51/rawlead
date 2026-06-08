# YouDo 403 / FL timeout — красные лампы /ops/

**Статус:** triage Lead **2026-06-08** · fix ops ⏸ · **O152** logging → @coder

## Симптом (владелец)

`/ops/` — **YouDo** и **FL.ru** 🔴 «Сломалось» · TG 🔴 · стабильности нет.

## Факты VPS journal (read-only)

### YouDo

| Время UTC | Факт |
|-----------|------|
| 09:45–09:50 | `no alive proxy slots for browser` · `pool exhausted (0/3 alive)` |
| **11:24–11:25** | 3× `gate.node-proxy.com:10000/1/2` → **HTTP 403** · ban **3600s** each |

**Корень:** не OR/O151 · **YOUDO_PROXY_URLS** (node-proxy RU) — YouDo antibot режет все 3 слота подряд.

### FL.ru

| Время UTC | Факт |
|-----------|------|
| 09:48–09:50 | Playwright `Page.goto` **timeout 30s** |
| **11:23** | ✅ `скачано 21 · новых 21` |

**Корень:** непрерывный **timeout Cloudflare/прокси** · цикл после рестарта radar **ожил**. Лампа 🔴 может держаться от **last_error** до следующего ok-fetch.

### TG

Radar **active** · сообщения идут (acc2/acc3) · часть `pipeline:skip filter` / L1 МИМО. 🔴 = **тишина/SLA**, не «бот мёртв».

### O151 side note

`fetch:proxy skip TELETHON_PROXY_ACC2 — host reserved for TG` — **норма**: acc2 (`38.154`) = TG + OR, **не** в пул YouDo. YouDo = только `YOUDO_PROXY_URLS`.

## Срочно (владелец / /ops/)

1. **YouDo:** после **O156** — browser-only · один слот · warm path (не «ещё прокси»)
2. **O155:** зарегистрировать [Healthchecks.io](https://healthchecks.io) · grace **15 min** · URL в VPS `.env`
3. **Сбросить баны** — по-прежнему общая кнопка (youdo включён), но цель — **не** жечь pool httpx'ом

## Следующий шаг (инженерия)

**§ O155 + O156** — external pulse · YouDo humanization · `deploy-o155-o156-vps.py`
