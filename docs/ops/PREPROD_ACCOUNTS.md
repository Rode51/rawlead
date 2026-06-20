# Pre-prod test accounts (O37b / O37c)

**Секреты не в git** — только `.env` / `.env.site` локально.

---

## Два разных «аккаунта» (не путать)

| | **acc1 Telethon** | **JWT для Playwright** |
|--|-------------------|------------------------|
| **Что это** | Файл `.session` на ПК (+66953964608) | Строка в `.env.site` |
| **Зачем** | Слушает TG-чаты · `/start` @rawlead_bot | Вход на **rawlead.ru** без браузерного TG |
| **Как получить** | Уже в `.env` (`TELETHON_SESSION_ACC1`) | **Скрипт mint** (см. ниже) |
| **Можно войти на /cabinet/ руками?** | **Нет** (нет телефона) | Скрипт подставляет token в Playwright |

**Личный token владельца из DevTools — не для gate.** Это ваш TG, не test acc.

---

## JWT для Playwright (J5 / J8 / O37c)

| Env | Назначение |
|-----|------------|
| `RAWLEAD_PREPROD_ACCESS_TOKEN` | Bearer JWT **acc1 test user** в Neon — обязателен для O37c |

### Способ 1 — mint на VPS (рекомендуется после O271)

Локальный `.env` с Neon **не нужен**. На VPS уже prod Postgres:

```powershell
cd C:\Users\hramo\uisness
.venv\Scripts\python.exe scripts\_owner_sync_preprod_token.py
```

Скрипт: mint на VPS (Telethon acc1 + prod DB) → копирует `RAWLEAD_PREPROD_ACCESS_TOKEN` в **локальный** `.env.site` → smoke `api /v1/me`.

### Способ 1b — mint локально (нужен SSH-туннель к VPS Postgres)

```powershell
ssh -i C:\Users\hramo\.ssh\id_rawlead_vps -L 15432:127.0.0.1:5432 root@62.113.103.231 -N
```

В `.env.site`: `DATABASE_URL=postgresql://rawlead:...@127.0.0.1:15432/rawlead?sslmode=disable` · затем `preprod_mint_token.py --account acc1 --write-env-site`.

### Способ 1c — mint локально (legacy, только если Neon ожил)

```powershell
.venv\Scripts\python.exe scripts\preprod_mint_token.py --account acc1 --write-env-site
```

**Проверка:** `user_id` в stdout **≠** owner `164786fe-b979-4bfa-a9dc-42416465f503` — иначе acc1 = ваш личный TG, нужен другой `.session`.

Потом:

```powershell
.venv\Scripts\python.exe scripts\preprod_playwright\ux_audit.py --base-url https://rawlead.ru --browser chromium --headed
```

### Способ 2 — DevTools (только если уже есть web-login test TG)

Не использовать owner JWT. Только если отдельный test TG залогинен на `/cabinet/`.

---

## O37c UX audit (U1–U10)

| Правило | Деталь |
|---------|--------|
| Token | **blocker** — exit 2 без `RAWLEAD_PREPROD_ACCESS_TOKEN` |
| Browser | `chromium+token` — не yandex-cdp владельца без token |
| Отчёты | `data/preprod_ux_audit.json` · `.md` · `preprod_ux_audit_human.md` · скрины `data/preprod_ux_audit/` |
| LLM | `AI_API_KEY` в `.env` |

---

## Neon test user (acc1)

После mint в docs здесь uuid (без секрета):

| Поле | Значение |
|------|----------|
| `tg_user_id` | `8233488286` (acc1 Telethon) |
| `user_id` (uuid) | `7a83dbd8-ab41-4350-a183-38370d5b5c1c` (VPS Postgres 2026-06-19) |
| Owner uuid (не использовать) | `164786fe-b979-4bfa-a9dc-42416465f503` |

---

## Monica (O218 j5 · tier smoke trial path)

**TG test persona** — не Telethon acc1. Сейчас на prod (**Neon 2026-06-17**):

| Поле | Значение |
|------|----------|
| `tg_user_id` | `8688264540` |
| `user_id` (uuid) | `8d5afb3d-e8bd-4970-a33d-21c3ddeafdef` |
| TG username | `@RawLead` (display RawLead) |
| `plan` | **agent** (premium) · `active_until` **2026-07-15** |
| Quiz tags | **27** в Neon |

**O218 j5:** Monica **как есть** — premium даёт реальный % на карточках (то же, что trial для UI). **Wipe не нужен.**

**JWT для headless Playwright (j5):**

```powershell
cd C:\Users\hramo\uisness
.venv\Scripts\python.exe scripts\grant_premium_local.py --username RawLead --plan agent --days 30
```

Токен → `data/_local_premium_token.txt` · Coder кладёт в `.env.site` как `RAWLEAD_MONICA_TOKEN` (не путать с acc1 `RAWLEAD_PREPROD_ACCESS_TOKEN`).

**Полный wipe** (удалить user/tags/sub) — только если нужен сценарий **первого входа → auto trial 3 дня** (`FOR_YOU.md` tier smoke §2), не для O218.

---

## Dolphin Anty / CDP

| Env | Default |
|-----|---------|
| `DOLPHIN_CDP_URL` | `http://127.0.0.1:9222` |

---

## @rawlead_bot smoke

`scripts/preprod_bot_smoke.py` → `data/preprod_bot_smoke.json`
