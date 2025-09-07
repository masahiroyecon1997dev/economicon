---
applyTo: "AnalysisApp/AnalysisApp/ApiServer/analysisapp/api/**"
---

# Django API 開発規約

## 全般的なルール

### インポート規約
- Django関連のインポートは上部にまとめる
- サードパーティライブラリ（polars、rest_frameworkなど）のインポート
- 相対インポートは`..`を使用して親ディレクトリから参照
- 型ヒント用のインポート（typing）を適切に使用

### 国際化対応
- 全てのユーザー向けメッセージは`django.utils.translation.gettext as _`を使用
- エラーメッセージは必ず翻訳可能な形式で記述

## Python API（python_apis）の規約

### クラス設計
- 全てのAPIクラスは`AbstractApi`を継承すること
- クラス名は機能名をPascalCaseで表現（例：`CreateTable`、`DeleteColumn`）
- docstringでクラスの目的と動作を日本語で説明

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
- API実行時エラーは`ApiError`を使用
- 予期しないエラーは`Exception`をキャッチし、適切なメッセージと共に`ApiError`でラップ

### 関数インターフェース
- クラスと同名のスネークケース関数を提供（例：`create_table`）
- 関数内でAPIクラスのインスタンスを作成し、`validate()`と`execute()`を順次実行
- バリデーションエラーがある場合は例外として再発生

## REST API（rest_apis）の規約

### クラス設計
- 全てのRESTクラスは`APIView`を継承
- クラス名は機能名に応じて命名（例：`CreateTable`、`RestDeleteColumn`）
- docstringでAPIの目的を簡潔に説明

### HTTPメソッド実装
- 主に`post`メソッドを実装
- リクエスト処理の標準的な流れ：
  1. `create_log_api_request(request)`でリクエストログ記録
  2. `json.loads(request.body)`でJSONデータ取得
  3. 対応するPython API関数を呼び出し
  4. 成功時は`create_success_response`、エラー時は`create_error_response`を返す

### エラーハンドリング階層
1. `ValidationError` → `HTTP_400_BAD_REQUEST`
2. `ApiError` → `HTTP_500_INTERNAL_SERVER_ERROR`
3. `Exception` → `HTTP_500_INTERNAL_SERVER_ERROR`（予期しないエラー用メッセージ付き）

### レスポンス形式
- 成功レスポンス：`create_success_response(status.HTTP_200_OK, result)`
- エラーレスポンス：`create_error_response(ステータスコード, メッセージ, 例外オブジェクト)`

## テスト（tests）の規約

### テストクラス設計
- `APITestCase`を継承
- クラス名は`TestApi + 機能名`の形式（例：`TestApiCreateTable`）

### setUp メソッド
- `TablesManager()`のインスタンスを作成し、テスト用データの準備

### テストメソッド命名
- `test_` + `機能名` + `_` + `テストシナリオ`
- 例：`test_create_table_success`、`test_create_table_invalid_table_name`

### テスト構造
1. **正常系テスト**
   - 有効なペイロードを作成
   - APIエンドポイントに対象APIのメソッドでリクエスト
   - レスポンスステータスとデータの検証
   - 実際のデータ変更の確認

2. **異常系テスト**
   - 各種無効なパラメータでのテスト
   - 期待されるエラーコードとメッセージの検証
   - バリデーションエラーの適切なハンドリング確認

### アサーション規約
- `self.assertEqual(response.status_code, 期待するステータス)`
- `self.assertEqual(response_data['code'], 'OK'/'NG')`
- `self.assertIn(response_data['message'], 期待するメッセージ)`
- 実際のデータ変更確認（`self.assertIn`、shape確認など）

## 命名規約

### ファイル命名
- Python API：機能名をスネークケース（例：`create_table.py`）
- REST API：`rest_` + 機能名をスネークケース（例：`rest_create_table.py`）
- テスト：`test_` + 機能名をスネークケース（例：`test_create_table.py`）

### 変数・パラメータ命名
- Pythonコードではスネークケース（例：`table_name`、`column_names`）
- JSONパラメータはcamelCase（例：`tableName`、`columnNames`）
- パラメータマッピング用の`param_names`辞書を使用

### URL エンドポイント
- ケバブケース形式（例：`/api/create-table`、`/api/delete-column`）

## データ処理

### データフレーム操作
- Polarsライブラリを使用
- `TablesManager`を通じてテーブル操作を実行
- データの型変換や検証を適切に実装

### バリデーション
- 専用のvalidatorモジュールを使用
- 共通的な検証ロジックは再利用可能な形で実装
- エラーメッセージは国際化対応

