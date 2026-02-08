# ==============================================================================
# �ݒ荀��
# ==============================================================================
$PYTHON_VERSION = "3.14.2" # �g�p������Python�o�[�W����
$PACKAGE_NAME = "economicon_Portable"
$PYTHON_DIST = "python_dist"

# �p�X�ݒ�
$API_SERVER_DIR = "api"
$REACT_BUILD_SCRIPT = ".\react_build.ps1"
$LAUNCH_BAT = "app_launch.bat"

# ==============================================================================
# �����̎��s
# ==============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  economicon �|�[�^�u�����̍\�z (uv��)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# uv�̑��݊m�F
Write-Host "--- uv�̊m�F ---" -ForegroundColor Yellow
try {
    $uvVersion = uv --version
    Write-Host "? uv ��������܂���: $uvVersion" -ForegroundColor Green
} catch {
    Write-Host "? uv ��������܂���Buv���C���X�g�[�����Ă��������B" -ForegroundColor Red
    Write-Host "  �C���X�g�[�����@: https://docs.astral.sh/uv/" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# �X�e�b�v1: React�A�v���̃r���h
Write-Host "--- [1/8] React�A�v�����r���h ---" -ForegroundColor Yellow
if (Test-Path $REACT_BUILD_SCRIPT) {
    & $REACT_BUILD_SCRIPT
    if ($LASTEXITCODE -ne 0) {
        Write-Host "? React�̃r���h�Ɏ��s���܂����B" -ForegroundColor Red
        exit 1
    }
    Write-Host "? React�̃r���h���������܂����B" -ForegroundColor Green
} else {
    Write-Host "?? $REACT_BUILD_SCRIPT ��������܂���B�X�L�b�v���܂��B" -ForegroundColor Yellow
}
Write-Host ""

# �X�e�b�v2: �p�b�P�[�W�t�H���_�̍쐬
Write-Host "--- [2/8] �p�b�P�[�W�t�H���_������ ---" -ForegroundColor Yellow
if (Test-Path $PACKAGE_NAME) {
    Write-Host "������ $PACKAGE_NAME ���폜��..."
    Remove-Item -Recurse -Force $PACKAGE_NAME
}
New-Item -ItemType Directory -Path "$PACKAGE_NAME/$PYTHON_DIST" | Out-Null
New-Item -ItemType Directory -Path "$PACKAGE_NAME/app" | Out-Null
New-Item -ItemType Directory -Path "$PACKAGE_NAME/libs" | Out-Null
Write-Host "? �t�H���_�\�����쐬���܂����B" -ForegroundColor Green
Write-Host ""

# �X�e�b�v3: uv��Python���C���X�g�[��
Write-Host "--- [3/8] uv�o�R��Python $PYTHON_VERSION ���C���X�g�[�� ---" -ForegroundColor Yellow
uv python install $PYTHON_VERSION
if ($LASTEXITCODE -ne 0) {
    Write-Host "? Python�̃C���X�g�[���Ɏ��s���܂����B" -ForegroundColor Red
    exit 1
}
Write-Host "? Python $PYTHON_VERSION ���C���X�g�[�����܂����B" -ForegroundColor Green
Write-Host ""

# �X�e�b�v4: �ꎞ�I�ȉ��z�����쐬���ăp�b�P�[�W���C���X�g�[��
Write-Host "--- [4/8] ���z�����쐬���Ĉˑ��֌W���C���X�g�[�� ---" -ForegroundColor Yellow
$tempVenvPath = "temp_uv_venv"

# �����̈ꎞ���z��������΍폜
if (Test-Path $tempVenvPath) {
    Remove-Item -Recurse -Force $tempVenvPath
}

# uv�ŉ��z�����쐬
Push-Location $API_SERVER_DIR
try {
    uv venv ../$tempVenvPath --python $PYTHON_VERSION
    if ($LASTEXITCODE -ne 0) {
        Write-Host "? ���z���̍쐬�Ɏ��s���܂����B" -ForegroundColor Red
        Pop-Location
        exit 1
    }

    # ���z���Ɉˑ��֌W���C���X�g�[��
    uv pip install --python ../$tempVenvPath/Scripts/python.exe -r pyproject.toml --no-cache
    if ($LASTEXITCODE -ne 0) {
        Write-Host "? �ˑ��֌W�̃C���X�g�[���Ɏ��s���܂����B" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    Write-Host "? ���z�����쐬���A�ˑ��֌W���C���X�g�[�����܂����B" -ForegroundColor Green
} finally {
    Pop-Location
}
Write-Host ""

# �X�e�b�v5: ���z����Python��site-packages���|�[�^�u�����ɃR�s�[
Write-Host "--- [5/8] ���z������|�[�^�u�����փR�s�[ ---" -ForegroundColor Yellow

# Python�o�C�i���ꎮ���擾�iuv���Ǘ�����Python����j
$uvPythonPath = (uv python find $PYTHON_VERSION).Trim()
if (-not $uvPythonPath -or -not (Test-Path $uvPythonPath)) {
    Write-Host "? Python���s�p�X�̎擾�Ɏ��s���܂����B" -ForegroundColor Red
    exit 1
}
$pythonHome = Split-Path -Parent $uvPythonPath

# Python�o�C�i�����R�s�[
Copy-Item -Path "$pythonHome\*" -Destination "$PACKAGE_NAME/$PYTHON_DIST" -Recurse -Force -Exclude "*.pth"
Write-Host "  ? Python�o�C�i�����R�s�[���܂����B"

# ���z����site-packages��libs�ɃR�s�[
$venvSitePackages = "$tempVenvPath\Lib\site-packages"
if (Test-Path $venvSitePackages) {
    Copy-Item -Path "$venvSitePackages\*" -Destination "$PACKAGE_NAME/libs" -Recurse -Force
    Write-Host "  ? site-packages��libs�ɃR�s�[���܂����B"
} else {
    Write-Host "? site-packages��������܂���: $venvSitePackages" -ForegroundColor Red
    exit 1
}

# �ꎞ���z�����폜
Remove-Item -Recurse -Force $tempVenvPath
Write-Host "? �|�[�^�u�����ւ̃R�s�[���������܂����B" -ForegroundColor Green
Write-Host ""

# �X�e�b�v6: pythonXXX._pth �̐ݒ�
Write-Host "--- [6/8] Python���p�X��ݒ� ---" -ForegroundColor Yellow
$pthFile = Get-ChildItem "$PACKAGE_NAME/$PYTHON_DIST" -Filter "*._pth" | Select-Object -First 1

if ($pthFile) {
    $majorMinor = ($PYTHON_VERSION -split '\.')[0..1] -join ''
    $content = @"
.
../libs
../app
../app/economicon
python$majorMinor.zip
import site
"@
    Set-Content -Path $pthFile.FullName -Value $content -Encoding UTF8
    Write-Host "? Python���p�X��ݒ肵�܂����B" -ForegroundColor Green
} else {
    Write-Host "?? *._pth �t�@�C����������܂���ł����B" -ForegroundColor Yellow
    Write-Host "  �蓮��PYTHONPATH��ݒ肷��K�v�����邩������܂���B" -ForegroundColor Yellow
}
Write-Host ""

# �X�e�b�v7: �A�v���P�[�V�����t�@�C���̃R�s�[
Write-Host "--- [7/8] �A�v���P�[�V�����t�@�C�����R�s�[ ---" -ForegroundColor Yellow

# api�f�B���N�g���̓��e���R�s�[
if (Test-Path "$API_SERVER_DIR/main.py") {
    Copy-Item -Path "$API_SERVER_DIR/main.py" -Destination "$PACKAGE_NAME/app/" -Force
    Write-Host "  ? main.py ���R�s�[���܂����B"
}

if (Test-Path "$API_SERVER_DIR/economicon") {
    Copy-Item -Path "$API_SERVER_DIR/economicon" -Destination "$PACKAGE_NAME/app/" -Recurse -Force
    Write-Host "  ? economicon �p�b�P�[�W���R�s�[���܂����B"
}

if (Test-Path "$API_SERVER_DIR/static") {
    Copy-Item -Path "$API_SERVER_DIR/static" -Destination "$PACKAGE_NAME/app/" -Recurse -Force
    Write-Host "  ? static �t�H���_�iReact�r���h�ς݁j���R�s�[���܂����B"
}

# �N���o�b�`�t�@�C�����R�s�[
if (Test-Path $LAUNCH_BAT) {
    Copy-Item -Path $LAUNCH_BAT -Destination "$PACKAGE_NAME/" -Force
    Write-Host "  ? $LAUNCH_BAT ���R�s�[���܂����B"
}

Write-Host "? �A�v���P�[�V�����t�@�C���̃R�s�[���������܂����B" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "  �|�[�^�u�����̍\�z�������I" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host " �p�b�P�[�W: $PACKAGE_NAME" -ForegroundColor Cyan
Write-Host " �N�����@: $PACKAGE_NAME �t�H���_���� $LAUNCH_BAT ���_�u���N���b�N" -ForegroundColor Cyan
Write-Host ""
