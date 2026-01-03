---
applyTo: "ApiServer/analysisapp/**"
---

# FastAPI API 開発規約

## Python 環境管理

### パッケージマネージャー

- このプロジェクトでは **uv** をパッケージマネージャーとして使用
- 依存関係は windows なら `python-requirements/windows-requirements.txt`、ubuntu なら `python-requirements/ubuntu-requirements.txt`、 で管理

### 仮想環境

- `.venv` ディレクトリをプロジェクトルートに作成
- 新しいパッケージを追加する場合は `windows-requirements.txt` を更新

```powershell
cd ApiServer
# 依存関係のインストール
uv add -r python-requirements/windows-requirements.txt

# 新しいパッケージの追加
uv add <package-name>
# requirements.txtに追記すること
```

### コード品質管理

- **Flake8** をコード規約チェックツールとして使用
- PEP 8 スタイルガイドに準拠したコードを記述すること
- コミット前に Flake8 でチェックを実施

```powershell
# Flake8によるコードチェック
flake8 api/

# 特定のファイルをチェック
flake8 api/apis/python_apis/your_file.py
```

#### Flake8 規約の主なポイント

- 1 行の最大文字数: 79 文字（docstring やコメントは 72 文字）
- インデント: スペース 4 つ
- 空行: 関数間は 2 行、クラス間は 2 行
- インポート: 標準ライブラリ、サードパーティ、ローカルの順に配置
- 命名規則: 関数・変数はスネークケース、クラスはパスカルケース

## 全般的なルール

### インポート規約

- FastAPI 関連のインポートは上部にまとめる（fastapi, pydantic など）
- サードパーティライブラリ（polars など）のインポート
- 相対インポートは`..`を使用して親ディレクトリから参照
- 型ヒント用のインポート（typing）を適切に使用

### 国際化対応

- 全てのユーザー向けメッセージは`analysisapp.i18n.translation.gettext_lazy as _`を使用
- エラーメッセージは必ず翻訳可能な形式で記述
- ContextVar ベースの言語設定を使用（スレッドセーフ）

## Services API（services）の規約

### クラス設計

- 全ての API クラスは`AbstractApi`を継承すること
- クラス名は機能名を PascalCase で表現（例：`CreateTable`、`DeleteColumn`）
- docstring でクラスの目的と動作を日本語で説明

### 必須メソッド実装

1. `__init__`メソッド

   - 必要なパラメータを受け取り、インスタンス変数に格納
   - `TablesManager()`のインスタンスを作成
   - `param_names`辞書でパラメータ名のマッピングを定義

2. `validate`メソッド

   - 入力値の検証を実行
   - `ValidationError`をキャッチして返す
   - 検証が成功した場合は`None`を返す

3. `execute`メソッド
   - 実際のビジネスロジックを実行
   - `ApiError`で予期される例外をハンドリング
   - 結果を辞書形式で返す

### エラーハンドリング

- バリデーションエラーは`ValidationError`を使用
- API 実行時エラーは`ApiError`を使用
- 予期しないエラーは`Exception`をキャッチし、適切なメッセージと共に`ApiError`でラップ

### 関数インターフェース

- クラスと同名のスネークケース関数を提供（例：`create_table`）
- 関数内で API クラスのインスタンスを作成し、`validate()`と`execute()`を順次実行
- バリデーションエラーがある場合は例外として再発生

## FastAPI Routers（routers）の規約

### ルーター設計

- FastAPI の`APIRouter`を使用してエンドポイントを定義
- 各ルーターファイルは機能ごとに分割（例：`add_column.py`、`create_table.py`）
- docstring で API の目的を簡潔に説明

### エンドポイント実装

- 主に`@router.post`デコレーターを使用
- リクエスト処理の標準的な流れ：
  1. Pydantic モデルで自動的にリクエストデータを検証
  2. 対応する Services 関数を呼び出し
  3. 成功時は`create_success_response`、エラー時は`create_error_response`を返す
  4. async/await を適切に使用（I/O 処理がある場合）

### エラーハンドリング階層

1. `ValidationError` → `status.HTTP_400_BAD_REQUEST`
2. `ApiError` → `status.HTTP_500_INTERNAL_SERVER_ERROR`
3. `Exception` → `status.HTTP_500_INTERNAL_SERVER_ERROR`（予期しないエラー用メッセージ付き）

### レスポンス形式

- 成功レスポンス：`create_success_response(status.HTTP_200_OK, result)`
- エラーレスポンス：`create_error_response(ステータスコード, メッセージ, 例外オブジェクト)`
- FastAPI の`JSONResponse`を使用

## テスト（tests）の規約

### テスト関数設計

- pytest 形式でテスト関数を記述
- 関数名は`test_ + 機能名 + _ + シナリオ`の形式（例：`test_create_table_success`）

### フィクスチャ

- `@pytest.fixture`を使用してテスト用データを準備
- `client`フィクスチャで FastAPI の`TestClient`を提供
- `tables_manager`フィクスチャで`TablesManager()`インスタンスを提供

### テスト構造

1. **正常系テスト**

   - 有効なペイロードを作成
   - `client.post()`で API エンドポイントにリクエスト
   - レスポンスステータスとデータの検証
   - 実際のデータ変更の確認

2. **異常系テスト**
   - 各種無効なパラメータでのテスト
   - 期待されるエラーコードとメッセージの検証
   - バリデーションエラーの適切なハンドリング確認

### アサーション規約

- `assert response.status_code == 期待するステータス`
- `assert response_data['code'] == 'OK'/'NG'`
- `assert 期待するメッセージ in response_data['message']`
- 実際のデータ変更確認（`assert ... in ...`、shape 確認など）

## 命名規約

### ファイル命名

- Services API：機能名をスネークケース（例：`create_table.py`）
- Routers：機能名をスネークケース（例：`create_table.py`）
- Schemas：機能分野をスネークケース（例：`column.py`、`table.py`、`common.py`）
- テスト：`test_` + 機能名をスネークケース（例：`test_create_table.py`）

### 変数・パラメータ命名

- Python コードではスネークケース（例：`table_name`、`column_names`）
- JSON パラメータは camelCase（例：`tableName`、`columnNames`）
- パラメータマッピング用の`param_names`辞書を使用

### URL エンドポイント

- ケバブケース形式（例：`/api/create-table`、`/api/delete-column`）
- main.py でルーターを登録（`app.include_router(router, prefix="/api")`）
- ルーター内で`@router.post("/endpoint-name")`のようにパスを定義

## データ処理

### データフレーム操作

- Polars ライブラリを使用
- `TablesManager`を通じてテーブル操作を実行
- データの型変換や検証を適切に実装

### バリデーション

- 専用の validator モジュールを使用
- 共通的な検証ロジックは再利用可能な形で実装
- エラーメッセージは国際化対応
