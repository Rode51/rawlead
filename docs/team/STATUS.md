# STATUS

Карта: **[`../ROADMAP.md`](../ROADMAP.md)** · владелец: **[`../FOR_YOU.md`](../FOR_YOU.md)** · архитектура: [`ARCHITECTURE.md`](ARCHITECTURE.md)

---

## Сейчас

- **Фаза 0–1** — FL, Kwork, TG, бот ✅
- **Пульт v2** — Tauri + `radar_control.py` ✅ (Lead принял 2026-05-23)
- **WP локально** — шаг 2 ✅ → шаг 3 (5 страниц)
- **TG** — пересылка + разбор (проверить после рестарта TG)

---

## Следующий шаг

| Кто | Действие |
|-----|----------|
| **Владелец** | `scripts\start-radar-desktop.bat` → чеклист ниже · WP §3 · `backup.bat` |
| **Lead** | После проверки пульта — WP/TG в TASKS |

---

## Приёмка пульта v2 (владелец)

1. `scripts\start-radar-desktop.bat` (Rust установлен → `tauri dev` или exe после `npm run tauri build`)
2. Compact: play синий, лампы серые, **by Rode51**
3. Play → stop зелёный, 3 python, логи вниз
4. ▼ свернуть логи — процессы работают
5. Stop → compact
6. Убить один процесс → лампа «нет»

Подробно: [`../ops/DESKTOP_LAUNCH.md`](../ops/DESKTOP_LAUNCH.md)

---

## Последняя сдача (Coder) — пульт v2

- `scripts/radar_control.py` — API `:18765`
- `desktop/` — Tauri 2, HTML/CSS по DESIGN_BRIEF v2
- `start-radar-desktop.bat` — API + Tauri
- PyQt6 `radar_desktop.py` — deprecated

---

## Блокеры

- нет (Rust у владельца ✅)
