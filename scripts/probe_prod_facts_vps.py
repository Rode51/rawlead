#!/usr/bin/env python3
"""VPS read-only probe → update PROD_FACTS auto section (Lead after deploy)."""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import deploy_vps_ssh as ssh  # noqa: E402

PROD_FACTS = ROOT / "docs" / "team" / "common" / "PROD_FACTS.md"
MARKER_START = "<!-- AUTO:VPS_PROBE:START -->"
MARKER_END = "<!-- AUTO:VPS_PROBE:END -->"

REMOTE = r"""
set -e
echo '=== systemd ==='
for u in rawlead-radar rawlead-api rawlead-bot-poll; do
  printf '%s ' "$u"
  systemctl is-active "$u" 2>/dev/null || echo inactive
done
echo '=== env ==='
grep -E '^YOUDO_BROWSER=|^RADAR_PROFILE=' /opt/rawlead/.env.site 2>/dev/null | head -5 || true
echo '=== theme ==='
curl -fsS -m 15 https://rawlead.ru/lenta/ 2>/dev/null | grep -oE 'rawlead[^"]*ver=1\.[0-9.]+' | head -1 | grep -oE 'ver=1\.[0-9.]+' || curl -fsS -m 15 https://rawlead.ru/lenta/ 2>/dev/null | grep -oE 'ver=1\.[0-9.]+' | head -1 || echo ver=unknown
echo '=== youdo last ok ==='
grep 'youdo:trace stage=fetch_end' /opt/rawlead/data/radar_site.log 2>/dev/null | grep 'kind=ok' | tail -1 || echo none
echo '=== o254 marker ==='
grep -c 'youdo_browser_teardown' /opt/rawlead/src/exchange_browser_fetch.py 2>/dev/null || echo 0
echo '=== tg join pending ==='
grep -c ',pending,' /opt/rawlead/docs/ops/TG_JOIN_QUEUE_v4.csv 2>/dev/null || echo 0
"""


def _parse_remote(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    section = ""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("=== "):
            section = line.strip("= ")
            continue
        if not line or line.startswith("---"):
            continue
        if section == "systemd":
            parts = line.split()
            if len(parts) >= 2:
                out[f"unit_{parts[0]}"] = parts[1]
        elif section == "env":
            if "=" in line:
                k, _, v = line.partition("=")
                out[k.strip()] = v.strip()
        elif section == "theme":
            out["theme_ver"] = line.replace("ver=", "") if "ver=" in line else line
        elif section == "youdo last ok":
            out["youdo_last_ok"] = line[:120] if line != "none" else "—"
        elif section == "o254 marker":
            out["o254_marker"] = line
        elif section == "tg join pending":
            out["tg_join_pending"] = line
    return out


def build_probe_block(data: dict[str, str]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    o254 = int(data.get("o254_marker") or "0") >= 1
    lines = [
        MARKER_START,
        f"**Probe:** {now} · `python scripts/probe_prod_facts_vps.py --write`",
        "",
        "| Unit | State |",
        "|------|-------|",
        f"| rawlead-radar | {data.get('unit_rawlead-radar', '?')} |",
        f"| rawlead-api | {data.get('unit_rawlead-api', '?')} |",
        f"| rawlead-bot-poll | {data.get('unit_rawlead-bot-poll', '?')} |",
        "",
        f"- **YOUDO_BROWSER:** `{data.get('YOUDO_BROWSER', '?')}`",
        f"- **RADAR_PROFILE:** `{data.get('RADAR_PROFILE', '?')}`",
        f"- **Theme prod `ver`:** `{data.get('theme_ver', '?')}`",
        f"- **Last YouDo ok:** {data.get('youdo_last_ok', '—')}",
        f"- **O254 code on VPS:** {'✅' if o254 else '❌'} (`youdo_browser_teardown`)",
        f"- **TG join v4 pending:** {data.get('tg_join_pending', '?')}",
        "",
        MARKER_END,
    ]
    return "\n".join(lines)


def write_prod_facts(block: str) -> None:
    text = PROD_FACTS.read_text(encoding="utf-8")
    pattern = re.compile(
        re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END),
        re.DOTALL,
    )
    if not pattern.search(text):
        raise SystemExit(f"Markers not found in {PROD_FACTS}")
    new_text = pattern.sub(block, text, count=1)
    date_line = re.compile(r"^\*\*Обновлено:\*\*.*$", re.MULTILINE)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    new_text = date_line.sub(
        f"**Обновлено:** {today} (probe_prod_facts_vps --write)",
        new_text,
        count=1,
    )
    PROD_FACTS.write_text(new_text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe VPS → PROD_FACTS auto block")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Replace AUTO block in docs/team/common/PROD_FACTS.md",
    )
    args = parser.parse_args()

    _, out, err = ssh.run(REMOTE.strip(), check=False)
    raw = (out or err or "").strip()
    if not raw:
        print("VPS probe failed: empty output", file=sys.stderr)
        return 1

    data = _parse_remote(raw)
    block = build_probe_block(data)
    print(block)

    if args.write:
        write_prod_facts(block)
        print(f"\nUpdated {PROD_FACTS}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
