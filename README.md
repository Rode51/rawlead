# FL Radar

Мониторинг **FL.ru + Kwork + TG (acc1)** → фильтр → ИИ → бот.  
Карта: [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Старт

| Кто | Куда |
|-----|------|
| **Владелец** | [`docs/FOR_YOU.md`](docs/FOR_YOU.md) · [`docs/KAK_ETO_RABOTAET.md`](docs/KAK_ETO_RABOTAET.md) |
| **Роли в Cursor** | `.cursor/rules/` · [`HOW_TO_USE_CURSOR.md`](docs/team/HOW_TO_USE_CURSOR.md) · цикл [`SCALE.md`](docs/team/SCALE.md) |
| **Запуск** | [`docs/ops/RUN.md`](docs/ops/RUN.md) |
| **Все docs** | [`docs/README.md`](docs/README.md) |

```powershell
Copy-Item .env.example .env
pip install -r requirements.txt
.venv\Scripts\python.exe src/main.py
```

**TG:** один бот (уведомления), чтение чатов — Telethon **user**-аккаунты; радар слушает только **acc1** (`data/telethon_chat_ids.txt`).

## Код

`src/` — парсеры, фильтр (`docs/ops/FILTERS.md`), ИИ (`docs/ops/PROFILE.md`).
