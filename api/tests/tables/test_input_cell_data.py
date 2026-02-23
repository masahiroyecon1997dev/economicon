import polars as pl
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.core.enums import ErrorCode
from economicon.services.data.tables_store import TablesStore
from main import app


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_store():
    """TablesStoreのフィクスチャ"""
    manager = TablesStore()
    manager.clear_tables()
    # テスト用テーブルをセット
    df = pl.DataFrame(
        {
            "A": [1, 2, 3, 4, 5, 6, 7, 1, 2, 3],
            "B": [4, 5, 6, 7, 8, 9, 10, 4, 5, 6],
        }
    )
    manager.store_table("TestTable", df)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


def test_input_cell_data_success(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "columnName": "A",
        "rowIndex": 1,
        "newValue": 99,
    }
    response = client.post(
        "/api/table/input-cell-data",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("TestTable").table
    assert df["A"][1] == 99  # noqa: PLR2004


def test_input_cell_data_success_with_string(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "columnName": "A",
        "rowIndex": 0,
        "newValue": "AAA",
    }
    response = client.post(
        "/api/table/input-cell-data",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("TestTable").table
    assert df["A"][0] == "AAA"


def test_input_cell_data_invalid_table(client, tables_store):
    payload = {
        "tableName": "NoTable",
        "columnName": "A",
        "rowIndex": 0,
        "newValue": 10,
    }
    response = client.post(
        "/api/table/input-cell-data",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert "tableName 'NoTable'は存在しません。" == response_data["message"]


def test_input_cell_data_invalid_column(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "columnName": "Z",
        "rowIndex": 0,
        "newValue": 10,
    }
    response = client.post(
        "/api/table/input-cell-data",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert "columnName 'Z'は存在しません。" == response_data["message"]


def test_input_cell_data_invalid_row_over(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "columnName": "A",
        "rowIndex": 100,
        "newValue": 10,
    }
    response = client.post(
        "/api/table/input-cell-data",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.ROW_OUT_OF_RANGE
    assert (
        "Requested rowIndex (100) exceeds the available rows (9)."
        == response_data["message"]
    )


def test_input_cell_data_invalid_row_string(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "columnName": "A",
        "rowIndex": "String",
        "newValue": 10,
    }
    response = client.post(
        "/api/table/input-cell-data",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "rowIndexは整数で入力してください。" == response_data["message"]
    assert ["rowIndexは整数で入力してください。"] == response_data["details"]


def test_input_cell_data_empty_table_name(client, tables_store):
    """
    tableNameが空文字列の場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/table/input-cell-data",
        json={
            "tableName": "",
            "columnName": "A",
            "rowIndex": 1,
            "newValue": 10,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert (
        "tableNameは1文字以上で入力してください。" == response_data["message"]
    )
    assert ["tableNameは1文字以上で入力してください。"] == response_data[
        "details"
    ]


def test_input_cell_data_empty_column_name(client, tables_store):
    """
    columnNameが空文字列の場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/table/input-cell-data",
        json={
            "tableName": "TestTable",
            "columnName": "",
            "rowIndex": 1,
            "newValue": 10,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert (
        "columnNameは1文字以上で入力してください。" == response_data["message"]
    )
    assert ["columnNameは1文字以上で入力してください。"] == response_data[
        "details"
    ]


def test_input_cell_data_negative_row_index(client, tables_store):
    """
    rowIndexが負の値の場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/table/input-cell-data",
        json={
            "tableName": "TestTable",
            "columnName": "A",
            "rowIndex": -1,
            "newValue": 10,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "rowIndexは0以上で入力してください。" == response_data["message"]
    assert ["rowIndexは0以上で入力してください。"] == response_data["details"]


def test_input_cell_data_missing_table_name(client, tables_store):
    """
    tableNameが欠損している場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/table/input-cell-data",
        json={"columnName": "A", "rowIndex": 1, "newValue": 10},
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "tableNameは必須項目です。" == response_data["message"]
    assert ["tableNameは必須項目です。"] == response_data["details"]


def test_input_cell_data_missing_column_name(client, tables_store):
    """
    columnNameが欠損している場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/table/input-cell-data",
        json={"tableName": "TestTable", "rowIndex": 1, "newValue": 10},
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "columnNameは必須項目です。" == response_data["message"]
    assert ["columnNameは必須項目です。"] == response_data["details"]


def test_input_cell_data_missing_row_index(client, tables_store):
    """
    rowIndexが欠損している場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/table/input-cell-data",
        json={"tableName": "TestTable", "columnName": "A", "newValue": 10},
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "rowIndexは必須項目です。" == response_data["message"]
    assert ["rowIndexは必須項目です。"] == response_data["details"]


def test_input_cell_data_missing_new_value(client, tables_store):
    """
    newValueが欠損している場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/table/input-cell-data",
        json={"tableName": "TestTable", "columnName": "A", "rowIndex": 1},
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "newValueは必須項目です。" == response_data["message"]
    assert ["newValueは必須項目です。"] == response_data["details"]


# ---------------------------------------------------------------------------
# 意地悪なリクエストテスト
# ---------------------------------------------------------------------------


def test_input_cell_data_tablename_only_spaces(client, tables_store):
    """
    tableNameがスペースのみの場合、トリム後に空文字になり422エラーになる
    """
    response = client.post(
        "/api/table/input-cell-data",
        json={
            "tableName": "   ",
            "columnName": "A",
            "rowIndex": 0,
            "newValue": 1,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "tableNameは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_input_cell_data_tablename_tab_chars(client, tables_store):
    """
    tableNameがタブ文字のみの場合、トリム後に空文字になり422エラーになる
    """
    response = client.post(
        "/api/table/input-cell-data",
        json={
            "tableName": "\t",
            "columnName": "A",
            "rowIndex": 0,
            "newValue": 1,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "tableNameは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_input_cell_data_tablename_leading_trailing_spaces(
    client, tables_store
):
    """
    tableNameの前後スペースはトリムされ、正常に動作する
    """
    response = client.post(
        "/api/table/input-cell-data",
        json={
            "tableName": "  TestTable  ",
            "columnName": "A",
            "rowIndex": 0,
            "newValue": 99,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]


def test_input_cell_data_tablename_japanese(client, tables_store):
    """
    tableNameに日本語を使った場合、型は有効だが存在しないので400になる
    """
    response = client.post(
        "/api/table/input-cell-data",
        json={
            "tableName": "日本語テーブル",
            "columnName": "A",
            "rowIndex": 0,
            "newValue": 1,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert ErrorCode.DATA_NOT_FOUND == response_data["code"]


def test_input_cell_data_tablename_emoji(client, tables_store):
    """
    tableNameに絵文字を使った場合、型は有効だが存在しないので400になる
    """
    response = client.post(
        "/api/table/input-cell-data",
        json={
            "tableName": "🚀テーブル",
            "columnName": "A",
            "rowIndex": 0,
            "newValue": 1,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert ErrorCode.DATA_NOT_FOUND == response_data["code"]


def test_input_cell_data_columnname_only_spaces(client, tables_store):
    """
    columnNameがスペースのみの場合、トリム後に空文字になり422エラーになる
    """
    response = client.post(
        "/api/table/input-cell-data",
        json={
            "tableName": "TestTable",
            "columnName": "   ",
            "rowIndex": 0,
            "newValue": 1,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "columnNameは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_input_cell_data_columnname_tab_chars(client, tables_store):
    """
    columnNameがタブ文字のみの場合、トリム後に空文字になり422エラーになる
    """
    response = client.post(
        "/api/table/input-cell-data",
        json={
            "tableName": "TestTable",
            "columnName": "\t",
            "rowIndex": 0,
            "newValue": 1,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "columnNameは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_input_cell_data_columnname_leading_trailing_spaces(
    client, tables_store
):
    """
    columnNameの前後スペースはトリムされ、正常に動作する
    """
    response = client.post(
        "/api/table/input-cell-data",
        json={
            "tableName": "TestTable",
            "columnName": "  A  ",
            "rowIndex": 0,
            "newValue": 99,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
