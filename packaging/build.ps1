# ==============================================================================
#  build.ps1  -  Economicon Tauri アプリ Windows ビルドスクリプト
#  !! このファイルは UTF-8 with BOM で保存してください !!
#     VS Code: 右下の "UTF-8" をクリック → "Save with Encoding" → "UTF-8 with BOM"
# ==============================================================================

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

# Tauri の bundle.resources に含まれるフォルダ（tauri.conf.json 参照）
$PYTHON_ENV_DIR  = Join-Path $TAURI_DIR "resources\python_env"

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
Write-Info "python_env 出力先  : $PYTHON_ENV_DIR"
Write-Info "成果物集約先       : $RELEASE_DIR"


# ==============================================================================
#  STEP 0: 前提ツールの確認
# ==============================================================================

Write-Step "[0/8] 前提ツールの確認"

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
    Write-Warn "tauri.conf.json の bundle.resources に python_env の設定がありません。"
    Write-Warn "下記の設定を tauri.conf.json の bundle セクションに追加してください:"
    Write-Host '    "resources": { "resources/python_env/**/*": "python_env" }' -ForegroundColor Yellow
    Write-Host ""
    $ans = Read-Host "  続行しますか？ [y/N]"
    if ($ans -ne 'y' -and $ans -ne 'Y') { exit 1 }
}


# ==============================================================================
#  STEP 1: Python Embedded Package の準備
# ==============================================================================

Write-Step "[1/8] Python $PYTHON_VERSION Embedded Package の準備"

# 既存の python_env を削除してクリーンビルド
if (Test-Path $PYTHON_ENV_DIR) {
    Write-Info "既存の python_env を削除中..."
    Remove-Item -Recurse -Force $PYTHON_ENV_DIR
}
New-Item -ItemType Directory -Path $PYTHON_ENV_DIR | Out-Null

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
Write-Info "展開中: $PYTHON_ENV_DIR"
Expand-Archive -Path $PYTHON_EMBED_ZIP -DestinationPath $PYTHON_ENV_DIR -Force
Write-Success "Embedded Python を展開しました。"

# ダウンロード済み ZIP を削除（任意）
Remove-Item -Force $PYTHON_EMBED_ZIP


# ==============================================================================
#  STEP 2: ._pth ファイルの編集（ポータブル化・import site 有効化）
# ==============================================================================

Write-Step "[2/8] ._pth ファイルの編集"

$pthFile = Get-ChildItem $PYTHON_ENV_DIR -Filter "*._pth" | Select-Object -First 1

if (-not $pthFile) {
    Write-Fail "._pth ファイルが見つかりません（python$PYTHON_VERSION_SHORT._pth）。"
    Write-Info "展開されたファイル一覧:"
    Get-ChildItem $PYTHON_ENV_DIR | Select-Object -ExpandProperty Name | ForEach-Object { Write-Info "  $_" }
    exit 1
}

Write-Info "._pth ファイル検出: $($pthFile.Name)"

# ._pth の内容を書き換える
# - python3XX.zip : 標準ライブラリ
# - .             : python_env/ 自身（実行時カレントで使用）
# - site-packages : uv --target でインストールするパッケージ群
# - import site   : コメントアウト解除でポータブル化完了（必須）
$pthContent = @"
python$PYTHON_VERSION_SHORT.zip
.
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
#  STEP 3: Python 依存パッケージのインストール（uv --target）
# ==============================================================================

Write-Step "[3/8] Python 依存パッケージのインストール (uv --target)"

$sitePackagesDir = Join-Path $PYTHON_ENV_DIR "site-packages"
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
#  STEP 4: Frontend（React / Vite）ビルド
# ==============================================================================

Write-Step "[4/8] Frontend ビルド (pnpm build)"

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
#  STEP 5: Tauri ビルド（MSI / EXE インストーラー生成）
# ==============================================================================

Write-Step "[5/8] Tauri ビルド (pnpm tauri build)"

Push-Location $APP_DIR
try {
    # NOTE: tauri.conf.json の bundle.resources に python_env が設定されている前提。
    #       設定がないと python_env はインストーラーに含まれません。
    Invoke-Step -ErrorMsg "pnpm tauri build に失敗しました。" -Block {
        pnpm tauri build
    }
} finally {
    Pop-Location
}

Write-Success "Tauri ビルド完了。"


# ==============================================================================
#  STEP 6: ライセンスファイルの収集
# ==============================================================================

Write-Step "[6/8] ライセンスファイルの収集"

# 出力先ディレクトリを初期化
if (Test-Path $RELEASE_DIR) {
    Remove-Item -Recurse -Force $RELEASE_DIR
}
New-Item -ItemType Directory -Path $RELEASE_DIR | Out-Null

$LicensesDir = Join-Path $RELEASE_DIR "licenses"
New-Item -ItemType Directory -Path $LicensesDir -Force | Out-Null

# ── 1. アプリ本体ライセンス ────────────────────────────────────────────────────
$appLicenseFile = Join-Path $PROJECT_ROOT "LICENSE"
if (Test-Path $appLicenseFile) {
    Copy-Item $appLicenseFile -Destination (Join-Path $LicensesDir "00_LICENSE.txt") -Force
    Write-Success "アプリライセンス: 00_LICENSE.txt"
} else {
    Write-Warn "LICENSE ファイルが見つかりません: $appLicenseFile"
}

# ── 2. Python 本体ライセンス (PSF License 2.0) ────────────────────────────────
$pythonPsfText = @"
PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2
============================================
Copyright (c) 2001-2026 Python Software Foundation; All Rights Reserved

1. This LICENSE AGREEMENT is between the Python Software Foundation ("PSF"), and
   the Individual or Organization ("Licensee") accessing and otherwise using
   Python $PYTHON_VERSION software in source or binary form and its associated documentation.

2. Subject to the terms and conditions of this License Agreement, PSF hereby
   grants Licensee a nonexclusive, royalty-free, world-wide license to reproduce,
   analyze, test, perform and/or display publicly, prepare derivative works,
   distribute, and otherwise use Python $PYTHON_VERSION alone or in any derivative version,
   provided, however, that PSF's License Agreement and PSF's notice of copyright,
   i.e., "Copyright (c) 2001-2026 Python Software Foundation; All Rights Reserved"
   are retained in Python $PYTHON_VERSION alone or in any derivative version prepared by
   Licensee.

3. In the event Licensee prepares a derivative work that is based on or incorporates
   Python $PYTHON_VERSION or any part thereof, and wants to make the derivative work available
   to others as provided herein, then Licensee hereby agrees to include in any such
   work a brief summary of the changes made to Python $PYTHON_VERSION.

4. PSF is making Python $PYTHON_VERSION available to Licensee on an "AS IS" basis.
   PSF MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR IMPLIED. BY WAY OF
   EXAMPLE, BUT NOT LIMITATION, PSF MAKES NO AND DISCLAIMS ANY REPRESENTATION OR
   WARRANTY OF MERCHANTABILITY OR FITNESS FOR ANY PARTICULAR PURPOSE OR THAT THE
   USE OF PYTHON $PYTHON_VERSION WILL NOT INFRINGE ANY THIRD PARTY RIGHTS.

5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON $PYTHON_VERSION FOR ANY
   INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS A RESULT OF MODIFYING,
   DISTRIBUTING, OR OTHERWISE USING PYTHON $PYTHON_VERSION, OR ANY DERIVATIVE THEREOF, EVEN
   IF ADVISED OF THE POSSIBILITY THEREOF.

6. This License Agreement will automatically terminate upon a material breach of
   its terms and conditions.

7. Nothing in this License Agreement shall be deemed to create any relationship of
   agency, partnership, or joint venture between PSF and Licensee.

8. By copying, installing or otherwise using Python $PYTHON_VERSION, Licensee agrees to be
   bound by the terms and conditions of this License Agreement.

Full text: https://docs.python.org/3/license.html
"@
[System.IO.File]::WriteAllText(
    (Join-Path $LicensesDir "01_PYTHON_PSF_LICENSE.txt"),
    $pythonPsfText,
    [System.Text.Encoding]::UTF8
)
Write-Success "Python ライセンス: 01_PYTHON_PSF_LICENSE.txt"

# ── 3. Python パッケージライセンス（pip-licenses） ────────────────────────────
# dev venv の pip-licenses で本番パッケージのライセンスを収集。
# dev 専用パッケージ（pytest, ruff 等）は --ignore-packages で除外する。
$pipLicensesExe = Join-Path $API_DIR ".venv\Scripts\pip-licenses.exe"
if (-not (Test-Path $pipLicensesExe)) {
    $pipLicensesExe = Join-Path $API_DIR ".venv\Scripts\pip-licenses"
}
if (Test-Path $pipLicensesExe) {
    Push-Location $API_DIR
    try {
        $pyPkgOut = Join-Path $LicensesDir "02_PYTHON_PACKAGES_LICENSES.txt"
        & $pipLicensesExe `
            --format=plain-vertical `
            --with-license-file `
            --no-license-path `
            --ignore-packages coverage httpx pip-licenses pipdeptree pytest `
                             pytest-cov radon ruff wooldridge `
            --output-file $pyPkgOut
        Write-Success "Python パッケージライセンス: 02_PYTHON_PACKAGES_LICENSES.txt"
    } catch {
        Write-Warn "pip-licenses の実行に失敗しました: $_"
    } finally {
        Pop-Location
    }
} else {
    Write-Warn "pip-licenses が見つかりません（api\.venv\Scripts\pip-licenses）。"
    Write-Warn "  'uv sync --group dev' で dev 依存をインストールしてください。"
}

# ── 4. npm / React パッケージライセンス（pnpm licenses list） ────────────────
Push-Location $APP_DIR
try {
    $npmPkgOut = Join-Path $LicensesDir "03_NPM_PACKAGES_LICENSES.txt"
    # --prod: devDependencies を除外
    pnpm licenses list --prod 2>&1 | Out-File -FilePath $npmPkgOut -Encoding UTF8
    Write-Success "npm パッケージライセンス: 03_NPM_PACKAGES_LICENSES.txt"
} catch {
    Write-Warn "pnpm licenses の実行に失敗しました: $_"
} finally {
    Pop-Location
}

# ── 5. Rust クレートライセンス（cargo-about） ─────────────────────────────────
$cargoAboutAvailable = $false
try {
    $null = cargo about --version 2>&1
    $cargoAboutAvailable = ($LASTEXITCODE -eq 0)
} catch {}

if ($cargoAboutAvailable) {
    Push-Location $APP_DIR
    try {
        $rustOut   = Join-Path $LicensesDir "04_RUST_CRATES_LICENSES.txt"
        $aboutToml = Join-Path $SCRIPT_DIR "about.toml"
        $aboutHbs  = Join-Path $SCRIPT_DIR "about.hbs"
        cargo about generate --config $aboutToml $aboutHbs 2>&1 | `
            Out-File -FilePath $rustOut -Encoding UTF8
        Write-Success "Rust クレートライセンス: 04_RUST_CRATES_LICENSES.txt"
    } catch {
        Write-Warn "cargo about の実行に失敗しました: $_"
    } finally {
        Pop-Location
    }
} else {
    Write-Warn "cargo-about が見つかりません。Rust クレートのライセンス収集をスキップします。"
    Write-Warn "  インストール: cargo install cargo-about"
    @"
Rust クレートのライセンス情報は以下のコマンドで収集できます:

  cargo install cargo-about
  cd app
  cargo about generate --config ..\packaging\about.toml ..\packaging\about.hbs > licenses\04_RUST_CRATES_LICENSES.txt
"@ | Out-File -FilePath (Join-Path $LicensesDir "04_RUST_CRATES_LICENSES_placeholder.txt") -Encoding UTF8
}

# ── 6. 全テキストライセンスを LICENSES.txt に結合（Inno Setup の LicenseFile 用）─
$combinedOut = Join-Path $RELEASE_DIR "LICENSES.txt"
$sb = [System.Text.StringBuilder]::new()
$null = $sb.AppendLine("==========================================================")
$null = $sb.AppendLine("  Economicon $APP_VERSION - Licenses")
$null = $sb.AppendLine("==========================================================")
$null = $sb.AppendLine("")
foreach ($f in (Get-ChildItem $LicensesDir -Filter "*.txt" | Sort-Object Name)) {
    $null = $sb.AppendLine("----------------------------------------------------------")
    $null = $sb.AppendLine("  $($f.BaseName)")
    $null = $sb.AppendLine("----------------------------------------------------------")
    $null = $sb.AppendLine([System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8))
    $null = $sb.AppendLine("")
}
[System.IO.File]::WriteAllText($combinedOut, $sb.ToString(), [System.Text.Encoding]::UTF8)
Write-Success "統合ライセンスファイル: release\LICENSES.txt"


# ==============================================================================
#  STEP 7: Inno Setup インストーラーの作成
# ==============================================================================

Write-Step "[7/8] Inno Setup インストーラーの作成"

# iscc.exe を検索（典型的なインストール先 → PATH の順）
$isccCandidates = @(
    "C:\Program Files (x86)\Inno Setup 6\iscc.exe",
    "C:\Program Files\Inno Setup 6\iscc.exe"
)
$isccPath = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $isccPath) {
    $isccCmd = Get-Command iscc -ErrorAction SilentlyContinue
    if ($isccCmd) { $isccPath = $isccCmd.Source }
}

if (-not $isccPath) {
    Write-Warn "Inno Setup (iscc.exe) が見つかりません。Inno Setup のコンパイルをスキップします。"
    Write-Warn "  インストール: https://jrsoftware.org/isdl.php"
    Write-Warn "  インストール後、以下のコマンドを手動実行してください:"
    Write-Host "    iscc `"$SCRIPT_DIR\installer.iss`"" -ForegroundColor Yellow
} else {
    Write-Info "iscc: $isccPath"
    $issFile = Join-Path $SCRIPT_DIR "installer.iss"

    Invoke-Step -ErrorMsg "Inno Setup のコンパイルに失敗しました。" -Block {
        & $isccPath $issFile
    }

    Write-Success "Inno Setup インストーラーを作成しました。"

    # 成果物をコピー
    $issOutputDir = Join-Path $PROJECT_ROOT "release\installer_output"
    if (Test-Path $issOutputDir) {
        Get-ChildItem $issOutputDir -Filter "*.exe" | ForEach-Object {
            Copy-Item $_.FullName -Destination $RELEASE_DIR -Force
            Write-Info "コピー: $($_.Name) → release\"
        }
    }
}

# installer.iss を参照用としてコピー
$issFile = Join-Path $SCRIPT_DIR "installer.iss"
if (Test-Path $issFile) {
    Copy-Item $issFile -Destination $RELEASE_DIR -Force
    Write-Info "installer.iss → release\ にコピー"
}


# ==============================================================================
#  STEP 8: 完了サマリー
# ==============================================================================

Write-Step "[8/8] ビルド完了"

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

Write-Host ""
