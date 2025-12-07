# ==============================================================================
# 🎯 変数の設定: パスの設定をここで行います
# ==============================================================================

# Reactプロジェクトのルートディレクトリ (package.jsonがある場所)
$ReactRootDir = Resolve-Path ".\front-analysis-app"

# ビルド成果物が出力されるディレクトリ (デフォルトは dist)
$DistDir = "$ReactRootDir\dist"

# Djangoのテンプレートディレクトリ (index.html を配置する場所)
$DjangoTemplateDir = ".\ApiServer\analysisapp\api\templates"

# Djangoの静的ファイルディレクトリ (JS, CSS などを配置する場所)
# Django App名/static/react/ の形式で配置するのが一般的ですが、今回は指定されたパスに直接配置します
$DjangoStaticDir = ".\ApiServer\analysisapp\api\static"

# HTMLの出力ファイル名
$TemplateFileName = "index.html"

# ==============================================================================
# 🛠️ 処理の実行
# ==============================================================================

Write-Host "--- 1. Reactのビルドを開始 ---" -ForegroundColor Cyan
try {
    # Reactプロジェクトディレクトリに移動し、ビルドを実行
    Set-Location $ReactRootDir
    yarn build
    Set-Location $PSScriptRoot # スクリプト実行ディレクトリに戻る
} catch {
    Write-Host "❌ ビルド中にエラーが発生しました。" -ForegroundColor Red
    exit 1
}

# ビルド後のHTMLファイルのパス
$OriginalHtmlPath = Join-Path $DistDir "index.html"
if (-not (Test-Path $OriginalHtmlPath)) {
    Write-Host "❌ index.html が $DistDir に見つかりません。ビルドが失敗したか、Viteの設定を確認してください。" -ForegroundColor Red
    exit 1
}

Write-Host "--- 2. index.html のパス修正 ---" -ForegroundColor Cyan

# 1. index.html の内容を読み込む
$HtmlContent = Get-Content $OriginalHtmlPath -Raw

# 2. パスの修正を実行
# href="/..." と src="/..." の両方を一度に置換
# 正規表現の OR (|) を使用して、両方のパターンを一括で置換します。
$ModifiedContent = $HtmlContent -replace '(href|src)="/', '$1="{% static '''

# 3. 閉じタグの前に '}' を追加
# $1 は正規表現でマッチした最初のグループ（今回の場合は .css" など）を指します。
# ここで閉じのシングルクォートと波括弧 '}' を追加します。
# 正規表現のマッチグループを使用するため、前の行で閉じのシングルクォートを導入しています。
$ModifiedContent = $ModifiedContent -replace '(\.(css|js|ico|png|svg|jpg|webp))"', "`$1' %}"""

# 4. HTMLの先頭に {% load static %} を追加
$ModifiedContent = "{% load static %}`n" + $ModifiedContent

# 5. 修正された内容を指定のテンプレートディレクトリに出力
$OutputHtmlPath = Join-Path $DjangoTemplateDir $TemplateFileName
$ModifiedContent | Out-File $OutputHtmlPath -Encoding UTF8

Write-Host "✅ HTMLファイルを修正し、$OutputHtmlPath として保存しました。" -ForegroundColor Green

Write-Host "--- 3. 静的アセットファイルのコピー ---" -ForegroundColor Cyan

# ターゲットディレクトリのクリーンアップ (既存ファイルを削除)
if (Test-Path $DjangoStaticDir) {
    # HTMLファイルはテンプレートとして残すため、dist/index.html 以外の全てを削除
    Get-ChildItem $DjangoStaticDir -Force | Remove-Item -Recurse -Force
} else {
    New-Item -Path $DjangoStaticDir -ItemType Directory | Out-Null
}

# dist ディレクトリ内の全ファイルとフォルダをコピー (index.html は除く)
Get-ChildItem $DistDir -Exclude "index.html" -Recurse | ForEach-Object {
    $Target = Join-Path $DjangoStaticDir $_.FullName.Substring($DistDir.Length)
    if ($_.PSIsContainer) {
        New-Item -Path $Target -ItemType Directory -Force | Out-Null
    } else {
        Copy-Item $_.FullName $Target -Force
    }
}

Write-Host "✅ 静的ファイル (JS/CSS/メディア) を $DjangoStaticDir にコピーしました。" -ForegroundColor Green

Write-Host "--- 🚀 デプロイスクリプトが正常に完了しました ---" -ForegroundColor Green
