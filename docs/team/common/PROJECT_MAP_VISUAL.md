# Карта RawLead — визуально (для владельца)

**Как смотреть:**

| Формат | Файл |
|--------|------|
| **Картинка (Designer ✅)** | [`../design/rawlead/project-map-owner.png`](../design/rawlead/project-map-owner.png) — открой в проводнике |
| **Mermaid в Cursor** | Preview этого файла (`Ctrl+Shift+V`) |

Текстовая карта для AI: [`PROJECT_MAP.md`](PROJECT_MAP.md) · архитектура: [`ARCHITECTURE.md`](../architect/ARCHITECTURE.md)

---

## 1. Ты → программы на ПК

```mermaid
flowchart TB
  YOU(["👤 Ты\n(владелец)"])
  VBS["📌 Ярлык\nstart-radar-desktop.vbs"]
  PULT["🖥️ Пульт RawLead\n(Tauri)"]
  API["⚙️ radar_control\n127.0.0.1:18765"]
  MAIN["📊 main.py\nFL.ru + Kwork"]
  TG["📱 tg_main.py\nTelethon acc1·2·3"]
  BOT["🤖 Telegram-бот\n(уведомления тебе)"]
  ENV["🔒 .env\n(только ты)"]
  DATA[("💾 data/\nБД, логи, сессии")]

  YOU -->|двойной клик| VBS
  YOU -->|правишь| ENV
  VBS --> PULT
  VBS --> API
  YOU -->|▶ / ■ / ✕| PULT
  PULT -->|HTTP| API
  API -->|запуск .venv| MAIN
  API -->|запуск .venv| TG
  MAIN --> DATA
  TG --> DATA
  MAIN --> BOT
  TG --> BOT
  BOT --> YOU
```

**Правило:** на ПК должно быть **не больше 2** python-процессов радара (`main` + `tg_main`), оба из **`.venv`**.

---

## 2. Откуда берутся заказы

```mermaid
flowchart LR
  subgraph sources["Источники"]
    FL["FL.ru"]
    KW["Kwork"]
    CH1["TG чаты acc1"]
    CH2["TG чаты acc2"]
    CH3["TG chаты acc3"]
  end

  subgraph radar["Рadar (твой ПК)"]
    P["Парсеры / монитор"]
    F["Фильтр слов\nFILTERS.md"]
    AI["ИИ\nOpenRouter"]
    DB[("SQLite\nдедуп")]
  end

  subgraph out["Тебе"]
    FWD["Пересылка поста\n(TG)"]
    CARD["Карточка разбора\n(бот)"]
  end

  FL --> P
  KW --> P
  CH1 --> P
  CH2 --> P
  CH3 --> P
  P --> DB --> F --> AI --> CARD
  P --> FWD
  FWD --> CARD
```

**Контур 1 (сейчас):** всё идёт **тебе в бота**. SaaS / сайт-лента — позже ([`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md)).

---

## 3. Кто что трогает (роли)

```mermaid
flowchart TB
  subgraph owner["Ты"]
    O1[".env, запуск, бэкап"]
    O2["FOR_YOU.md"]
  end

  subgraph lead["Lead @lead-architect"]
    L1["docs/team/*"]
    L2["CODER_PROMPT"]
    L3["PROJECT_MAP"]
  end

  subgraph coder["Coder @coder"]
    C1["src/ scripts/ desktop/\nтолько файлы из промпта"]
  end

  subgraph mechanic["Mechanic @mechanic"]
    M1["чинит по тикету\n docs/problems/"]
  end

  subgraph designer["Designer @designer"]
    D1["docs/design/\nUI, макеты"]
  end

  owner -->|задача| lead
  lead -->|промпт| coder
  lead -->|бриф| designer
  lead -->|тикет| mechanic
  designer -->|DESIGN_BRIEF| coder
  coder -->|STATUS| lead
  mechanic -->|закрытие тикета| lead
```

---

## 4. Пульт — что не ломать

```mermaid
stateDiagram-v2
  [*] --> Idle: открыл vbs
  Idle --> Running: ▶ Старт
  Running --> Running: — свернуть окно\n(радар работает)
  Running --> Idle: ■ Стоп
  Running --> Idle: ✕ закрыть\n(должен = стоп)
  Idle --> [*]: закрыл окно

  note right of Running
    2 процесса: main + tg_main
    Не запускать bat параллельно
  end note
```

---

## Красивая картинка (PNG — без Figma)

**Готово (Designer):** [`../design/rawlead/project-map-owner.png`](../design/rawlead/project-map-owner.png) — одна страница: пульт, 2 процесса, acc1–3, бот, роли Lead/Coder/Mechanic. Исходник: `docs/design/rawlead/project-map-owner.svg`.

Mermaid в Markdown — **бесплатно и уже здесь** (Preview в Cursor). Figma **не нужна**.

| Способ | Стоимость | Как |
|--------|-----------|-----|
| **PNG выше** | 0 | открыть как картинку |
| **Preview этого файла** | 0 | Cursor `Ctrl+Shift+V` — 4 схемы сразу |
| **[Mermaid Live](https://mermaid.live)** | 0 | вставить блок `mermaid` → Export PNG |
| **[Excalidraw](https://excalidraw.com)** | 0 | правки → Export PNG → `docs/design/rawlead/` |

Правка большой схемы — чат **`@designer`** + SVG в `docs/design/rawlead/`.

---

_Lead · 2026-05-24_
