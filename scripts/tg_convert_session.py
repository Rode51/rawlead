"""Pyrogram .session → Telethon (рядом *_telethon.session)."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))


def main() -> None:
    if len(sys.argv) < 2:
        print("Использование: python scripts/tg_convert_session.py PATH_WITHOUT_EXT")
        print("Пример: python scripts/tg_convert_session.py C:/Users/.../Parser/+66953964608")
        raise SystemExit(1)

    base = Path(sys.argv[1])
    src = base if base.suffix == ".session" else Path(f"{base}.session")
    if not src.is_file():
        print(f"Нет файла: {src}")
        raise SystemExit(1)

    dst = src.with_name(f"{src.stem}_telethon.session")
    from session_converter import SessionManager

    SessionManager.from_pyrogram_session_file(str(src)).telethon_file(str(dst))
    print(dst)


if __name__ == "__main__":
    main()
