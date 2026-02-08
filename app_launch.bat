@echo off
setlocal

:: ���[�g�f�B���N�g���̐ݒ�i���̃o�b�`�t�@�C��������ꏊ�j
set ROOT_DIR=%~dp0

:: PYTHONPATH�̐ݒ�i��΃p�X�Őݒ�j
set PYTHONPATH=%ROOT_DIR%libs

:: Python���s�t�@�C���̃p�X
set PYTHON_EXE=%ROOT_DIR%python_dist\python.exe

:: �|�[�^�u���ł�Python���g����FastAPI�A�v�����N��
echo ========================================
echo  economicon ���N�����Ă��܂�...
echo ========================================
echo.

:: app �f�B���N�g���Ɉړ����Ă��� main.py �����s
cd /d "%ROOT_DIR%app"
"%PYTHON_EXE%" main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo ========================================
    echo  �G���[���������܂���
    echo ========================================
    pause
    exit /b %ERRORLEVEL%
)

pause
