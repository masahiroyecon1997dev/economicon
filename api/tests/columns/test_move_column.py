import polars as pl
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.core.enums import ErrorCode
from economicon.services.data.tables_store import TablesStore
from main import app

# ========================================
# 定数
# ========================================

TABLE_NAME = "TestTable"
TABLE_NONEXISTENT = "NotExistTable"
COL_A = "A"
COL_B = "B"
COL_C = "C"
COL_D = "D"
COL_NONEXISTENT = "Z"

DATA = {
    COL_A: [1, 2, 3],
    COL_B: [4, 5, 6],
    COL_C: [7, 8, 9],
    COL_D: [10, 11, 12],
}


# ========================================
# フィクスチャ
# ========================================


@pytest.fixture
def client():
    """TestClient のフィクスチャ"""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def tables_store():
    """TablesStore のフィクスチャ"""
    manager = TablesStore()
    manager.clear_tables()
    df = pl.DataFrame(DATA)
    manager.store_table(TABLE_NAME, df)
    yield manager
    manager.clear_tables()


# ========================================
# 正常系テスト
# ========================================


def test_move_column_success_before_anchor(client, tables_store):
    """正常系: anchor の直前に列が挿入される（A, B, C, D → A, C, B, D）"""
    payload = {
        "tableName": TABLE_NAME,
        "columnName": COL_C,
        "anchorColumnName": COL_B,
    }
    response = client.post("/api/column/move", json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == TABLE_NAME
    assert response_data["result"]["columnNames"] == [
        COL_A,
        COL_C,
        COL_B,
        COL_D,
    ]

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.columns == [COL_A, COL_C, COL_B, COL_D]


def test_move_column_success_append_to_end(client, tables_store):
    """
    正常系: anchorColumnName が null のとき末尾に移動される
    （A, B, C, D → B, C, D, A）
    """
    payload = {
        "tableName": TABLE_NAME,
        "columnName": COL_A,
        "anchorColumnName": None,
    }
    response = client.post("/api/column/move", json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["columnNames"] == [
        COL_B,
        COL_C,
        COL_D,
        COL_A,
    ]

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.columns == [COL_B, COL_C, COL_D, COL_A]


def test_move_column_success_move_to_head(client, tables_store):
    """正常系: 先頭列の直前に挿入 → 先頭への移動（A, B, C, D → D, A, B, C）"""
    payload = {
        "tableName": TABLE_NAME,
        "columnName": COL_D,
        "anchorColumnName": COL_A,
    }
    response = client.post("/api/column/move", json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["result"]["columnNames"] == [
        COL_D,
        COL_A,
        COL_B,
        COL_C,
    ]


# ========================================
# 異常系テスト
# ========================================


def test_move_column_table_not_found(client, tables_store):
    """異常系: 存在しないテーブルを指定した場合は 400 エラー"""
    payload = {
        "tableName": TABLE_NONEXISTENT,
        "columnName": COL_A,
        "anchorColumnName": COL_B,
    }
    response = client.post("/api/column/move", json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    expected_msg = f"tableName '{TABLE_NONEXISTENT}'は存在しません。"
    assert response_data["message"] == expected_msg


def test_move_column_column_not_found(client, tables_store):
    """異常系: 移動対象列が存在しない場合は 400 エラー"""
    payload = {
        "tableName": TABLE_NAME,
        "columnName": COL_NONEXISTENT,
        "anchorColumnName": COL_B,
    }
    response = client.post("/api/column/move", json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    expected_msg = f"columnName '{COL_NONEXISTENT}'は存在しません。"
    assert response_data["message"] == expected_msg


def test_move_column_anchor_not_found(client, tables_store):
    """異常系: anchor 列が存在しない場合は 400 エラー"""
    payload = {
        "tableName": TABLE_NAME,
        "columnName": COL_A,
        "anchorColumnName": COL_NONEXISTENT,
    }
    response = client.post("/api/column/move", json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    expected_msg = f"anchorColumnName '{COL_NONEXISTENT}'は存在しません。"
    assert response_data["message"] == expected_msg


def test_move_column_same_column_as_anchor(client, tables_store):
    """異常系: columnName と anchorColumnName が同一の場合は 422 エラー"""
    payload = {
        "tableName": TABLE_NAME,
        "columnName": COL_A,
        "anchorColumnName": COL_A,
    }
    response = client.post("/api/column/move", json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
