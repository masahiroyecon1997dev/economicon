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

## 今後の課題
1. ジョイン・ユニオン機能の追加（キーは同じ列名のみでいい）
2. エクセルライクなグリッド機能
3. gretlと同等の分析機能

