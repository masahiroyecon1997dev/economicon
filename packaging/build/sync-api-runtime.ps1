[CmdletBinding()]
param(
    [switch]$Compile = $false
)

$ErrorActionPreference = 'Stop'

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "-----------------------------------------------" -ForegroundColor DarkGray
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "-----------------------------------------------" -ForegroundColor DarkGray
}

function Write-Success { param([string]$Msg) Write-Host "  [OK] $Msg" -ForegroundColor Green }
function Write-Info    { param([string]$Msg) Write-Host "  [INFO] $Msg" -ForegroundColor Gray }
function Write-Fail    { param([string]$Msg) Write-Host "  [FAIL] $Msg" -ForegroundColor Red }

function Exit-WithFailure {
    param([string]$Message)
    Write-Fail $Message
    exit 1
}

function Sync-ApiSourcesToResources {
    param(
        [string]$TargetResourcesDir,
        [string]$TargetLabel
    )

    $targetRuntimeDir = Join-Path $TargetResourcesDir "runtime"
    $targetSitePackagesDir = Join-Path $targetRuntimeDir "site-packages"
    $targetMainDst = Join-Path $TargetResourcesDir "main.py"
    $targetEconomiconDst = Join-Path $targetSitePackagesDir "economicon"

    if (-not (Test-Path $targetRuntimeDir)) {
        Write-Info "Skipped $TargetLabel sync because runtime directory was not found: $targetRuntimeDir"
        return $null
    }

    if (-not (Test-Path $targetSitePackagesDir)) {
        Write-Info "Skipped $TargetLabel sync because site-packages directory was not found: $targetSitePackagesDir"
        return $null
    }

    New-Item -ItemType Directory -Path $TargetResourcesDir -Force | Out-Null

    Copy-Item $mainSrc -Destination $targetMainDst -Force
    Write-Success "main.py -> $TargetLabel/main.py"

    if (Test-Path $targetEconomiconDst) {
        Remove-Item $targetEconomiconDst -Recurse -Force
        Write-Info "Removed existing $TargetLabel/runtime/site-packages/economicon"
    }

    Copy-Item $economiconSrc -Destination $targetEconomiconDst -Recurse -Force
    Write-Success "economicon/ -> $TargetLabel/runtime/site-packages/economicon/"

    Get-ChildItem $targetEconomiconDst -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force
    Write-Success "Removed copied __pycache__ directories under $TargetLabel"

    return @{
        RuntimeDir = $targetRuntimeDir
        MainPath = $targetMainDst
        EconomiconDir = $targetEconomiconDst
    }
}

$SCRIPT_DIR = $PSScriptRoot
$PACKAGING_DIR = Split-Path -Parent $SCRIPT_DIR
$PROJECT_ROOT = Split-Path -Parent $PACKAGING_DIR
$API_DIR = Join-Path $PROJECT_ROOT "api"
$APP_DIR = Join-Path $PROJECT_ROOT "app"
$TAURI_DIR = Join-Path $APP_DIR "src-tauri"
$TARGET_DEBUG_RESOURCES_DIR = Join-Path $TAURI_DIR "target\debug\resources"
$RESOURCES_DIR = Join-Path $TAURI_DIR "resources"
$RUNTIME_DIR = Join-Path $RESOURCES_DIR "runtime"
$SITE_PACKAGES_DIR = Join-Path $RUNTIME_DIR "site-packages"

$mainSrc = Join-Path $API_DIR "main.py"
$mainDst = Join-Path $RESOURCES_DIR "main.py"
$economiconSrc = Join-Path $API_DIR "economicon"
$economiconDst = Join-Path $SITE_PACKAGES_DIR "economicon"
$pythonExe = Join-Path $RUNTIME_DIR "python.exe"

Write-Step "API runtime incremental sync"
Write-Info "Project root : $PROJECT_ROOT"
Write-Info "Runtime dir  : $RUNTIME_DIR"

if (-not (Test-Path $RUNTIME_DIR)) {
    Exit-WithFailure "runtime directory was not found. Run packaging/build/build.ps1 once first."
}

if (-not (Test-Path $SITE_PACKAGES_DIR)) {
    Exit-WithFailure "site-packages directory was not found. The existing runtime looks incomplete."
}

if (-not (Test-Path $mainSrc)) {
    Exit-WithFailure "Source file was not found: $mainSrc"
}

if (-not (Test-Path $economiconSrc)) {
    Exit-WithFailure "Source package was not found: $economiconSrc"
}

$primarySync = Sync-ApiSourcesToResources -TargetResourcesDir $RESOURCES_DIR -TargetLabel "resources"

$debugSync = $null
if (Test-Path $TARGET_DEBUG_RESOURCES_DIR) {
    $debugSync = Sync-ApiSourcesToResources -TargetResourcesDir $TARGET_DEBUG_RESOURCES_DIR -TargetLabel "target/debug/resources"
} else {
    Write-Info "Skipped target/debug/resources sync because the directory does not exist."
}

if ($Compile) {
    if (-not (Test-Path $pythonExe)) {
        Exit-WithFailure "Runtime Python was not found: $pythonExe"
    }

    Write-Step "Python precompile"

    & $pythonExe -O -m compileall -q -l $RESOURCES_DIR
    if ($LASTEXITCODE -ne 0) {
        Exit-WithFailure "Failed to precompile resources/main.py"
    }
    Write-Success "Precompiled resources/main.py"

    & $pythonExe -O -m compileall -q -j 0 $economiconDst
    if ($LASTEXITCODE -ne 0) {
        Exit-WithFailure "Failed to precompile runtime/site-packages/economicon"
    }
    Write-Success "Precompiled runtime/site-packages/economicon"

    if ($debugSync -and (Test-Path $pythonExe)) {
        & $pythonExe -O -m compileall -q -l $TARGET_DEBUG_RESOURCES_DIR
        if ($LASTEXITCODE -ne 0) {
            Exit-WithFailure "Failed to precompile target/debug/resources/main.py"
        }
        Write-Success "Precompiled target/debug/resources/main.py"

        & $pythonExe -O -m compileall -q -j 0 $debugSync.EconomiconDir
        if ($LASTEXITCODE -ne 0) {
            Exit-WithFailure "Failed to precompile target/debug/resources/runtime/site-packages/economicon"
        }
        Write-Success "Precompiled target/debug/resources/runtime/site-packages/economicon"
    }
}

Write-Host ""
Write-Success "API runtime incremental sync completed."
