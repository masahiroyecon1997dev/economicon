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

## 今後の課題
1. ジョイン・ユニオン機能の追加（キーは同じ列名のみでいい）
2. エクセルライクなグリッド機能
3. gretlと同等の分析機能

### API機能
・インポート（csv, tsv, excel, parquet）〇
・エクスポート（csv, tsv, excel, parquet）　　
・テーブル作成、テーブル名変更、テーブル削除〇
・列作成、列名変更、列削除〇
・行作成、行削除　　　　　　　　　　　　　　　
・セル値入力〇
・行抽出（単一項目）　　〇　　　　　　　　　　　
・ジョイン、ユニオン
・列入力（シミュレーションデータ）
・列変換（log）
・ダミー変数作成
・列同士の計算
・Z検定、t検定、F検定
・回帰分析
・ロジット・プロビット分析
・固定効果モデル、変量効果モデル