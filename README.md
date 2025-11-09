# AnalysisApp

## 開発環境の開発手順
1. dockerのインストール
2. Visual Studio Codeにて以下の拡張機能を追加
     ・Dev Containers
3. Dev Containersの「開発コンテナー: キャッシュなしでリビルドし、コンテナーで再度開く」を実行
   ※次回以降「開発コンテナー: コンテナーで再度開く」を実行

## デバッグ
・api-server: REST APIサーバのデバッグ（python）
・Launch Chrome: フロントエンドのデバッグ（react）

## コマンド
yarn start: フロントエンド（react）の実行
yarn lint: ESLintチェックの実行
yarn lint:fix: ESLint自動修正の実行
yarn format: Prettierでフォーマット
python3 manage.py compilemessages -l ja(en): 多言語対応コンパイルファイル作成

## ライセンスチェック
### React
一覧
yarn license-checker --summary
json形式でファイル出力
yarn license-checker --json > license_confirm.json
### Python
一覧
pip-licenses

## gitのプッシュからマージの流れ
### 1. 作業ブランチの作成（devから派生）
git checkout dev
git pull origin dev
git checkout -b feature/your-feature-name

### 2. 作業完了後、devにPRを作成
git push -u origin feature/your-feature-name
#### GitHubでfeature/your-feature-name → dev のPRを作成

### 3. devでの作業が完了したら、mainにPRを作成
#### GitHubでdev → main のPRを作成

## テストカバレッジ調査
### 1. テストカバレッジコード
$ cd /AnalysisApp/AnalysisApp/ApiServer/analysisapp
$ coverage run manage.py test
$ coverage report -m

## 今後の課題
1. ジョイン・ユニオン機能の追加（キーは同じ列名のみでいい）
2. エクセルライクなグリッド機能
3. gretlと同等の分析機能

### API機能
1.行作成、行削除
2.ダミー変数作成（複数の値を1にする、数値幅で1にできるようにする機能を追加）
3.Z検定、t検定、F検定
4.回帰分析、ロジット・プロビット分析（t分布を使用する、標準誤差計算オプションを追加）
5.固定効果モデル、変量効果モデル
6.操作変数法

