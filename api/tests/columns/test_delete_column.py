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
TABLE_NONEXISTENT = "NotExistTable"

# テーブルの初期値
DATA_A = [1, 2, 3]
DATA_B = [4, 5, 6]
DATA_C = [7, 8, 9]


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


def test_delete_column_success(client, tables_store):
    """指定した列が正常に削除される"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/delete",
        json={"tableName": TABLE_NAME, "columnName": COL_A},
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == TABLE_NAME

    df_after = tables_store.get_table(TABLE_NAME).table
    assert COL_A not in df_after.columns
    assert COL_B in df_after.columns
    assert COL_C in df_after.columns
    # 残った列のデータは変わらない
    assert df_after[COL_B].to_list() == df_before[COL_B].to_list()
    assert df_after[COL_C].to_list() == df_before[COL_C].to_list()


# ========================================
# 異常系テスト（Pydantic バリデーション: 422）
# ========================================


def test_delete_column_missing_table_name(client, tables_store):
    """tableName が未指定の場合は 422 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/delete",
        json={"columnName": COL_A},
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


def test_delete_column_missing_column_name(client, tables_store):
    """columnName が未指定の場合は 422 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/delete",
        json={"tableName": TABLE_NAME},
    )

    expected_msg = "columnNameは必須項目です。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_delete_column_empty_table_name(client, tables_store):
    """tableName が空文字の場合は 422 を返す（minlength=1 違反）"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/delete",
        json={"tableName": "", "columnName": COL_A},
    )

    expected_msg = "tableNameは1文字以上で入力してください。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_delete_column_empty_column_name(client, tables_store):
    """columnName が空文字の場合は 422 を返す（minlength=1 違反）"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/delete",
        json={"tableName": TABLE_NAME, "columnName": ""},
    )

    expected_msg = "columnNameは1文字以上で入力してください。"

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


def test_delete_column_invalid_table_name(client, tables_store):
    """存在しないテーブル名を指定した場合は 400 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/delete",
        json={
            "tableName": TABLE_NONEXISTENT,
            "columnName": COL_A,
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


def test_delete_column_invalid_column_name(client, tables_store):
    """存在しない列名を指定した場合は 400 を返す"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/delete",
        json={
            "tableName": TABLE_NAME,
            "columnName": COL_NONEXISTENT,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert (
        response_data["message"]
        == f"columnName '{COL_NONEXISTENT}'は存在しません。"
    )

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


# ========================================
# 意地悪な入力テスト (N1-N7: 名前バリエーション)
# ========================================


def test_delete_column_japanese_column_name(client, tables_store):
    """N1: 日本語の列名でも正常に削除される"""
    tables_store.update_table(
        TABLE_NAME,
        pl.DataFrame({"売上": DATA_A, COL_B: DATA_B, COL_C: DATA_C}),
    )
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/delete",
        json={"tableName": TABLE_NAME, "columnName": "売上"},
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    assert "売上" not in df.columns
    assert len(df.columns) == len(df_before.columns) - 1


def test_delete_column_emoji_column_name(client, tables_store):
    """N2: 絵文字の列名でも正常に削除される"""
    tables_store.update_table(
        TABLE_NAME,
        pl.DataFrame({"🔥": DATA_A, COL_B: DATA_B, COL_C: DATA_C}),
    )
    response = client.post(
        "/api/column/delete",
        json={"tableName": TABLE_NAME, "columnName": "🔥"},
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    assert "🔥" not in df.columns


def test_delete_column_strip_whitespace_column_name(client, tables_store):
    """N3: columnName の前後スペースは除去されて正常に削除される"""
    response = client.post(
        "/api/column/delete",
        json={"tableName": TABLE_NAME, "columnName": "  A  "},
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    assert COL_A not in df.columns


def test_delete_column_strip_whitespace_table_name(client, tables_store):
    """N4: tableName の前後スペースは除去されて正常に削除される"""
    response = client.post(
        "/api/column/delete",
        json={"tableName": f"  {TABLE_NAME}  ", "columnName": COL_A},
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    assert COL_A not in df.columns


def test_delete_column_long_table_name_not_found(client, tables_store):
    """N5: 非常に長いテーブル名は存在しないため400エラーになる"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/delete",
        json={"tableName": "x" * 256, "columnName": COL_A},
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_delete_column_tab_char_column_name_not_found(client, tables_store):
    """N6: タブ文字を含む列名は存在しないため400エラーになる"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/delete",
        json={"tableName": TABLE_NAME, "columnName": "col	A"},
    )
    response_data = response.json()
    # ColumnName 型は pattern なし → strip でも変更なし → DATA_NOT_FOUND になる
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)
