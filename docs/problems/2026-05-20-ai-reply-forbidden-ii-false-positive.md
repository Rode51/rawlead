# ИИ: «Разбор недоступен» из‑за «ии» в «вентиляции»

**Статус:** решено

## Симптом
TG с полным MVP + «📋 Задача», но **«⚠️ Разбор ИИ недоступен»** вместо блока «🤖 Разбор». Пример: Kwork «Разработать автоматику ИТП», бюджет до 50 000 ₽.

Дубль в блоке задачи: `📋 Задача:` + снова `Задача:` (snippet Kwork).

## Ожидалось
OpenRouter отвечает → полный разбор с `work_summary`, `money`, откликом.

## Фактически
`_validate_reply_draft`: regex `ии` срабатывал на подстроку в **«вентил…ии»** → parse fail ×2 → `analyze()` → `None` → fallback.

## Контекст
ИИ v3, `google/gemini-2.5-flash-lite`, Windows.

---

## Решение (заполняет Mechanic)

**Статус:** решено  
**Дата:** 2026-05-20

### Причина
`_FORBIDDEN_REPLY_RE` искал `ии` как подстроку, без границ слова.

### Что сделано
- `src/ai_analyze.py`: «ИИ»/«агент» — только отдельное слово (`(?<![а-яё…])ии(?![а-яё…])`).
- `src/telegram_notify.py`: снятие ведущего «Задача:» из snippet/summary перед блоком «📋 Задача».

### Изменённые файлы
- `src/ai_analyze.py`
- `src/telegram_notify.py`

### Как проверить
```powershell
python -c "import sys;sys.path.insert(0,'src');from config import load_config;from ai_analyze import analyze;c=load_config();r=analyze(c,title='ИТП',budget_text='50000',description='автоматика ИТП и вентиляции',url='https://kwork.ru/x');print('OK' if r else 'FAIL')"
```
→ `OK`, не `FAIL`.
