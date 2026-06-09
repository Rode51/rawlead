# Coder — горячий контур (активное)

**→ Сейчас:** § **O161-OPS-PRO** — профессиональная админ-панель: пароль · лайв-лог · русские статусы парсеров · управление

**Блокер ads:** ingest smoke 24h ⏸ · perf p95 @50 (параллельно O161)

**Закрыто:** O160 ✅ deploy 2026-06-09 · O159 burst 3/3 ✅ · O158 deploy ✅

**Deploy:** `scripts/deploy-o161-ops-vps.py` (создать)

**Архив DoD:** [`CODER_PROMPT_ARCHIVE.md`](../archive/CODER_PROMPT_ARCHIVE.md)

---

## § O161-OPS-PRO — профессиональный пульт управления

**Owner 2026-06-09:** `/ops/` стать уровня топ-коммерческих приложений · пароль · лайв-лог · понятные русские статусы · управление парсерами.

### A. Пароль (форма входа)

**Текущий механизм:** `RAWLEAD_OPS_KEY` в `.env` → cookie `rl_ops_key`. **Оставить!** Просто заменить блок инструкции на красивую HTML-форму.

**Поведение:**
- Без cookie → показать форму логина (не инструкцию Telegram)
- Форма: поле «Пароль», кнопка «Войти», логотип RawLead
- `POST /ops/login` body `{password: "..."}` → сравнение с `RAWLEAD_OPS_KEY` через `secrets.compare_digest` → если ок: cookie `rl_ops_key` (httponly, secure, 30d) + redirect `/ops/`
- `GET /ops/logout` → удалить cookie + redirect `/ops/`
- Кнопка «Выйти» в шапке пульта (маленькая, правый угол)
- **Env:** `RAWLEAD_OPS_KEY` — уже есть в `.env`; Coder не трогает значение

### B. Лайв-лог радара

**Новый endpoint:** `GET /ops/log/stream` → `text/event-stream` (SSE, no auth cookie required but only from same-origin или с `rl_ops_key` cookie)

```python
# Алгоритм:
# 1. открыть radar_site.log (путь = cfg.radar_log_path или RADAR_LOG_PATH env)
# 2. seek(-1, 2) → вычитать последние 100 строк
# 3. отправить как SSE data: ...
# 4. loop: readline() → если пусто — sleep(0.5) → иначе: yield data: line
# 5. timeout 5 мин (client reconnect сам)
```

**JS в `/ops/`:**
- Новый раздел «Логи» в nav (между «Управление» и «Лента»)
- `<pre id="rl-ops-log">` — моноширинный, тёмный фон, высота 400px, overflow-y: scroll
- `EventSource("/rawlead/v1/ops/log/stream")` (через WP proxy)
- Авто-прокрутка вниз если пользователь не скроллил вверх
- Кнопка «⏸ Пауза» / «▶ Live»
- **Раскраска строк** (добавить CSS класс по содержимому):
  - `── Цикл ──` → синий жирный
  - `fetch:fl|kwork|youdo` → оранжевый (активный парсинг)
  - `listing:fl|kwork|youdo parsed=` → зелёный (успех)
  - `wall-clock|watchdog|timeout` → красный жирный
  - `ошибка|error|err=|HTTP 4|HTTP 5` → красный
  - `тг:|tg:` → фиолетовый
  - `neon_insert` → зелёный тонкий

### C. Статусы парсеров — простой русский язык

**Улучшить карточки бирж** в разделе «Биржи». Для каждого источника:

```
┌──────────────────────────────────────┐
│  🟢 FL.ru — Работает                  │  ← большой заголовок
│  Последний цикл: 3 минуты назад       │  ← человеческое время
│  Сегодня найдено новых заказов: 12    │  ← из health stats
│  Последнее: "parsed=30 fresh=2"       │  ← последняя строка лога
│  [Перезапустить] [Сбросить баны]      │  ← кнопки
└──────────────────────────────────────┘
```

**Статус-логика (из `exchange_health` + `last_ok_at`):**
- `last_ok_at < 15 мин назад` → 🟢 **Работает**
- `15–60 мин назад` → 🟡 **Задержка — ждём следующего цикла**
- `> 60 мин назад` → 🔴 **Не отвечает — нужна проверка**
- Текст ошибки из `last_error_short` → перевести в понятное: "403 = заблокирован прокси", "timeout = завис, перезапустил", "antibot = сайт распознал бота"

**Человеческое время** (`_human_ago(ts: float) -> str`):
```
< 1 мин → "только что"
1–59 мин → "N минут назад"
1–24 ч → "N часов назад"
> 24 ч → "больше суток назад (!)"
```

### D. Перезапуск отдельного парсера

**Новое действие** в `POST /ops/control`:
```json
{"action": "restart_source", "target": "fl"}  // fl | kwork | youdo | tg
```

**Реализация:**
- Записать в SQLite settings: `restart_source_fl = 1`
- В `main.py` `_fetch_source`: если флаг стоит → `close_all_browser_contexts()` для этого source → сбросить флаг → продолжить
- Ответ: `{"message": "FL.ru перезапустится на следующем цикле (~2 мин)"}`
- Кнопка на карточке биржи: «Перезапустить источник»

### E. UX-улучшения

1. **Toast-уведомления**: вместо изменения `#rl-ops-status` — всплывающий тост в правом нижнем углу (3 сек, автоисчезает)
2. **Авто-обновление сводки**: каждые 30с fetch `/v1/admin/dashboard` + обновить только числа (без перезагрузки страницы) — уже частично есть, довести
3. **Шапка**: название «Пульт RawLead» + дата/время последнего обновления + кнопка «Выйти»
4. **Все тексты по-русски**: проверить что нет английских фраз в интерфейсе
5. **Мобильный**: nav чипы переносятся на 2 строки — добавить `overflow-x: auto; flex-wrap: nowrap` с горизонтальным скроллом

### Файлы

| Файл | Что |
|------|-----|
| `src/owner_admin.py` | HTML/CSS/JS: форма логина, лог-секция, улучш. карточки бирж, toast, _human_ago |
| `src/api_server.py` | `POST /ops/login` · `GET /ops/logout` · `GET /ops/log/stream` (SSE) · обновить `_ops_access_granted` |
| `src/ops_log_stream.py` | новый: SSE tail логфайла (генератор) |
| `src/main.py` | `restart_source` флаг из settings в `_fetch_source` |
| `scripts/deploy-o161-ops-vps.py` | создать |

**Не трогать:** Neon schema · WP theme · `exchange_health.py` (только read) · `RAWLEAD_OPS_KEY` значение

### DoD

- [ ] `/ops/` без cookie → форма логина (не 404 и не инструкция TG)
- [ ] Правильный пароль → cookie → пульт открывается
- [ ] Неправильный пароль → «Неверный пароль» (без деталей)
- [ ] Раздел «Логи» — SSE stream, строки раскрашены, авто-прокрутка
- [ ] Карточки бирж — статус по-русски, «X минут назад», кнопка «Перезапустить источник»
- [ ] Toast при action
- [ ] `pytest tests/test_o161_ops_auth.py` — login ok/fail, logout
- [ ] deploy VPS → smoke: войти паролем → видеть логи → перезапустить FL

### Verify

```bash
# На VPS убедиться что RAWLEAD_OPS_KEY задан в .env
grep OPS_KEY /opt/rawlead/.env
# Войти через форму → видеть лог → /ops/logout → снова форма
```

---

## § O160-RADAR-INGEST — стабильность конвейера навсегда ✅ Lead 2026-06-09

**DoD:** pytest **4/4** · deploy VPS ✅ · `systemctl is-active` = active · `── Цикл ──` пошёл · 24h smoke ⏸ owner

### Что сделал Coder

| Слой | Файл | Что |
|------|------|-----|
| **L1** | `exchange_browser_fetch.py` | `_FETCH_LOCKS: dict[str, Lock]` — per-source вместо глобального `_FETCH_LOCK` |
| **L2** | `fl_parser.py` | `fetch_listing_html_browser_wall_clock` + fallback httpx · env `FL_LISTING_TIMEOUT_SEC=120` |
| **L3** | `youdo_parser.py` | wall-clock · env `YOUDO_LISTING_TIMEOUT_SEC=120` |
| **L4** | `main.py` | `_fetch_source` — thread wrapper с timeout · on kill → `close_all_browser_contexts()` · env `RADAR_SOURCE_FETCH_WALL_SEC=180` |
| **L5** | `main.py` | `_CycleWatchdog` — kill browser + raise если цикл > `RADAR_CYCLE_WALL_SEC=600` |
| **L6a** | `rawlead-radar.service` | `WatchdogSec=660` + `NotifyAccess=all` + `sd_notify(WATCHDOG=1)` каждый цикл |
| **L6b** | `healthchecks.py` | `ping_cycle_overrun()` → `HEALTHCHECKS_SITE_FAIL_URL` при overrun |

**Lead fix при deploy:** `NotifyAccess=main` → `NotifyAccess=all` (sd_notify из Python subprocess, не bash).

### Verify

```powershell
# Tail radar log: ── Цикл ── каждые ~2–5 мин
.venv\Scripts\python.exe scripts\_tmp_ingest_diag_vps.py
```

**Owner 24h smoke:** ни одного gap >15 min в `── Цикл ──` · HC fail URL — нет алертов.

**Не трогать:** draft API · WP theme · Neon schema.

---

## Archived §§ (grep по номеру в CODER_PROMPT_ARCHIVE.md)

| § | Суть | Дата |
|---|------|------|
| O159 | OR semaphore · burst 3/3 · queue_ahead | 2026-06-08 |
| O158 | match push dedup · шкала fill · ?lead= | 2026-06-08 |
| O157 | YouDo traffic ↓ residential | 2026-06-08 |
| O156 | YouDo human browser · cooldown | 2026-06-08 |
| O155 | HC dead man's switch | 2026-06-08 |
| O154 | grid neighbor no jump | 2026-06-08 |
| O153 | card chips collapse +n | 2026-06-08 |
| O152 | exchange trace jsonl · /ops/ | 2026-06-08 |
| O151 | OR acc2 UX | 2026-06-08 |
| O150 | draft UX polish | 2026-06-08 |
| O149 | no-flip inline expand | 2026-06-08 |
| O148 | draft pre-warm · OR proxy · tools regex | 2026-06-08 |
| O147 | match bar · trial hide (flip → O149) | 2026-06-08 |
| O146 | draft card UX flip lock | 2026-06-08 |
