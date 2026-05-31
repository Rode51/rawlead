# Cursor Team Kit — bootstrap rules + docs skeleton
# Usage: .\bootstrap.ps1 -TargetRoot C:\path\to\project [-RulesOnly] [-DocsOnly]

param(
    [Parameter(Mandatory = $false)]
    [string]$TargetRoot = (Get-Location).Path,
    [switch]$RulesOnly,
    [switch]$DocsOnly
)

$ErrorActionPreference = "Stop"
$KitRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$TargetRoot = (Resolve-Path $TargetRoot).Path

function Ensure-Dir($path) {
    if (-not (Test-Path $path)) { New-Item -ItemType Directory -Path $path -Force | Out-Null }
}

if (-not $DocsOnly) {
    $rulesSrc = Join-Path $KitRoot "rules"
    $rulesDst = Join-Path $TargetRoot ".cursor\rules"
    Ensure-Dir $rulesDst
    Copy-Item -Path (Join-Path $rulesSrc "*.mdc") -Destination $rulesDst -Force
    Copy-Item -Path (Join-Path $rulesSrc "README.md") -Destination $rulesDst -Force -ErrorAction SilentlyContinue
    Write-Host "OK rules -> $rulesDst"
}

if (-not $RulesOnly) {
    $skel = Join-Path $KitRoot "docs-skeleton"
    if (Test-Path $skel) {
        $docsDst = Join-Path $TargetRoot "docs"
        Ensure-Dir $docsDst
        Copy-Item -Path (Join-Path $skel "*") -Destination $docsDst -Recurse -Force
        Write-Host "OK docs-skeleton -> $docsDst (replace [PROJECT] placeholders)"
    }
}

# gitignore hint
$gi = Join-Path $TargetRoot ".gitignore"
$snippet = @"

# Cursor Team Kit — track rules in git
.cursor/
!.cursor/rules/
!.cursor/rules/**
"@
if (Test-Path $gi) {
    $content = Get-Content $gi -Raw
    if ($content -notmatch '!\.cursor/rules/') {
        Add-Content -Path $gi -Value $snippet
        Write-Host "OK appended .cursor/rules exception to .gitignore"
    }
} else {
    Set-Content -Path $gi -Value $snippet.Trim()
    Write-Host "OK created .gitignore with .cursor/rules exception"
}

Write-Host "Done. Next: SETUP_NEW_PROJECT.md — fill [PROJECT] and first CODER_PROMPT task."
