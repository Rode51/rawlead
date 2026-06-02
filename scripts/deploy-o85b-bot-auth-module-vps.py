#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

root = Path(__file__).resolve().parents[1]
files = ("src/bot_auth.py", "src/api_server.py", "src/telegram_control.py")
remotes = []
for rel in files:
    remote = "/opt/rawlead/" + rel.replace("\\", "/")
    ssh.upload(root / rel, remote)
    remotes.append(remote)
    print("up", rel)
ssh.run("chown rawlead:rawlead " + " ".join(remotes))
_, out, _ = ssh.run(
    "systemctl restart rawlead-api rawlead-bot-poll && sleep 4 && "
    "systemctl is-active rawlead-api rawlead-bot-poll && "
    "curl -sf http://127.0.0.1:8000/health; echo && "
    "cd /opt/rawlead && sudo -u rawlead .venv/bin/python -c "
    "'import sys; sys.path.insert(0,\"src\"); from bot_auth import authorize_bot_auth_session; print(\"import_ok\")' && "
    "curl -sf -o /dev/null -w 'wp=%{http_code}\\n' "
    "-X POST https://rawlead.ru/wp-json/rawlead/v1/auth/bot-session "
    "-H 'Content-Type: application/json' -d '{}'",
    check=False,
)
print(out or "")
