# フロントエンドセットアップガイド

economicon のフロントエンド（React/TypeScript）環境を構築する手順を説明します。

## 技術スタック

- **Node.js**: 18 以上
- **パッケージマネージャー**: pnpm (推奨)
- **フレームワーク**: React 19.2.3 + TypeScript
- **ビルドツール**: Vite 7.2.7
- **デスクトップアプリ**: Tauri（任意）
- **スタイリング**: Tailwind CSS 4.1.18
- **UI コンポーネント**: Radix UI
- **テスト**: Vitest, Playwright

## 1. Node.js バージョンマネージャー（fnm）のインストール

fnm (Fast Node Manager) は、複数の Node.js バージョンを管理するための高速なツールです。

### Windows

#### PowerShell でインストール

```powershell
# winget を使用（推奨）
winget install Schniz.fnm

# または Chocolatey を使用
choco install fnm

# 環境変数の設定を PowerShell プロファイルに追加
notepad $PROFILE
```

`$PROFILE` ファイルに以下を追加：

```powershell
# fnm の設定
fnm env --use-on-cd | Out-String | Invoke-Expression
```

PowerShell を再起動して設定を反映。

### Linux

```bash
# curl を使用してインストール
curl -fsSL https://fnm.vercel.app/install | bash

# シェル設定ファイルに追加（bash の場合）
echo 'eval "$(fnm env --use-on-cd)"' >> ~/.bashrc
source ~/.bashrc

# zsh の場合
echo 'eval "$(fnm env --use-on-cd)"' >> ~/.zshrc
source ~/.zshrc
```

### macOS

```bash
# Homebrew を使用
brew install fnm

# シェル設定ファイルに追加
echo 'eval "$(fnm env --use-on-cd)"' >> ~/.zshrc
source ~/.zshrc
```

### インストール確認

```powershell
fnm --version
# fnm x.x.x と表示されることを確認
```

## 2. Node.js のインストール（fnm を使用）

### 最新 LTS バージョンをインストール

```powershell
# 利用可能な LTS バージョンを確認
fnm ls-remote

# 最新の LTS バージョンをインストール
fnm install --lts

# インストールした Node.js を使用
fnm use lts-latest

# デフォルトバージョンとして設定
fnm default lts-latest
```

### 特定バージョンをインストール（推奨: Node.js 20 LTS）

```powershell
# Node.js 20 LTS をインストール
fnm install 20

# Node.js 20 を使用
fnm use 20

# デフォルトとして設定
fnm default 20
```

### インストール確認

```powershell
node --version
# v20.x.x または v18.x.x と表示されることを確認

npm --version
# 10.x.x と表示されることを確認
```

### プロジェクトごとの Node.js バージョン管理（推奨）

```powershell
# プロジェクトルートに .node-version ファイルを作成
cd economicon
echo "20" > .node-version

# ディレクトリに入ると自動的に切り替わる
cd economicon
# fnm が自動的に Node.js 20 を使用
```

## 3. pnpm のインストール

pnpm は高速でディスク効率の良いパッケージマネージャーです。

### インストール方法

```powershell
# npm を使用してグローバルインストール（推奨）
npm install -g pnpm@latest

# または Corepack を使用（Node.js 16.9+ に同梱）
corepack enable
corepack prepare pnpm@latest --activate
```

### インストール確認

```powershell
pnpm --version
# 9.x.x と表示されることを確認
```

### pnpm の設定（任意）

```powershell
# グローバルストアの場所を確認
pnpm store path

# ストアをクリーンアップ（容量削減）
pnpm store prune
```

## 4. Vite プロジェクトのセットアップ

Vite は高速なビルドツールで、既にプロジェクトに組み込まれています。

### 依存パッケージのインストール

```powershell
# プロジェクトディレクトリに移動
cd economicon/front-analysis-app

# 依存関係をインストール
pnpm install
```

#### インストールされる主要パッケージ

- **React & React DOM**: UI ライブラリ
- **TypeScript**: 型安全性
- **Vite**: ビルドツール
- **Tailwind CSS**: ユーティリティファーストの CSS フレームワーク
- **Radix UI**: アクセシブルな UI コンポーネント
- **Zustand**: 軽量な状態管理
- **react-i18next**: 国際化
- **Vitest**: ユニットテストフレームワーク
- **Playwright**: E2E テストフレームワーク

### 開発サーバーの起動

```powershell
# 開発サーバーを起動
pnpm dev
```

ブラウザで自動的に開かない場合は、http://localhost:5173 にアクセス。

### Vite の主要コマンド

```powershell
# 開発サーバー起動
pnpm dev

# プロダクションビルド
pnpm build

# ビルド結果のプレビュー
pnpm preview

# リンターの実行
pnpm lint

# リンターの自動修正
pnpm lint:fix
```

## 5. Tauri のセットアップ（デスクトップアプリ化）

Tauri を使用すると、Web アプリをネイティブデスクトップアプリに変換できます。

### 前提条件

#### Windows

```powershell
# Microsoft C++ Build Tools をインストール
winget install Microsoft.VisualStudio.2022.BuildTools --override "--wait --passive --add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64"

# WebView2 をインストール（Windows 11 には標準搭載）
winget install Microsoft.EdgeWebView2Runtime
```

#### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install libwebkit2gtk-4.0-dev \
    build-essential \
    curl \
    wget \
    file \
    libssl-dev \
    libgtk-3-dev \
    libayatana-appindicator3-dev \
    librsvg2-dev
```

#### macOS

```bash
# Xcode Command Line Tools をインストール
xcode-select --install
```

### Rust のインストール

Tauri は Rust で書かれているため、Rust ツールチェーンが必要です。

#### Windows/Linux/macOS

```powershell
# rustup を使用してインストール
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# パスを通す（Linux/macOS）
source $HOME/.cargo/env

# Windows の場合は PowerShell を再起動
```

#### インストール確認

```powershell
rustc --version
cargo --version
```

### Tauri CLI のインストール

```powershell
# プロジェクトの依存関係として既に含まれています
cd front-analysis-app
pnpm install
```

### Tauri の開発サーバー起動

```powershell
# バックエンドを先に起動
cd ../ApiServer
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 別のターミナルで Tauri 開発サーバーを起動
cd ../front-analysis-app
pnpm tauri dev
```

### Tauri アプリのビルド

```powershell
# プロダクションビルド（インストーラー作成）
pnpm tauri build
```

ビルドされたアプリは `src-tauri/target/release/bundle/` に生成されます。

### Tauri の主要コマンド

```powershell
# 開発モードで起動
pnpm tauri dev

# プロダクションビルド
pnpm tauri build

# ビルド設定の確認
pnpm tauri info
```

## 6. テスト環境のセットアップ

### ユニットテスト（Vitest）

```powershell
# テストの実行
pnpm test

# UI モードでテスト
pnpm test:ui

# カバレッジ付きテスト
pnpm test:coverage
```

### E2E テスト（Playwright）

```powershell
# Playwright ブラウザのインストール
pnpm exec playwright install

# E2E テストの実行
pnpm test:e2e

# UI モードで実行
pnpm test:e2e:ui

# ブラウザを表示して実行
pnpm test:e2e:headed
```

## 7. VS Code でのデバッグ設定

### React アプリのデバッグ

1. VS Code で `front-analysis-app` を開く
2. F5 キーを押す、または「実行とデバッグ」パネルから「Launch Chrome」を選択
3. ブレークポイントを設定してデバッグ開始

### デバッグ設定（`.vscode/launch.json`）

プロジェクトには既に設定が含まれています。

## 開発コマンド一覧

```powershell
# 開発サーバー起動
pnpm dev

# Tauri 開発サーバー起動
pnpm tauri dev

# ビルド
pnpm build

# ビルド結果のプレビュー
pnpm preview

# リント
pnpm lint

# ユニットテスト
pnpm test

# E2E テスト
pnpm test:e2e

# すべてのテスト
pnpm test && pnpm test:e2e

# カバレッジ
pnpm test:coverage

# 型チェック
pnpm tsc --noEmit
```

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

Vite は自動的に別のポートを使用しますが、手動で指定することも可能：

```powershell
pnpm dev --port 3000
```

### pnpm のストレージ容量が大きい

```powershell
# 不要なパッケージを削除
pnpm store prune
```

### Playwright ブラウザのインストールエラー

```powershell
# 手動でブラウザをインストール
pnpm exec playwright install --with-deps
```

### Tauri ビルドエラー（Windows）

```powershell
# Visual Studio Build Tools が正しくインストールされているか確認
# 必要に応じて再インストール
winget install Microsoft.VisualStudio.2022.BuildTools
```

### fnm で Node.js バージョンが切り替わらない

```powershell
# PowerShell プロファイルを確認
notepad $PROFILE

# 以下が含まれているか確認
# fnm env --use-on-cd | Out-String | Invoke-Expression

# PowerShell を再起動
```

## 次のステップ

- [バックエンドセットアップ](./backend.md) - Python/FastAPI 環境の構築
- コンポーネントの開発
- テストの追加
- Tauri アプリのカスタマイズ

## 参考リンク

- [fnm ドキュメント](https://github.com/Schniz/fnm)
- [pnpm ドキュメント](https://pnpm.io/)
- [Vite ガイド](https://vitejs.dev/guide/)
- [Tauri ガイド](https://tauri.app/v1/guides/)
- [React ドキュメント](https://react.dev/)
- [Vitest ガイド](https://vitest.dev/)
- [Playwright ドキュメント](https://playwright.dev/)
