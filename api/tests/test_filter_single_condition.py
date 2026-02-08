import polars as pl
import pytest
from economicon.services.data.tables_store import TablesStore
from fastapi import status
from fastapi.testclient import TestClient
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
            "B": [11, 12, 30, 40, 1, 2, 3, 40, 10, 2],
            "C": [1, 1, 4, 8, 4, 6, 7, 2, 3, 2],
        }
    )
    manager.store_table("TestTable", df)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


def test_filter_equals(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "columnName": "A",
        "condition": "equals",
        "isCompareColumn": "false",
        "compareValue": 2,
    }
    response = client.post(
        "/api/operation/filter-single-condition",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    assert df.shape[0] == 2
    assert df["A"].to_list() == [2, 2]


def test_filter_greater_than(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "columnName": "B",
        "condition": "greaterThan",
        "isCompareColumn": "false",
        "compareValue": 10,
    }
    response = client.post(
        "/api/operation/filter-single-condition",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    assert df.shape[0] == 5
    assert df["B"].to_list() == [11, 12, 30, 40, 40]


def test_filter_not_equals(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "columnName": "A",
        "condition": "notEquals",
        "isCompareColumn": "false",
        "compareValue": 2,
    }
    response = client.post(
        "/api/operation/filter-single-condition",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    assert df.shape[0] == 8
    assert 2 not in df["A"].to_list()


def test_filter_greater_than_or_equals(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "columnName": "B",
        "condition": "greaterThanOrEquals",
        "isCompareColumn": "false",
        "compareValue": 30,
    }
    response = client.post(
        "/api/operation/filter-single-condition",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    assert df.shape[0] == 3
    assert df["B"].to_list() == [30, 40, 40]


def test_filter_less_than(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "columnName": "A",
        "condition": "lessThan",
        "isCompareColumn": "false",
        "compareValue": 3,
    }
    response = client.post(
        "/api/operation/filter-single-condition",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    assert df.shape[0] == 4
    assert df["A"].to_list() == [1, 2, 1, 2]


def test_filter_less_than_or_equals(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "columnName": "B",
        "condition": "lessThanOrEquals",
        "isCompareColumn": "false",
        "compareValue": 12,
    }
    response = client.post(
        "/api/operation/filter-single-condition",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    assert df.shape[0] == 7
    assert df["B"].to_list() == [11, 12, 1, 2, 3, 10, 2]


def test_filter_equals_compare_column(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "columnName": "A",
        "condition": "equals",
        "isCompareColumn": "true",
        "compareValue": "C",
    }
    response = client.post(
        "/api/operation/filter-single-condition",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    # A==Cとなる行
    assert df.shape[0] == 3
    assert df["A"].to_list() == [1, 6, 7]
    assert df["C"].to_list() == [1, 6, 7]


def test_filter_greater_than_compare_column(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "columnName": "A",
        "condition": "greaterThan",
        "isCompareColumn": "true",
        "compareValue": "C",
    }
    response = client.post(
        "/api/operation/filter-single-condition",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    # B>Cとなる行
    assert df.shape[0] == 3
    assert df["A"].to_list() == [2, 5, 3]
    assert df["C"].to_list() == [1, 4, 2]


def test_filter_less_than_or_equals_compare_column(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "columnName": "A",
        "condition": "lessThanOrEquals",
        "isCompareColumn": "true",
        "compareValue": "C",
    }
    response = client.post(
        "/api/operation/filter-single-condition",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    # A<=C
    assert df.shape[0] == 7
    assert df["A"].to_list() == [1, 3, 4, 6, 7, 1, 2]
    assert df["C"].to_list() == [1, 4, 8, 6, 7, 2, 3]


def test_filter_invalid_table(client, tables_store):
    payload = {
        "tableName": "NoTable",
        "newTableName": "FilteredTable",
        "columnName": "A",
        "condition": "equals",
        "isCompareColumn": "false",
        "compareValue": 1,
    }
    response = client.post(
        "/api/operation/filter-single-condition",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "NG"
    assert "tableName 'NoTable'は存在しません。" == response_data["message"]


def test_filter_invalid_column(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "columnName": "Z",
        "condition": "equals",
        "isCompareColumn": "false",
        "compareValue": 1,
    }
    response = client.post(
        "/api/operation/filter-single-condition",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "NG"
    assert "columnName 'Z'は存在しません。" == response_data["message"]


def test_filter_invalid_condition(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "columnName": "A",
        "condition": "invalid_condition",
        "isCompareColumn": "false",
        "compareValue": 1,
    }
    response = client.post(
        "/api/operation/filter-single-condition",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "NG"
    message = (
        "condition 'invalid_condition'はサポートされていません。"
        "サポートされるcondition: equals, notEquals, greaterThan, "
        "lessThan, greaterThanOrEquals, lessThanOrEquals"
    )
    assert message == response_data["message"]


def test_filter_single_condition_empty_table_name(client, tables_store):
    """
    tableNameが空文字列の場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/operation/filter-single-condition",
        json={
            "tableName": "",
            "newTableName": "FilteredTable",
            "columnName": "A",
            "condition": "equals",
            "isCompareColumn": "false",
            "compareValue": 1,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "tableName" in response_data["message"]


def test_filter_single_condition_empty_new_table_name(client, tables_store):
    """
    newTableNameが空文字列の場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/operation/filter-single-condition",
        json={
            "tableName": "TestTable",
            "newTableName": "",
            "columnName": "A",
            "condition": "equals",
            "isCompareColumn": "false",
            "compareValue": 1,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "newTableName" in response_data["message"]


def test_filter_single_condition_empty_column_name(client, tables_store):
    """
    columnNameが空文字列の場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/operation/filter-single-condition",
        json={
            "tableName": "TestTable",
            "newTableName": "FilteredTable",
            "columnName": "",
            "condition": "equals",
            "isCompareColumn": "false",
            "compareValue": 1,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "columnName" in response_data["message"]


def test_filter_single_condition_empty_condition(client, tables_store):
    """
    conditionが空文字列の場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/operation/filter-single-condition",
        json={
            "tableName": "TestTable",
            "newTableName": "FilteredTable",
            "columnName": "A",
            "condition": "",
            "isCompareColumn": "false",
            "compareValue": 1,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "condition" in response_data["message"]


def test_filter_single_condition_empty_is_compare_column(client, tables_store):
    """
    isCompareColumnが空文字列の場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/operation/filter-single-condition",
        json={
            "tableName": "TestTable",
            "newTableName": "FilteredTable",
            "columnName": "A",
            "condition": "equals",
            "isCompareColumn": "",
            "compareValue": 1,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "isCompareColumn" in response_data["message"]


def test_filter_single_condition_missing_table_name(client, tables_store):
    """
    tableNameが欠損している場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/operation/filter-single-condition",
        json={
            "newTableName": "FilteredTable",
            "columnName": "A",
            "condition": "equals",
            "isCompareColumn": "false",
            "compareValue": 1,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "tableName" in response_data["message"]


def test_filter_single_condition_missing_new_table_name(client, tables_store):
    """
    newTableNameが欠損している場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/operation/filter-single-condition",
        json={
            "tableName": "TestTable",
            "columnName": "A",
            "condition": "equals",
            "isCompareColumn": "false",
            "compareValue": 1,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "newTableName" in response_data["message"]


def test_filter_single_condition_missing_column_name(client, tables_store):
    """
    columnNameが欠損している場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/operation/filter-single-condition",
        json={
            "tableName": "TestTable",
            "newTableName": "FilteredTable",
            "condition": "equals",
            "isCompareColumn": "false",
            "compareValue": 1,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "columnName" in response_data["message"]


def test_filter_single_condition_missing_condition(client, tables_store):
    """
    conditionが欠損している場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/operation/filter-single-condition",
        json={
            "tableName": "TestTable",
            "newTableName": "FilteredTable",
            "columnName": "A",
            "isCompareColumn": "false",
            "compareValue": 1,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "condition" in response_data["message"]


def test_filter_single_condition_missing_is_compare_column(
    client, tables_store
):
    """
    isCompareColumnが欠損している場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/operation/filter-single-condition",
        json={
            "tableName": "TestTable",
            "newTableName": "FilteredTable",
            "columnName": "A",
            "condition": "equals",
            "compareValue": 1,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "isCompareColumn" in response_data["message"]


def test_filter_single_condition_missing_compare_value(client, tables_store):
    """
    compareValueが欠損している場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/operation/filter-single-condition",
        json={
            "tableName": "TestTable",
            "newTableName": "FilteredTable",
            "columnName": "A",
            "condition": "equals",
            "isCompareColumn": "false",
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "NG" == response_data["code"]
    assert "compareValue" in response_data["message"]
