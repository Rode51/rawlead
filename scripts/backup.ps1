# Backup project secrets and local data (Windows PowerShell)
param(
    [string]$ConfigPath = ""
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ConfigPath) {
    $ConfigPath = Join-Path $scriptDir "backup.config.json"
}
if (-not (Test-Path $ConfigPath)) {
    Write-Error "Config not found: $ConfigPath. Copy backup.config.example.json -> backup.config.json"
}

$config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
$projectRoot = (Resolve-Path $config.projectRoot).Path
$backupRoot = $config.backupRoot
$projectName = $config.projectName
$stamp = Get-Date -Format "yyyy-MM-dd_HHmm"
$dest = Join-Path (Join-Path $backupRoot $projectName) $stamp

New-Item -ItemType Directory -Force -Path $dest | Out-Null
$manifest = @()
$manifest += "backup_at=$stamp"
$manifest += "projectRoot=$projectRoot"

# .env
$envFile = if ($config.envFile) { $config.envFile } else { ".env" }
$envSrc = Join-Path $projectRoot $envFile
if (Test-Path $envSrc) {
    Copy-Item $envSrc $dest -Force
    $manifest += "ok: $envFile"
} else {
    $manifest += "missing: $envFile"
}

# data files
$dataDirRel = if ($config.PSObject.Properties.Name -contains "dataDir" -and $config.dataDir) { $config.dataDir } else { "data" }
$dataDir = Join-Path $projectRoot $dataDirRel
if ($config.dataFiles) {
    foreach ($name in $config.dataFiles) {
        $src = Join-Path $dataDir $name
        if (Test-Path $src) {
            Copy-Item $src $dest -Force
            $manifest += "ok: data\$name"
        } else {
            $manifest += "skip: data\$name"
        }
    }
}

# session dirs
if ($config.sessionDirs) {
    foreach ($sessDir in $config.sessionDirs) {
        if (-not (Test-Path $sessDir)) {
            $manifest += "missing sessionDir: $sessDir"
            continue
        }
        $leaf = Split-Path $sessDir -Leaf
        $sessDest = Join-Path $dest "sessions_$leaf"
        New-Item -ItemType Directory -Force -Path $sessDest | Out-Null
        Copy-Item (Join-Path $sessDir "*") $sessDest -Recurse -Force -ErrorAction SilentlyContinue
        $count = (Get-ChildItem $sessDest -File -ErrorAction SilentlyContinue).Count
        $manifest += "ok: sessions_$leaf files=$count"
    }
}

# extra paths (files or dirs relative to project or absolute)
if ($config.extraPaths) {
    foreach ($p in $config.extraPaths) {
        $src = if ([System.IO.Path]::IsPathRooted($p)) { $p } else { Join-Path $projectRoot $p }
        if (Test-Path $src) {
            $leaf = Split-Path $src -Leaf
            $out = Join-Path $dest "extra_$leaf"
            if ((Get-Item $src).PSIsContainer) {
                Copy-Item $src $out -Recurse -Force
            } else {
                Copy-Item $src $out -Force
            }
            $manifest += "ok: extra $p"
        } else {
            $manifest += "skip: extra $p"
        }
    }
}

$manifest | Set-Content (Join-Path $dest "manifest.txt") -Encoding UTF8
Write-Host ""
Write-Host "BACKUP OK: $dest"
Write-Host "manifest.txt written."
Get-ChildItem $dest | Select-Object Name, Length | Format-Table -AutoSize
