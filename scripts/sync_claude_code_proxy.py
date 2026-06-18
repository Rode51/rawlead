"""Синхронизация прокси Claude Code через тот же relay, что и Cursor.

Пишет HTTP_PROXY / HTTPS_PROXY в %USERPROFILE%\\.claude\\settings.json
и опционально npm proxy (для install / uipro).

Запуск:
  .venv\\Scripts\\python.exe scripts\\sync_claude_code_proxy.py
  .venv\\Scripts\\python.exe scripts\\sync_claude_code_proxy.py --npm
  .venv\\Scripts\\python.exe scripts\\sync_claude_code_proxy.py --probe-only
  .venv\\Scripts\\python.exe scripts\\sync_claude_code_proxy.py --off
  scripts\\sync-claude-code-proxy.bat
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from dotenv import load_dotenv  # noqa: E402

_CLAUDE_SETTINGS = Path.home() / ".claude" / "settings.json"
_MANAGED_ENV_KEYS = ("HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY")
_NO_PROXY_VALUE = "localhost,127.0.0.1"


def _load_settings(path: Path) -> dict:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8-sig")
    text = re.sub(r"/\*[\s\S]*?\*/", "", text)
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    return json.loads(text)


def _save_settings(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _relay_port() -> int:
    raw = os.environ.get("CURSOR_PROXY_RELAY_PORT", "18777").strip()
    try:
        return max(1024, min(65535, int(raw)))
    except ValueError:
        return 18777


def _relay_url() -> str:
    return f"http://127.0.0.1:{_relay_port()}"


def _apply_proxy_env(settings: dict, proxy_url: str) -> None:
    env = settings.setdefault("env", {})
    if not isinstance(env, dict):
        env = {}
        settings["env"] = env
    env["HTTP_PROXY"] = proxy_url
    env["HTTPS_PROXY"] = proxy_url
    env["NO_PROXY"] = _NO_PROXY_VALUE


def _clear_proxy_env(settings: dict) -> None:
    env = settings.get("env")
    if not isinstance(env, dict):
        return
    for key in _MANAGED_ENV_KEYS:
        env.pop(key, None)
    if not env:
        settings.pop("env", None)


def _sync_npm_proxy(proxy_url: str, *, clear: bool = False) -> int:
    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    try:
        if clear:
            for key in ("proxy", "https-proxy"):
                subprocess.run([npm, "config", "delete", key], check=False, capture_output=True)
            print("npm: proxy удалён (direct registry)")
            return 0
        subprocess.run([npm, "config", "set", "proxy", proxy_url], check=True, capture_output=True)
        subprocess.run([npm, "config", "set", "https-proxy", proxy_url], check=True, capture_output=True)
        print(f"npm: proxy -> {proxy_url}")
        return 0
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"npm: не удалось обновить proxy — {exc}", file=sys.stderr)
        return 1


def _probe_relay_pool() -> int:
    probe = _ROOT / "scripts" / "cursor_proxy_relay.py"
    if not probe.is_file():
        print("FAIL: нет scripts/cursor_proxy_relay.py", file=sys.stderr)
        return 1
    py = sys.executable
    result = subprocess.run([py, str(probe), "--probe-only"], cwd=_ROOT)
    return result.returncode


def main() -> int:
    load_dotenv(_ROOT / ".env")

    parser = argparse.ArgumentParser(description="Sync Claude Code proxy via Cursor relay")
    parser.add_argument("--probe-only", action="store_true", help="TCP probe upstream pool")
    parser.add_argument("--off", action="store_true", help="Убрать proxy из Claude Code и npm")
    parser.add_argument("--npm", action="store_true", help="Также прописать npm proxy")
    parser.add_argument(
        "--relay",
        action="store_true",
        help="Всегда 127.0.0.1:CURSOR_PROXY_RELAY_PORT (как install bat)",
    )
    args = parser.parse_args()

    if args.probe_only:
        return _probe_relay_pool()

    settings = _load_settings(_CLAUDE_SETTINGS)

    if args.off:
        _clear_proxy_env(settings)
        _save_settings(_CLAUDE_SETTINGS, settings)
        print("Claude Code: proxy убран из settings.json")
        print(f"Файл: {_CLAUDE_SETTINGS}")
        if args.npm:
            return _sync_npm_proxy("", clear=True)
        return 0

    use_relay = args.relay or os.environ.get("CURSOR_PROXY_RELAY", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )
    if use_relay:
        proxy_url = _relay_url()
        _apply_proxy_env(settings, proxy_url)
        _save_settings(_CLAUDE_SETTINGS, settings)
        print(f"Claude Code: relay -> {proxy_url}")
        print("Запусти relay: scripts\\start-cursor-proxy-relay.bat")
        print(f"Файл: {_CLAUDE_SETTINGS}")
        if args.npm:
            return _sync_npm_proxy(proxy_url)
        return 0

    direct = os.environ.get("CURSOR_PROXY_URL", "").strip()
    if not direct:
        print(
            "CURSOR_PROXY_RELAY=0 и нет CURSOR_PROXY_URL — нечего прописать.",
            file=sys.stderr,
        )
        return 1
    _apply_proxy_env(settings, direct)
    _save_settings(_CLAUDE_SETTINGS, settings)
    print(f"Claude Code: direct proxy -> {direct}")
    print(f"Файл: {_CLAUDE_SETTINGS}")
    if args.npm:
        return _sync_npm_proxy(direct)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
