@echo off
setlocal

:: ルートディレクトリの設定（このバッチファイルがある場所）
set ROOT_DIR=%~dp0

:: PYTHONPATHの設定（絶対パスで設定）
set PYTHONPATH=%ROOT_DIR%libs

:: Python実行ファイルのパス
set PYTHON_EXE=%ROOT_DIR%python_dist\python.exe

:: ポータブル版のPythonを使ってFastAPIアプリを起動
echo ========================================
echo  AnalysisApp を起動しています...
echo ========================================
echo.

:: app ディレクトリに移動してから main.py を実行
cd /d "%ROOT_DIR%app"
"%PYTHON_EXE%" main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo ========================================
    echo  エラーが発生しました
    echo ========================================
    pause
    exit /b %ERRORLEVEL%
)

pause
