# Django から FastAPI への移行ガイド

## 移行の概要

このドキュメントは、`ApiServer/analysisapp`の Django REST Framework から FastAPI への移行方針をまとめたものです。

## 完了した作業

### 1. 環境のセットアップ ✅

- **仮想環境**: `ApiServer/.venv` に作成
- **パッケージ**: fastapi, uvicorn, pytest, httpx, babel, python-multipart, polars, pandas 等

### 2. 基本構造の作成 ✅

- **メインアプリ**: `ApiServer/main.py` - FastAPI アプリケーションのエントリーポイント
- **ルーター**: `analysisapp/api/routers/` - エンドポイントの実装
- **ユーティリティ**: `analysisapp/api/utilities_fastapi/` - レスポンス作成等のヘルパー関数

### 3. 国際化（i18n）対応 ✅

- **翻訳モジュール**: `analysisapp/api/i18n/translation.py`
  - `django.utils.translation.gettext` → 独自の`gettext_lazy`関数
  - 既存の`locale/`ディレクトリ（django.po/mo）を活用
  - 使用例: `from ..i18n import _`

### 4. Django 依存の除去 ✅

- **validator**: `apis/utilities/validator/common_validators.py` - Django 依存を除去
- **python_apis**: `django_compat.py` を作成して Django 翻訳関数を互換実装
- **ステータスコード**: REST Framework のステータスコードを標準の数値に変更

### 5. サンプル実装 ✅

- **エンドポイント**: `analysisapp/api/routers/add_column.py`

  - Django REST Framework の APIView から FastAPI のルーターへ変換
  - Pydantic モデルでリクエストバリデーション
  - 既存の`python_apis`をそのまま使用可能

- **テスト**: `ApiServer/tests/test_add_column.py`
  - `unittest.TestCase` → pytest 形式
  - `APITestCase` → `TestClient`
  - フィクスチャを活用

### 6. 動作確認 ✅

- FastAPI サーバーが正常に起動
- Swagger UI (http://127.0.0.1:8000/docs) で API ドキュメントが確認可能

## 移行手順

### エンドポイントの移行

#### 1. Django REST Framework 版（旧）

```python
from rest_framework import status
from rest_framework.views import APIView
import json
from django.utils.translation import gettext as _

class AddColumn(APIView):
    def post(self, request):
        request_data = json.loads(request.body)
        # ...処理...
        return create_success_response(status.HTTP_200_OK, result)
```

#### 2. FastAPI 版（新）

```python
from fastapi import APIRouter, Request, status as http_status
from pydantic import BaseModel, Field
from ..i18n import _

router = APIRouter()

class AddColumnRequest(BaseModel):
    tableName: str = Field(..., description="テーブル名")
    newColumnName: str = Field(..., description="新しいカラム名")
    addPositionColumn: str = Field(..., description="追加位置の基準となるカラム名")

@router.post("/add-column")
async def add_column_endpoint(request: Request, body: AddColumnRequest):
    # ...処理...
    return create_success_response(http_status.HTTP_200_OK, result)
```

#### 主な変更点

1. **インポート**:

   - `rest_framework` → `fastapi`
   - `django.utils.translation` → `..i18n`

2. **リクエスト処理**:

   - `json.loads(request.body)` → Pydantic モデルで自動パース

3. **レスポンス**:

   - `rest_framework.response.Response` → `fastapi.responses.JSONResponse`
   - ヘルパー関数は`utilities_fastapi`を使用

4. **ステータスコード**:
   - `status.HTTP_200_OK` → `http_status.HTTP_200_OK`（alias が必要）

### テストの移行

#### 1. unittest 版（旧）

```python
from rest_framework.test import APITestCase
from rest_framework import status

class TestApiAddColumn(APITestCase):
    def setUp(self):
        self.tables_manager = TablesManager()
        # セットアップ...

    def test_add_column_success(self):
        response = self.client.post('/api/add-column', ...)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
```

#### 2. pytest 版（新）

```python
import pytest
from fastapi.testclient import TestClient
from fastapi import status

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def tables_manager():
    manager = TablesManager()
    # セットアップ...
    yield manager
    # クリーンアップ...

def test_add_column_success(client, tables_manager):
    response = client.post('/api/add-column', json=...)
    assert response.status_code == status.HTTP_200_OK
```

#### 主な変更点

1. **クラスベース → 関数ベース**: `TestCase`クラスの代わりに pytest の関数を使用
2. **setUp → フィクスチャ**: `@pytest.fixture`でテストデータを準備
3. **アサーション**: `self.assertEqual()` → `assert`
4. **TestClient**: FastAPI の`TestClient`を使用

## 残りの移行作業

### 対象エンドポイント（42 個）

以下のエンドポイントを順次移行する必要があります：

1. `rest_add_dummy_column.py`
2. `rest_add_lag_lead_column.py`
3. `rest_add_simulation_column.py`
4. `rest_calculate_column.py`
5. `rest_clear_tables.py`
   ... （全 42 個）

### 移行の流れ

1. **ルーターファイルの作成**:

   ```bash
   # ファイル名: analysisapp/api/routers/{endpoint_name}.py
   # 例: add_dummy_column.py
   ```

2. **Pydantic モデルの定義**:

   - リクエストボディの構造を定義
   - バリデーションルールを追加

3. **エンドポイント関数の実装**:

   - 既存の`python_apis`を呼び出す
   - エラーハンドリングを実装

4. **main.py への登録**:

   ```python
   from analysisapp.api.routers import new_endpoint
   app.include_router(new_endpoint.router, prefix="/api", tags=["tag"])
   ```

5. **テストの作成**:
   - `tests/test_{endpoint_name}.py`
   - pytest 形式で実装

### 注意点

#### python_apis の活用

- 既存の`analysisapp/api/apis/python_apis/`のコードは**そのまま使用可能**
- ビジネスロジックは変更不要

#### バリデーション

- `common_validators`の`ValidationError`は引き続き使用
- Pydantic の型チェックと組み合わせる

#### 翻訳

- 既存の`locale/ja/LC_MESSAGES/django.po`を活用
- `from ..i18n import _`でインポート

#### ログ

- `create_log`系の関数はそのまま使用可能
- `utilities_fastapi`にコピー済み

## 実行方法

### 開発サーバーの起動

```powershell
cd ApiServer
.\.venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### テストの実行

```powershell
cd ApiServer
.\.venv\Scripts\activate
pytest tests/ -v
```

### 特定のテストの実行

```powershell
pytest tests/test_add_column.py -v
```

## ディレクトリ構造

```
ApiServer/
├── main.py                          # FastAPIアプリケーション
├── .venv/                           # 仮想環境
├── tests/                           # pytestテスト
│   ├── conftest.py
│   └── test_add_column.py
└── analysisapp/
    └── api/
        ├── i18n/                    # 国際化モジュール
        │   ├── __init__.py
        │   └── translation.py
        ├── routers/                 # FastAPIルーター
        │   └── add_column.py
        ├── utilities_fastapi/       # FastAPI用ユーティリティ
        │   ├── __init__.py
        │   ├── create_response.py
        │   └── create_log.py
        ├── apis/
        │   ├── python_apis/         # ビジネスロジック（変更不要）
        │   └── rest_apis/           # 旧Django REST Framework（参照用）
        └── locale/                  # 翻訳ファイル
            └── ja/LC_MESSAGES/
                ├── django.po
                └── django.mo
```

## 次のステップ

1. **動作確認**: サンプル実装（add_column）をテストして動作を確認
2. **順次移行**: 残りの 41 個のエンドポイントを 1 つずつ移行
3. **統合テスト**: 全エンドポイントの移行後、統合テストを実施
4. **Django 依存の削除**: 移行完了後、Django 関連のパッケージを削除

## 参考資料

- [FastAPI 公式ドキュメント](https://fastapi.tiangolo.com/)
- [Pydantic 公式ドキュメント](https://docs.pydantic.dev/)
- [pytest 公式ドキュメント](https://docs.pytest.org/)
