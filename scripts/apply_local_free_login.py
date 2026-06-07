#!/usr/bin/env python3
"""Copy BrowserSync login snippet for minted free token (local only)."""
from __future__ import annotations

import sys
from pathlib import Path

_TOKEN = Path(__file__).resolve().parents[1] / "data" / "_local_free_token.txt"


def main() -> int:
    if not _TOKEN.is_file():
        print("Run first: .venv\\Scripts\\python.exe scripts\\mint_free_local_token.py --account acc2")
        return 1
    token = _TOKEN.read_text(encoding="utf-8").strip()
    if not token:
        print("Token file empty")
        return 1
    snippet = (
        "localStorage.setItem('rawlead_access_token',"
        + repr(token)
        + ");document.cookie='rl_access='+encodeURIComponent("
        + repr(token)
        + ")+'; path=/; max-age=604800; samesite=lax';location.reload();"
    )
    try:
        import pyperclip  # type: ignore

        pyperclip.copy(snippet)
        print("Snippet copied to clipboard. On http://localhost:3011/lenta/ → F12 → Console → Ctrl+V → Enter")
    except Exception:
        out = Path(__file__).resolve().parents[1] / "data" / "_local_free_login_snippet.js"
        out.write_text(snippet + "\n", encoding="utf-8")
        print(f"Paste in browser console from: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
