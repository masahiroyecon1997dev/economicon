"""
fetch_data_to_arrow APIのテスト
"""

import base64

import polars as pl
import pyarrow as pa
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from analysisapp.services.data.tables_store import TablesStore
from main import app

# test用テーブル名とデータ
table_name = "test_table"
test_data = pl.DataFrame(
    {
        "column1": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "column2": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"],
        "column3": [1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8, 9.9, 10.0],
    }
)


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_store():
    """TablesStoreのフィクスチャ"""
    # テスト用のテーブルをセットアップ
    manager = TablesStore()
    # テーブルをクリア
    manager.clear_tables()
    manager.store_table(table_name, test_data)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


def test_fetch_data_to_arrow_success(client, tables_store):
    """正常系テスト: Arrow形式でデータを取得"""
    start_row = 2
    chunk_size = 3
    response = client.post(
        "/api/table/fetch-data-arrow",
        json={
            "tableName": table_name,
            "startRow": start_row,
            "chunkSize": chunk_size,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == table_name
    # メタ情報の確認
    assert response_data["result"]["totalRows"] == 10
    assert response_data["result"]["startRow"] == start_row
    assert response_data["result"]["endRow"] == start_row + chunk_size - 1

    # Arrowデータのデコードと検証
    arrow_base64 = response_data["result"]["arrowData"]
    arrow_bytes = base64.b64decode(arrow_base64)
    reader = pa.ipc.open_stream(arrow_bytes)
    arrow_table = reader.read_all()

    # 期待されるデータと比較
    expected_data = test_data[1:4]
    expected_arrow = expected_data.to_arrow()

    assert arrow_table.num_rows == expected_arrow.num_rows
    assert arrow_table.num_columns == expected_arrow.num_columns
    assert arrow_table.schema.equals(expected_arrow.schema)


def test_fetch_data_to_arrow_default_chunk_size(client, tables_store):
    """正常系テスト: デフォルトのチャンクサイズ（500行）"""
    start_row = 1
    response = client.post(
        "/api/table/fetch-data-arrow",
        json={"tableName": table_name, "startRow": start_row},
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    # テーブルが10行しかないので、全行取得される
    assert response_data["result"]["endRow"] == 10


def test_fetch_data_to_arrow_fetch_beyond_table(client, tables_store):
    """正常系テスト: テーブルの最後を超えて取得"""
    start_row = 8
    chunk_size = 500
    response = client.post(
        "/api/table/fetch-data-arrow",
        json={
            "tableName": table_name,
            "startRow": start_row,
            "chunkSize": chunk_size,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    # テーブルの最後までのみ取得される
    assert response_data["result"]["startRow"] == 8
    assert response_data["result"]["endRow"] == 10

    # Arrowデータの検証
    arrow_base64 = response_data["result"]["arrowData"]
    arrow_bytes = base64.b64decode(arrow_base64)
    reader = pa.ipc.open_stream(arrow_bytes)
    arrow_table = reader.read_all()
    assert arrow_table.num_rows == 3


def test_fetch_data_to_arrow_table_not_found(client, tables_store):
    """異常系テスト: 存在しないテーブル名"""
    not_existent_table = "non_existent_table"
    start_row = 1
    chunk_size = 500
    response = client.post(
        "/api/table/fetch-data-arrow",
        json={
            "tableName": not_existent_table,
            "startRow": start_row,
            "chunkSize": chunk_size,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    message = "tableName 'non_existent_table'は存在しません。"
    assert message == response_data["message"]


def test_fetch_data_to_arrow_invalid_start_row_range(client, tables_store):
    """異常系テスト: 無効な行範囲 startRow"""
    start_row = 0
    chunk_size = 500
    response = client.post(
        "/api/table/fetch-data-arrow",
        json={
            "tableName": table_name,
            "startRow": start_row,
            "chunkSize": chunk_size,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "startRow は1以上である必要があります。" in response_data["message"]


def test_fetch_data_to_arrow_invalid_chunk_size_zero(client, tables_store):
    """異常系テスト: チャンクサイズが0"""
    start_row = 1
    chunk_size = 0
    response = client.post(
        "/api/table/fetch-data-arrow",
        json={
            "tableName": table_name,
            "startRow": start_row,
            "chunkSize": chunk_size,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert (
        "chunkSize は1以上である必要があります。" in response_data["message"]
    )


def test_fetch_data_to_arrow_invalid_chunk_size_too_large(
    client, tables_store
):
    """異常系テスト: チャンクサイズが上限を超える"""
    start_row = 1
    chunk_size = 10001
    response = client.post(
        "/api/table/fetch-data-arrow",
        json={
            "tableName": table_name,
            "startRow": start_row,
            "chunkSize": chunk_size,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "chunkSize" in response_data["message"]


def test_fetch_data_to_arrow_missing_table_name(client, tables_store):
    """異常系テスト: テーブル名が未指定"""
    response = client.post(
        "/api/table/fetch-data-arrow", json={"startRow": 1, "chunkSize": 500}
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "tableName" in response_data["message"]


def test_fetch_data_to_arrow_missing_start_row(client, tables_store):
    """異常系テスト: 開始行が未指定"""
    response = client.post(
        "/api/table/fetch-data-arrow",
        json={"tableName": table_name, "chunkSize": 500},
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "startRow" in response_data["message"]


def test_fetch_data_to_arrow_empty_table_name(client, tables_store):
    """異常系テスト: 空のテーブル名"""
    response = client.post(
        "/api/table/fetch-data-arrow",
        json={"tableName": "", "startRow": 1, "chunkSize": 500},
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "tableName" in response_data["message"]


def test_fetch_data_to_arrow_start_row_beyond_table(client, tables_store):
    """異常系テスト: 開始行がテーブルの行数を超える"""
    start_row = 11
    chunk_size = 500
    response = client.post(
        "/api/table/fetch-data-arrow",
        json={
            "tableName": table_name,
            "startRow": start_row,
            "chunkSize": chunk_size,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "startRow" in response_data["message"]


def test_fetch_data_to_arrow_single_row(client, tables_store):
    """正常系テスト: 1行のみ取得"""
    start_row = 5
    chunk_size = 1
    response = client.post(
        "/api/table/fetch-data-arrow",
        json={
            "tableName": table_name,
            "startRow": start_row,
            "chunkSize": chunk_size,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["result"]["startRow"] == 5
    assert response_data["result"]["endRow"] == 5

    # Arrowデータの検証
    arrow_base64 = response_data["result"]["arrowData"]
    arrow_bytes = base64.b64decode(arrow_base64)
    reader = pa.ipc.open_stream(arrow_bytes)
    arrow_table = reader.read_all()
    assert arrow_table.num_rows == 1
