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
    assert response_data["result"]["columnName"] == COL_C
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


# ========================================
# 意地悪な入力テスト (N1-N7: 名前バリエーション)
# ========================================


def test_rename_column_japanese_new_column_name(client, tables_store):
    """N1: 日本語の新規列名でも正常にリネームされる"""
    response = client.post(
        "/api/column/rename",
        json={
            "tableName": TABLE_NAME,
            "oldColumnName": COL_A,
            "newColumnName": "売上高",
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == TABLE_NAME
    assert response_data["result"]["columnName"] == "売上高"

    df = tables_store.get_table(TABLE_NAME).table
    assert "売上高" in df.columns
    assert COL_A not in df.columns


def test_rename_column_japanese_old_column_name(client, tables_store):
    """N2: 日本語の既存列名も正常にリネーム対象になる"""
    tables_store.update_table(
        TABLE_NAME,
        pl.DataFrame({"売上①": DATA_A, COL_B: DATA_B}),
    )
    response = client.post(
        "/api/column/rename",
        json={
            "tableName": TABLE_NAME,
            "oldColumnName": "売上①",
            "newColumnName": "Revenue",
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["columnName"] == "Revenue"

    df = tables_store.get_table(TABLE_NAME).table
    assert "Revenue" in df.columns
    assert "売上①" not in df.columns


def test_rename_column_emoji_new_column_name(client, tables_store):
    """N3: 絵文字のみの新規列名でも正常にリネームされる"""
    response = client.post(
        "/api/column/rename",
        json={
            "tableName": TABLE_NAME,
            "oldColumnName": COL_A,
            "newColumnName": "🏷️",
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["columnName"] == "🏷️"

    df = tables_store.get_table(TABLE_NAME).table
    assert "🏷️" in df.columns


def test_rename_column_strip_whitespace_old_column_name(client, tables_store):
    """N4: oldColumnName の前後スペースは除去されて正常に処理される"""
    response = client.post(
        "/api/column/rename",
        json={
            "tableName": TABLE_NAME,
            "oldColumnName": "  A  ",
            "newColumnName": COL_C,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["columnName"] == COL_C

    df = tables_store.get_table(TABLE_NAME).table
    assert COL_C in df.columns
    assert COL_A not in df.columns


def test_rename_column_max_length_new_column_name(client, tables_store):
    """N5: 128文字（最大長境界値）の新規列名は正常にリネームされる"""
    long_name = "x" * 128
    response = client.post(
        "/api/column/rename",
        json={
            "tableName": TABLE_NAME,
            "oldColumnName": COL_A,
            "newColumnName": long_name,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == TABLE_NAME
    assert response_data["result"]["columnName"] == long_name
    df = tables_store.get_table(TABLE_NAME).table
    assert long_name in df.columns


def test_rename_column_too_long_new_column_name(client, tables_store):
    """N6: 129文字（最大長超過）の新規列名は422エラーになる"""
    response = client.post(
        "/api/column/rename",
        json={
            "tableName": TABLE_NAME,
            "oldColumnName": COL_A,
            "newColumnName": "x" * 129,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "newColumnNameは128文字以内で入力してください。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_rename_column_tab_char_new_column_name(client, tables_store):
    """N7: タブ文字を含む新規列名は422エラーになる"""
    response = client.post(
        "/api/column/rename",
        json={
            "tableName": TABLE_NAME,
            "oldColumnName": COL_A,
            "newColumnName": "col	A",
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "newColumnNameに使用できない文字が含まれています。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]
