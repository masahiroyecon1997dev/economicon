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
COL_A = "A"
COL_B = "B"
COL_C = "C"
COL_NONEXISTENT = "Z"
TABLE_NONEXISTENT = "NoTable"

COL_A_COPY = "A_Copy"
COL_B_DUPLICATE = "B_Duplicate"
COL_C_CLONE = "C_Clone"

# テーブルの初期値
DATA_A = [1, 2, 3]
DATA_B = [4, 5, 6]
DATA_C = ["x", "y", "z"]


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
    df = pl.DataFrame({COL_A: DATA_A, COL_B: DATA_B, COL_C: DATA_C})
    manager.store_table(TABLE_NAME, df)
    yield manager
    manager.clear_tables()


# ========================================
# 正常系テスト
# ========================================


def test_duplicate_column_success(client, tables_store):
    """先頭列を複製すると元列の右隣に挿入される"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/duplicate",
        json={
            "tableName": TABLE_NAME,
            "sourceColumnName": COL_A,
            "newColumnName": COL_A_COPY,
            "addPositionColumn": COL_A,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == TABLE_NAME
    assert response_data["result"]["columnName"] == COL_A_COPY

    df_after = tables_store.get_table(TABLE_NAME).table
    # COL_A の右隣に挿入される
    assert df_after.columns == [COL_A, COL_A_COPY, COL_B, COL_C]
    # 複製列の値が元と一致する
    assert df_after[COL_A_COPY].to_list() == df_before[COL_A].to_list()
    # 既存列のデータは変わらない
    assert df_after[COL_A].to_list() == df_before[COL_A].to_list()
    assert df_after[COL_B].to_list() == df_before[COL_B].to_list()


def test_duplicate_column_success_middle_column(client, tables_store):
    """中間列を複製すると元列の右隣に挿入される"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/duplicate",
        json={
            "tableName": TABLE_NAME,
            "sourceColumnName": COL_B,
            "newColumnName": COL_B_DUPLICATE,
            "addPositionColumn": COL_B,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df_after = tables_store.get_table(TABLE_NAME).table
    # COL_B の右隣に挿入される
    assert df_after.columns == [COL_A, COL_B, COL_B_DUPLICATE, COL_C]
    assert df_after[COL_B_DUPLICATE].to_list() == df_before[COL_B].to_list()


def test_duplicate_column_success_string_column(client, tables_store):
    """文字列列を複製できる"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/duplicate",
        json={
            "tableName": TABLE_NAME,
            "sourceColumnName": COL_C,
            "newColumnName": COL_C_CLONE,
            "addPositionColumn": COL_C,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == TABLE_NAME
    assert response_data["result"]["columnName"] == COL_C_CLONE

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after[COL_C_CLONE].to_list() == df_before[COL_C].to_list()


# ========================================
# 異常系テスト（Pydantic バリデーション: 422）
# ========================================


def test_duplicate_column_missing_table_name(client, tables_store):
    """tableName が未指定の場合は 422 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/duplicate",
        json={
            "sourceColumnName": COL_A,
            "newColumnName": COL_A_COPY,
            "addPositionColumn": COL_A,
        },
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


def test_duplicate_column_missing_source_column_name(client, tables_store):
    """sourceColumnName が未指定の場合は 422 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/duplicate",
        json={
            "tableName": TABLE_NAME,
            "newColumnName": COL_A_COPY,
            "addPositionColumn": COL_A,
        },
    )

    expected_msg = "sourceColumnNameは必須項目です。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_duplicate_column_missing_new_column_name(client, tables_store):
    """newColumnName が未指定の場合は 422 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/duplicate",
        json={
            "tableName": TABLE_NAME,
            "sourceColumnName": COL_A,
            "addPositionColumn": COL_A,
        },
    )

    expected_msg = "newColumnNameは必須項目です。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_duplicate_column_missing_add_position_column(client, tables_store):
    """addPositionColumn が未指定の場合は 422 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/duplicate",
        json={
            "tableName": TABLE_NAME,
            "sourceColumnName": COL_A,
            "newColumnName": COL_A_COPY,
        },
    )

    expected_msg = "addPositionColumnは必須項目です。"

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


def test_duplicate_column_invalid_table_name(client, tables_store):
    """存在しないテーブル名を指定した場合は 400 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/duplicate",
        json={
            "tableName": TABLE_NONEXISTENT,
            "sourceColumnName": COL_A,
            "newColumnName": COL_A_COPY,
            "addPositionColumn": COL_A,
        },
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


def test_duplicate_column_invalid_source_column(client, tables_store):
    """存在しないソース列名を指定した場合は 400 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/duplicate",
        json={
            "tableName": TABLE_NAME,
            "sourceColumnName": COL_NONEXISTENT,
            "newColumnName": f"{COL_NONEXISTENT}_Copy",
            "addPositionColumn": COL_A,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert (
        response_data["message"]
        == f"sourceColumnName '{COL_NONEXISTENT}'は存在しません。"
    )

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_duplicate_column_duplicate_new_column_name(client, tables_store):
    """既存列名と同じ newColumnName を指定した場合は 400 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/duplicate",
        json={
            "tableName": TABLE_NAME,
            "sourceColumnName": COL_A,
            "newColumnName": COL_B,  # 既存の列名
            "addPositionColumn": COL_A,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_ALREADY_EXISTS
    assert (
        response_data["message"]
        == f"newColumnName '{COL_B}'は既に存在します。"
    )

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_duplicate_column_invalid_add_position_column(client, tables_store):
    """存在しない addPositionColumn を指定した場合は 400 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/duplicate",
        json={
            "tableName": TABLE_NAME,
            "sourceColumnName": COL_A,
            "newColumnName": COL_A_COPY,
            "addPositionColumn": COL_NONEXISTENT,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert (
        response_data["message"]
        == f"addPositionColumn '{COL_NONEXISTENT}'は存在しません。"
    )

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


# ========================================
# 意地悪な入力テスト (N1-N7: 名前バリエーション)
# ========================================


def test_duplicate_column_japanese_new_column_name(client, tables_store):
    """N1: 日本語の新規列名でも正常に複製される"""
    response = client.post(
        "/api/column/duplicate",
        json={
            "tableName": TABLE_NAME,
            "sourceColumnName": COL_A,
            "newColumnName": "A_コピー",
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    assert "A_コピー" in df.columns
    assert df["A_コピー"].to_list() == DATA_A


def test_duplicate_column_japanese_source_column(client, tables_store):
    """N2: 日本語の元列名を複製しても正常に動作する"""
    tables_store.update_table(
        TABLE_NAME,
        pl.DataFrame({"売上①": DATA_A, COL_B: DATA_B, COL_C: DATA_C}),
    )
    response = client.post(
        "/api/column/duplicate",
        json={
            "tableName": TABLE_NAME,
            "sourceColumnName": "売上①",
            "newColumnName": "売上①_Copy",
            "addPositionColumn": "売上①",
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    assert "売上①_Copy" in df.columns
    assert df["売上①_Copy"].to_list() == DATA_A


def test_duplicate_column_emoji_new_column_name(client, tables_store):
    """N3: 絵文字のみの新規列名でも正常に複製される"""
    response = client.post(
        "/api/column/duplicate",
        json={
            "tableName": TABLE_NAME,
            "sourceColumnName": COL_A,
            "newColumnName": "🆕",
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    assert "🆕" in df.columns


def test_duplicate_column_strip_whitespace_source_column(client, tables_store):
    """N4: sourceColumnName の前後スペースは除去されて正常に複製される"""
    response = client.post(
        "/api/column/duplicate",
        json={
            "tableName": TABLE_NAME,
            "sourceColumnName": "  A  ",
            "newColumnName": COL_A_COPY,
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    assert COL_A_COPY in df.columns
    assert df[COL_A_COPY].to_list() == DATA_A


def test_duplicate_column_max_length_new_column_name(client, tables_store):
    """N5: 128文字（最大長境界値）の新規列名は正常に複製される"""
    long_name = "x" * 128
    response = client.post(
        "/api/column/duplicate",
        json={
            "tableName": TABLE_NAME,
            "sourceColumnName": COL_A,
            "newColumnName": long_name,
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    assert long_name in df.columns


def test_duplicate_column_too_long_new_column_name(client, tables_store):
    """N6: 129文字（最大長超過）の新規列名は422エラーになる"""
    response = client.post(
        "/api/column/duplicate",
        json={
            "tableName": TABLE_NAME,
            "sourceColumnName": COL_A,
            "newColumnName": "x" * 129,
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "newColumnNameは128文字以内で入力してください。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_duplicate_column_tab_char_new_column_name(client, tables_store):
    """N7: タブ文字を含む新規列名は422エラーになる"""
    response = client.post(
        "/api/column/duplicate",
        json={
            "tableName": TABLE_NAME,
            "sourceColumnName": COL_A,
            "newColumnName": "col	A",
            "addPositionColumn": COL_A,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "newColumnNameに使用できない文字が含まれています。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]
