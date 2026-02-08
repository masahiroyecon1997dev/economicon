import polars as pl
import pytest
from fastapi import status
from fastapi.testclient import TestClient

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
    assert df["A"][1] == 99


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
    assert response_data["code"] == "NG"
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
    assert response_data["code"] == "NG"
    assert "columnName 'Z'は存在しません。" in response_data["message"]


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
    assert response_data["code"] == "NG"
    assert (
        "rowIndexは0から9の間である必要があります。"
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
    # response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    # assert response_data['code'] == 'NG'
    # assert "rowIndex must be an integer." == response_data['message']


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
    assert "NG" == response_data["code"]
    assert "tableName" in response_data["message"]


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
    assert "NG" == response_data["code"]
    assert "columnName" in response_data["message"]


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
    assert "NG" == response_data["code"]
    assert "rowIndex" in response_data["message"]


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
    assert "NG" == response_data["code"]
    assert "tableName" in response_data["message"]


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
    assert "NG" == response_data["code"]
    assert "columnName" in response_data["message"]


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
    assert "NG" == response_data["code"]
    assert "rowIndex" in response_data["message"]


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
    assert "NG" == response_data["code"]
    assert "newValue" in response_data["message"]
