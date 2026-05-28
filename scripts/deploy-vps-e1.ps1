# E1: API on VPS. Needs SSH key on server (see .env VPS_SSH_*).
param([switch]$SkipClone, [switch]$DryRun)
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

function Get-EnvLine([string]$key) {
    $p = Join-Path $Root ".env"
    if (-not (Test-Path $p)) { return $null }
    foreach ($line in Get-Content $p) {
        if ($line -match ('^\s*' + [regex]::Escape($key) + '\s*=\s*(.+)\s*$')) {
            return $Matches[1].Trim().Trim('"')
        }
    }
    return $null
}

$VpsHost = Get-EnvLine "VPS_SSH_HOST"
if (-not $VpsHost) { $VpsHost = "62.113.103.231" }
$User = Get-EnvLine "VPS_SSH_USER"
if (-not $User) { $User = "root" }
$Key = Get-EnvLine "VPS_SSH_KEY"
if (-not $Key) { $Key = "$env:USERPROFILE\.ssh\id_rawlead_vps" }
$Repo = Get-EnvLine "VPS_GIT_URL"
if (-not $Repo) { $Repo = "https://github.com/Rode51/uisness.git" }

$sshArgs = @("-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=15")
if (Test-Path $Key) { $sshArgs += @("-i", $Key) }
$Target = "$User@$VpsHost"

function Invoke-SshCmd([string]$cmd) {
    if ($DryRun) { Write-Host "[dry-run] ssh $Target -- $cmd"; return }
    & ssh @sshArgs $Target $cmd
    if ($LASTEXITCODE -ne 0) { throw "SSH failed (exit $LASTEXITCODE): $cmd" }
}

function Invoke-ScpFile([string]$local, [string]$remote) {
    if ($DryRun) { Write-Host "[dry-run] scp $local -> ${Target}:$remote"; return }
    & scp @sshArgs $local "${Target}:${remote}"
    if ($LASTEXITCODE -ne 0) { throw "SCP failed: $local" }
}

Write-Host "=== RawLead E1 -> $Target ==="

if (-not $DryRun) {
    & ssh @sshArgs -o BatchMode=yes $Target "echo OK" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "SSH denied. Add public key to VPS panel (SSH keys):"
        if (Test-Path "$Key.pub") { Get-Content "$Key.pub" }
        Write-Host "Or set VPS_SSH_PASSWORD in .env and use key-based auth after manual ssh-copy-id."
        Write-Host "Key file: $Key"
        exit 2
    }
}

& "$PSScriptRoot\prep-vps-env.ps1"

$setup = 'set -e; export DEBIAN_FRONTEND=noninteractive; apt-get update -qq; apt-get install -y -qq git python3 python3-venv python3-pip nginx certbot python3-certbot-nginx rsync; if ! swapon --show | grep -q swapfile; then fallocate -l 1G /swapfile 2>/dev/null || dd if=/dev/zero of=/swapfile bs=1M count=1024; chmod 600 /swapfile; mkswap /swapfile; swapon /swapfile; grep -q swapfile /etc/fstab || echo "/swapfile none swap sw 0 0" >> /etc/fstab; fi; id rawlead >/dev/null 2>&1 || adduser --disabled-password --gecos "" rawlead; mkdir -p /opt/rawlead/data/sessions; chown -R rawlead:rawlead /opt/rawlead'
Invoke-SshCmd $setup

if (-not $SkipClone) {
    Invoke-SshCmd "test -d /opt/rawlead/.git || sudo -u rawlead git clone $Repo /opt/rawlead"
    Invoke-SshCmd "cd /opt/rawlead; sudo -u rawlead git pull --ff-only"
}

$venv = 'cd /opt/rawlead; sudo -u rawlead test -d .venv || sudo -u rawlead python3 -m venv .venv; sudo -u rawlead .venv/bin/pip install -q -r requirements.txt; chmod +x deploy/run-radar-site.sh'
Invoke-SshCmd $venv

$staging = Join-Path $Root "data\vps-staging"
Invoke-ScpFile (Join-Path $staging ".env") "/opt/rawlead/.env"
Invoke-ScpFile (Join-Path $staging ".env.site") "/opt/rawlead/.env.site"
Invoke-SshCmd "chmod 600 /opt/rawlead/.env /opt/rawlead/.env.site; chown rawlead:rawlead /opt/rawlead/.env /opt/rawlead/.env.site"

$systemd = 'cp /opt/rawlead/deploy/systemd/rawlead-api.service /etc/systemd/system/; cp /opt/rawlead/deploy/systemd/rawlead-radar.service /etc/systemd/system/; systemctl daemon-reload; systemctl enable --now rawlead-api; ln -sf /opt/rawlead/deploy/nginx/api.rawlead.ru.conf /etc/nginx/sites-enabled/rawlead-api.conf; nginx -t; systemctl reload nginx'
Invoke-SshCmd $systemd

Write-Host ""
Write-Host "Health on VPS:"
Invoke-SshCmd "curl -s http://127.0.0.1:8000/health || true"
Write-Host ""
Write-Host "Next: certbot --nginx -d api.rawlead.ru (on VPS)"
Write-Host "WP wp-config: RAWLEAD_API_URL http://127.0.0.1:8000"
Write-Host "E2: scp telethon .session files, then systemctl enable --now rawlead-radar"
