# AnalysisApp

## 開発環境の開発手順

1. docker のインストール
2. Visual Studio Code にて以下の拡張機能を追加
   ・Dev Containers
3. Dev Containers の「開発コンテナー: キャッシュなしでリビルドし、コンテナーで再度開く」を実行
   ※次回以降「開発コンテナー: コンテナーで再度開く」を実行

## デバッグ

・api-server: REST API サーバのデバッグ（python）
・Launch Chrome: フロントエンドのデバッグ（react）

## コマンド

pnpm start: フロントエンド（react）の実行
pnpm lint: ESLint チェックの実行
pnpm lint:fix: ESLint 自動修正の実行
pnpm format: Prettier でフォーマット
python3 manage.py compilemessages -l ja(en): 多言語対応コンパイルファイル作成

## ライセンスチェック

### React

一覧
pnpm license-checker --summary
json 形式でファイル出力
pnpm license-checker --json > license_confirm.json

### Python

一覧
pip-licenses

## git のプッシュからマージの流れ

### 1. 作業ブランチの作成（dev から派生）

git checkout dev
git pull origin dev
git checkout -b feature/your-feature-name

### 2. 作業完了後、dev に PR を作成

git push -u origin feature/your-feature-name

#### GitHub で feature/your-feature-name → dev の PR を作成

### 3. dev での作業が完了したら、main に PR を作成

#### GitHub で dev → main の PR を作成

## テストカバレッジ調査

### 1. テストカバレッジコード

$ cd /AnalysisApp/AnalysisApp/ApiServer/analysisapp
$ coverage run manage.py test
$ coverage report -m

## 今後の課題

1. ジョイン・ユニオン機能の追加（キーは同じ列名のみでいい）
2. エクセルライクなグリッド機能
3. gretl と同等の分析機能

### API 機能

1.行作成、行削除 2.ダミー変数作成（複数の値を 1 にする、数値幅で 1 にできるようにする機能を追加）
3.Z 検定、t 検定、F 検定 4.回帰分析、ロジット・プロビット分析（t 分布を使用する、標準誤差計算オプションを追加） 5.固定効果モデル、変量効果モデル 6.操作変数法
