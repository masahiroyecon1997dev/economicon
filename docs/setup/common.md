# 開発環境セットアップ - 共通

このドキュメントでは、economicon の開発環境を構築するための共通の前提条件と全体的な流れを説明します。

## 前提条件

### オペレーティングシステム

- **Windows 11**

> **注意**: 現在、開発環境は Windows 11 のみをサポートしています。

### 必須ツール

- **Git**: バージョン管理
- **Visual Studio Code**: 推奨エディタ

## ツールのインストール

### Git のインストール

1. [Git公式サイト](https://git-scm.com/download/win) から Windows版をダウンロード
2. インストーラーを実行
3. デフォルト設定で進める（推奨）

#### インストール確認

```powershell
git --version
# git version 2.x.x と表示されることを確認
```

### Visual Studio Code のインストール

1. [Visual Studio Code公式サイト](https://code.visualstudio.com/) から Windows版をダウンロード
2. インストーラーを実行
3. 推奨設定:
   - 「PATH への追加」にチェック
   - 「コンテキストメニューに追加」にチェック

#### インストール確認

```powershell
code --version
```

### VS Code 推奨拡張機能

プロジェクトには推奨拡張機能リストが含まれています。

1. VS Code を開く
2. 拡張機能パネル（Ctrl+Shift+X）を開く
3. 検索欄に `@recommended` と入力
4. 「ワークスペースの推奨事項」に表示される拡張機能をすべてインストール

> `.vscode/extensions.json` に推奨拡張機能のリストが定義されています。

## セットアップの流れ

1. **リポジトリのクローン**

   ```powershell
   git clone xxx
   cd economicon
   ```

2. **バックエンドのセットアップ**
   - [バックエンドセットアップガイド](./backend.md) を参照

3. **フロントエンドのセットアップ**
   - [フロントエンドセットアップガイド](./frontend.md) を参照

4. **開発サーバーの起動とデバッグ**
   - [開発・デバッグガイド](../debug/debug.md) を参照

## トラブルシューティング

### ポート競合エラー

バックエンドサーバーがポート 8000 で起動できない場合：

```powershell
# ポートを使用しているプロセスを確認
netstat -ano | findstr :8000

# プロセスを終了
taskkill /PID <プロセスID> /F
```

フロントエンドがポート 5173 で起動できない場合：

```powershell
# Vite は自動的に別のポートを使用しますが、手動で指定することも可能
pnpm dev --port 3000
```

## 次のステップ

- [バックエンドセットアップ](./backend.md) - Python/FastAPI 環境の構築
- [フロントエンドセットアップ](./frontend.md) - Node.js/React/Tauri 環境の構築
- [開発・デバッグガイド](../debug/debug.md) - 開発サーバーの起動方法とデバッグ方法
