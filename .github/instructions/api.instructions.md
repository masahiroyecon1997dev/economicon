---
applyTo: "api/**"
---

# FastAPI バックエンド実装ルール

## 1. 環境とツール

- **Pythonバージョン**: Python 3.14+
- **パッケージ管理**: `uv`
- **リント**: `ruff`
  - **最大行長**: 79文字（docstring/コメントは72文字）
  - **インデント**: 4スペース
- **主要ライブラリ**:
  - **データ処理**: Polars（Pandasは使用しない）
  - **スキーマ定義**: Pydantic
  - **統計分析**: statsmodels, linearmodels, scipy, numpy
  - **テスト**: pytest

## 2. 国際化（i18n）とグローバルコンテキスト

- **翻訳関数**: `economicon.i18n.translation.gettext as _`
- **言語設定**: `ContextVar`ベースのスレッドセーフな設定を使用
- **ルール**: ユーザー向けの文字列は必ず`_()`でラップする
- **注意**: `gettext_lazy`は後方互換性のため存在しますが、`gettext`を使用してください

## 3. サービス（DataOperation）要件

すべてのAPIサービスクラスは`DataOperation`プロトコルに適合する必要があります:

1. `__init__`: `self.param_names`を定義（`camelCase`を`snake_case`にマッピング）、`TablesStore()`を初期化
2. `validate() -> Optional[ValidationError]`: 成功時は`None`を返し、失敗時は`ValidationError`を送出
3. `execute() -> Optional[Dict | bytes]`: `Polars`を使用したコアロジック。期待されるエラーは`ApiError`を送出

**注意**: `DataOperation`はProtocolによる構造的部分型（structural subtyping）を使用しており、継承は不要です。

**データ管理の原則**:

- データの読み書きや保持は必ず`TablesStore`を介して行う
- Polarsを使用し、パフォーマンスと型安全性を重視する

## 4. ルーターとレスポンスパターン

- **エンドポイント**: `@router.post("/kebab-case-path")`
- **エラーマッピング**:
  - `ValidationError` → `status.HTTP_400_BAD_REQUEST`
  - `ApiError` / `Exception` → `status.HTTP_500_INTERNAL_SERVER_ERROR`
- **ヘルパー**: `create_success_response`または`create_error_response`を使用

## 5. 命名規則リファレンス

| カテゴリ       | 規則       | 例                  |
| :------------- | :--------- | :------------------ |
| **ファイル**   | snake_case | `create_table.py`   |
| **クラス**     | PascalCase | `CreateTable`       |
| **JSONキー**   | camelCase  | `tableName`         |
| **Python変数** | snake_case | `table_name`        |
| **URL**        | kebab-case | `/api/create-table` |

## 6. テスト（pytest）

- **ファイル名**: `test_*.py`
- **関数名**: `test_[機能]_[シナリオ]`
- **必須フィクスチャ**: `client`, `tables_store`
- **標準アサーション**:
  - `response.status_code`
  - `response_data['code'] == 'OK'/'NG'`
