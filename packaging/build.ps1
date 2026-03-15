# ==============================================================================
#  build.ps1  -  Economicon Tauri アプリ Windows ビルドスクリプト
#  !! このファイルは UTF-8 with BOM で保存してください !!
#     VS Code: 右下の "UTF-8" をクリック → "Save with Encoding" → "UTF-8 with BOM"
# ==============================================================================

# ==============================================================================
#  引数　（モード）
# ==============================================================================
param (
    # 引数がない場合は "build"（インストーラー作成）をデフォルトにする
    [ValidateSet("dev", "build")]
    [string]$Mode = "build"
)


# ── コンソール出力を UTF-8 に統一（日本語文字化け防止）─────────────────────────
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding              = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

# ==============================================================================
#  設定値（環境に合わせて変更してください）
# ==============================================================================

# --- Python -------------------------------------------------------------------
# ★ pyproject.toml は requires-python = ">=3.14" を要求していますが、
#    公式 embeddable package は 3.14 が正式安定版になり次第バージョンを更新してください。
#    現時点では 3.14 の最新安定版 (3.14.3) を使用する想定です。
#    https://www.python.org/downloads/windows/ で "Windows embeddable package (64-bit)" を確認。
$PYTHON_VERSION        = "3.14.3"
# バージョン短縮形: 3.14.3 → 314（._pth ファイル名に使用）
$PYTHON_VERSION_SHORT  = ($PYTHON_VERSION -split '\.')[0..1] -join ''

# --- アプリ情報 ----------------------------------------------------------------
$APP_NAME    = "economicon"
$APP_VERSION = "0.1.0"    # tauri.conf.json の version と合わせてください

# --- ディレクトリ --------------------------------------------------------------
$SCRIPT_DIR    = $PSScriptRoot                          # packaging/
$PROJECT_ROOT  = Split-Path -Parent $SCRIPT_DIR        # リポジトリルート
$API_DIR       = Join-Path $PROJECT_ROOT "api"
$APP_DIR       = Join-Path $PROJECT_ROOT "app"
$TAURI_DIR     = Join-Path $APP_DIR "src-tauri"

# Tauri の externalBin に配置する実行ファイルのディレクトリ
$BINARIES_DIR = Join-Path $TAURI_DIR "binaries"

# Tauri の bundle.resources に含まれるフォルダ（tauri.conf.json 参照）
$RESOURCES_DIR = Join-Path $TAURI_DIR "resources"
$RUNTIME_DIR  = Join-Path $RESOURCES_DIR "runtime"

# ビルド成果物の集約先
$RELEASE_DIR   = Join-Path $PROJECT_ROOT "release"

# --- Python Embeddable Package ダウンロード URL --------------------------------
$PYTHON_EMBED_URL = "https://www.python.org/ftp/python/$PYTHON_VERSION/python-$PYTHON_VERSION-embed-amd64.zip"
$PYTHON_EMBED_ZIP = Join-Path $SCRIPT_DIR "python_embed_tmp.zip"

# ==============================================================================
#  ユーティリティ関数
# ==============================================================================

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "────────────────────────────────────────────────────" -ForegroundColor DarkGray
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "────────────────────────────────────────────────────" -ForegroundColor DarkGray
}

function Write-Success { param([string]$Msg) Write-Host "  ✔ $Msg" -ForegroundColor Green }
function Write-Info    { param([string]$Msg) Write-Host "  ℹ $Msg" -ForegroundColor Gray }
function Write-Warn    { param([string]$Msg) Write-Host "  ⚠ $Msg" -ForegroundColor Yellow }
function Write-Fail    { param([string]$Msg) Write-Host "  ✘ $Msg" -ForegroundColor Red }

function Invoke-Step {
    param([scriptblock]$Block, [string]$ErrorMsg)
    & $Block
    if ($LASTEXITCODE -ne 0) {
        Write-Fail $ErrorMsg
        exit 1
    }
}

# ==============================================================================
#  ヘッダー表示
# ==============================================================================

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Economicon - Windows インストーラー ビルド         ║" -ForegroundColor Cyan
Write-Host "║   Python $PYTHON_VERSION (Embedded) + React + Tauri v2   ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Info "プロジェクトルート : $PROJECT_ROOT"
Write-Info "runtime 出力先  : $RUNTIME_DIR"
Write-Info "成果物集約先       : $RELEASE_DIR"


# ==============================================================================
#  STEP 0: 前提ツールの確認
# ==============================================================================

Write-Step "[0/9] 前提ツールの確認"

$prerequisites = @(
    @{ Name = "uv";        Command = { uv --version } },
    @{ Name = "pnpm";      Command = { pnpm --version } },
    @{ Name = "cargo";     Command = { cargo --version } },
    @{ Name = "tauri-cli"; Command = { cargo tauri --version } }
)

foreach ($tool in $prerequisites) {
    try {
        $ver = & $tool.Command 2>&1
        Write-Success "$($tool.Name) : $ver"
    } catch {
        Write-Fail "$($tool.Name) が見つかりません。インストール後に再実行してください。"
        exit 1
    }
}

# tauri.conf.json に resources が設定されているか警告チェック
$tauriConf = Get-Content (Join-Path $TAURI_DIR "tauri.conf.json") | ConvertFrom-Json
if (-not $tauriConf.bundle.resources) {
    Write-Warn "tauri.conf.json の bundle.resources に runtime の設定がありません。"
    Write-Warn "下記の設定を tauri.conf.json の bundle セクションに追加してください:"
    Write-Host '    "resources": { "resources/runtime/**/*": "runtime" }' -ForegroundColor Yellow
    Write-Host ""
    $ans = Read-Host "  続行しますか？ [y/N]"
    if ($ans -ne 'y' -and $ans -ne 'Y') { exit 1 }
}


# ==============================================================================
#  STEP 1: Python Embedded Package の準備
# ==============================================================================

Write-Step "[1/9] Python $PYTHON_VERSION Embedded Package の準備"

# 既存の resources を削除してクリーンビルド
if (Test-Path $RESOURCES_DIR) {
    Write-Info "既存の resources を削除中..."
    Remove-Item -Recurse -Force $RESOURCES_DIR
}
New-Item -ItemType Directory -Path $RESOURCES_DIR | Out-Null

# 既存の binaries を削除してクリーンビルド
if (Test-Path $BINARIES_DIR) {
    Write-Info "既存の binaries を削除中..."
    Remove-Item -Recurse -Force $BINARIES_DIR
}

# ZIP ダウンロード（既存があればスキップ）
if (-not (Test-Path $PYTHON_EMBED_ZIP)) {
    Write-Info "ダウンロード中: $PYTHON_EMBED_URL"
    try {
        Invoke-WebRequest -Uri $PYTHON_EMBED_URL -OutFile $PYTHON_EMBED_ZIP -UseBasicParsing
        Write-Success "ダウンロード完了: $PYTHON_EMBED_ZIP"
    } catch {
        Write-Fail "ダウンロードに失敗しました: $_"
        Write-Info "手動でダウンロードして $PYTHON_EMBED_ZIP に配置してください。"
        exit 1
    }
} else {
    Write-Info "既存の ZIP を再利用: $PYTHON_EMBED_ZIP"
}

# ZIP 展開
New-Item -ItemType Directory -Path $RUNTIME_DIR | Out-Null
Write-Info "展開中: $RUNTIME_DIR"
Expand-Archive -Path $PYTHON_EMBED_ZIP -DestinationPath $RUNTIME_DIR -Force
Write-Success "Embedded Python を展開しました。"

# ダウンロード済み ZIP を削除（任意）
Remove-Item -Force $PYTHON_EMBED_ZIP


# ==============================================================================
#  STEP 2: ._pth ファイルの編集（ポータブル化・import site 有効化）
# ==============================================================================

Write-Step "[2/9] ._pth ファイルの編集"

$pthFile = Get-ChildItem $RUNTIME_DIR -Filter "*._pth" | Select-Object -First 1

if (-not $pthFile) {
    Write-Fail "._pth ファイルが見つかりません（python$PYTHON_VERSION_SHORT._pth）。"
    Write-Info "展開されたファイル一覧:"
    Get-ChildItem $RUNTIME_DIR | Select-Object -ExpandProperty Name | ForEach-Object { Write-Info "  $_" }
    exit 1
}

Write-Info "._pth ファイル検出: $($pthFile.Name)"

# ._pth の内容を書き換える
# - python3XX.zip : 標準ライブラリ
# - .             : runtime/ 自身（実行時カレントで使用）
# - site-packages : uv --target でインストールするパッケージ群
# - import site   : コメントアウト解除でポータブル化完了（必須）
$pthContent = @"
.
python$PYTHON_VERSION_SHORT.zip
site-packages
import site
"@

# UTF-8 (without BOM) で書き込み
[System.IO.File]::WriteAllText(
    $pthFile.FullName,
    $pthContent,
    [System.Text.Encoding]::UTF8
)

Write-Success "._pth を更新しました（import site 有効化 + site-packages パス追加）。"


# ==============================================================================
#  STEP 3: Python 本体と付属ファイルを bin/ へコピー（サイドカー用）
# ==============================================================================

Write-Step "[3/9] Python 本体を bin/ へコピー (サイドカー用)"


New-Item -ItemType Directory -Path $BINARIES_DIR -Force | Out-Null

# python.exe → python-x86_64-pc-windows-msvc.exe（Tauri externalBin の命名規則に準拠）
$srcPythonExe = Join-Path $RUNTIME_DIR "python.exe"
$dstPythonExe = Join-Path $BINARIES_DIR "python-x86_64-pc-windows-msvc.exe"
Copy-Item $srcPythonExe -Destination $dstPythonExe -Force
Write-Success "python.exe → binaries\python-x86_64-pc-windows-msvc.exe"

Write-Success "binaries/ へのコピー完了。"


# ==============================================================================
#  STEP 4: Python 依存パッケージのインストール（uv --target）
# ==============================================================================

Write-Step "[4/9] Python 依存パッケージのインストール (uv --target)"

$sitePackagesDir = Join-Path $RUNTIME_DIR "site-packages"
New-Item -ItemType Directory -Path $sitePackagesDir -Force | Out-Null

Write-Info "インストール先: $sitePackagesDir"
Write-Info "Python バージョン指定: $PYTHON_VERSION"
Write-Info "依存定義: $API_DIR\pyproject.toml"
Write-Host ""

Push-Location $API_DIR
try {
    # uv pip install で pyproject.toml の本番依存のみを
    # embedded Python の site-packages へ直接展開する。
    # --no-dev    : dev グループ（pytest, ruff 等）を除外
    # --no-cache  : キャッシュを使わずクリーンインストール
    Invoke-Step -ErrorMsg "uv によるパッケージインストールに失敗しました。" -Block {
        uv pip install `
            --python $PYTHON_VERSION `
            --target $sitePackagesDir `
            --no-cache `
            -r pyproject.toml
    }
} finally {
    Pop-Location
}

Write-Success "パッケージを site-packages へインストールしました。"


# ==============================================================================
#  STEP 5: API ファイルを resources/api/ へコピー
# ==============================================================================

Write-Step "[5/9] API ファイルを resources/ へコピー"

# main.py のコピー
Copy-Item (Join-Path $API_DIR "main.py") -Destination $RESOURCES_DIR -Force
Write-Success "main.py → resources\main.py"

# economicon/ パッケージのコピー（__pycache__・tests を除外）
$economiconSrc = Join-Path $API_DIR "economicon"
$economiconDst = Join-Path $RUNTIME_DIR "\site-packages\economicon"
Copy-Item $economiconSrc -Destination $economiconDst -Recurse -Force

# __pycache__ ディレクトリを再帰的に削除
Get-ChildItem $economiconDst -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

Write-Success "economicon/ → runtime/site-packages/economicon/"
Write-Success "API ファイルのコピー完了。"


# ==============================================================================
#  STEP 6: Frontend（React / Vite）ビルド
# ==============================================================================

Write-Step "[6/9] Frontend ビルド (pnpm build)"

Push-Location $APP_DIR
try {
    Invoke-Step -ErrorMsg "pnpm build に失敗しました。" -Block {
        pnpm build
    }
} finally {
    Pop-Location
}

Write-Success "Frontend ビルド完了（$APP_DIR\dist）。"


# ==============================================================================
#  開発モードの場合はここで終了（ビルドせずに試運転したいとき用）
# ==============================================================================
if ($Mode -eq "dev") {
    Write-Host "--- Mode: dev ---" -ForegroundColor Cyan
    Write-Host "開発用（試運転）なので、ビルドせずにここで終了します。" -ForegroundColor Yellow
    # スクリプトをここで抜ける
    return
}


# ==============================================================================
#  STEP 5: Tauri ビルド（MSI / EXE インストーラー生成）
# ==============================================================================

Write-Step "[7/9] Tauri ビルド (pnpm tauri build)"

Push-Location $APP_DIR
try {
    # NOTE: tauri.conf.json の bundle.resources に runtime が設定されている前提。
    #       設定がないと runtime はインストーラーに含まれません。
    Invoke-Step -ErrorMsg "pnpm tauri build に失敗しました。" -Block {
        pnpm tauri build
    }
} finally {
    Pop-Location
}

Write-Success "Tauri ビルド完了。"


# ==============================================================================
#  STEP 6: 成果物の集約
# ==============================================================================

Write-Step "[8/9] 成果物を release/ へ集約"

# 出力先を初期化
if (Test-Path $RELEASE_DIR) {
    Remove-Item -Recurse -Force $RELEASE_DIR
}
New-Item -ItemType Directory -Path $RELEASE_DIR | Out-Null

$bundleDir = Join-Path $TAURI_DIR "target\release\bundle"
$copied    = 0

# NSIS exe
$exeFiles = Get-ChildItem (Join-Path $bundleDir "nsis") -Filter "*.exe" -ErrorAction SilentlyContinue
foreach ($f in $exeFiles) {
    Copy-Item $f.FullName -Destination $RELEASE_DIR -Force
    Write-Info "コピー: $($f.Name) → release\"
    $copied++
}

# exe（WiX などその他）
if ($copied -eq 0) {
    Write-Warn "MSI / NSIS 成果物が見つかりませんでした。bundle ディレクトリを確認してください:"
    Write-Info $bundleDir
} else {
    Write-Success "$copied 個の成果物を release/ にコピーしました。"
}


# ==============================================================================
#  STEP 7: 完了サマリー
# ==============================================================================

Write-Step "[9/9] ビルド完了"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✔  ビルドが正常に完了しました！                    ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  成果物フォルダ : $RELEASE_DIR" -ForegroundColor White
Write-Host ""

Get-ChildItem $RELEASE_DIR | ForEach-Object {
    Write-Host "    $($_.Name)" -ForegroundColor White
}
