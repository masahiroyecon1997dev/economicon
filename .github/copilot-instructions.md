# Economicon — Copilot Instructions

Economicon はスタンドアロン型計量経済分析デスクトップアプリ（Windows）。
**FastAPI Python サイドカー** + **React 19 / Tauri 2** 構成。フロントエンド↔バックエンドの通信は Tauri `invoke` のみ（HTTP fetch 禁止）。

## 詳細ルール

| 対象                       | ドキュメント                                                                         |
| -------------------------- | ------------------------------------------------------------------------------------ |
| API 実装ルール全般         | [instructions/api.instructions.md](instructions/api.instructions.md)                 |
| App 実装ルール全般         | [instructions/app.instructions.md](instructions/app.instructions.md)                 |
| アプリコンセプト・不変条件 | [instructions/app-concept.instructions.md](instructions/app-concept.instructions.md) |
| 開発環境セットアップ       | [docs/README.md](../docs/README.md)                                                  |

## ビルド・テストコマンド

| タスク                | コマンド                                                         |
| --------------------- | ---------------------------------------------------------------- |
| API lint              | `cd api; .venv\Scripts\ruff check .`                             |
| API テスト            | `cd api; .venv\Scripts\pytest`                                   |
| App ユニットテスト    | `cd app; pnpm test --run`                                        |
| App E2E テスト        | `cd app; pnpm test:e2e`                                          |
| TS クライアント再生成 | `cd app; pnpm gen:all`                                           |
| メッセージコンパイル  | `cd api; .venv\Scripts\pybabel compile -f -d economicon/locales` |

> **API スキーマを変更したら必ず `pnpm gen:all` を実行**してフロントエンドの型を同期すること。

## クロスカット規約（陥りやすいミス）

- **Polars 優先**: API では Polars を使う。Pandas は statsmodels / linearmodels との連携時のみ
- **型の手書き禁止**: フロントエンドの型・Zod スキーマは `@/api/model` / `@/api/zod`（Orval 生成）から import
- **i18n**: API のユーザー向け文字列は `_()` でラップ。JSX 内に日本語ハードコード禁止（`t("Key")` を使用）
- **データ不変性**: 操作時は元テーブルを上書きせず新テーブルを生成する
- **テスト**: API の `message`/`details` は完全一致でアサートする

## カスタムエージェント

10 種類のエージェントを [agents/](agents/) で定義:

| エージェント             | 用途                                   |
| ------------------------ | -------------------------------------- |
| `api-architect`          | FastAPI / Polars 設計・実装            |
| `app-architect`          | React / Tauri フロントエンド設計・実装 |
| `api-reviewer`           | API コードレビュー                     |
| `app-reviewer`           | フロントエンドコードレビュー           |
| `api-test-engineer`      | pytest テスト設計・実装                |
| `app-test-engineer`      | Vitest / Playwright テスト設計・実装   |
| `app-design-reviewer`    | UI/UX レビュー                         |
| `ci-cd-build-specialist` | CI/CD・リリース管理                    |
| `document-writer`        | ドキュメント作成・更新                 |
| `agent-manager`          | エージェント定義・instructions の保守  |
