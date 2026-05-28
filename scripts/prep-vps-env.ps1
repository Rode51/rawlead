# Build Linux .env copies in data/vps-staging/
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Out = Join-Path $Root "data\vps-staging"
New-Item -ItemType Directory -Force -Path $Out | Out-Null

function Convert-LinuxPaths([string]$text) {
    $text = $text.Replace('C:/Users/hramo/Desktop/Parser/', '/opt/rawlead/data/sessions/')
    $text = $text.Replace('C:\Users\hramo\Desktop\Parser\', '/opt/rawlead/data/sessions/')
    return $text
}

$files = @('.env', '.env.site')
foreach ($name in $files) {
    $src = Join-Path $Root $name
    if (-not (Test-Path $src)) {
        Write-Warning "Skip missing $name"
        continue
    }
    $body = Get-Content $src -Raw -Encoding UTF8
    $body = Convert-LinuxPaths $body
    if ($name -eq '.env.site') {
        if ($body -notmatch 'RADAR_CORS_ORIGINS=') {
            $body = $body + "`nRADAR_CORS_ORIGINS=https://rawlead.ru`n"
        }
        if ($body -notmatch 'SITE_NOTIFY_OWNER=') {
            $body = $body + "SITE_NOTIFY_OWNER=0`n"
        }
    }
    $dst = Join-Path $Out $name
    [System.IO.File]::WriteAllText($dst, $body)
    Write-Host "Wrote $dst"
}
