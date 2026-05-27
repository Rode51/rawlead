# Инцидент: Legacy consumer падает `sleep length must be non-negative`

## Контекст

После split (legacy/site) биржи парсит **Site** и пишет в Neon, а **Legacy** должен читать Neon и слать в **@FLPARSINGBOT** (личный поток владельца).

Сейчас уведомления владельцу от **Site** отключены (по умолчанию `SITE_NOTIFY_OWNER=0`), поэтому критично, чтобы **Legacy consumer** работал стабильно.

## Симптом (факты)

В `data/radar_legacy_exchanges.log` процесс `src/neon_legacy_consumer.py` падает:

- `ValueError: sleep length must be non-negative`

Фрагмент (по логу):

- `2026-05-27 15:54:39 neon:старт` → traceback → `ValueError: sleep length must be non-negative`
- `2026-05-27 16:14:15 neon:старт` → traceback → `ValueError: sleep length must be non-negative`

Дополнительно: в `data/radar_legacy.log` видно, что выборка из Neon иногда идёт (`выборка 8`, `выборка 32`), но `новых 0 │ в бот 0` — то есть поток в @FLPARSINGBOT не доезжает.

## Ожидаемое поведение

- `neon_legacy_consumer.py --profile legacy` работает 24/7, не падает.
- При появлении новых лидов бирж в Neon, после `FILTERS_LEGACY` + legacy-ИИ отправляет уведомления в Telegram (бот legacy = @FLPARSINGBOT) и пишет в `data/radar_legacy.log` счётчики `новых > 0`, `в бот > 0` (когда есть подходящие).

## Гипотеза причины

В `src/neon_legacy_consumer.py` внутри `_sleep_with_tg_poll(...)` считается `end - time.monotonic()` и попадает отрицательное значение в `time.sleep(min(2.0, ...))`, что и вызывает `ValueError`.

## Задача (Mechanic)

### 1) Hotfix: не падать на отрицательном sleep

- Найти место, где вычисляется sleep-дельта (по traceback: `_sleep_with_tg_poll`, строка около 139).
- Сделать безопасный clamp: `sleep_sec = max(0.0, min(2.0, end - time.monotonic()))`.
- Добавить минимальный лог (в `radar_legacy.log` или stderr) при частом `sleep_sec=0`, чтобы понять, не ушли ли мы в tight-loop.

### 2) Приёмка: работает стабильно и шлёт в legacy-бот

- Запуск legacy через обычный ярлык/VBS.
- 30 минут работы: **нет** повторов traceback в `data/radar_legacy_exchanges.log`.
- В `data/radar_legacy.log` появляются строки `neon:цикл │ выборка N` регулярно, без падений.
- Если в Neon есть свежие лиды, удовлетворяющие `FILTERS_LEGACY` и ИИ не падает — `в бот > 0`.

## Файлы

- `src/neon_legacy_consumer.py`
- `data/radar_legacy_exchanges.log`
- `data/radar_legacy.log`

## Как воспроизвести

1. Запустить Legacy (`--profile legacy`) так, чтобы стартовал `neon_legacy_consumer.py`.
2. Убедиться, что в `data/radar_legacy_exchanges.log` появляется `neon:старт`, затем traceback с `sleep length must be non-negative`.

## Статус

- Статус: **решено**
- Lead verify: `data/radar_legacy.log` `2026-05-27 16:37:16` — `neon:цикл │ выборка 39 │ новых 0 │ в бот 0` (цикл проходит без падения `sleep length must be non-negative`).

## Решение

В `src/neon_legacy_consumer.py` добавлен безопасный clamp для `sleep_sec = max(0.0, min(2.0, end - time.monotonic()))`. Это предотвращает передачу отрицательных значений в `time.sleep()`.
Добавлено логирование в `radar_legacy.log` в случае, если `sleep_sec` равен 0, чтобы отслеживать потенциальные tight-loop состояния.

## Измененные файлы

- `src/neon_legacy_consumer.py`

## Как проверить

Выполните шаги из раздела "Приёмка", описанные выше:
1. Запуск legacy через обычный ярлык/VBS.
2. 30 минут работы: **нет** повторов traceback в `data/radar_legacy_exchanges.log`.
3. В `data/radar_legacy.log` появляются строки `neon:цикл │ выборка N` регулярно, без падений.
4. Если в Neon есть свежие лиды, удовлетворяющие `FILTERS_LEGACY` и ИИ не падает — `в бот > 0`.

