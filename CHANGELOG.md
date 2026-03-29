# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-24

### Added

- **データインポート/エクスポート**
  - CSV, Excel, Parquet 形式のインポートに対応
  - 解析済みデータの CSV, Excel, Parquet 形式での保存機能
- **データマネジメント**
  - データセットの名前変更、複製、削除機能
- **データ加工・生成**
  - テーブル結合 (Join) および 結合 (Union) 機能
  - シミュレーションデータ生成機能
  - 各種変数計算機能
- **統計解析**
  - 基本統計量の算出
  - 回帰分析 (OLS等) の実行機能
- **システム設定**
  - アプリケーションテーマの切り替え（ダーク/ライトモード等）
  - 多言語サポート
  - ファイルエンコーディング設定の変更

[0.1.0]: https://github.com/masahiroyecon1997dev/Economicon/releases/tag/v0.1.0

---

## [0.2.0] - 2026-03-29

### Added

- **相関行列作成**: 相関行列データを作成する機能を追加。
- **基本統計量の拡充**: 基本統計量の算出項目に「null数」「null割合」「有効サンプル数」「母分散」を追加。
- **シミュレーションの再現性向上**: シミュレーションデータ生成および列追加において、シード値を手動で指定できるオプションを追加。
- **データフィルタリング**: 列メニューからデータをフィルタリングできる機能を追加。

### Fixed

- **UI/UX の改善**: レスポンスが高速な場合にローディング表示がちらつく（閃光現象）問題を修正。
- **エラーハンドリングの強化**: サーバー起動に失敗した際、ローディングが止まらずエラーダイアログが表示されない問題を修正。
- **セキュリティと安定性**: 依存パッケージを最新バージョンに更新。

[0.2.0]: https://github.com/masahiroyecon1997dev/Economicon/releases/tag/v0.2.0

---
