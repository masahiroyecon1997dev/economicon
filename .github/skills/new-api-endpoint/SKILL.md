---
name: new-api-endpoint
description: FastAPI で新しいエンドポイントを Economicon に追加するときのワークフロー。
---

# Skill: new-api-endpoint

新しい FastAPI エンドポイントを Economicon に追加するときのワークフロー。

## 前提確認

- 類似サービス（`api/economicon/services/`）を必ず参照してから実装を始める
- スキーマは `api/economicon/schemas/` の既存定義を最大限再利用する

## Step 1: スキーマ定義

`api/economicon/schemas/<ドメイン>.py` にリクエスト・レスポンス型を追加する。

```python
class XxxRequestBody(BaseRequest):
    """camelCase alias は alias_generator=to_camel で自動生成"""
    table_name: Annotated[str, Field(min_length=1, max_length=MAX_TABLE_NAME_LEN)]
    column_name: str

class XxxResult(BaseModel):
    result_value: float  # レスポンスは snake_case OK（フロントが型参照）
```

**注意**:

- `BaseRequest` を継承（`alias_generator=to_camel` / `strict=True` が有効になる）
- 数値は `ge` / `le` で範囲を必ず制限
- `schemas/__init__.py` に追加して公開する

## Step 2: サービス実装

`api/economicon/services/<ドメイン>/<機能名>.py` を作成する。

```python
class XxxService:
    PARAM_NAMES: ClassVar[dict[str, str]] = {
        "tableName": "table_name",
        "columnName": "column_name",
    }

    def __init__(self, body: XxxRequestBody, tables_store: TablesStore) -> None:
        self.tables_store = tables_store
        self.table_name = body.table_name
        self.column_name = body.column_name

    def validate(self) -> None:
        validate_existence(self.tables_store, self.table_name, "tableName")
        # ... 追加バリデーション

    def execute(self) -> dict:
        df = self.tables_store.get_table(self.table_name).df
        # Polars で処理（Pandas は statsmodels/linearmodels 連携時のみ）
        result_df = df.with_columns(...)
        self.tables_store.store_table(new_name, result_df)  # 元テーブルを上書きしない
        return {"tableName": new_name}
```

**注意**:

- `validate()` でビジネスルール違反は `ValidationError` を送出
- `execute()` でシステムエラーは `ApiError` を送出
- 元テーブルを上書きせず必ず新テーブルを生成する
- ユーザー向けメッセージは `_()` でラップ（i18n）

## Step 3: ルーター登録

`api/economicon/routers/<ドメイン>.py` にエンドポイントを追加する。

```python
@router.post(
    "/kebab-case-path",
    response_model=SuccessResponse[XxxResult],
    responses=COMMON_ERROR_RESPONSES,
)
async def xxx_endpoint(
    request: Request,
    body: XxxRequestBody,
    tables_store: TablesStoreDep,
) -> JSONResponse:
    api = XxxService(body, tables_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK,
        response_object=result,
    )
```

`main.py` に新しいルーターを登録していない場合は追加する。

## Step 4: i18n メッセージ追加

`_()` でラップした文字列は **必ず** `messages.po` に対応エントリを追加してからコンパイルする。

```bash
cd api; .venv\Scripts\pybabel compile -f -d economicon/locales
```

## Step 5: フロントエンド型を同期

```bash
cd app; pnpm gen:all
```

**スキーマを変更したら必ず実行**。`src/api/model/` と `src/api/zod/` が自動更新される。

## Step 6: テスト実装

`api/tests/<ドメイン>/test_<機能名>.py` を作成する。

```python
_BASE_PAYLOAD = {"tableName": "test_table", "columnName": "col"}

class TestXxxSuccess:
    def test_xxx_success(self, client, tables_store):
        """正常系: ..."""
        response = client.post("/api/<path>", json=_BASE_PAYLOAD)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["code"] == "OK"

class TestXxxValidation:
    def test_xxx_table_not_found(self, client, tables_store):
        """異常系: 存在しないテーブル"""
        response = client.post("/api/<path>", json={**_BASE_PAYLOAD, "tableName": "NONE"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["message"] == "tableName 'NONE'は存在しません。"  # 完全一致
```

テストは 4 段階で作成する:

1. 正常系（`HTTP_200_OK`, `code == "OK"`）
2. ビジネスロジック異常系（`HTTP_400_BAD_REQUEST`, `message` 完全一致）
3. Pydantic バリデーション（`HTTP_422_UNPROCESSABLE_CONTENT`, `details` 完全一致）
4. エッジケース（境界値・空配列・最大長超過）

## チェックリスト

- [ ] `schemas/__init__.py` に新スキーマを追加
- [ ] `validate()` に全バリデーションを実装
- [ ] `_()` ラップ済みの文字列を `messages.po` に追加し `pybabel compile` 実行
- [ ] `pnpm gen:all` でフロントエンド型を同期
- [ ] `ruff check .` がクリア
- [ ] テスト 4 段階（正常・ビジネス異常・Pydantic・エッジ）を実装
