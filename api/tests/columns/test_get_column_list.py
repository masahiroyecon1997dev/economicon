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
TABLE_NONEXISTENT = "non_existent_table"

COL_INT = "col1"
COL_STR = "col2"
COL_FLOAT = "col3"

# テーブルの初期値
DATA_INT = [1, 2, 3]
DATA_STR = ["a", "b", "c"]
DATA_FLOAT = [1.1, 2.2, 3.3]


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
    df = pl.DataFrame(
        {COL_INT: DATA_INT, COL_STR: DATA_STR, COL_FLOAT: DATA_FLOAT}
    )
    manager.store_table(TABLE_NAME, df)
    yield manager
    manager.clear_tables()


# ========================================
# 正常系テスト
# ========================================


def test_get_column_list_success(client, tables_store):
    """テーブルが存在する場合、全列の情報リストを返す"""
    response = client.post(
        "/api/column/get-list",
        json={"tableName": TABLE_NAME},
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    result = response_data["result"]
    assert result["tableName"] == TABLE_NAME

    # スキーマ順にすべての列情報が返る
    df = tables_store.get_table(TABLE_NAME).table
    expected_columns = [
        {"name": name, "type": str(dtype)}
        for name, dtype in df.schema.items()
    ]
    assert result["columnInfoList"] == expected_columns


def test_get_column_list_number_only(client, tables_store):
    """isNumberOnly=True の場合、数値型の列のみ返す"""
    response = client.post(
        "/api/column/get-list",
        json={"tableName": TABLE_NAME, "isNumberOnly": True},
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    result = response_data["result"]
    assert result["tableName"] == TABLE_NAME

    df = tables_store.get_table(TABLE_NAME).table
    expected_columns = [
        {"name": name, "type": str(dtype)}
        for name, dtype in df.schema.items()
        if dtype.is_numeric()
    ]
    assert result["columnInfoList"] == expected_columns
    # 文字列列は含まれない
    names = [c["name"] for c in result["columnInfoList"]]
    assert COL_STR not in names
    assert COL_INT in names
    assert COL_FLOAT in names


def test_get_column_list_is_number_only_false_explicit(client, tables_store):
    """isNumberOnly=False を明示した場合、全列を返す（デフォルトと同じ）"""
    response = client.post(
        "/api/column/get-list",
        json={"tableName": TABLE_NAME, "isNumberOnly": False},
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK

    result = response_data["result"]
    df = tables_store.get_table(TABLE_NAME).table
    assert len(result["columnInfoList"]) == len(df.columns)


# ========================================
# 異常系テスト（Pydantic バリデーション: 422）
# ========================================


def test_get_column_list_missing_table_name(client, tables_store):
    """tableName が未指定の場合は 422 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/get-list",
        json={},
    )

    expected_msg = "tableNameは必須項目です。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


# ========================================
# 異常系テスト（内部バリデーション: 400）
# ========================================


def test_get_column_list_table_not_found(client, tables_store):
    """存在しないテーブル名を指定した場合は 400 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/get-list",
        json={"tableName": TABLE_NONEXISTENT},
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert (
        response_data["message"]
        == f"tableName '{TABLE_NONEXISTENT}'は存在しません。"
    )

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


# ========================================
# 異常系テスト（予期せぬ例外: 500）
# ========================================


def test_get_column_list_unexpected_exception(client, tables_store):
    """execute 内で予期せぬ例外が発生した場合は 500 を返す"""
    original_get_schema = tables_store.get_schema

    def raise_exception(table_name: str):
        raise RuntimeError("unexpected DB error")

    tables_store.get_schema = raise_exception

    try:
        response = client.post(
            "/api/column/get-list",
            json={"tableName": TABLE_NAME},
        )

        response_data = response.json()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response_data["code"] == ErrorCode.GET_COLUMN_LIST_PROCESS_ERROR
    finally:
        tables_store.get_schema = original_get_schema
