# ADR — стек пульта (замена PyQt6)

**Статус:** принято Lead · 2026-05-20  
**Контекст:** владелец дал референс [`../design/references/u-boost-ref.png`](../design/references/u-boost-ref.png) (ЮБуст). Текущий PyQt6 + QSS **не достигает** уровня polish (градиенты, glow, pill-controls, типографика). **PyQt6 для пульта — снят с обслуживания.**

---

## Что не меняется

- Пульт = **лаунчер** 3 subprocess (биржи, TG, join), tail логов, статус, lock
- Логика уже в `scripts/radar_desktop.py` — **переиспользовать**, не переписывать радар
- Python 3.11+, `.venv`, Windows 10/11

---

## Решение (стек UI)

| Слой | Технология | Зачем |
|------|------------|--------|
| **Оболочка** | **Tauri 2** (Rust + WebView2) | Нативное окно, малый exe, CSS как в референсе |
| **Интерфейс** | **HTML + CSS** (+ при необходимости лёгкий TS/Vanilla) | Pixel-perfect под Designer |
| **Мост к Python** | **Sidecar**: тот же `radar_desktop.py` режим `--api` **или** отдельный `scripts/radar_control.py` | Старт/стоп, poll PID, tail log — без дублирования бизнес-логики |
| **Связь UI ↔ Python** | localhost HTTP (127.0.0.1) или Tauri `Command` → spawn | Простая отладка, Coder знает requests |

**Запасной план** (если Tauri-сборка на ПК владельца займёт >1 дня): **pywebview** + тот же HTML/CSS + тот же Python API. Визуал тот же, оболочка проще.

**Не берём:** Electron (тяжёлый), Flutter (новый язык), чистый WPF (отдельный стек), **PyQt6** (отклонено).

---

## Структура (целевая)

```
desktop/
  src/                 # UI (HTML/CSS/TS)
  src-tauri/           # Tauri config, window
scripts/
  radar_control.py     # API: start/stop/status/logs (вынести из radar_desktop)
  radar_desktop.py     # deprecated → удалить после миграции
```

Ярлык владельца: `start-radar-desktop.bat` → запуск **нового** exe / `tauri dev` на этапе разработки.

---

## Этапы

| # | Кто | Что |
|---|-----|-----|
| 1 | **Designer** | Brief v2: compact как ЮБуст + expanded с логами; **не QSS** |
| 2 | **Lead** | Утвердить brief + этот ADR |
| 3 | **Coder** | Tauri shell + Python API + перенос логики subprocess |
| 4 | **Владелец** | Проверка, ярлык, `backup.bat` |

---

## Риски

| Риск | Митигация |
|------|-----------|
| Нужен Node + Rust для сборки | Один раз настроить; в `docs/ops/DESKTOP_LAUNCH.md` пошагово |
| WebView2 на Win10 | Обычно уже есть; иначе установщик Tauri подтянет |
| Два процесса (UI + Python) | Один lock `data/.radar_desktop.lock` как сейчас |

---

_Следующий артефакт: `DESIGN_BRIEF.md` v2 (Designer)._
