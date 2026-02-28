"""
fetch_data_to_arrow APIのテスト
"""

import base64
import io

import polars as pl
import pyarrow as pa
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.core.enums import ErrorCode
from economicon.services.data.tables_store import TablesStore
from main import app

# ─────────────────────────────────────────────────────────────
# 定数
# ─────────────────────────────────────────────────────────────
_TABLE_NAME = "test_table"
_DEFAULT_CHUNK_SIZE = 500
_MAX_CHUNK_SIZE = 10000

_SOURCE_DF = pl.DataFrame(
    {
        "column1": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "column2": [
            "a",
            "b",
            "c",
            "d",
            "e",
            "f",
            "g",
            "h",
            "i",
            "j",
        ],
        "column3": [
            1.1,
            2.2,
            3.3,
            4.4,
            5.5,
            6.6,
            7.7,
            8.8,
            9.9,
            10.0,
        ],
    }
)

_BASE_PAYLOAD: dict = {
    "tableName": _TABLE_NAME,
    "startRow": 0,
    "chunkSize": _DEFAULT_CHUNK_SIZE,
}


# ─────────────────────────────────────────────────────────────
# フィクスチャ
# ─────────────────────────────────────────────────────────────
@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_store():
    """TablesStoreのフィクスチャ"""
    manager = TablesStore()
    manager.clear_tables()
    manager.store_table(_TABLE_NAME, _SOURCE_DF)
    yield manager
    manager.clear_tables()


# ─────────────────────────────────────────────────────────────
# ヘルパー
# ─────────────────────────────────────────────────────────────
def _decode_arrow_table(response) -> pa.Table:
    """JSONレスポンスから base64 エンコードされた Arrow データを復元する"""
    data = response.json()
    assert data["code"] == "OK"
    arrow_bytes = base64.b64decode(data["result"]["arrowData"])
    return pa.ipc.open_file(io.BytesIO(arrow_bytes)).read_all()


# ─────────────────────────────────────────────────────────────
# 正常系
# ─────────────────────────────────────────────────────────────
def test_fetch_data_to_arrow_success(client, tables_store):
    """正常系テスト: Arrow形式でデータを取得"""
    _start_row = 1
    _chunk_size = 3
    payload = {
        **_BASE_PAYLOAD,
        "startRow": _start_row,
        "chunkSize": _chunk_size,
    }
    response = client.post("/api/table/fetch-data-to-arrow", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert "application/json" in response.headers["content-type"]

    result = response.json()["result"]
    assert result["tableName"] == _TABLE_NAME
    assert result["startRow"] == _start_row
    assert result["endRow"] == _start_row + _chunk_size
    assert result["totalRows"] == len(_SOURCE_DF)

    arrow_table = _decode_arrow_table(response)
    expected_arrow = _SOURCE_DF[1:4].to_arrow()
    assert arrow_table.num_rows == expected_arrow.num_rows
    assert arrow_table.num_columns == expected_arrow.num_columns
    assert arrow_table.schema.equals(expected_arrow.schema)


def test_fetch_data_to_arrow_default_chunk_size(client, tables_store):
    """正常系テスト: chunkSize省略時はデフォルト（500行）が適用される"""
    response = client.post(
        "/api/table/fetch-data-to-arrow",
        json={"tableName": _TABLE_NAME, "startRow": 0},
    )
    assert response.status_code == status.HTTP_200_OK
    expected_row_count = (
        10  # テーブルの行数は10行なので、500指定しても10行のみ取得される
    )
    assert _decode_arrow_table(response).num_rows == expected_row_count


def test_fetch_data_to_arrow_fetch_beyond_table(client, tables_store):
    """正常系テスト: chunkSizeがテーブル残行数を超える場合は残行のみ取得"""
    payload = {**_BASE_PAYLOAD, "startRow": 7, "chunkSize": _MAX_CHUNK_SIZE}
    response = client.post("/api/table/fetch-data-to-arrow", json=payload)
    assert response.status_code == status.HTTP_200_OK
    expected_row_count = 3  # startRow=7で行数10のテーブルなので、残りは3行
    assert _decode_arrow_table(response).num_rows == expected_row_count


def test_fetch_data_to_arrow_single_row(client, tables_store):
    """正常系テスト: 1行のみ取得"""
    payload = {**_BASE_PAYLOAD, "startRow": 5, "chunkSize": 1}
    response = client.post("/api/table/fetch-data-to-arrow", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert _decode_arrow_table(response).num_rows == 1


# ─────────────────────────────────────────────────────────────
# 異常系 400
# ─────────────────────────────────────────────────────────────
def test_fetch_data_to_arrow_table_not_found(client, tables_store):
    """異常系テスト: 存在しないテーブル名を指定すると 400 DATA_NOT_FOUND"""
    payload = {**_BASE_PAYLOAD, "tableName": "non_existent_table"}
    response = client.post("/api/table/fetch-data-to-arrow", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert (
        response_data["message"]
        == "tableName 'non_existent_table'は存在しません。"
    )
    assert "details" not in response_data


def test_fetch_data_to_arrow_start_row_beyond_table(client, tables_store):
    """異常系テスト: startRowがテーブルの行数を超えると 400 ROW_OUT_OF_RANGE"""
    # 10行テーブルの最終インデックスは9。11を指定すると超過
    payload = {**_BASE_PAYLOAD, "startRow": 11}
    response = client.post("/api/table/fetch-data-to-arrow", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.ROW_OUT_OF_RANGE
    assert "startRow" in response_data["message"]
    assert "details" not in response_data


# ─────────────────────────────────────────────────────────────
# 異常系 422：Pydanticバリデーションエラー
# ─────────────────────────────────────────────────────────────
def test_fetch_data_to_arrow_pydantic_empty_table_name(client, tables_store):
    """tableNameが空文字列の場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "tableName": ""}
    response = client.post("/api/table/fetch-data-to-arrow", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"] == "tableNameは1文字以上で入力してください。"
    )
    assert response_data["details"] == [
        "tableNameは1文字以上で入力してください。"
    ]


def test_fetch_data_to_arrow_pydantic_missing_table_name(client, tables_store):
    """tableNameが欠損の場合は 422 VALIDATION_ERROR"""
    payload = {"startRow": 0, "chunkSize": _DEFAULT_CHUNK_SIZE}
    response = client.post("/api/table/fetch-data-to-arrow", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "tableNameは必須です。"
    assert response_data["details"] == ["tableNameは必須です。"]


def test_fetch_data_to_arrow_pydantic_missing_start_row(client, tables_store):
    """startRowが欠損の場合は 422 VALIDATION_ERROR"""
    payload = {"tableName": _TABLE_NAME, "chunkSize": _DEFAULT_CHUNK_SIZE}
    response = client.post("/api/table/fetch-data-to-arrow", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "startRowは必須です。"
    assert response_data["details"] == ["startRowは必須です。"]


def test_fetch_data_to_arrow_pydantic_start_row_negative(client, tables_store):
    """startRowが負の場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "startRow": -1}
    response = client.post("/api/table/fetch-data-to-arrow", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "startRowは0以上で入力してください。"
    assert response_data["details"] == ["startRowは0以上で入力してください。"]


def test_fetch_data_to_arrow_pydantic_chunk_size_zero(client, tables_store):
    """chunkSizeが0の場合は 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "chunkSize": 0}
    response = client.post("/api/table/fetch-data-to-arrow", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == "chunkSizeは1以上で入力してください。"
    assert response_data["details"] == ["chunkSizeは1以上で入力してください。"]


def test_fetch_data_to_arrow_pydantic_chunk_size_too_large(
    client, tables_store
):
    """chunkSizeが上限（10000）を超えると 422 VALIDATION_ERROR"""
    payload = {**_BASE_PAYLOAD, "chunkSize": _MAX_CHUNK_SIZE + 1}
    response = client.post("/api/table/fetch-data-to-arrow", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"]
        == f"chunkSizeは{_MAX_CHUNK_SIZE}以下で入力してください。"
    )
    assert response_data["details"] == [
        f"chunkSizeは{_MAX_CHUNK_SIZE}以下で入力してください。"
    ]


# ─────────────────────────────────────────────────────────────
# 意地悪テスト（N1-N7）
# ─────────────────────────────────────────────────────────────
def test_n1_table_name_japanese(client, tables_store):
    """N1: 日本語テーブル名でも正常取得できる"""
    tables_store.store_table("日本語テーブル", _SOURCE_DF)
    payload = {**_BASE_PAYLOAD, "tableName": "日本語テーブル"}
    response = client.post("/api/table/fetch-data-to-arrow", json=payload)
    assert response.status_code == status.HTTP_200_OK


def test_n2_table_name_surrounding_spaces(client, tables_store):
    """N2: tableNameの前後スペースはトリムされ正常取得できる"""
    payload = {**_BASE_PAYLOAD, "tableName": f"  {_TABLE_NAME}  "}
    response = client.post("/api/table/fetch-data-to-arrow", json=payload)
    assert response.status_code == status.HTTP_200_OK


def test_n3_table_name_only_spaces(client, tables_store):
    """N3: tableNameがスペースのみはトリム後に空になり 422"""
    payload = {**_BASE_PAYLOAD, "tableName": "   "}
    response = client.post("/api/table/fetch-data-to-arrow", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert (
        response_data["message"] == "tableNameは1文字以上で入力してください。"
    )


def test_n4_chunk_size_min_boundary(client, tables_store):
    """N4: chunkSize=1（最小値）でも正常取得できる"""
    payload = {**_BASE_PAYLOAD, "startRow": 0, "chunkSize": 1}
    response = client.post("/api/table/fetch-data-to-arrow", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert _decode_arrow_table(response).num_rows == 1


def test_n5_chunk_size_max_boundary(client, tables_store):
    """N5: chunkSize=10000（最大値）でも正常取得できる"""
    payload = {**_BASE_PAYLOAD, "startRow": 0, "chunkSize": _MAX_CHUNK_SIZE}
    response = client.post("/api/table/fetch-data-to-arrow", json=payload)
    assert response.status_code == status.HTTP_200_OK
    expected_row_count = (
        10  # テーブルの行数は10行なので、10000指定しても10行のみ取得される
    )
    assert _decode_arrow_table(response).num_rows == expected_row_count
