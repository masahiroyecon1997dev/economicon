import datetime

import polars as pl
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.core.enums import ErrorCode
from economicon.services.data.tables_store import TablesStore
from main import app

# --- 定数 ---
TABLE_NAME = "TestTable"
TABLE_NONEXISTENT = "NoTable"
COL_A = "A"
COL_B = "B"
COL_C = "C"
COL_NONEXISTENT = "Z"
ENDPOINT = "/api/column/cast"


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def tables_store():
    """TablesStoreのフィクスチャ（文字列データを含む）"""
    manager = TablesStore()
    manager.clear_tables()
    df = pl.DataFrame(
        {
            COL_A: ["1,234.5", "  0.5  ", "abc", None],
            COL_B: ["2026/02/26", "2025/01/01", "invalid", None],
            COL_C: [1, 2, 3, 4],
        }
    )
    manager.store_table(TABLE_NAME, df)
    yield manager
    manager.clear_tables()


# ========================================
# 正常系テスト
# ========================================


def test_cast_column_str_to_float_with_comma(client, tables_store):
    """正常系 (Numeric): "1,234.5" をカンマ削除後に float に変換できること"""
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "targetType": "float",
        "newColumnName": "A_float",
        "addPositionColumn": COL_A,
        "cleanupWhitespace": True,
        "removeCommas": True,
        "strict": False,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == TABLE_NAME
    assert response_data["result"]["columnName"] == "A_float"

    df = tables_store.get_table(TABLE_NAME).table
    # "1,234.5" → カンマ削除 → "1234.5" → 1234.5
    assert df["A_float"][0] == pytest.approx(1234.5)
    # "  0.5  " → 空白削除 → "0.5" → 0.5
    assert df["A_float"][1] == pytest.approx(0.5)
    # "abc" → 変換失敗 → null (strict=False)
    assert df["A_float"][2] is None


def test_cast_column_str_to_date(client, tables_store):
    """
    正常系 (Date): "2026/02/26" をフォーマット %Y/%m/%d で
    date 型に変換できること
    """
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_B,
        "targetType": "date",
        "newColumnName": "B_date",
        "addPositionColumn": COL_B,
        "datetimeFormat": "%Y/%m/%d",
        "strict": False,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    assert df["B_date"].dtype == pl.Date
    # "2026/02/26" → date(2026, 2, 26)
    assert df["B_date"][0] == datetime.date(2026, 2, 26)
    assert df["B_date"][1] == datetime.date(2025, 1, 1)
    # "invalid" → null (strict=False)
    assert df["B_date"][2] is None


def test_cast_column_insert_position(client, tables_store):
    """正常系: 新しい列が add_position_column の右隣に配置されること"""
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "targetType": "str",
        "newColumnName": "A_copy",
        "addPositionColumn": COL_C,
        "cleanupWhitespace": False,
        "removeCommas": False,
        "strict": False,
    }
    response = client.post(ENDPOINT, json=payload)

    assert response.status_code == status.HTTP_200_OK
    df = tables_store.get_table(TABLE_NAME).table
    # COL_C の右隣に "A_copy" が挿入される
    expected_order = [COL_A, COL_B, COL_C, "A_copy"]
    assert df.columns == expected_order


def test_cast_column_int_non_strict_null(client, tables_store):
    """
    正常系 (Non-Strict): strict=False のとき不適切な文字列が
    null になり処理が続行されること
    """
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "targetType": "int",
        "newColumnName": "A_int",
        "addPositionColumn": COL_A,
        "cleanupWhitespace": True,
        "removeCommas": True,
        "strict": False,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    # "abc" → null
    assert df["A_int"][2] is None
    # None → null
    assert df["A_int"][3] is None


# ========================================
# 異常系テスト
# ========================================


def test_cast_column_strict_error(client, tables_store):
    """
    異常系 (Strict): strict=True のとき不適切な文字列で
    400 エラーが発生すること
    """
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "targetType": "int",
        "newColumnName": "A_int",
        "addPositionColumn": COL_A,
        "cleanupWhitespace": False,
        "removeCommas": False,
        "strict": True,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.CAST_COLUMN_TYPE_ERROR


def test_cast_column_strict_date_error(client, tables_store):
    """
    異常系 (Strict/Date): strict=True のとき不適切な日付文字列で
    400 エラーが発生すること
    """
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_B,
        "targetType": "date",
        "newColumnName": "B_date",
        "addPositionColumn": COL_B,
        "datetimeFormat": "%Y/%m/%d",
        "strict": True,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.CAST_COLUMN_TYPE_ERROR


def test_cast_column_invalid_table(client, tables_store):
    """異常系: 存在しないテーブルを指定した場合に 400 エラーが発生すること"""
    payload = {
        "tableName": TABLE_NONEXISTENT,
        "sourceColumnName": COL_A,
        "targetType": "float",
        "newColumnName": "A_float",
        "addPositionColumn": COL_A,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND


def test_cast_column_invalid_source_column(client, tables_store):
    """異常系: 存在しない変換元列を指定した場合に 400 エラーが発生すること"""
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_NONEXISTENT,
        "targetType": "float",
        "newColumnName": "Z_float",
        "addPositionColumn": COL_A,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND


def test_cast_column_invalid_position_column(client, tables_store):
    """異常系: 存在しない挿入位置列を指定した場合に 400 エラーが発生すること"""
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "targetType": "float",
        "newColumnName": "A_float",
        "addPositionColumn": COL_NONEXISTENT,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND


def test_cast_column_duplicate_column_name(client, tables_store):
    """
    異常系: 既存列名と重複する新列名を指定した場合に
    400 エラーが発生すること
    """
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "targetType": "float",
        "newColumnName": COL_B,  # 既存列名と重複
        "addPositionColumn": COL_A,
    }
    response = client.post(ENDPOINT, json=payload)
    response_data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_ALREADY_EXISTS


def test_cast_column_invalid_target_type(client, tables_store):
    """異常系: 無効な targetType を指定した場合に 422 エラーが発生すること"""
    payload = {
        "tableName": TABLE_NAME,
        "sourceColumnName": COL_A,
        "targetType": "invalid_type",
        "newColumnName": "A_new",
        "addPositionColumn": COL_A,
    }
    response = client.post(ENDPOINT, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
