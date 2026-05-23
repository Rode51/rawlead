# Cursor Universal — роли для любого проекта

Скопируй этот каталог в **новый** репозиторий и запусти установку.

## Быстрый старт

```powershell
cd C:\path\to\new-project
Copy-Item -Recurse C:\Users\hramo\uisness\templates\cursor-universal .\cursor-universal-tmp
.\cursor-universal-tmp\INSTALL.ps1 -TargetRoot (Get-Location)
Remove-Item -Recurse .\cursor-universal-tmp
```

Или из **этого** шаблона напрямую:

```powershell
cd C:\path\to\new-project
C:\Users\hramo\uisness\templates\cursor-universal\INSTALL.ps1 -TargetRoot C:\path\to\new-project
```

## Что ставится

| Откуда | Куда |
|--------|------|
| `cursor-rules/*.mdc` | `.cursor/rules/` |
| `docs-starter/*` | `docs/` (не перезаписывает существующие) |
| `scripts/backup.ps1`, `backup.bat` | `scripts/` |
| `scripts/backup.config.example.json` | `scripts/backup.config.example.json` |

## После установки

1. **Lead-чат:** `@lead-architect` (правило `.cursor/rules/lead-architect.mdc`)
2. Заполни `docs/FOR_YOU.md`, `docs/ROADMAP.md` под проект
3. `Copy-Item scripts\backup.config.example.json scripts\backup.config.json` → пути
4. Cursor: **Settings → Rules** → Project Rules включены

## Хранение шаблона

Держи копию папки `cursor-universal` на флешке или в `C:\Users\hramo\Templates\cursor-universal` — не привязано к FL Radar.
