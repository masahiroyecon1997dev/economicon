# ==============================================================================
# ? 設定項目
# ==============================================================================
$PYTHON_VERSION = "3.13.1" # 使用したいPythonバージョン
$PACKAGE_NAME = "AnalysisApp_Portable"
$PYTHON_DIST = "python_dist"
$DL_URL = "https://www.python.org/ftp/python/$PYTHON_VERSION/python-$PYTHON_VERSION-embed-amd64.zip"

# パス設定
$REQUIREMENTS_FILE = "ApiServer\python-requirements\windows-requirements.txt"
$API_SERVER_DIR = "ApiServer"
$REACT_BUILD_SCRIPT = ".\app_build.ps1"
$LAUNCH_BAT = "app_launch.bat"

# ==============================================================================
# ?? 処理の実行
# ==============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AnalysisApp ポータブル環境の構築" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ステップ1: Reactアプリのビルド
Write-Host "--- [1/7] Reactアプリをビルド ---" -ForegroundColor Yellow
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
Write-Host "--- [2/7] パッケージフォルダを準備 ---" -ForegroundColor Yellow
if (Test-Path $PACKAGE_NAME) {
    Write-Host "既存の $PACKAGE_NAME を削除中..."
    Remove-Item -Recurse -Force $PACKAGE_NAME
}
New-Item -ItemType Directory -Path "$PACKAGE_NAME/$PYTHON_DIST" | Out-Null
New-Item -ItemType Directory -Path "$PACKAGE_NAME/app" | Out-Null
New-Item -ItemType Directory -Path "$PACKAGE_NAME/libs" | Out-Null
Write-Host "? フォルダ構造を作成しました。" -ForegroundColor Green
Write-Host ""

# ステップ3: Python Embeddable のダウンロードと解凍
Write-Host "--- [3/7] Python $PYTHON_VERSION をダウンロード ---" -ForegroundColor Yellow
$zipFile = "$PACKAGE_NAME/python_dist.zip"
Invoke-WebRequest -Uri $DL_URL -OutFile $zipFile
Expand-Archive -Path $zipFile -DestinationPath "$PACKAGE_NAME/$PYTHON_DIST" -Force
Remove-Item $zipFile
Write-Host "? Pythonを解凍しました。" -ForegroundColor Green
Write-Host ""

# ステップ4: pipをセットアップ
Write-Host "--- [4/7] pipをセットアップ ---" -ForegroundColor Yellow
$get_pip = "$PACKAGE_NAME/get-pip.py"
Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $get_pip
& "$PACKAGE_NAME/$PYTHON_DIST/python.exe" $get_pip --target "$PACKAGE_NAME/libs" --no-warn-script-location
Remove-Item $get_pip
Write-Host "? pipのセットアップが完了しました。" -ForegroundColor Green
Write-Host ""

# ステップ5: pythonXXX._pth の修正
Write-Host "--- [5/7] Python環境パスを設定 ---" -ForegroundColor Yellow
$pthFile = Get-ChildItem "$PACKAGE_NAME/$PYTHON_DIST" -Filter "*._pth" | Select-Object -First 1
$majorMinor = ($PYTHON_VERSION -split '\.')[0..1] -join ''
$content = @"
.
../libs
../app
../app/analysisapp
python$majorMinor.zip
python$majorMinor.dll
import site
"@
Set-Content -Path $pthFile.FullName -Value $content -Encoding UTF8
Write-Host "? Python環境パスを設定しました。" -ForegroundColor Green
Write-Host ""

# ステップ6: ライブラリのインストール
Write-Host "--- [6/7] 必要なライブラリをインストール ---" -ForegroundColor Yellow
if (Test-Path $REQUIREMENTS_FILE) {
    & "$PACKAGE_NAME/$PYTHON_DIST/python.exe" -m pip install -r $REQUIREMENTS_FILE --target "$PACKAGE_NAME/libs" --no-warn-script-location
    Write-Host "? ライブラリのインストールが完了しました。" -ForegroundColor Green
} else {
    Write-Host "? requirements.txt が見つかりません: $REQUIREMENTS_FILE" -ForegroundColor Red
    exit 1
}
Write-Host ""

# ステップ7: アプリケーションファイルのコピー
Write-Host "--- [7/7] アプリケーションファイルをコピー ---" -ForegroundColor Yellow

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
Write-Host "  ? ポータブル環境の構築が完了！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "? パッケージ: $PACKAGE_NAME" -ForegroundColor Cyan
Write-Host "? 起動方法: $PACKAGE_NAME フォルダ内の $LAUNCH_BAT をダブルクリック" -ForegroundColor Cyan
Write-Host ""
