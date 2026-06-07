# O122 deploy: radar crash + delist cURL 28

**Статус:** открыто

## Симптом

1. После `deploy-o122-delist-vps.py` — `rawlead-radar` **activating/crash**: `ModuleNotFoundError: trial_subscription`
2. `/ops/` «Проверить ссылки» → **cURL error 28: Operation timed out after 20001 milliseconds**

## Причина

| # | Root cause |
|---|------------|
| 1 | O122 залил `main.py` (import trial), но **не** `trial_subscription.py` (O107) |
| 2 | WP `rawlead_api_post` timeout **20s**; delist до 40 URL × HTTP ~2–20s → API не успевает ответить |

Delist на API **может** отрабатывать, но браузер/WP обрывает соединение → owner видит timeout.

## Fix (@coder § O122-hotfix-vps)

См. `CODER_PROMPT.md` § O122-hotfix-vps

---

**Статус:** решено · **2026-06-05**

| # | Изменение |
|---|-----------|
| 1 | `trial_subscription.py` в `deploy-o122-delist-vps.py` · radar **active** |
| 2 | WP `/ops/control` delist → timeout **120s** |
| 3 | Ручной delist **limit=15** в `_run_delist_batch_ops` |
| 4 | Theme `rawlead-api.php` скопирован на prod path |

**VPS verify:** radar+api **active** · trial_ok · timeout 120 · limit=15
