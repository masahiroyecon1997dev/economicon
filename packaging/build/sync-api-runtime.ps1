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

$SCRIPT_DIR = $PSScriptRoot
$PACKAGING_DIR = Split-Path -Parent $SCRIPT_DIR
$PROJECT_ROOT = Split-Path -Parent $PACKAGING_DIR
$API_DIR = Join-Path $PROJECT_ROOT "api"
$APP_DIR = Join-Path $PROJECT_ROOT "app"
$TAURI_DIR = Join-Path $APP_DIR "src-tauri"
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

New-Item -ItemType Directory -Path $RESOURCES_DIR -Force | Out-Null

Copy-Item $mainSrc -Destination $mainDst -Force
Write-Success "main.py -> resources/main.py"

if (Test-Path $economiconDst) {
    Remove-Item $economiconDst -Recurse -Force
    Write-Info "Removed existing runtime/site-packages/economicon"
}

Copy-Item $economiconSrc -Destination $economiconDst -Recurse -Force
Write-Success "economicon/ -> runtime/site-packages/economicon/"

Get-ChildItem $economiconDst -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force
Write-Success "Removed copied __pycache__ directories"

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
}

Write-Host ""
Write-Success "API runtime incremental sync completed."
