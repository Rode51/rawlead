# RawLead Kadence Child

Child theme для Local WP: editorial light по [`docs/design/wp/REFERENCE.md`](../../docs/design/wp/REFERENCE.md).

**Родитель:** [Kadence](https://wordpress.org/themes/kadence/) (обязательно установить до активации child).

## Быстрая установка

```powershell
cd C:\Users\hramo\uisness
.venv\Scripts\python.exe scripts\wp_install_rawlead_theme.py
```

Или вручную: скопируй папку `rawlead-kadence-child` в:

`C:\Users\hramo\Local Sites\radarzakaz\app\public\wp-content\themes\`

Затем WP Admin → Внешний вид → Темы → активируй **RawLead Kadence Child**.

Подробно: [`docs/ops/WP_KADENCE_INSTALL.md`](../../docs/ops/WP_KADENCE_INSTALL.md).

## Что делает тема

| Файл | Роль |
|------|------|
| `front-page.php` | Главная по REFERENCE §3 (hero, поток, манифест, 01–03, аудитория, тарифы) |
| `assets/css/rawlead.css` | Токены §2, стили внутренних страниц |
| `patterns/*.php` | Block patterns для редактора (опционально) |
| `functions.php` | Inter, body class, CTA на how/pricing/faq/contact |

Плагин [`rawlead-landing`](../rawlead-landing/) создаёт страницы и меню — **не отключать**.
