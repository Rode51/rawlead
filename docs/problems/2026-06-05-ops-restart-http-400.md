# /ops/ «Перезапуск» → HTTP 400

**Статус:** решено

## Симптом (владелец 2026-06-05)

- На `/ops/` кнопки **Перезапуск** (боты / radar) → в UI **«HTTP 400»**
- Текст причины из API **не виден**

## Вероятные причины (Lead triage)

| # | Причина | Как проверить на VPS |
|---|---------|----------------------|
| 1 | **Legacy restart → queued `/stop`** → unit `inactive` после restart (см. [`2026-06-05-flparsingbot-dead-parsers.md`](2026-06-05-flparsingbot-dead-parsers.md)) → `run_ops_control` `ok=False` → API **400** | `journalctl -u rawlead-radar-legacy -n 20` |
| 2 | **O121-w0b не задеployен** на `api.rawlead.ru` → target `rawlead-bot` / `flparsing-bot` → `Unsupported control target/action` | `grep flparsing-bot /opt/rawlead/src/owner_admin.py` |
| 3 | **`rawlead` без прав systemctl** → restart exit ≠ 0 | `sudo -u rawlead systemctl restart rawlead-bot-poll` |
| 4 | **UX:** JS `if (!r.ok) throw new Error("HTTP " + r.status)` — **не читает** `detail` из тела 400 | код `owner_admin.py` bindControls |

## Ожидалось

- Кнопка перезапуска → зелёный статус + сообщение «… is-active=active»
- При сбое — **понятный текст**, не голый HTTP 400

## Fix (@coder § O121-w0c)

1. **JS:** на 4xx парсить JSON `{detail}` / WP `{message}` и показывать в `ctl-status`
2. **Legacy restart:** `sudo /opt/rawlead/deploy/radar-ctl.sh` (расширить `restart`) · drain getUpdates offset перед restart · recovery start
3. **bot-poll:** `deploy/bot-ctl.sh` + sudoers или polkit
4. **`ok` logic:** после restart sleep 2s + recheck; `activating` → warn не fail
5. Deploy: `deploy-o121-w0c-vps.py` · smoke curl control с owner Bearer

## Workaround (владелец)

```bash
sudo systemctl restart rawlead-bot-poll
sudo systemctl start rawlead-radar-legacy   # start, не restart — меньше шанс съесть /stop
sudo systemctl is-active rawlead-bot-poll rawlead-radar-legacy
```

---

## Решение (Coder)

**Статус:** решено · **2026-06-05**

| # | Изменение |
|---|-----------|
| 1 | JS `ctlFetchErr` — на 4xx показывает `detail` / `message` из тела |
| 2 | `radar-ctl.sh` + `bot-ctl.sh` — restart через sudo wrappers |
| 3 | Legacy restart: stop → drain getUpdates → start (queued `/stop` не выполняется) |
| 4 | bot-poll: sleep 2s + recheck; `activating` → ok с пометкой |
| 5 | Deploy `scripts/deploy-o121-w0c-vps.py` — VPS ✅ |

**Файлы:** `src/owner_admin.py` · `deploy/radar-ctl.sh` · `deploy/bot-ctl.sh` · `deploy/sudoers.d/rawlead-radar-ctl` · `scripts/deploy-o121-w0c-vps.py`

**Как проверить:** `/ops/` Ctrl+Shift+R → «Перезапуск» на @rawlead_bot / @FLPARSINGBOT / оба / Radar — зелёный статус или текст ошибки (не «HTTP 400»)
