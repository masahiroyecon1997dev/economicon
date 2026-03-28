---
applyTo: "api/**"
---

# FastAPI バックエンド実装ルール

## 環境・スタック

- Python 3.14+ / パッケージ管理: `uv` / リント: `ruff`（行長79, docstring72）
- **データ処理**: Polars優先。Pandasはstatsmodels/linearmodels連携時のみ限定使用
- **スキーマ**: Pydantic / **統計**: statsmodels, linearmodels, scipy, numpy / **テスト**: pytest

## i18n

- `from economicon.i18n.translation import gettext as _`
- ユーザー向け文字列は必ず`_()`でラップ（ContextVarベース・スレッドセーフ）

## DataOperation プロトコル

全サービスは以下を実装（継承不要・構造的部分型）:

1. `__init__`: `self.param_names`（camelCase→snake_caseマッピング）、`TablesStore()`初期化
2. `validate() -> Optional[ValidationError]`: 成功→`None`、失敗→`ValidationError`送出
3. `execute() -> Optional[Dict | bytes]`: Polarsロジック、エラーは`ApiError`送出

データ読み書きは`TablesStore`経由のみ。

## ルーター・レスポンス

- エンドポイント: `@router.post("/kebab-case-path")`
- `ValidationError`→400 / `ApiError`・`Exception`→500
- ヘルパー: `create_success_response` / `create_error_response`

## 命名規則

- ファイル: snake_case / クラス: PascalCase / JSONキー: camelCase / URL: kebab-case

## テスト（pytest）

- 命名: `test_[機能]_[シナリオ]` / フィクスチャ: `client`, `tables_store`
- アサーション: `response.status_code` / `response_data['code'] == 'OK'/'NG'`
