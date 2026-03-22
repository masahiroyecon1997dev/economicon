# フロントエンドセットアップガイド

economicon のフロントエンド（React/TypeScript/Tauri）環境を構築する手順を説明します。

## 技術スタック

- **Node.js**: 24 LTS（推奨）
- **パッケージマネージャー**: pnpm
- **フレームワーク**: React 19 + TypeScript
- **ビルドツール**: Vite 7
- **デスクトップアプリ**: Tauri 2
- **スタイリング**: Tailwind CSS 4
- **UI コンポーネント**: Radix UI
- **テスト**: Vitest, Playwright

## 1. fnm のインストール

fnm (Fast Node Manager) は、複数の Node.js バージョンを管理するための高速なツールです。

### Chocolatey 経由でインストール

```powershell
# Chocolatey をインストール（未インストールの場合）
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# fnm をインストール
choco install fnm
```

### 環境変数の設定

PowerShell プロファイルに fnm の設定を追加：

```powershell
# プロファイルを開く
notepad $PROFILE
```

以下を追加して保存：

```powershell
# fnm の設定
fnm env --use-on-cd | Out-String | Invoke-Expression
```

PowerShell を再起動して設定を反映。

### インストール確認

```powershell
fnm --version
# fnm x.x.x と表示されることを確認
```

## 2. Node.js 24 のインストール

### fnm を使用してインストール

```powershell
# Node.js 24 LTS をインストール
fnm install 24

# Node.js 24 を使用
fnm use 24

# デフォルトバージョンとして設定
fnm default 24
```

### インストール確認

```powershell
node --version
# v24.x.x と表示されることを確認

npm --version
# 10.x.x と表示されることを確認
```

### プロジェクトごとのバージョン管理

プロジェクトルートに `.node-version` ファイルが既に存在します。

```powershell
# プロジェクトディレクトリに入ると自動的に切り替わる
cd economicon
# fnm が自動的に Node.js 24 を使用
```

## 3. pnpm のインストール

pnpm は高速でディスク効率の良いパッケージマネージャーです。

### npm 経由でインストール

```powershell
# グローバルインストール
npm install -g pnpm@latest
```

### インストール確認

```powershell
pnpm --version
# 9.x.x と表示されることを確認
```

## 4. Rust のインストール（Tauri 用）

Tauri は Rust で書かれているため、Rust ツールチェーンが必要です。

### Rust インストーラーのダウンロード

1. [Rust公式サイト](https://www.rust-lang.org/tools/install) にアクセス
2. Windows 用インストーラー（rustup-init.exe）をダウンロード
3. インストーラーを実行
4. デフォルト設定で進める（推奨）

### インストール確認

```powershell
# PowerShell を再起動後
rustc --version
cargo --version
```

## 5. Microsoft C++ Build Tools のインストール

Tauri のビルドに必要です。

### インストール方法（推奨）

1. [Visual Studio Installer](https://visualstudio.microsoft.com/downloads/) にアクセス
2. 「Build Tools for Visual Studio 2022」をダウンロード
3. インストーラーを実行
4. 「C++ によるデスクトップ開発」ワークロードを選択
5. インストール

### WebView2 のインストール確認

Windows 11 には標準搭載されています。

## 6. フロントエンドプロジェクトのセットアップ

### 依存パッケージのインストール

```powershell
# プロジェクトディレクトリに移動
cd economicon\app

# 依存関係をインストール
pnpm install
```

#### インストールされる主要パッケージ

- **React & React DOM**: UI ライブラリ
- **TypeScript**: 型安全性
- **Vite**: ビルドツール
- **Tailwind CSS**: スタイリング
- **Radix UI**: アクセシブルな UI コンポーネント
- **Zustand**: 状態管理
- **react-i18next**: 国際化
- **Vitest**: ユニットテスト
- **Playwright**: E2Eテスト
- **Tauri CLI**: デスクトップアプリビルドツール

## 7. Playwright ブラウザのインストール

E2E テストに必要です。

```powershell
# Playwright ブラウザをインストール
pnpm exec playwright install
```

## 次のステップ

- [バックエンドセットアップ](./backend.md) - Python/FastAPI 環境の構築（未起動の場合）
- [開発・デバッグガイド](../debug/debug.md) - 開発サーバーの起動方法とデバッグ方法

## トラブルシューティング

### node_modules のクリーンインストール

```powershell
# node_modules を削除
Remove-Item -Recurse -Force node_modules

# ロックファイルを削除（必要な場合）
Remove-Item pnpm-lock.yaml

# 再インストール
pnpm install
```

### ポート 5173 が使用中

```powershell
# 手動でポートを指定
pnpm dev --port 3000
```

### Tauri ビルドエラー

```powershell
# Rust を最新版に更新
rustup update

# Tauri CLI を再インストール
pnpm add -D @tauri-apps/cli
```

### fnm で Node.js バージョンが切り替わらない

```powershell
# PowerShell プロファイルを確認
notepad $PROFILE

# 以下が含まれているか確認し、なければ追加
# fnm env --use-on-cd | Out-String | Invoke-Expression

# PowerShell を再起動
```

### pnpm のストレージ容量が大きい

```powershell
# 不要なパッケージを削除
pnpm store prune
```

## 参考リンク

- [fnm ドキュメント](https://github.com/Schniz/fnm)
- [pnpm ドキュメント](https://pnpm.io/)
- [Vite ガイド](https://vitejs.dev/guide/)
- [Tauri ガイド](https://tauri.app/v1/guides/)
- [React ドキュメント](https://react.dev/)
- [Rust 公式サイト](https://www.rust-lang.org/)
- [Vitest ガイド](https://vitest.dev/)
- [Playwright ドキュメント](https://playwright.dev/)
