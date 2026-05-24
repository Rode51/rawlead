# Пул MCP — внешние инструменты для AI

**Канон:** когда и как подключать MCP-серверы в Cursor / Claude Code.  
**Секреты не в repo** — только в `~/.cursor/mcp.json` (Cursor) или `~/.claude.json` (Claude Code).

Шаблон конфига: [`mcp.pool.example.json`](mcp.pool.example.json)

---

## Для всех AI (правило)

| Ситуация | Действие |
|----------|----------|
| MCP **уже включён** в сессии (видны tools) | Используй по таблице § «Когда какой» |
| MCP **нет**, а задача требует веб/браузер/скрейп/картинки | **Не выдумывай** результат — напиши владельцу: какой сервер из пула включить + ссылка на этот файл |
| Нужен только **факт из repo** | Файлы `docs/`, код — без Perplexity |
| Конкуренты / чужой сайт **без** API | Firecrawl или Playwright; Perplexity — для сводок и новостей |
| **Уже открыт** сайт в Chrome, логин есть | Chrome (`claude-in-chrome`) или Playwright — не дублировать без нужды |

**Lead / Coder / Mechanic:** не коммитить API-ключи; не добавлять `mcp.json` в корень репо с ключами.

---

## Пять серверов (кратко)

| # | Имя | Зачем | OSS | Деньги |
|---|-----|-------|-----|--------|
| 1 | **Perplexity** | Поиск и ответы по интернету в реальном времени | [ppl-ai/modelcontextprotocol](https://github.com/perplexityai/modelcontextprotocol) | Нужен **API key** [Perplexity API](https://www.perplexity.ai/settings/api) |
| 2 | **Playwright** | Автоматизация браузера: формы, E2E, скриншоты, a11y-снимки | [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | Бесплатно (Node 18+) |
| 3 | **Firecrawl** | Скрапинг URL → markdown в контекст (конкуренты, лендинги) | [firecrawl/firecrawl-mcp-server](https://github.com/firecrawl/firecrawl-mcp-server) | API key; есть [free tier](https://firecrawl.dev) |
| 4 | **Glif** | Картинки/видео через workflow glif.app (много моделей) | [glifxyz/glif-mcp-server](https://github.com/glifxyz/glif-mcp-server) | Токен [glif.app/settings/api-tokens](https://glif.app/settings/api-tokens) |
| 5 | **Chrome (Claude in Chrome)** | Текущие вкладки, логин, консоль — из Claude Code | Встроено в Claude Code (не отдельный npm) | План Anthropic + расширение Chrome |

> «Все бесплатные» в постах — **серверы** часто open source, но Perplexity / Firecrawl / Glif **съедают квоты API**. Playwright и Chrome MCP — без отдельного SaaS за скрап (кроме плана Claude для Chrome).

---

## Когда какой (для агентов)

| Задача | Первый выбор | Запасной |
|--------|--------------|----------|
| Актуальные новости, цены, «что сейчас в сети» | Perplexity | — |
| Скачать **структурированно** страницу / сайт в markdown | Firecrawl | Playwright `get_page_content` |
| E2E-тест пульта, клики, регресс UI | Playwright | Chrome MCP |
| Сайт уже открыт, нужен **ваш** логин / cookies | Chrome MCP | Playwright (чистый профиль) |
| Иконка, мокап, картинка для `docs/design/` | Glif | Владелец вручную / Designer |
| Данные **только** из этого репо | — (без MCP) | — |

**RawLead-специфика:** runtime TG, `.env`, `data/` — MCP не заменяет; смотри `docs/ops/`, `STATUS.md`.

---

## Установка (владелец, один раз)

### Cursor (Windows)

Файл: `%USERPROFILE%\.cursor\mcp.json`

Settings → **Features → MCP** → Edit JSON, или скопировать из [`mcp.pool.example.json`](mcp.pool.example.json) и подставить ключи.

После правки — **перезапуск Cursor** или Reload MCP.

### Claude Code

```powershell
# Perplexity
claude mcp add perplexity --env PERPLEXITY_API_KEY="ВАШ_КЛЮЧ" -- npx -y @perplexity-ai/mcp-server

# Playwright
claude mcp add playwright npx @playwright/mcp@latest

# Firecrawl
claude mcp add firecrawl --env FIRECRAWL_API_KEY="fc-..." -- npx -y firecrawl-mcp

# Glif
claude mcp add glif --env GLIF_API_TOKEN="..." -- npx -y @glifxyz/glif-mcp-server@latest
```

Chrome: `claude --chrome` или в сессии `/chrome` → Enabled.  
Док: [Use Claude Code with Chrome](https://code.claude.com/docs/en/chrome) · расширение [Claude in Chrome](https://chromewebstore.google.com) · CC ≥ 2.0.73, ext ≥ 1.0.36.

### Уже в проекте

| MCP | Назначение |
|-----|------------|
| **Neon** | Postgres (облако) — если включён в Cursor |

Не путать Neon (БД) с веб-MCP из этого пула.

---

## Playwright vs Chrome MCP

| | Playwright MCP | Chrome (claude-in-chrome) |
|--|----------------|---------------------------|
| Профиль | Отдельный / headless | **Ваш** Chrome, сессии |
| Где | Cursor, Claude Code, VS Code | В основном **Claude Code** |
| Лучше для | CI-подобные тесты, скрейп без логина | Дебаг пульта, формы под вашим аккаунтом |

Для **desktop/** пульта: сначала локальный `http://127.0.0.1:18765` + Playwright; если нужен залогиненный SaaS — Chrome MCP.

---

## Ограничения и безопасность

- Ключи — только локально; не в `git`, не в `CODER_PROMPT`, не в чат.
- Firecrawl / Playwright на **чужих** сайтах — уважать ToS и rate limit.
- Glif — платные генерации на аккаунте glif.app.
- Perplexity — токены API на вашем счёте.

---

## Чеклист владельца

- [ ] Node.js 18+ (`node -v`)
- [ ] Скопирован [`mcp.pool.example.json`](mcp.pool.example.json) → `%USERPROFILE%\.cursor\mcp.json`
- [ ] Ключи Perplexity / Firecrawl / Glif (по необходимости)
- [ ] Playwright: `npx @playwright/mcp@latest` один раз отработал без ошибки
- [ ] Claude Code: при необходимости `claude --chrome` + расширение
- [ ] В чате агенту: «смотри `docs/team/MCP_POOL.md`»

---

## Ссылки

| Сервер | Документация |
|--------|----------------|
| Perplexity | https://docs.perplexity.ai/docs/getting-started/integrations/mcp-server |
| Playwright | https://playwright.dev/docs/getting-started-mcp |
| Firecrawl | https://github.com/firecrawl/firecrawl-mcp-server |
| Glif | https://github.com/glifxyz/glif-mcp-server |
| Chrome | https://code.claude.com/docs/en/chrome |

---

_Ведёт Lead · 2026-05-24 · общий пул для всех проектов владельца_
