# Пульт: ✕ не останавливает радар + логи сами разворачиваются

**Дата:** 2026-05-24  
**Статус:** fixed ✅ принято Lead 2026-05-24 · **регрессия:** ✕ зависает → [`2026-05-24-pult-close-hang.md`](2026-05-24-pult-close-hang.md)  
**Промпт:** [`docs/team/CODER_PROMPT.md`](../team/CODER_PROMPT.md) § C

## Симптом

1. Закрыть окно пульта **✕** без **■** — `tg_main` / `main.py` остаются в фоне.
2. Снова ▶ — второй `tg_main` → `database is locked`, TG «не читает».
3. При ▶ логи сразу разворачиваются — владельцу нужно только по **стрелке**.

## Ожидание

| Действие | Поведение |
|----------|-----------|
| ✕ / CloseRequested | `POST /stop`, затем закрыть окно |
| — (свернуть) | процессы **не** трогать |
| ▶ | компактное окно, логи **свёрнуты** |
| стрелка `#btn-collapse` | развернуть/свернуть логи |

## Где смотреть

- `desktop/src/main.ts` — `btnClose`, `pollStatus` (авто-логи ~352), `onHeroClick` / `runStart`
- `scripts/radar_control.py` — `/stop` (уже ок)

## Приёмка

См. CODER_PROMPT § «Как проверить C».

## Решение (2026-05-24)

- `stopRadarCore()` + `requestAppClose()` — общий путь для ■, ✕, `onCloseRequested`
- **2026-05-24:** ✕ всегда `POST /stop` (не только при `running` в UI); таймер 12 с — повторный `/stop` + `destroy`
- `pollStatus`: при `running` — полоска логов свёрнута, без авто-разворота
- `runStart` / `onHeroClick`: `/ui-expanded: false`, `logsCollapsed=true` при ▶
- `onCollapseClick`: `/ui-expanded` синхронизируется со стрелкой
