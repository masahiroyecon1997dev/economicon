# 開発環境セットアップ - 共通

このドキュメントでは、economicon の開発環境を構築するための共通の前提条件と全体的な流れを説明します。

## 前提条件

### オペレーティングシステム

- **Windows**: Windows 10/11 (推奨)
- **Linux**: Ubuntu 20.04 以上
- **macOS**: macOS 12 (Monterey) 以上

### 必須ツール

- **Git**: バージョン管理
- **Visual Studio Code**: 推奨エディタ（任意）

### Git のインストール

#### Windows

```powershell
# Windows Package Manager (winget) を使用
winget install Git.Git

# または Chocolatey を使用
choco install git
```

#### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install git
```

#### macOS

```bash
# Homebrew を使用
brew install git
```

### Visual Studio Code のインストール（推奨）

#### Windows

```powershell
winget install Microsoft.VisualStudioCode
```

#### Linux

```bash
sudo snap install code --classic
```

#### macOS

```bash
brew install --cask visual-studio-code
```

### VS Code 推奨拡張機能

開発を効率化するための推奨拡張機能：

- **Python**: ms-python.python
- **Pylance**: ms-python.vscode-pylance
- **ESLint**: dbaeumer.vscode-eslint
- **Prettier**: esbenp.prettier-vscode
- **Tailwind CSS IntelliSense**: bradlc.vscode-tailwindcss
- **TypeScript Vue Plugin (Volar)**: Vue.vscode-typescript-vue-plugin
- **GitHub Copilot**: github.copilot

## セットアップの流れ

1. **リポジトリのクローン**

   ```bash
   git clone https://github.com/MasahiroYamada1997-1/economicon.git
   cd economicon
   ```

2. **バックエンドのセットアップ**
   - [バックエンドセットアップガイド](./backend.md) を参照

3. **フロントエンドのセットアップ**
   - [フロントエンドセットアップガイド](./frontend.md) を参照

4. **開発サーバーの起動**
   - バックエンド: `cd ApiServer && uvicorn main:app --reload --host 0.0.0.0 --port 8000`
   - フロントエンド: `cd app && pnpm dev`

## Docker 環境での開発

Docker を使用した開発環境も提供しています。

### Docker のインストール

#### Windows

```powershell
winget install Docker.DockerDesktop
```

#### Linux

```bash
# Docker Engine のインストール
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

#### macOS

```bash
brew install --cask docker
```

### Dev Container を使用した開発

1. **Visual Studio Code に拡張機能をインストール**
   - Dev Containers: ms-vscode-remote.remote-containers

2. **コンテナで開く**
   - VS Code で `F1` を押し、「Dev Containers: Rebuild and Reopen in Container」を実行
   - 初回は時間がかかりますが、次回以降は「Dev Containers: Reopen in Container」で高速に起動

3. **コンテナ内での作業**
   - すべての依存関係が自動的にインストールされます
   - ターミナルはコンテナ内で実行されます

## トラブルシューティング

### ポート競合エラー

バックエンドサーバーがポート 8000 で起動できない場合：

```powershell
# Windows: ポートを使用しているプロセスを確認
netstat -ano | findstr :8000

# プロセスを終了
taskkill /PID <プロセスID> /F
```

```bash
# Linux/macOS
lsof -i :8000
kill -9 <プロセスID>
```

### 権限エラー（Linux/macOS）

```bash
# sudo なしで Docker を実行できるようにする
sudo usermod -aG docker $USER
newgrp docker
```

## 次のステップ

- [バックエンドセットアップ](./backend.md) - Python/FastAPI 環境の構築
- [フロントエンドセットアップ](./frontend.md) - Node.js/React 環境の構築
