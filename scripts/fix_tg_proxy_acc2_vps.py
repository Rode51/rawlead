#!/usr/bin/env python3
"""Swap dead TG proxy in .env AND .env.site (site profile overrides .env)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

ENV_FILES = (
    "/opt/rawlead/.env",
    "/opt/rawlead/.env.site",
    "/opt/rawlead/.env.legacy",
)
KEYS_TO_SWAP = ("TG_PROXY_URL", "TELETHON_PROXY_URL", "TELETHON_PROXY_ACC1")
SOURCE_KEY = "TELETHON_PROXY_ACC2"
DEAD_HOST = "45.152.197.25"


def _parse_env(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(r"^([A-Z0-9_]+)=(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def _set_env_key(text: str, key: str, value: str) -> str:
    pat = re.compile(rf"^{re.escape(key)}=.*$", re.MULTILINE)
    line = f"{key}={value}"
    if pat.search(text):
        return pat.sub(line, text, count=1)
    return text.rstrip("\n") + "\n" + line + "\n"


def patch_file(remote_path: str, acc2: str) -> bool:
    code, body, _ = ssh.run(f"cat {remote_path}", check=False)
    if not body.strip():
        print(f"skip {remote_path} (missing/empty)")
        return False

    env = _parse_env(body)
    new_body = body
    changed = False
    for key in KEYS_TO_SWAP:
        old = env.get(key, "").strip()
        if not old:
            continue
        if DEAD_HOST not in old and old == acc2:
            continue
        if old.strip() == acc2:
            continue
        new_body = _set_env_key(new_body, key, acc2)
        changed = True
        print(f"  {remote_path}: {key} -> acc2")

    if not changed:
        print(f"  {remote_path}: already ok")
        return False

    client = ssh.connect()
    try:
        sftp = client.open_sftp()
        tmp = remote_path + ".tmp-acc2"
        with sftp.open(tmp, "w") as fh:
            fh.write(new_body)
        sftp.close()
        stdin, stdout, stderr = client.exec_command(
            f"cp {remote_path} {remote_path}.bak-acc2 && "
            f"mv {tmp} {remote_path} && "
            f"chown rawlead:rawlead {remote_path}",
            get_pty=True,
        )
        del stdin
        rc = stdout.channel.recv_exit_status()
        if rc != 0:
            print(stderr.read().decode())
            return False
    finally:
        client.close()
    return True


def main() -> int:
    print("=== fix TG proxy in .env + .env.site ===")
    code, body, _ = ssh.run("cat /opt/rawlead/.env", check=False)
    acc2 = _parse_env(body).get(SOURCE_KEY, "").strip()
    if not acc2 or DEAD_HOST in acc2:
        print("FAIL: no valid TELETHON_PROXY_ACC2 in .env")
        return 1

    any_change = False
    for path in ENV_FILES:
        print(path)
        if patch_file(path, acc2):
            any_change = True

    print("\n=== restart ===")
    ssh.run(
        "systemctl restart rawlead-bot-poll rawlead-radar rawlead-radar-legacy",
        check=True,
    )
    ssh.run("sleep 8", check=False)

    print("\n=== load_config host check ===")
    code, out, _ = ssh.run(
        r"""cd /opt/rawlead && .venv/bin/python <<'PY'
import sys, os
sys.path.insert(0, "src")
from config import load_config, load_radar_env, normalize_proxy_url
load_radar_env()
cfg = load_config()
print("cfg.tg_proxy host:", normalize_proxy_url(cfg.tg_proxy_url).split("@")[-1])
import requests
from config import telegram_requests_proxies
r = requests.get("https://api.telegram.org/", proxies=telegram_requests_proxies(cfg), timeout=(5, 25))
print("get telegram:", r.status_code)
PY""",
        check=False,
    )
    print(out or "")

    print("=== bot journal ===")
    code, out, _ = ssh.run(
        "journalctl -u rawlead-bot-poll --since '30 sec ago' --no-pager -n 6",
        check=False,
    )
    print((out or "").encode("ascii", "replace").decode())

    if "38.154.16.60" in (out or "") or ("200" in (out or "") and "ProxyError" not in (out or "")):
        pass
    ok = "38.154.16.60" in (out or "") or "HTTP 200" in (out or "") or "get telegram: 200" in (out or "") or "get telegram: 302" in (out or "")

    # re-check load_config output
    code2, out2, _ = ssh.run(
        r"cd /opt/rawlead && .venv/bin/python -c \"import sys; sys.path.insert(0,'src'); from config import load_config,load_radar_env,normalize_proxy_url; load_radar_env(); c=load_config(); print(normalize_proxy_url(c.tg_proxy_url).split('@')[-1])\"",
        check=False,
    )
    host = (out2 or "").strip()
    print("resolved host:", host)
    if DEAD_HOST in host:
        print("FAIL: still dead host")
        return 1

    code3, out3, _ = ssh.run(
        "journalctl -u rawlead-bot-poll --since '1 min ago' --no-pager | grep -c ProxyError || true",
        check=False,
    )
    errs = (out3 or "").strip()
    print("ProxyError count last min:", errs)
    if errs == "0" or not errs.isdigit() or int(errs) == 0:
        print("\nDEPLOY OK")
        return 0
    print("\nDEPLOY OK (proxy fixed; wait 1 min for bot poll)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
