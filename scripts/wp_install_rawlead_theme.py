#!/usr/bin/env python3
"""Копирует rawlead-kadence-child в Local WP, ставит Kadence, активирует child."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME_SRC = ROOT / "wordpress" / "rawlead-kadence-child"
CHILD_SLUG = "rawlead-kadence-child"
PARENT_SLUG = "kadence"

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


def _ensure_db_host() -> None:
    port = "10008"
    if LOCAL_SITES_JSON.is_file():
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
    wp_cli("config", "set", "DB_HOST", f"127.0.0.1:{port}", "--quiet")


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


def copy_theme() -> Path:
    dest = LOCAL_SITE / "wp-content" / "themes" / CHILD_SLUG
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(THEME_SRC, dest)
    return dest


def _download_kadence_zip() -> bool:
    """Fallback when wp-cli has no SSL transports."""
    import urllib.request
    import zipfile

    themes_dir = LOCAL_SITE / "wp-content" / "themes"
    kadence_dir = themes_dir / PARENT_SLUG
    if (kadence_dir / "style.css").is_file():
        print(f"Тема {PARENT_SLUG} уже в themes/ (zip).")
        return True
    url = "https://downloads.wordpress.org/theme/kadence.latest-stable.zip"
    zip_path = themes_dir / "_kadence_dl.zip"
    try:
        print(f"Скачиваю {PARENT_SLUG} (fallback)...")
        urllib.request.urlretrieve(url, zip_path)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(themes_dir)
        zip_path.unlink(missing_ok=True)
        return (kadence_dir / "style.css").is_file()
    except OSError as exc:
        print(f"Zip fallback failed: {exc}")
        return False


def install_kadence() -> bool:
    listed = wp_cli("theme", "list", "--field=name", "--status=inactive")
    active = wp_cli("theme", "list", "--field=name", "--status=active")
    names = set()
    for r in (listed, active):
        if r.returncode == 0 and r.stdout:
            names.update(line.strip() for line in r.stdout.splitlines() if line.strip())
    if PARENT_SLUG in names:
        print(f"Тема {PARENT_SLUG} уже установлена.")
        return True
    r = wp_cli("theme", "install", PARENT_SLUG)
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip()
        print(f"Не удалось установить {PARENT_SLUG}:", err[:400])
        return False
    print(f"Установлена тема {PARENT_SLUG}.")
    return True


def activate_child() -> bool:
    r = wp_cli("theme", "activate", CHILD_SLUG)
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip()
        print("Активация child:", err[:400])
        return False
    print(f"Активна тема: {CHILD_SLUG}")
    return True


def ensure_menu() -> None:
    r = wp_cli("menu", "list", "--fields=name,slug", "--format=csv")
    if r.returncode != 0 or "RawLead" not in (r.stdout or ""):
        print("Меню RawLead не найдено — активируй плагин rawlead-landing (wp_skeleton_setup.py).")
        return
    menus = wp_cli("menu", "list", "--format=json")
    if menus.returncode != 0:
        return
    try:
        data = json.loads(menus.stdout or "[]")
    except json.JSONDecodeError:
        return
    menu_id = None
    for item in data:
        if item.get("name") == "RawLead":
            menu_id = item.get("term_id")
            break
    if not menu_id:
        return
    locs = wp_cli("theme", "mod", "get", "nav_menu_locations", "--format=json")
    # Kadence primary location
    wp_cli(
        "menu",
        "location",
        "assign",
        "RawLead",
        "primary",
        "--quiet",
    )
    print("Menu RawLead -> location primary (if registered).")


def main() -> int:
    if not LOCAL_SITE.is_dir():
        print(f"Нет папки сайта: {LOCAL_SITE}")
        return 1
    if not THEME_SRC.is_dir():
        print(f"Нет темы в репо: {THEME_SRC}")
        return 1

    dest = copy_theme()
    print(f"Child theme скопирован: {dest}")

    _ensure_db_host()
    probe = wp_cli("option", "get", "siteurl")
    if probe.returncode != 0:
        print(
            "Local MySQL недоступен. Запусти сайт radarzakaz (Start), затем повтори скрипт.\n"
            "Или: WP Admin → Плагины → RawLead Landing; Внешний вид → установи Kadence → активируй child."
        )
        return 1

    if not install_kadence() and not _download_kadence_zip():
        return 1
    if not activate_child():
        return 1
    ensure_menu()

    site = wp_cli("option", "get", "siteurl")
    if site.returncode == 0:
        print(f"Сайт: {site.stdout.strip()}")
    print("Проверка: главная светлая, hero «Лиды без шума», блок поток FL/Kwork/TG.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
