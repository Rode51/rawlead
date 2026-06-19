# MiMo audit — copy repo without secrets (owner pilot)
# Run: powershell -ExecutionPolicy Bypass -File scripts\copy-mimo-audit.ps1

$ErrorActionPreference = "Stop"
$Src = "C:\Users\hramo\uisness"
$Dst = "C:\Users\hramo\uisness-mimo-audit"

$ExcludeDirs = @(
    "node_modules", ".next", "MagicMock", ".venv", ".tools", "__pycache__",
    ".playwright-mcp", "target", "dist"
)
$ExcludeFiles = @(
    ".env", ".env.site", ".env.legacy",
    "mcp.pool.json", "backup.config.json",
    "wp-vps-credentials.txt"
)
$ExcludeWildcards = @("*.session", "*.session-journal", "*.pem", "*.p12", "*.ppk", "*credentials*.txt")

if (Test-Path $Dst) {
    Write-Host "Removing old copy: $Dst"
    Remove-Item -LiteralPath $Dst -Recurse -Force
}

New-Item -ItemType Directory -Path $Dst -Force | Out-Null

$xd = ($ExcludeDirs | ForEach-Object { "/XD", $_ }) -join " "
$xf = (($ExcludeFiles + $ExcludeWildcards) | ForEach-Object { "/XF", $_ }) -join " "

# Main tree (no data/ yet — handled separately)
$robocopyArgs = @(
    $Src, $Dst,
    "/E", "/NFL", "/NDL", "/NJH", "/NJS", "/NC", "/NS", "/NP",
    "/XD", "data", "node_modules", ".next", "MagicMock", ".venv", ".tools",
    "__pycache__", ".playwright-mcp", "target", "dist",
    "/XF", ".env", ".env.site", ".env.legacy", "mcp.pool.json",
    "backup.config.json", "wp-vps-credentials.txt",
    "*.session", "*.session-journal", "*.pem", "*.p12", "*.ppk", "*credentials*.txt",
    "id_rsa", "id_ed25519"
)
& robocopy @robocopyArgs | Out-Null
# robocopy exit 0-7 = success
if ($LASTEXITCODE -gt 7) { throw "robocopy failed: $LASTEXITCODE" }

# data/ — only safe whitelist (quiz + preprod reports)
$dataSrc = Join-Path $Src "data"
$dataDst = Join-Path $Dst "data"
New-Item -ItemType Directory -Path $dataDst -Force | Out-Null
$safeData = @(
    ".gitkeep",
    "quiz_pool_allowlist.json",
    "quiz_cards_v1.json",
    "quiz_cards_v2-pilot.json",
    "quiz_cards_v2.json",
    "preprod_*.json",
    "preprod_*.md"
)
foreach ($pattern in $safeData) {
    Get-ChildItem -Path $dataSrc -Filter $pattern -File -ErrorAction SilentlyContinue |
        Copy-Item -Destination $dataDst -Force
}
$sessionsReadme = Join-Path $dataSrc "sessions\README.txt"
if (Test-Path $sessionsReadme) {
    New-Item -ItemType Directory -Path (Join-Path $dataDst "sessions") -Force | Out-Null
    Copy-Item $sessionsReadme (Join-Path $dataDst "sessions\README.txt") -Force
}

# Verify no secrets slipped in
$leaks = @()
foreach ($name in @(".env", ".env.site", ".env.legacy", "mcp.pool.json")) {
    $p = Join-Path $Dst $name
    if (Test-Path $p) { $leaks += $p }
}
Get-ChildItem -Path $Dst -Recurse -Include "*.session", "*.session-journal", "mcp.pool.json", ".env" -Force -ErrorAction SilentlyContinue |
    ForEach-Object { $leaks += $_.FullName }

if ($leaks.Count -gt 0) {
    Write-Error ("SECRET LEAK in copy:`n" + ($leaks -join "`n"))
}

$hasExample = Test-Path (Join-Path $Dst ".env.example")
Write-Host ""
Write-Host "OK: $Dst"
Write-Host "  .env.example present: $hasExample"
Write-Host "  data/: whitelist only (no DB, sessions, logs)"
Write-Host ""
Write-Host "Next: cd $Dst && mimo"
