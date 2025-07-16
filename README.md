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

## 今後の課題
1. ジョイン・ユニオン機能の追加（キーは同じ列名のみでいい）
2. エクセルライクなグリッド機能
3. gretlと同等の分析機能

### API機能
1.インポート（csv, tsv, excel, parquet）〇
2.エクスポート（csv, tsv, excel, parquet）　　
3.テーブル作成、テーブル名変更、テーブル削除〇
4.列作成、列名変更、列削除〇
5.行作成、行削除　　　　　　　　　　　　　　　
6.セル値入力〇
7.行抽出（単一項目）　　〇　　　　　　　　　　　
8.ジョイン、ユニオン
9.列入力（シミュレーションデータ）
10.列変換（log）
11.ダミー変数作成
12.列同士の計算
13.Z検定、t検定、F検定
14.回帰分析
15.ロジット・プロビット分析
16.固定効果モデル、変量効果モデル