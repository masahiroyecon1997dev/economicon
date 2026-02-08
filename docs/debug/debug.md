# 開発・デバッグガイド

このドキュメントでは、economicon プロジェクトの開発サーバー起動方法と VS Code でのデバッグ方法を説明します。

## 前提条件

- [共通セットアップ](../setup/common.md) が完了していること
- [バックエンドセットアップ](../setup/backend.md) が完了していること
- [フロントエンドセットアップ](../setup/frontend.md) が完了していること
- VS Code の推奨拡張機能がインストール済みであること

## 開発サーバーの起動

### バックエンド（FastAPI）

```powershell
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- **ポート**: 8000
- **API ドキュメント**: http://localhost:8000/docs

### フロントエンド（Tauri デスクトップアプリ）

```powershell
cd app
pnpm tauri dev
```

- バックエンドを先に起動しておくこと
- Vite 開発サーバーが自動起動（ポート 5173）

### ブラウザ確認用（Tauri なし）

```powershell
cd app
pnpm dev
```

- ブラウザで http://localhost:5173 にアクセス

## テストコマンド

### バックエンドテスト

```powershell
cd api
pytest                    # すべてのテスト
pytest -v                 # 詳細表示
pytest tests/test_*.py    # 特定のテスト
pytest --cov=economicon   # カバレッジ付き
```

### フロントエンドテスト

```powershell
cd app
pnpm test                 # ユニットテスト（Vitest）
pnpm test:ui              # UI モード
pnpm test:coverage        # カバレッジ付き
pnpm test:e2e             # E2E テスト（Playwright）
pnpm test:e2e:headed      # ブラウザ表示
pnpm test:e2e:debug       # デバッグモード
```

## ビルドコマンド

### フロントエンド

```powershell
cd app
pnpm build                # プロダクションビルド
pnpm tauri build          # Tauri インストーラー作成
pnpm lint                 # リンター実行
```

### バックエンド

```powershell
cd api
ruff check .              # リント
ruff check --fix .        # 自動修正
ruff format .             # フォーマット
```

## デバッグ設定の概要

プロジェクトには `.vscode/launch.json` にデバッグ設定が含まれています。

### 利用可能なデバッグ設定

| 設定名                             | 説明                               | 用途                                 |
| ---------------------------------- | ---------------------------------- | ------------------------------------ |
| **api-server**                     | FastAPI バックエンドのデバッグ     | Python/FastAPI コードのデバッグ      |
| **Tauri Development (Windows)**    | Tauri デスクトップアプリのデバッグ | Rust コードのデバッグ                |
| **pytest**                         | pytest テストのデバッグ            | Python テストコードのデバッグ        |
| **Full Stack Debug (API + Tauri)** | フルスタック同時デバッグ           | API + Tauri を同時に起動してデバッグ |

## 1. FastAPI バックエンドのデバッグ

### 手順

1. Python ファイルを開く
2. 行番号の左をクリックしてブレークポイントを設定
3. 「実行とデバッグ」（Ctrl+Shift+D）を開く
4. **`api-server`** を選択して F5 を押す

### 動作

- FastAPI サーバーがポート 8000 で起動
- ブレークポイントで停止
- 変数の確認・変更が可能
- デバッグコンソール（Ctrl+Shift+Y）で Python コード実行可能

## 2. Tauri デスクトップアプリのデバッグ

### Rust コードのデバッグ

1. Rust ファイルを開く
2. ブレークポイントを設定
3. **`Tauri Development (Windows)`** を選択して F5 を押す

### 動作

- Vite 開発サーバーが自動起動
- Tauri アプリがビルドされて起動
- Rust コードのブレークポイントで停止

### 必要な拡張機能

- **C/C++** (`ms-vscode.cpptools`)

### React/TypeScript コードのデバッグ

- Tauri アプリ内で右クリック → 「Inspect Element」
- DevTools でブレークポイントを設定
- または、コードに `debugger;` 文を挿入

## 3. pytest テストのデバッグ

### 手順

1. テストファイルを開く
2. ブレークポイントを設定
3. **`pytest`** を選択して F5 を押す

### 動作

- すべてのテストが実行
- ブレークポイントで停止

## 4. フルスタックデバッグ（API + Tauri）

### 手順

1. **`Full Stack Debug (API + Tauri)`** を選択して F5 を押す

### 動作

- FastAPI サーバーと Tauri アプリが同時に起動
- 両方にブレークポイントを設定可能
- 一方を停止すると両方が停止

## デバッグ機能

### 条件付きブレークポイント

- ブレークポイントを右クリック → 「ブレークポイントの編集」
- 条件を入力（例：`table_name == "test_table"`）

### ログポイント

- 行番号を右クリック → 「ログポイントの追加」
- 実行を停止せずにログを出力

### 変数ウォッチ

- デバッグビューの「ウォッチ」セクションで変数を追加
- 実行中に常に値が表示

### コールスタック

- デバッグビューの「コールスタック」セクションで呼び出し履歴を確認

## トラブルシューティング

### デバッグが開始されない

- Python: Ctrl+Shift+P → "Python: Select Interpreter" → `api/.venv` を選択
- Tauri: C/C++ 拡張機能がインストールされているか確認

### ブレークポイントで停止しない

- ブレークポイントが灰色 → コードが実行されていない
- `justMyCode: false` を設定してライブラリコードも含める

## キーボードショートカット

| 操作                      | ショートカット |
| ------------------------- | -------------- |
| デバッグ開始              | F5             |
| 停止                      | Shift+F5       |
| 再起動                    | Ctrl+Shift+F5  |
| ステップオーバー          | F10            |
| ステップイン              | F11            |
| ステップアウト            | Shift+F11      |
| 続行                      | F5             |
| ブレークポイント設定/解除 | F9             |

## 次のステップ

- [バックエンドセットアップ](../setup/backend.md) - Python 環境の詳細設定
- [フロントエンドセットアップ](../setup/frontend.md) - React/Tauri 環境の詳細設定

## 参考リンク

- [VS Code デバッグガイド](https://code.visualstudio.com/docs/editor/debugging)
- [Python デバッグ in VS Code](https://code.visualstudio.com/docs/python/debugging)
- [C++ デバッグ in VS Code](https://code.visualstudio.com/docs/cpp/cpp-debug)
