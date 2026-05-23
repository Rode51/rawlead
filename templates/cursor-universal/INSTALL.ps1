param(
    [Parameter(Mandatory = $true)]
    [string]$TargetRoot
)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$target = (Resolve-Path $TargetRoot).Path

Write-Host "Install cursor-universal -> $target"

# .cursor/rules
$rulesDest = Join-Path $target ".cursor\rules"
New-Item -ItemType Directory -Force -Path $rulesDest | Out-Null
Copy-Item (Join-Path $here "cursor-rules\*.mdc") $rulesDest -Force

# docs-starter -> docs/
$docsSrc = Join-Path $here "docs-starter"
$docsDest = Join-Path $target "docs"
function Copy-Tree($src, $dest) {
    Get-ChildItem $src -Recurse -File | ForEach-Object {
        $rel = $_.FullName.Substring($src.Length).TrimStart("\")
        $out = Join-Path $dest $rel
        $dir = Split-Path $out -Parent
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
        if (-not (Test-Path $out)) {
            Copy-Item $_.FullName $out
            Write-Host "  + $rel"
        } else {
            Write-Host "  skip (exists): $rel"
        }
    }
}
Copy-Tree $docsSrc $docsDest

# scripts backup
$scriptsDest = Join-Path $target "scripts"
New-Item -ItemType Directory -Force -Path $scriptsDest | Out-Null
foreach ($f in @("backup.ps1", "backup.bat", "backup.config.example.json")) {
    $src = Join-Path $here "scripts\$f"
    $out = Join-Path $scriptsDest $f
    Copy-Item $src $out -Force
    Write-Host "  script: $f"
}

$configExample = Join-Path $scriptsDest "backup.config.example.json"
$configLocal = Join-Path $scriptsDest "backup.config.json"
if (-not (Test-Path $configLocal)) {
    Copy-Item $configExample $configLocal
    Write-Host "  created backup.config.json — отредактируй пути"
}

Write-Host "OK. Открой docs/FOR_YOU.md; роли — .cursor/rules/ (@lead-architect @coder @mechanic @owner)"
