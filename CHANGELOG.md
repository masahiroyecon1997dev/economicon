# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-03-29

### ✨ Added

- **相関行列作成**: 相関行列データを作成する機能を追加。
- **基本統計量の拡充**: `null数`, `null割合`, `有効サンプル数`, `母分散` を追加。
- **シミュレーションの再現性**: シード値を手動で指定できるオプションを追加。
- **データフィルタリング**: 列メニューからデータをフィルタリングできる機能を追加。

### 🐞 Fixed

- **UI/UX 改善**: 高速レスポンス時のローディングの「ちらつき」を解消。
- **エラーハンドリング**: サーバー起動失敗時にダイアログが出ない問題を修正。

### 🔒 Security

- **安定性向上**: 依存パッケージを最新バージョンに更新。

[0.2.0]: https://github.com/masahiroyecon1997dev/Economicon/releases/tag/v0.2.0

---

## [0.1.0] - 2026-03-24

### ✨ Added

- **📥 データインポート/エクスポート**
  - **多形式対応**: CSV, Excel, Parquet 形式のインポートにネイティブ対応。
  - **データ保存**: 解析済みデータを CSV, Excel, Parquet 形式で出力・保存する機能。
- **🗂️ データマネジメント**
  - **基本操作**: データセットの名前変更、複製、削除機能。
- **🛠️ データ加工・生成**
  - **テーブル操作**: 複数のデータを統合する `Join`（結合）および `Union`（連結）機能。
  - **シミュレーション**: 統計モデル構築のためのテスト用データ生成機能。
  - **変数操作**: 既存の列に基づいた高度な変数計算機能。
- **📊 統計解析**
  - **基本統計量**: 平均、分散、中央値などの記述統計量の算出。
  - **推定モデル**: 回帰分析 (OLS等) の実行機能。
- **⚙️ システム設定**
  - **外観カスタマイズ**: ダークモード/ライトモードのテーマ切り替え。
  - **国際化 (i18n)**: 複数言語でのインターフェース表示をサポート。
  - **エンコーディング**: 日本語データ等で重要なファイル文字コード設定の変更機能。

[0.1.0]: https://github.com/masahiroyecon1997dev/Economicon/releases/tag/v0.1.0

---
