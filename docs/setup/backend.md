# バックエンドセットアップガイド

economicon のバックエンド（Python/FastAPI）環境を構築する手順を説明します。

## 技術スタック

- **Python**: 3.14
- **フレームワーク**: FastAPI 0.128.7+
- **パッケージマネージャー**: uv
- **データ処理**: Polars, NumPy, SciPy, statsmodels
- **ASGI サーバー**: Uvicorn 0.40.0+
- **テスト**: pytest 9.0.2

## 1. uv のインストール

uv は高速な Python パッケージマネージャーです。Python 本体も uv 経由でインストールします。

### PowerShell でインストール

```powershell
# uv をインストール
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### インストール確認

```powershell
uv --version
# uv 0.x.x と表示されることを確認
```

> **注意**: PowerShell を再起動して PATH を反映させてください。

## 2. Python 3.14 のインストール（uv 経由）

uv を使用して Python をインストールします。

```powershell
# Python 3.14 をインストール
uv python install 3.14

# インストール確認
uv python list
```

## 3. バックエンドプロジェクトのセットアップ

### プロジェクトディレクトリに移動

```powershell
# プロジェクトルートに移動
cd economicon\api
```

### 仮想環境の作成

```powershell
# Python 3.14 を指定して仮想環境を作成
uv venv --python 3.14
```

### 仮想環境の有効化

```powershell
# PowerShell
.\.venv\Scripts\Activate.ps1
```

> **注意**: PowerShell で実行ポリシーエラーが発生する場合：
>
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 依存パッケージのインストール

```powershell
# pyproject.toml から依存関係をインストール
uv sync
```

#### 主要パッケージ

- **FastAPI**: Web フレームワーク
- **Uvicorn**: ASGI サーバー
- **Polars**: 高速データ処理ライブラリ
- **NumPy**: 数値計算ライブラリ
- **SciPy**: 科学計算ライブラリ
- **statsmodels**: 統計モデリング
- **Pydantic**: データバリデーション
- **Babel**: 国際化サポート
- **pytest**: テストフレームワーク

## 4. 開発サーバーの起動確認

開発サーバーの起動方法は [開発・デバッグガイド](../debug/debug.md) を参照してください。

起動後、ブラウザで以下にアクセスして動作確認：

- **API ドキュメント**: http://localhost:8000/docs
- **代替ドキュメント**: http://localhost:8000/redoc

## 5. テストとコード品質

### テストの実行

```powershell
pytest                    # すべてのテスト
pytest -v                 # 詳細表示
pytest --cov=economicon   # カバレッジ付き
```

### コード品質チェック

```powershell
ruff check .              # リント
ruff check --fix .        # 自動修正
ruff format .             # フォーマット
```

詳細なコマンドは [開発・デバッグガイド](../debug/debug.md) を参照してください。

## 6. 開発とデバッグ

開発サーバーの起動方法とデバッグ方法については [開発・デバッグガイド](../debug/debug.md) を参照してください。

## トラブルシューティング

### パッケージインストールエラー

```powershell
# uv を最新版に更新
uv self update

# キャッシュをクリアして再インストール
uv cache clean
uv pip install -e .
```

### ImportError が発生する

プロジェクトルート（`api/`）から起動しているか確認：

```powershell
cd api
uvicorn main:app --reload
```

### ポート 8000 が使用中

```powershell
# 別のポートを使用
uvicorn main:app --reload --port 8001
```

または、他のプロセスを終了：

```powershell
# ポートを使用しているプロセスを確認
netstat -ano | findstr :8000

# プロセスを終了
taskkill /PID <プロセスID> /F
```

### 仮想環境が認識されない（VS Code）

1. `Ctrl+Shift+P` を押す
2. "Python: Select Interpreter" を選択
3. `api/.venv` 内の Python インタープリターを選択

## 次のステップ

- [フロントエンドセットアップ](./frontend.md) - React/Tauri 環境の構築
- [開発・デバッグガイド](../debug/debug.md) - 開発サーバーの起動方法とデバッグ方法

## 参考リンク

- [FastAPI 公式ドキュメント](https://fastapi.tiangolo.com/)
- [uv 公式ドキュメント](https://docs.astral.sh/uv/)
- [Polars ガイド](https://pola-rs.github.io/polars/)
- [pytest ドキュメント](https://docs.pytest.org/)
