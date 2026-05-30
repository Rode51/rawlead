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

### Способ 1 — mint (рекомендуется, § O37c-a)

```powershell
cd C:\Users\hramo\uisness
.venv\Scripts\python.exe scripts\preprod_mint_token.py --account acc1 --write-env-site
```

Скрипт: Telethon acc1 → Neon user → `plan=agent` active → запись в `.env.site`.

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
| `user_id` (uuid) | `895912a1-ffb6-46fb-be7e-4e051f2ff8c1` |
| Owner uuid (не использовать) | `164786fe-b979-4bfa-a9dc-42416465f503` |

---

## Dolphin Anty / CDP

| Env | Default |
|-----|---------|
| `DOLPHIN_CDP_URL` | `http://127.0.0.1:9222` |

---

## @rawlead_bot smoke

`scripts/preprod_bot_smoke.py` → `data/preprod_bot_smoke.json`
