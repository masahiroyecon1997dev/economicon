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
DATA_A = [3, 1, 2]
DATA_B = [6, 4, 5]
DATA_C = ["c", "a", "b"]


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def tables_store():
    """TablesStoreのフィクスチャ"""
    manager = TablesStore()
    manager.clear_tables()
    df = pl.DataFrame({COL_A: DATA_A, COL_B: DATA_B, COL_C: DATA_C})
    manager.store_table(TABLE_NAME, df)
    yield manager
    manager.clear_tables()


def test_sort_single_column_ascending(client, tables_store):
    """正常系: 単一列で昇順ソートできることを検証する"""
    # SortInstruction は BaseModel なので JSON キーは snake_case
    payload = {
        "tableName": TABLE_NAME,
        "sortColumns": [{"column_name": COL_A, "ascending": True}],
    }
    response = client.post("/api/column/sort", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == TABLE_NAME
    df = tables_store.get_table(TABLE_NAME).table
    assert df[COL_A].to_list() == [1, 2, 3]
    assert df[COL_B].to_list() == [4, 5, 6]
    assert df[COL_C].to_list() == ["a", "b", "c"]


def test_sort_single_column_descending(client, tables_store):
    """正常系: 単一列で降順ソートできることを検証する"""
    payload = {
        "tableName": TABLE_NAME,
        "sortColumns": [{"column_name": COL_A, "ascending": False}],
    }
    response = client.post("/api/column/sort", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table(TABLE_NAME).table
    assert df[COL_A].to_list() == [3, 2, 1]
    assert df[COL_B].to_list() == [6, 5, 4]
    assert df[COL_C].to_list() == ["c", "b", "a"]


def test_sort_multiple_columns(client, tables_store):
    """正常系: 複数列のソート（A昇順・B降順）が正しく動作することを検証する"""
    df_complex = pl.DataFrame(
        {
            COL_A: [1, 2, 1, 2],
            COL_B: [4, 3, 2, 1],
            COL_C: ["d", "c", "b", "a"],
        }
    )
    tables_store.update_table(TABLE_NAME, df_complex)
    payload = {
        "tableName": TABLE_NAME,
        "sortColumns": [
            {"column_name": COL_A, "ascending": True},
            {"column_name": COL_B, "ascending": False},
        ],
    }
    response = client.post("/api/column/sort", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table(TABLE_NAME).table
    assert df[COL_A].to_list() == [1, 1, 2, 2]
    assert df[COL_B].to_list() == [4, 2, 3, 1]
    assert df[COL_C].to_list() == ["d", "b", "c", "a"]


def test_sort_invalid_table(client, tables_store):
    """
    異常系:
        存在しないテーブル名を指定した場合は400エラーになることを検証する
    """
    payload = {
        "tableName": TABLE_NONEXISTENT,
        "sortColumns": [{"column_name": COL_A, "ascending": True}],
    }
    response = client.post("/api/column/sort", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    expected_msg = f"tableName '{TABLE_NONEXISTENT}'は存在しません。"
    assert response_data["message"] == expected_msg


def test_sort_invalid_column(client, tables_store):
    """異常系: 存在しない列名を指定した場合は400エラーになることを検証する"""
    df_before = tables_store.get_table(TABLE_NAME).table
    payload = {
        "tableName": TABLE_NAME,
        "sortColumns": [{"column_name": COL_NONEXISTENT, "ascending": True}],
    }
    response = client.post("/api/column/sort", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    expected_msg = f"columnName '{COL_NONEXISTENT}'は存在しません。"
    assert response_data["message"] == expected_msg
    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_sort_empty_columns(client, tables_store):
    """異常系: sortColumnsが空リストの場合は422エラーになることを検証する"""
    payload = {"tableName": TABLE_NAME, "sortColumns": []}
    response = client.post("/api/column/sort", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "sortColumnsは1件以上ある必要があります。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_sort_missing_table_name(client, tables_store):
    """異常系: tableNameが欠けている場合は422エラーになることを検証する"""
    payload = {"sortColumns": [{"column_name": COL_A, "ascending": True}]}
    response = client.post("/api/column/sort", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "tableNameは必須項目です。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_sort_missing_sort_columns(client, tables_store):
    """異常系: sortColumnsが欠けている場合は422エラーになることを検証する"""
    payload = {"tableName": TABLE_NAME}
    response = client.post("/api/column/sort", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "sortColumnsは必須項目です。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_sort_missing_column_name(client, tables_store):
    """
    異常系:
        sortColumns要素にcolumn_nameが欠けている場合は422エラーになることを検証する
    """
    payload = {
        "tableName": TABLE_NAME,
        "sortColumns": [{"ascending": True}],
    }
    response = client.post("/api/column/sort", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "sortColumns.0.column_nameは必須項目です。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_sort_missing_ascending(client, tables_store):
    """
    異常系:
        sortColumns要素にascendingが欠けている場合は422エラーになることを検証する
    """
    payload = {
        "tableName": TABLE_NAME,
        "sortColumns": [{"column_name": COL_A}],
    }
    response = client.post("/api/column/sort", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "sortColumns.0.ascendingは必須項目です。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_sort_invalid_ascending_type(client, tables_store):
    """異常系: ascendingがnullの場合は422エラーになることを検証する"""
    payload = {
        "tableName": TABLE_NAME,
        "sortColumns": [{"column_name": COL_A, "ascending": None}],
    }
    response = client.post("/api/column/sort", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "sortColumns.0.ascendingは真偽値で入力してください。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_sort_process_error(client, tables_store):
    """異常系: update_tableが例外を送出するとき500エラーになることを検証する"""
    original_update_table = tables_store.update_table
    try:

        def raise_error(*args, **kwargs):
            raise RuntimeError("forced error")

        tables_store.update_table = raise_error
        payload = {
            "tableName": TABLE_NAME,
            "sortColumns": [{"column_name": COL_A, "ascending": True}],
        }
        response = client.post("/api/column/sort", json=payload)
        response_data = response.json()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response_data["code"] == ErrorCode.SORT_COLUMNS_PROCESS_ERROR
    finally:
        tables_store.update_table = original_update_table


# ========================================
# 意地悪な入力テスト (N1-N7: 名前バリエーション)
# ========================================


def test_sort_columns_japanese_column_name(client, tables_store):
    """N1: 日本語の列名を含む SortInstruction でも正常にソートされる"""
    tables_store.update_table(
        TABLE_NAME,
        pl.DataFrame({"売上": [3, 1, 2], COL_B: DATA_B, COL_C: DATA_C}),
    )
    response = client.post(
        "/api/column/sort",
        json={
            "tableName": TABLE_NAME,
            "sortColumns": [{"column_name": "売上", "ascending": True}],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    assert df["売上"].to_list() == [1, 2, 3]


def test_sort_columns_emoji_column_name(client, tables_store):
    """N2: 絵文字の列名を含む SortInstruction でも正常にソートされる"""
    tables_store.update_table(
        TABLE_NAME,
        pl.DataFrame({"🔥": [3, 1, 2], COL_B: DATA_B, COL_C: DATA_C}),
    )
    response = client.post(
        "/api/column/sort",
        json={
            "tableName": TABLE_NAME,
            "sortColumns": [{"column_name": "🔥", "ascending": True}],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    assert df["🔥"].to_list() == [1, 2, 3]


def test_sort_columns_strip_whitespace_table_name(client, tables_store):
    """N3: tableName の前後スペースは除去されて正常にソートされる"""
    response = client.post(
        "/api/column/sort",
        json={
            "tableName": f"  {TABLE_NAME}  ",
            "sortColumns": [{"column_name": COL_A, "ascending": True}],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table(TABLE_NAME).table
    assert df[COL_A].to_list() == [1, 2, 3]


def test_sort_columns_many_sort_keys(client, tables_store):
    """N4: 多数のソートキー（列数と同じ3つ）を指定しても正常にソートされる"""
    response = client.post(
        "/api/column/sort",
        json={
            "tableName": TABLE_NAME,
            "sortColumns": [
                {"column_name": COL_A, "ascending": True},
                {"column_name": COL_B, "ascending": False},
                {"column_name": COL_C, "ascending": True},
            ],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"


def test_sort_columns_nonexistent_sort_column(client, tables_store):
    """N5: 存在しない列名で SortInstruction を指定すると400エラーになる"""
    df_before = tables_store.get_table(TABLE_NAME).table.clone()

    response = client.post(
        "/api/column/sort",
        json={
            "tableName": TABLE_NAME,
            "sortColumns": [
                {"column_name": COL_NONEXISTENT, "ascending": True}
            ],
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    df_after = tables_store.get_table(TABLE_NAME).table
    assert df_after.equals(df_before)


def test_sort_columns_empty_table_name(client, tables_store):
    """N6: tableName が空文字の場合は422エラーになる"""
    response = client.post(
        "/api/column/sort",
        json={
            "tableName": "",
            "sortColumns": [{"column_name": COL_A, "ascending": True}],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "tableNameは1文字以上で入力してください。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_sort_columns_empty_sort_column_name(client, tables_store):
    """N7: SortInstruction の column_name が空文字の場合は422エラーになる"""
    response = client.post(
        "/api/column/sort",
        json={
            "tableName": TABLE_NAME,
            "sortColumns": [{"column_name": "", "ascending": True}],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "sortColumns.0.column_nameは1文字以上で入力してください。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]
