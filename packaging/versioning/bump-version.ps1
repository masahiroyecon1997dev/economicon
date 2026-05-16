# ==============================================================================
#  bump-version.ps1  -  Economicon バージョン一括更新スクリプト
#  !! このファイルは UTF-8 with BOM で保存してください !!
# ==============================================================================

param (
    [Parameter(Mandatory = $true)]
    [string]$Version,

    # -DryRun を指定するとファイルを変更せず差分のみ表示する
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

# ── コンソール出力を UTF-8 に統一 ──────────────────────────────────────────────
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding          = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

# ==============================================================================
#  ユーティリティ
# ==============================================================================

function Write-Step    { param([string]$Msg) Write-Host "`n────────────────────────────────────────" -ForegroundColor DarkGray; Write-Host "  $Msg" -ForegroundColor Cyan }
function Write-Success { param([string]$Msg) Write-Host "  ✔ $Msg" -ForegroundColor Green }
function Write-Info    { param([string]$Msg) Write-Host "  ℹ $Msg" -ForegroundColor Gray }
function Write-Warn    { param([string]$Msg) Write-Host "  ⚠ $Msg" -ForegroundColor Yellow }
function Write-Fail    { param([string]$Msg) Write-Host "  ✘ $Msg" -ForegroundColor Red }

# ファイル内の1箇所を置換し、変更有無を返す
# -UseBOM: $true = UTF-8 with BOM（.ps1 など）、$false = UTF-8 without BOM（既定）
function Update-FileVersion {
    param(
        [string]$FilePath,
        [string]$Pattern,
        [string]$Replacement,
        [bool]$UseBOM = $false
    )

    $content = [System.IO.File]::ReadAllText($FilePath, [System.Text.Encoding]::UTF8)
    $newContent = [regex]::Replace($content, $Pattern, $Replacement)

    if ($content -eq $newContent) {
        Write-Warn "$FilePath : パターンにマッチする箇所が見つかりませんでした。"
        return $false
    }

    if ($DryRun) {
        $match = [regex]::Match($content, $Pattern)
        Write-Info "[DryRun] $FilePath"
        Write-Host "    - $($match.Value)" -ForegroundColor Red
        Write-Host "    + $Replacement" -ForegroundColor Green
    } else {
        $enc = if ($UseBOM) { [System.Text.Encoding]::UTF8 }
               else         { New-Object System.Text.UTF8Encoding($false) }
        [System.IO.File]::WriteAllText($FilePath, $newContent, $enc)
        Write-Success "$FilePath"
    }
    return $true
}

# ==============================================================================
#  バリデーション
# ==============================================================================

if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    Write-Fail "バージョン形式が不正です: '$Version'"
    Write-Info "正しい形式: X.Y.Z (例: 1.2.3)"
    exit 1
}

$SCRIPT_DIR    = $PSScriptRoot
$PACKAGING_DIR = Split-Path -Parent $SCRIPT_DIR
$PROJECT_ROOT  = Split-Path -Parent $PACKAGING_DIR

# ==============================================================================
#  ヘッダー
# ==============================================================================

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Economicon - バージョン一括更新                    ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Info "新しいバージョン : $Version"
if ($DryRun) {
    Write-Warn "DryRun モード: ファイルは変更されません"
}

# ==============================================================================
#  更新対象ファイルの定義
# ==============================================================================

$targets = @(
    @{
        Label   = "api/pyproject.toml"
        Path    = Join-Path $PROJECT_ROOT "api\pyproject.toml"
        # [project] セクション直下の version = "..." のみ対象
        Pattern = '(?m)(?<=^version\s=\s")[^"]+'
        Replace = $Version
        UseBOM  = $false
    },
    @{
        Label   = "app/src-tauri/Cargo.toml"
        Path    = Join-Path $PROJECT_ROOT "app\src-tauri\Cargo.toml"
        # [package] セクション直下の version = "..." のみ対象
        Pattern = '(?m)(?<=^version\s=\s")[^"]+'
        Replace = $Version
        UseBOM  = $false
    },
    @{
        Label   = "app/package.json"
        Path    = Join-Path $PROJECT_ROOT "app\package.json"
        # ルートの "version": "..." のみ対象（依存パッケージのバージョンは変更しない）
        Pattern = '(?m)(?<="version":\s")[^"]+(?=",?\s*$)'
        Replace = $Version
        UseBOM  = $false
    },
    @{
        Label   = "app/src-tauri/tauri.conf.json"
        Path    = Join-Path $PROJECT_ROOT "app\src-tauri\tauri.conf.json"
        Pattern = '(?m)(?<="version":\s")[^"]+(?=",?\s*$)'
        Replace = $Version
        UseBOM  = $false
    },
    @{
        Label   = "packaging/build/build.ps1"
        Path    = Join-Path $PROJECT_ROOT "packaging\build\build.ps1"
        Pattern = '(?<=\$APP_VERSION\s+=\s+")[^"]+'
        Replace = $Version
        UseBOM  = $true   # PowerShell スクリプトは UTF-8 with BOM で保存
    },
    @{
        Label   = "api/gen_openapi.py"
        Path    = Join-Path $PROJECT_ROOT "api\gen_openapi.py"
        Pattern = '(?<=version=")[^"]+'
        Replace = $Version
        UseBOM  = $false
    }
)

# ==============================================================================
#  一括更新
# ==============================================================================

Write-Step "バージョンを $Version に更新中..."

$successCount = 0
$failCount    = 0

foreach ($t in $targets) {
    if (-not (Test-Path $t.Path)) {
        Write-Warn "$($t.Label) : ファイルが見つかりません。スキップします。"
        $failCount++
        continue
    }
    $ok = Update-FileVersion -FilePath $t.Path -Pattern $t.Pattern -Replacement $t.Replace -UseBOM $t.UseBOM
    if ($ok) { $successCount++ } else { $failCount++ }
}

# ==============================================================================
#  結果サマリー
# ==============================================================================

Write-Host ""
Write-Host "────────────────────────────────────────" -ForegroundColor DarkGray
if ($DryRun) {
    Write-Warn "DryRun 完了: $successCount 件が更新対象です。（ファイルは変更されていません）"
    Write-Info "実際に更新するには -DryRun を外して実行してください。"
} else {
    Write-Success "完了: $successCount 件を更新しました。"
    if ($failCount -gt 0) {
        Write-Warn "$failCount 件が失敗またはスキップされました。"
    }
    Write-Host ""
    Write-Warn "CHANGELOG.md は自動更新されません。手動で更新してください。"
    Write-Info "  参考: https://keepachangelog.com/ja/1.0.0/"
}
Write-Host ""
