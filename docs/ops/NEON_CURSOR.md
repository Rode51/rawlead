# Neon + Cursor (как Supabase MCP)

Два уровня — оба нужны для радара:

| Уровень | Зачем |
|---------|--------|
| **`DATABASE_URL` в `.env`** | Радар (Python) пишет лиды |
| **MCP Neon в Cursor** | Coder/агент: таблицы, SQL, миграции из чата |

---

## Подключить MCP (рекомендуется)

В терминале **корня проекта** (`uisness`).

**Windows:** если PowerShell ругается на `npx.ps1` (execution policy), используй **один** из вариантов:

```powershell
npx.cmd neonctl@latest init
```

или **cmd** (не PowerShell):

```cmd
cd C:\Users\hramo\uisness
npx neonctl@latest init
```

или один раз в PowerShell (только для тебя):

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
npx neonctl@latest init
```

После успеха:

- OAuth в браузере
- Перезапусти Cursor
- В чате: «Get started with Neon»

**Без терминала:** Cursor → **Settings → MCP** → добавить сервер **Neon** (Install / [документация](https://neon.com/docs/ai/neon-mcp-server)) — OAuth в браузере.

Гайд: [cursor-mcp-neon](https://neon.com/guides/cursor-mcp-neon)

---

## Отличие от Supabase MCP

| | Supabase plugin | Neon MCP |
|---|-----------------|----------|
| Проекты | Лимит 2 на Free | Отдельный аккаунт Neon |
| REST для WP | Было удобно | Через Python API позже |
| SQL из Cursor | ✅ `execute_sql` | ✅ через Neon MCP |
| Радар Python | SDK / URL | `DATABASE_URL` |

Плагин **Supabase** в Cursor можно **не отключать** для старых проектов; для **FL Radar** используем **Neon**.

---

## `.env` (обязательно для кода)

**Не путать:**

| В Neon Console | Для чего | В `.env`? |
|----------------|----------|-----------|
| **Connection string** (`postgresql://…`) | Радар Python | ✅ **`DATABASE_URL=`** |
| **Data API / REST** (`…apirest…/rest/v1`) | HTTP как у Supabase REST | ❌ не для радара (позже WP) |

Скопировать: Dashboard → проект → **Connect** → **Connection string** → вкладка **Python** или **psql**.

Пример вида:

```
DATABASE_URL=postgresql://user:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require
```

MCP **не заменяет** строку в `.env`.

---

## MCP не подключается — вручную

В репозитории уже лежит **`.cursor/mcp.json`** (Neon HTTP). После правок — **Reload Window** или перезапуск Cursor.

Без UI / `neonctl init`:

1. Cursor → **Settings** → **MCP** (или Features → MCP).
2. **Add new MCP server** → тип **HTTP** / Remote.
3. URL: `https://mcp.neon.tech/mcp`
4. Сохранить → **перезапуск Cursor** → при первом запросе — OAuth в браузере.

Если сервер красный: отключи VPN, перелогинься в Neon в браузере.

**MCP не обязателен** для старта — достаточно `DATABASE_URL` + Coder. SQL можно в [Neon SQL Editor](https://console.neon.tech) в браузере.

---

_Секреты в Git не коммитить._
