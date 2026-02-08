# ==============================================================================
# ? �ϐ��̐ݒ�: �p�X�̐ݒ�������ōs���܂�
# ==============================================================================

# React�v���W�F�N�g�̃��[�g�f�B���N�g�� (package.json������ꏊ)
$ReactRootDir = Resolve-Path ".\app"

# �r���h���ʕ����o�͂����f�B���N�g�� (�f�t�H���g�� dist)
$DistDir = "$ReactRootDir\dist"

# FastAPI�̐ÓI�t�@�C���f�B���N�g�� (�r���h����React�A�v����z�u����ꏊ)
$FastApiStaticDir = ".\api\static"

# ==============================================================================
# ?? �����̎��s
# ==============================================================================

Write-Host "--- 1. �����̐ÓI�t�@�C���f�B���N�g�����N���[���A�b�v ---" -ForegroundColor Cyan
if (Test-Path $FastApiStaticDir) {
    Remove-Item $FastApiStaticDir -Recurse -Force
    Write-Host "? ������ $FastApiStaticDir ���폜���܂����B" -ForegroundColor Green
}

# �ÓI�t�@�C���f�B���N�g�����쐬
New-Item -Path $FastApiStaticDir -ItemType Directory | Out-Null
Write-Host "? $FastApiStaticDir ���쐬���܂����B" -ForegroundColor Green

Write-Host "--- 2. React�̃r���h���J�n ---" -ForegroundColor Cyan
try {
    # React�v���W�F�N�g�f�B���N�g���Ɉړ����A�r���h�����s
    Set-Location $ReactRootDir
    pnpm build
    Set-Location $PSScriptRoot # �X�N���v�g���s�f�B���N�g���ɖ߂�
} catch {
    Write-Host "? �r���h���ɃG���[���������܂����B" -ForegroundColor Red
    exit 1
}

# �r���h���dist�f�B���N�g���̑��݊m�F
if (-not (Test-Path $DistDir)) {
    Write-Host "? dist �f�B���N�g����������܂���B�r���h�����s�������AVite�̐ݒ���m�F���Ă��������B" -ForegroundColor Red
    exit 1
}

Write-Host "--- 3. �r���h�����t�@�C����ÓI�t�@�C���f�B���N�g���ɃR�s�[ ---" -ForegroundColor Cyan

# dist �f�B���N�g�����̑S�t�@�C���ƃt�H���_���R�s�[
Get-ChildItem $DistDir -Recurse | ForEach-Object {
    $Target = Join-Path $FastApiStaticDir $_.FullName.Substring($DistDir.Length)
    if ($_.PSIsContainer) {
        New-Item -Path $Target -ItemType Directory -Force | Out-Null
    } else {
        Copy-Item $_.FullName $Target -Force
    }
}

Write-Host "? �r���h�t�@�C���� $FastApiStaticDir �ɃR�s�[���܂����B" -ForegroundColor Green

Write-Host "--- ? �r���h�X�N���v�g������Ɋ������܂��� ---" -ForegroundColor Green
