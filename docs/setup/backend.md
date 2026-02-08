# バックエンドセットアップガイド

economicon のバックエンド（Python/FastAPI）環境を構築する手順を説明します。

## 技術スタック

- **Python**: 3.14
- **フレームワーク**: FastAPI 0.128.0
- **パッケージマネージャー**: uv
- **データ処理**: Polars, NumPy, SciPy, statsmodels
- **ASGI サーバー**: Uvicorn 0.40.0
- **テスト**: pytest 9.0.2, Coverage

## 1. Python 3.14 のインストール

### Windows

#### 方法1: 公式インストーラー（推奨）

1. [Python公式サイト](https://www.python.org/downloads/) から Python 3.14 をダウンロード
2. インストーラーを実行
3. **重要**: 「Add Python 3.14 to PATH」にチェックを入れる
4. 「Install Now」をクリック

#### 方法2: winget を使用

```powershell
# 利用可能なバージョンを確認
winget search Python.Python

# Python 3.14 をインストール
winget install Python.Python.3.14
```

#### 方法3: Chocolatey を使用

```powershell
choco install python --version=3.14.0
```

#### インストール確認

```powershell
python --version
# Python 3.14.x と表示されることを確認
```

### Linux (Ubuntu/Debian)

```bash
# deadsnakes PPA を追加（最新バージョン用）
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

# Python 3.14 をインストール
sudo apt install python3.14 python3.14-venv python3.14-dev

# デフォルトの python3 として設定（任意）
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.14 1

# インストール確認
python3.14 --version
```

### macOS

```bash
# Homebrew を使用
brew install python@3.14

# パスを通す（~/.zshrc または ~/.bash_profile に追加）
echo 'export PATH="/usr/local/opt/python@3.14/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# インストール確認
python3.14 --version
```

## 2. uv のインストール

uv は高速な Python パッケージマネージャーです。

### Windows

```powershell
# PowerShell でインストール
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# または pip を使用
pip install uv
```

### Linux/macOS

```bash
# curl を使用してインストール（推奨）
curl -LsSf https://astral.sh/uv/install.sh | sh

# または pip を使用
pip install uv
```

### インストール確認

```powershell
uv --version
# uv 0.x.x と表示されることを確認
```

## 3. バックエンドプロジェクトのセットアップ

### 仮想環境の作成

```powershell
# プロジェクトルートに移動
cd economicon/ApiServer

# Python 3.14 を指定して仮想環境を作成
uv venv --python 3.14
```

### 仮想環境の有効化

#### Windows (PowerShell)

```powershell
.\.venv\Scripts\Activate.ps1
```

#### Windows (コマンドプロンプト)

```cmd
.venv\Scripts\activate.bat
```

#### Linux/macOS

```bash
source .venv/bin/activate
```

> **注意**: PowerShell で実行ポリシーエラーが発生する場合：
>
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 依存パッケージのインストール

#### Windows

```powershell
# Windows 用の依存関係をインストール
uv pip install -r python-requirements\windows-requirements.txt
```

#### Linux

```bash
# Ubuntu 用の依存関係をインストール
uv pip install -r python-requirements/ubuntu-requirements.txt
```

#### 主要パッケージ

- **FastAPI**: Web フレームワーク
- **Uvicorn**: ASGI サーバー
- **Polars**: 高速データ処理ライブラリ
- **NumPy**: 数値計算ライブラリ
- **SciPy**: 科学計算ライブラリ
- **statsmodels**: 統計モデリング
- **Pydantic**: データバリデーション
- **fastapi-babel**: 国際化サポート
- **pytest**: テストフレームワーク

## 4. 開発サーバーの起動

### 基本的な起動

```powershell
# ApiServer ディレクトリで実行
uvicorn main:app --reload
```

### 推奨オプション付きで起動

```powershell
# ホストとポートを指定して起動
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level info
```

オプション説明：

- `--reload`: コード変更時に自動リロード（開発時のみ使用）
- `--host 0.0.0.0`: すべてのネットワークインターフェースでリスン
- `--port 8000`: ポート番号の指定
- `--log-level info`: ログレベルの設定

### 起動確認

ブラウザで以下にアクセス：

- **API ドキュメント**: http://localhost:8000/docs
- **代替ドキュメント**: http://localhost:8000/redoc
- **ヘルスチェック**: http://localhost:8000/api/health (存在する場合)

## 5. 開発ツール

### テストの実行

```powershell
# すべてのテストを実行
pytest tests

# 詳細表示でテスト実行
pytest tests -v

# 特定のテストファイルを実行
pytest tests/test_create_table.py

# カバレッジ付きテスト
pytest tests --cov=analysisapp --cov-report=html

# カバレッジレポートの表示
coverage report -m
```

### コード品質チェック

```powershell
# Ruff でリント（設定されている場合）
ruff check .

# フォーマットチェック
ruff format --check .

# 自動フォーマット
ruff format .
```

### 型チェック

```powershell
# mypy で型チェック（設定されている場合）
mypy analysisapp
```

## 6. VS Code でのデバッグ設定

プロジェクトには `.vscode/launch.json` が含まれています。

### デバッグの開始

1. VS Code で `ApiServer/main.py` を開く
2. F5 キーを押す、または「実行とデバッグ」パネルから「api-server」を選択
3. ブレークポイントを設定してデバッグ開始

## トラブルシューティング

### パッケージインストールエラー

```powershell
# uv を最新版に更新
pip install --upgrade uv

# キャッシュをクリアして再インストール
uv cache clean
uv pip install --reinstall -r python-requirements\windows-requirements.txt
```

### ImportError: No module named 'analysisapp'

プロジェクトルート（`ApiServer/`）から起動しているか確認：

```powershell
cd ApiServer
uvicorn main:app --reload
```

### ポート 8000 が使用中

別のポートを使用：

```powershell
uvicorn main:app --reload --port 8001
```

または、他のプロセスを終了：

```powershell
# Windows
netstat -ano | findstr :8000
taskkill /PID <プロセスID> /F
```

### SSL/TLS エラー（Windows）

```powershell
# pip の SSL 証明書を更新
pip install --upgrade certifi
```

### 仮想環境が認識されない（VS Code）

1. Ctrl+Shift+P を押す
2. "Python: Select Interpreter" を選択
3. `.venv` 内の Python インタープリターを選択

## 次のステップ

- [フロントエンドセットアップ](./frontend.md) - React 環境の構築
- API エンドポイントの開発
- テストの追加
- ドキュメントの拡充

## 参考リンク

- [FastAPI 公式ドキュメント](https://fastapi.tiangolo.com/)
- [uv 公式ドキュメント](https://github.com/astral-sh/uv)
- [Polars ガイド](https://pola-rs.github.io/polars-book/)
- [pytest ドキュメント](https://docs.pytest.org/)
