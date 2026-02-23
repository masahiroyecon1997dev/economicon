import polars as pl
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.core.enums import ErrorCode
from economicon.services.data.tables_store import TablesStore
from main import app

# --- 定数 ---
TABLE_NAME = "TestTable"
TABLE_NONEXISTENT = "NotExistTable"
COL_A = "A"
COL_B = "B"
COL_C = "C"
COL_NONEXISTENT = "Z"
DATA_A = [1, 2]
DATA_B = [3, 4]


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def tables_store():
    """TablesStoreのフィクスチャ"""
    manager = TablesStore()
    manager.clear_tables()
    df = pl.DataFrame({COL_A: DATA_A, COL_B: DATA_B})
    manager.store_table(TABLE_NAME, df)
    yield manager
    manager.clear_tables()


def test_rename_column_success(client, tables_store):
    """正常系: 列名変更が成功することを検証する"""
    df_before = tables_store.get_table(TABLE_NAME).table
    payload = {
        "tableName": TABLE_NAME,
        "oldColumnName": COL_A,
        "newColumnName": COL_C,
    }
    response = client.post("/api/column/rename", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df_after = tables_store.get_table(TABLE_NAME).table
    assert COL_C in df_after.columns
    assert COL_A not in df_after.columns
    assert df_after[COL_C].to_list() == df_before[COL_A].to_list()


def test_rename_column_not_found(client, tables_store):
    """異常系: 変更前の列名が存在しない場合は400エラーになることを検証する"""
    df_before = tables_store.get_table(TABLE_NAME).table
    payload = {
        "tableName": TABLE_NAME,
        "oldColumnName": COL_NONEXISTENT,
        "newColumnName": COL_C,
    }
    response = client.post("/api/column/rename", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    expected_msg = f"oldColumnName '{COL_NONEXISTENT}'は存在しません。"
    assert response_data["message"] == expected_msg
    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_rename_column_new_name_already_exists(client, tables_store):
    """
    異常系:
        変更後の列名が既存の列名と重複する場合は400エラーになることを検証する
    """
    df_before = tables_store.get_table(TABLE_NAME).table
    payload = {
        "tableName": TABLE_NAME,
        "oldColumnName": COL_A,
        "newColumnName": COL_B,
    }
    response = client.post("/api/column/rename", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_ALREADY_EXISTS
    expected_msg = f"newColumnName '{COL_B}'は既に存在します。"
    assert response_data["message"] == expected_msg
    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_rename_column_table_not_found(client, tables_store):
    """
    異常系:
        存在しないテーブルを指定した場合は400エラーになることを検証する
    """
    payload = {
        "tableName": TABLE_NONEXISTENT,
        "oldColumnName": COL_A,
        "newColumnName": COL_C,
    }
    response = client.post("/api/column/rename", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    expected_msg = f"tableName '{TABLE_NONEXISTENT}'は存在しません。"
    assert response_data["message"] == expected_msg


def test_rename_column_empty_old_column_name(client, tables_store):
    """異常系: oldColumnNameが空文字の場合は422エラーになることを検証する"""
    payload = {
        "tableName": TABLE_NAME,
        "oldColumnName": "",
        "newColumnName": COL_C,
    }
    response = client.post("/api/column/rename", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "oldColumnNameは1文字以上で入力してください。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_rename_column_empty_new_column_name(client, tables_store):
    """異常系: newColumnNameが空文字の場合は422エラーになることを検証する"""
    payload = {
        "tableName": TABLE_NAME,
        "oldColumnName": COL_A,
        "newColumnName": "",
    }
    response = client.post("/api/column/rename", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "newColumnNameは1文字以上で入力してください。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_rename_column_missing_table_name(client, tables_store):
    """異常系: tableNameが欠けている場合は422エラーになることを検証する"""
    payload = {"oldColumnName": COL_A, "newColumnName": COL_C}
    response = client.post("/api/column/rename", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "tableNameは必須項目です。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_rename_column_missing_old_column_name(client, tables_store):
    """異常系: oldColumnNameが欠けている場合は422エラーになることを検証する"""
    payload = {"tableName": TABLE_NAME, "newColumnName": COL_C}
    response = client.post("/api/column/rename", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "oldColumnNameは必須項目です。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_rename_column_missing_new_column_name(client, tables_store):
    """異常系: newColumnNameが欠けている場合は422エラーになることを検証する"""
    payload = {"tableName": TABLE_NAME, "oldColumnName": COL_A}
    response = client.post("/api/column/rename", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "newColumnNameは必須項目です。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_rename_column_process_error(client, tables_store):
    """異常系: update_tableが例外を送出するとき500エラーになることを検証する"""
    original_update_table = tables_store.update_table
    try:

        def raise_error(*args, **kwargs):
            raise RuntimeError("forced error")

        tables_store.update_table = raise_error
        payload = {
            "tableName": TABLE_NAME,
            "oldColumnName": COL_A,
            "newColumnName": COL_C,
        }
        response = client.post("/api/column/rename", json=payload)
        response_data = response.json()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response_data["code"] == ErrorCode.RENAME_COLUMN_PROCESS_ERROR
    finally:
        tables_store.update_table = original_update_table
