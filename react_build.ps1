# ==============================================================================
# ? 変数の設定: パスの設定をここで行います
# ==============================================================================

# Reactプロジェクトのルートディレクトリ (package.jsonがある場所)
$ReactRootDir = Resolve-Path ".\front-analysis-app"

# ビルド成果物が出力されるディレクトリ (デフォルトは dist)
$DistDir = "$ReactRootDir\dist"

# FastAPIの静的ファイルディレクトリ (ビルドしたReactアプリを配置する場所)
$FastApiStaticDir = ".\ApiServer\static"

# ==============================================================================
# ?? 処理の実行
# ==============================================================================

Write-Host "--- 1. 既存の静的ファイルディレクトリをクリーンアップ ---" -ForegroundColor Cyan
if (Test-Path $FastApiStaticDir) {
    Remove-Item $FastApiStaticDir -Recurse -Force
    Write-Host "? 既存の $FastApiStaticDir を削除しました。" -ForegroundColor Green
}

# 静的ファイルディレクトリを作成
New-Item -Path $FastApiStaticDir -ItemType Directory | Out-Null
Write-Host "? $FastApiStaticDir を作成しました。" -ForegroundColor Green

Write-Host "--- 2. Reactのビルドを開始 ---" -ForegroundColor Cyan
try {
    # Reactプロジェクトディレクトリに移動し、ビルドを実行
    Set-Location $ReactRootDir
    pnpm build
    Set-Location $PSScriptRoot # スクリプト実行ディレクトリに戻る
} catch {
    Write-Host "? ビルド中にエラーが発生しました。" -ForegroundColor Red
    exit 1
}

# ビルド後のdistディレクトリの存在確認
if (-not (Test-Path $DistDir)) {
    Write-Host "? dist ディレクトリが見つかりません。ビルドが失敗したか、Viteの設定を確認してください。" -ForegroundColor Red
    exit 1
}

Write-Host "--- 3. ビルドしたファイルを静的ファイルディレクトリにコピー ---" -ForegroundColor Cyan

# dist ディレクトリ内の全ファイルとフォルダをコピー
Get-ChildItem $DistDir -Recurse | ForEach-Object {
    $Target = Join-Path $FastApiStaticDir $_.FullName.Substring($DistDir.Length)
    if ($_.PSIsContainer) {
        New-Item -Path $Target -ItemType Directory -Force | Out-Null
    } else {
        Copy-Item $_.FullName $Target -Force
    }
}

Write-Host "? ビルドファイルを $FastApiStaticDir にコピーしました。" -ForegroundColor Green

Write-Host "--- ? ビルドスクリプトが正常に完了しました ---" -ForegroundColor Green
