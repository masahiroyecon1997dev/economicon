@echo off
set ROOT_DIR=%~dp0
set PYTHONPATH=%ROOT_DIR%libs;%ROOT_DIR%app

:: ポータブル版のPythonを使ってアプリを起動
"%ROOT_DIR%python_dist\python.exe" "%ROOT_DIR%app\main.py"

pause
