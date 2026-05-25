#!/usr/bin/env python3
"""Копирует rawlead-landing в Local WP и активирует через WP-CLI (если MySQL запущен)."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_SRC = ROOT / "wordpress" / "rawlead-landing"
SKELETON = ROOT / "docs" / "archive" / "wp-skeleton"
CONTENT_OUT = PLUGIN_SRC / "content"

LOCAL_SITE = Path.home() / "Local Sites" / "radarzakaz" / "app" / "public"
LOCAL_SITES_JSON = Path.home() / "AppData" / "Roaming" / "Local" / "sites.json"
LOCAL_PHP = Path(
    r"C:\Users\hramo\AppData\Local\Programs\Local\resources\extraResources"
    r"\lightning-services\php-8.2.29+0\bin\win64\php.exe"
)
LOCAL_EXT = LOCAL_PHP.parent / "ext"
WP_CLI = Path(
    r"C:\Users\hramo\AppData\Local\Programs\Local\resources\extraResources"
    r"\bin\wp-cli\wp-cli.phar"
)

PAGES = [
    ("home", "Главная", "home.md"),
    ("how", "Как работает", "how.md"),
    ("pricing", "Тарифы", "pricing.md"),
    ("faq", "Вопросы", "faq.md"),
    ("contact", "Контакты", "contact.md"),
]


def md_to_html(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    out: list[str] = []
    in_ul = False
    in_table = False
    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if in_table:
                out.append("</tbody></table>")
                in_table = False
            continue
        if line.startswith("## "):
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f"<h2>{_esc(line[3:].strip())}</h2>")
            continue
        if line.startswith("### "):
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f"<h3>{_esc(line[4:].strip())}</h3>")
            continue
        if line.startswith("|") and "|" in line[1:]:
            if re.match(r"^\|[\s\-:|]+\|$", line):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not in_table:
                out.append("<table><tbody>")
                in_table = True
                tag = "th" if cells and cells[0] else "td"
            else:
                tag = "td"
            row = "".join(f"<{tag}>{_inline(c)}</{tag}>" for c in cells)
            out.append(f"<tr>{row}</tr>")
            continue
        if line.startswith("- "):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{_inline(line[2:].strip())}</li>")
            continue
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_table:
            out.append("</tbody></table>")
            in_table = False
        out.append(f"<p>{_inline(line.strip())}</p>")
    if in_ul:
        out.append("</ul>")
    if in_table:
        out.append("</tbody></table>")
    return "\n".join(out)


def _esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _inline(s: str) -> str:
    s = _esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def build_content_files() -> None:
    CONTENT_OUT.mkdir(parents=True, exist_ok=True)
    for slug, _title, md_name in PAGES:
        md_path = SKELETON / md_name
        html = md_to_html(md_path.read_text(encoding="utf-8"))
        (CONTENT_OUT / f"{slug}.html").write_text(html, encoding="utf-8")


def copy_plugin() -> Path:
    dest = LOCAL_SITE / "wp-content" / "plugins" / "rawlead-landing"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(PLUGIN_SRC, dest)
    return dest


def _ensure_db_host() -> None:
    """Local MySQL слушает не 3306, а порт из sites.json (часто 10008)."""
    port = "10008"
    if LOCAL_SITES_JSON.is_file():
        import json

        try:
            sites = json.loads(LOCAL_SITES_JSON.read_text(encoding="utf-8"))
            for site in sites.values():
                if isinstance(site, dict) and "radarzakaz" in str(site.get("path", "")):
                    mysql = site.get("services", {}).get("mysql", {})
                    ports = mysql.get("ports", {}).get("MYSQL", [])
                    if ports:
                        port = str(ports[0])
                    break
        except (json.JSONDecodeError, OSError):
            pass
    host = f"127.0.0.1:{port}"
    wp_cli("config", "set", "DB_HOST", host, "--quiet")


def wp_cli(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [
        str(LOCAL_PHP),
        f"-dextension_dir={LOCAL_EXT}",
        "-dextension=mysqli",
        str(WP_CLI),
        f"--path={LOCAL_SITE}",
        *args,
    ]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def try_wp_activate() -> bool:
    if not LOCAL_SITE.is_dir():
        print(f"Нет папки сайта: {LOCAL_SITE}")
        return False
    _ensure_db_host()
    wp_cli("plugin", "deactivate", "fl-radar-landing", "--quiet")
    r = wp_cli("plugin", "activate", "rawlead-landing")
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip()
        print("WP-CLI:", err[:500])
        return False
    print(r.stdout.strip() or "Плагин активирован, страницы созданы хуком activation.")
    return True


def main() -> int:
    build_content_files()
    dest = copy_plugin()
    print(f"Плагин скопирован: {dest}")
    if try_wp_activate():
        site = wp_cli("option", "get", "siteurl")
        if site.returncode == 0:
            print(f"Сайт: {site.stdout.strip()}")
        return 0
    print(
        "\nLocal: zapusti sait RadarZakaz (Start), zatem:\n"
        "  .venv\\Scripts\\python.exe scripts\\wp_skeleton_setup.py\n"
        "Ili WP Admin -> Plaginy -> RawLead Landing -> Aktivirovat."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
