# Пульт v2: кнопки не работают, вид не как DESIGN_BRIEF

**Статус:** решено · 2026-05-23  
**Кто:** Coder (`@coder` + `CODER_PROMPT.md`)

---

## Симптомы (владелец)

1. Tauri запустился (`tauri dev` / `desktop.exe`), но **вид не как у Designer** (canvas `fl-radar-pult-v2`, [`DESIGN_BRIEF.md`](../team/design/DESIGN_BRIEF.md) v2).
2. **Кнопки не работают** (play, обновить статус, табы).
3. **Плашка Windows** — убрать стандартный title bar (decorations).
4. **Не открывать PowerShell** — запуск как у обычного приложения (vbs / exe).

---

## Гипотеза Lead

| Проблема | Деталь |
|----------|--------|
| **API заблокирован** | UI ходит на `http://127.0.0.1:18765` — в Tauri 2 нужны permissions `http` на localhost в `capabilities/default.json` |
| **radar_control не запущен** | bat должен поднять `pythonw radar_control.py`; проверить `http://127.0.0.1:18765/health` в браузере |
| **Дизайн** | Сверить `desktop/src/styles/*.css` с canvas и brief; glow, hero 220px, лампы с подписями |

---

## Проверка владельца (до Coder)

1. Браузер: http://127.0.0.1:18765/health → `{"ok":true}` (или аналог)
2. Клик play → если **alert** «radar_control» — API не доступен из WebView
3. http://localhost:1420 в Chrome — если там кнопки **работают**, виноват Tauri permissions

---

## Задача Coder

См. [`../team/architect/CODER_PROMPT.md`](../team/architect/CODER_PROMPT.md).

---

## Решение

1. **Кнопки:** `tauri-plugin-http` + scope `http://127.0.0.1:18765/*` в `capabilities/default.json`; fetch из UI через `@tauri-apps/plugin-http`; CSP `connect-src` на API.
2. **Title bar:** `decorations: false`, `shadow: true`; drag на «FL RADAR»; ✕/— в header.
3. **Запуск:** health-check в bat через Python (без PowerShell); ярлык на `start-radar-desktop.vbs`.

Проверка владельца: `start-radar-desktop.vbs` → play без alert, 3 процесса, логи/табы.
