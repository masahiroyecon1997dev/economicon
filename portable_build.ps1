# ==============================================================================
# 設定項目
# ==============================================================================
$PYTHON_VERSION = "3.14.2" # 使用したいPythonバージョン
$PACKAGE_NAME = "AnalysisApp_Portable"
$PYTHON_DIST = "python_dist"

# パス設定
$API_SERVER_DIR = "ApiServer"
$REACT_BUILD_SCRIPT = ".\react_build.ps1"
$LAUNCH_BAT = "app_launch.bat"

# ==============================================================================
# 処理の実行
# ==============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AnalysisApp ポータブル環境の構築 (uv版)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# uvの存在確認
Write-Host "--- uvの確認 ---" -ForegroundColor Yellow
try {
    $uvVersion = uv --version
    Write-Host "? uv が見つかりました: $uvVersion" -ForegroundColor Green
} catch {
    Write-Host "? uv が見つかりません。uvをインストールしてください。" -ForegroundColor Red
    Write-Host "  インストール方法: https://docs.astral.sh/uv/" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# ステップ1: Reactアプリのビルド
Write-Host "--- [1/8] Reactアプリをビルド ---" -ForegroundColor Yellow
if (Test-Path $REACT_BUILD_SCRIPT) {
    & $REACT_BUILD_SCRIPT
    if ($LASTEXITCODE -ne 0) {
        Write-Host "? Reactのビルドに失敗しました。" -ForegroundColor Red
        exit 1
    }
    Write-Host "? Reactのビルドが完了しました。" -ForegroundColor Green
} else {
    Write-Host "?? $REACT_BUILD_SCRIPT が見つかりません。スキップします。" -ForegroundColor Yellow
}
Write-Host ""

# ステップ2: パッケージフォルダの作成
Write-Host "--- [2/8] パッケージフォルダを準備 ---" -ForegroundColor Yellow
if (Test-Path $PACKAGE_NAME) {
    Write-Host "既存の $PACKAGE_NAME を削除中..."
    Remove-Item -Recurse -Force $PACKAGE_NAME
}
New-Item -ItemType Directory -Path "$PACKAGE_NAME/$PYTHON_DIST" | Out-Null
New-Item -ItemType Directory -Path "$PACKAGE_NAME/app" | Out-Null
New-Item -ItemType Directory -Path "$PACKAGE_NAME/libs" | Out-Null
Write-Host "? フォルダ構造を作成しました。" -ForegroundColor Green
Write-Host ""

# ステップ3: uvでPythonをインストール
Write-Host "--- [3/8] uv経由でPython $PYTHON_VERSION をインストール ---" -ForegroundColor Yellow
uv python install $PYTHON_VERSION
if ($LASTEXITCODE -ne 0) {
    Write-Host "? Pythonのインストールに失敗しました。" -ForegroundColor Red
    exit 1
}
Write-Host "? Python $PYTHON_VERSION をインストールしました。" -ForegroundColor Green
Write-Host ""

# ステップ4: 一時的な仮想環境を作成してパッケージをインストール
Write-Host "--- [4/8] 仮想環境を作成して依存関係をインストール ---" -ForegroundColor Yellow
$tempVenvPath = "temp_uv_venv"

# 既存の一時仮想環境があれば削除
if (Test-Path $tempVenvPath) {
    Remove-Item -Recurse -Force $tempVenvPath
}

# uvで仮想環境を作成
Push-Location $API_SERVER_DIR
try {
    uv venv ../$tempVenvPath --python $PYTHON_VERSION
    if ($LASTEXITCODE -ne 0) {
        Write-Host "? 仮想環境の作成に失敗しました。" -ForegroundColor Red
        Pop-Location
        exit 1
    }

    # 仮想環境に依存関係をインストール
    uv pip install --python ../$tempVenvPath/Scripts/python.exe -r pyproject.toml --no-cache
    if ($LASTEXITCODE -ne 0) {
        Write-Host "? 依存関係のインストールに失敗しました。" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    Write-Host "? 仮想環境を作成し、依存関係をインストールしました。" -ForegroundColor Green
} finally {
    Pop-Location
}
Write-Host ""

# ステップ5: 仮想環境のPythonとsite-packagesをポータブル環境にコピー
Write-Host "--- [5/8] 仮想環境からポータブル環境へコピー ---" -ForegroundColor Yellow

# Pythonバイナリ一式を取得（uvが管理するPythonから）
$uvPythonPath = (uv python find $PYTHON_VERSION).Trim()
if (-not $uvPythonPath -or -not (Test-Path $uvPythonPath)) {
    Write-Host "? Python実行パスの取得に失敗しました。" -ForegroundColor Red
    exit 1
}
$pythonHome = Split-Path -Parent $uvPythonPath

# Pythonバイナリをコピー
Copy-Item -Path "$pythonHome\*" -Destination "$PACKAGE_NAME/$PYTHON_DIST" -Recurse -Force -Exclude "*.pth"
Write-Host "  ? Pythonバイナリをコピーしました。"

# 仮想環境のsite-packagesをlibsにコピー
$venvSitePackages = "$tempVenvPath\Lib\site-packages"
if (Test-Path $venvSitePackages) {
    Copy-Item -Path "$venvSitePackages\*" -Destination "$PACKAGE_NAME/libs" -Recurse -Force
    Write-Host "  ? site-packagesをlibsにコピーしました。"
} else {
    Write-Host "? site-packagesが見つかりません: $venvSitePackages" -ForegroundColor Red
    exit 1
}

# 一時仮想環境を削除
Remove-Item -Recurse -Force $tempVenvPath
Write-Host "? ポータブル環境へのコピーが完了しました。" -ForegroundColor Green
Write-Host ""

# ステップ6: pythonXXX._pth の設定
Write-Host "--- [6/8] Python環境パスを設定 ---" -ForegroundColor Yellow
$pthFile = Get-ChildItem "$PACKAGE_NAME/$PYTHON_DIST" -Filter "*._pth" | Select-Object -First 1

if ($pthFile) {
    $majorMinor = ($PYTHON_VERSION -split '\.')[0..1] -join ''
    $content = @"
.
../libs
../app
../app/analysisapp
python$majorMinor.zip
import site
"@
    Set-Content -Path $pthFile.FullName -Value $content -Encoding UTF8
    Write-Host "? Python環境パスを設定しました。" -ForegroundColor Green
} else {
    Write-Host "?? *._pth ファイルが見つかりませんでした。" -ForegroundColor Yellow
    Write-Host "  手動でPYTHONPATHを設定する必要があるかもしれません。" -ForegroundColor Yellow
}
Write-Host ""

# ステップ7: アプリケーションファイルのコピー
Write-Host "--- [7/8] アプリケーションファイルをコピー ---" -ForegroundColor Yellow

# ApiServerディレクトリの内容をコピー
if (Test-Path "$API_SERVER_DIR/main.py") {
    Copy-Item -Path "$API_SERVER_DIR/main.py" -Destination "$PACKAGE_NAME/app/" -Force
    Write-Host "  ? main.py をコピーしました。"
}

if (Test-Path "$API_SERVER_DIR/analysisapp") {
    Copy-Item -Path "$API_SERVER_DIR/analysisapp" -Destination "$PACKAGE_NAME/app/" -Recurse -Force
    Write-Host "  ? analysisapp パッケージをコピーしました。"
}

if (Test-Path "$API_SERVER_DIR/static") {
    Copy-Item -Path "$API_SERVER_DIR/static" -Destination "$PACKAGE_NAME/app/" -Recurse -Force
    Write-Host "  ? static フォルダ（Reactビルド済み）をコピーしました。"
}

# 起動バッチファイルをコピー
if (Test-Path $LAUNCH_BAT) {
    Copy-Item -Path $LAUNCH_BAT -Destination "$PACKAGE_NAME/" -Force
    Write-Host "  ? $LAUNCH_BAT をコピーしました。"
}

Write-Host "? アプリケーションファイルのコピーが完了しました。" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "  ポータブル環境の構築が完了！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host " パッケージ: $PACKAGE_NAME" -ForegroundColor Cyan
Write-Host " 起動方法: $PACKAGE_NAME フォルダ内の $LAUNCH_BAT をダブルクリック" -ForegroundColor Cyan
Write-Host ""
