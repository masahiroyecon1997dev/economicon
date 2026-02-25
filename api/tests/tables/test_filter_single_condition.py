import polars as pl
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.core.enums import ErrorCode
from economicon.services.data.tables_store import TablesStore
from main import app

# conditionのバリデーションエラーメッセージ
_CONDITION_ERROR = (
    "conditionは次のいずれかである必要があります: "
    "equals, notEquals, greaterThan, lessThan, "
    "greaterThanOrEquals, lessThanOrEquals"
)
# newTableName の最大文字数
_MAX_TABLE_NAME_LEN = 128


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
        "isCompareColumn": False,
        "compareValue": 2,
    }
    response = client.post(
        "/api/table/filter-single-condition",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    expected_row_count = 2
    assert df.shape[0] == expected_row_count
    assert df["A"].to_list() == [2, 2]


def test_filter_greater_than(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "columnName": "B",
        "condition": "greaterThan",
        "isCompareColumn": False,
        "compareValue": 10,
    }
    response = client.post(
        "/api/table/filter-single-condition",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    expected_row_count = 5
    assert df.shape[0] == expected_row_count
    assert df["B"].to_list() == [11, 12, 30, 40, 40]


def test_filter_not_equals(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "columnName": "A",
        "condition": "notEquals",
        "isCompareColumn": False,
        "compareValue": 2,
    }
    response = client.post(
        "/api/table/filter-single-condition",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    expected_row_count = 8
    assert df.shape[0] == expected_row_count
    not_expected_value = 2
    assert not_expected_value not in df["A"].to_list()


def test_filter_greater_than_or_equals(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "columnName": "B",
        "condition": "greaterThanOrEquals",
        "isCompareColumn": False,
        "compareValue": 30,
    }
    response = client.post(
        "/api/table/filter-single-condition",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    expected_row_count = 3
    assert df.shape[0] == expected_row_count
    assert df["B"].to_list() == [30, 40, 40]


def test_filter_less_than(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "columnName": "A",
        "condition": "lessThan",
        "isCompareColumn": False,
        "compareValue": 3,
    }
    response = client.post(
        "/api/table/filter-single-condition",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    expected_row_count = 4
    assert df.shape[0] == expected_row_count
    assert df["A"].to_list() == [1, 2, 1, 2]


def test_filter_less_than_or_equals(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "columnName": "B",
        "condition": "lessThanOrEquals",
        "isCompareColumn": False,
        "compareValue": 12,
    }
    response = client.post(
        "/api/table/filter-single-condition",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    expected_row_count = 7
    assert df.shape[0] == expected_row_count
    assert df["B"].to_list() == [11, 12, 1, 2, 3, 10, 2]


def test_filter_equals_compare_column(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "columnName": "A",
        "condition": "equals",
        "isCompareColumn": True,
        "compareValue": "C",
    }
    response = client.post(
        "/api/table/filter-single-condition",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    # A==Cとなる行
    expected_row_count = 3
    assert df.shape[0] == expected_row_count
    assert df["A"].to_list() == [1, 6, 7]
    assert df["C"].to_list() == [1, 6, 7]


def test_filter_greater_than_compare_column(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "columnName": "A",
        "condition": "greaterThan",
        "isCompareColumn": True,
        "compareValue": "C",
    }
    response = client.post(
        "/api/table/filter-single-condition",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    # B>Cとなる行
    expected_row_count = 3
    assert df.shape[0] == expected_row_count
    assert df["A"].to_list() == [2, 5, 3]
    assert df["C"].to_list() == [1, 4, 2]


def test_filter_less_than_or_equals_compare_column(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "columnName": "A",
        "condition": "lessThanOrEquals",
        "isCompareColumn": True,
        "compareValue": "C",
    }
    response = client.post(
        "/api/table/filter-single-condition",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    # A<=C
    expected_row_count = 7
    assert df.shape[0] == expected_row_count
    assert df["A"].to_list() == [1, 3, 4, 6, 7, 1, 2]
    assert df["C"].to_list() == [1, 4, 8, 6, 7, 2, 3]


def test_filter_invalid_table(client, tables_store):
    payload = {
        "tableName": "NoTable",
        "newTableName": "FilteredTable",
        "columnName": "A",
        "condition": "equals",
        "isCompareColumn": False,
        "compareValue": 1,
    }
    response = client.post(
        "/api/table/filter-single-condition",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert "tableName 'NoTable'は存在しません。" == response_data["message"]


def test_filter_invalid_column(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "columnName": "Z",
        "condition": "equals",
        "isCompareColumn": False,
        "compareValue": 1,
    }
    response = client.post(
        "/api/table/filter-single-condition",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert "columnName 'Z'は存在しません。" == response_data["message"]


def test_filter_invalid_condition(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "columnName": "A",
        "condition": "invalid_condition",
        "isCompareColumn": False,
        "compareValue": 1,
    }
    response = client.post(
        "/api/table/filter-single-condition",
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert _CONDITION_ERROR == response_data["message"]
    assert [_CONDITION_ERROR] == response_data["details"]


def test_filter_single_condition_empty_table_name(client, tables_store):
    """
    tableNameが空文字列の場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/table/filter-single-condition",
        json={
            "tableName": "",
            "newTableName": "FilteredTable",
            "columnName": "A",
            "condition": "equals",
            "isCompareColumn": False,
            "compareValue": 1,
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


def test_filter_single_condition_empty_new_table_name(client, tables_store):
    """
    newTableNameが空文字列の場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/table/filter-single-condition",
        json={
            "tableName": "TestTable",
            "newTableName": "",
            "columnName": "A",
            "condition": "equals",
            "isCompareColumn": False,
            "compareValue": 1,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert (
        "newTableNameは1文字以上で入力してください。"
        == response_data["message"]
    )
    assert ["newTableNameは1文字以上で入力してください。"] == response_data[
        "details"
    ]


def test_filter_single_condition_empty_column_name(client, tables_store):
    """
    columnNameが空文字列の場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/table/filter-single-condition",
        json={
            "tableName": "TestTable",
            "newTableName": "FilteredTable",
            "columnName": "",
            "condition": "equals",
            "isCompareColumn": False,
            "compareValue": 1,
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


def test_filter_single_condition_empty_condition(client, tables_store):
    """
    conditionが空文字列の場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/table/filter-single-condition",
        json={
            "tableName": "TestTable",
            "newTableName": "FilteredTable",
            "columnName": "A",
            "condition": "",
            "isCompareColumn": False,
            "compareValue": 1,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert _CONDITION_ERROR == response_data["message"]
    assert [_CONDITION_ERROR] == response_data["details"]


def test_filter_single_condition_empty_is_compare_column(client, tables_store):
    """
    isCompareColumnに真偽値以外が渡された場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/table/filter-single-condition",
        json={
            "tableName": "TestTable",
            "newTableName": "FilteredTable",
            "columnName": "A",
            "condition": "equals",
            "isCompareColumn": "not_a_bool",
            "compareValue": 1,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert (
        "isCompareColumnは真偽値で入力してください。"
        == response_data["message"]
    )
    assert ["isCompareColumnは真偽値で入力してください。"] == response_data[
        "details"
    ]


def test_filter_single_condition_missing_table_name(client, tables_store):
    """
    tableNameが欠損している場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/table/filter-single-condition",
        json={
            "newTableName": "FilteredTable",
            "columnName": "A",
            "condition": "equals",
            "isCompareColumn": False,
            "compareValue": 1,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "tableNameは必須です。" == response_data["message"]
    assert ["tableNameは必須です。"] == response_data["details"]


def test_filter_single_condition_missing_new_table_name(client, tables_store):
    """
    newTableNameが欠損している場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/table/filter-single-condition",
        json={
            "tableName": "TestTable",
            "columnName": "A",
            "condition": "equals",
            "isCompareColumn": False,
            "compareValue": 1,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "newTableNameは必須です。" == response_data["message"]
    assert ["newTableNameは必須です。"] == response_data["details"]


def test_filter_single_condition_missing_column_name(client, tables_store):
    """
    columnNameが欠損している場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/table/filter-single-condition",
        json={
            "tableName": "TestTable",
            "newTableName": "FilteredTable",
            "condition": "equals",
            "isCompareColumn": False,
            "compareValue": 1,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "columnNameは必須です。" == response_data["message"]
    assert ["columnNameは必須です。"] == response_data["details"]


def test_filter_single_condition_missing_condition(client, tables_store):
    """
    conditionが欠損している場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/table/filter-single-condition",
        json={
            "tableName": "TestTable",
            "newTableName": "FilteredTable",
            "columnName": "A",
            "isCompareColumn": False,
            "compareValue": 1,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "conditionは必須です。" == response_data["message"]
    assert ["conditionは必須です。"] == response_data["details"]


def test_filter_single_condition_missing_is_compare_column(
    client, tables_store
):
    """
    isCompareColumnが欠損している場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/table/filter-single-condition",
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
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "isCompareColumnは必須です。" == response_data["message"]
    assert ["isCompareColumnは必須です。"] == response_data["details"]


def test_filter_single_condition_missing_compare_value(client, tables_store):
    """
    compareValueが欠損している場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/table/filter-single-condition",
        json={
            "tableName": "TestTable",
            "newTableName": "FilteredTable",
            "columnName": "A",
            "condition": "equals",
            "isCompareColumn": False,
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "compareValueは必須です。" == response_data["message"]
    assert ["compareValueは必須です。"] == response_data["details"]


# ---------------------------------------------------------------------------
# 意地悪なリクエストテスト
# ---------------------------------------------------------------------------

_BASE_FILTER = {
    "tableName": "TestTable",
    "newTableName": "FilteredTable",
    "columnName": "A",
    "condition": "equals",
    "isCompareColumn": False,
    "compareValue": 1,
}


def test_filter_tablename_only_spaces(client, tables_store):
    """
    tableNameがスペースのみの場合、トリム後に空文字になり422エラーになる
    """
    payload = {**_BASE_FILTER, "tableName": "   "}
    response = client.post("/api/table/filter-single-condition", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "tableNameは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_filter_tablename_tab_chars(client, tables_store):
    """
    tableNameがタブ文字のみの場合、トリム後に空文字になり422エラーになる
    """
    payload = {**_BASE_FILTER, "tableName": "\t"}
    response = client.post("/api/table/filter-single-condition", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "tableNameは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_filter_tablename_leading_trailing_spaces(client, tables_store):
    """
    tableNameの前後スペースはトリムされ、正常にフィルタできる
    """
    payload = {**_BASE_FILTER, "tableName": "  TestTable  "}
    response = client.post("/api/table/filter-single-condition", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]


def test_filter_tablename_japanese(client, tables_store):
    """
    tableNameに日本語を使った場合、型は有効だが存在しないので400になる
    """
    payload = {**_BASE_FILTER, "tableName": "日本語テーブル"}
    response = client.post("/api/table/filter-single-condition", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert ErrorCode.DATA_NOT_FOUND == response_data["code"]


def test_filter_tablename_emoji(client, tables_store):
    """
    tableNameに絵文字を使った場合、型は有効だが存在しないので400になる
    """
    payload = {**_BASE_FILTER, "tableName": "🚀table"}
    response = client.post("/api/table/filter-single-condition", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert ErrorCode.DATA_NOT_FOUND == response_data["code"]


def test_filter_new_tablename_only_spaces(client, tables_store):
    """
    newTableNameがスペースのみの場合、トリム後に空文字になり422エラーになる
    """
    payload = {**_BASE_FILTER, "newTableName": "   "}
    response = client.post("/api/table/filter-single-condition", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "newTableNameは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_filter_new_tablename_tab_in_middle(client, tables_store):
    """
    newTableNameにタブ文字が含まれる場合、パターンエラーで422になる
    """
    payload = {**_BASE_FILTER, "newTableName": "Filtered\tTable"}
    response = client.post("/api/table/filter-single-condition", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "newTableNameに使用できない文字が含まれています。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_filter_new_tablename_max_length(client, tables_store):
    """
    newTableNameが最大文字数（128文字）のとき正常にフィルタできる
    """
    max_name = "a" * _MAX_TABLE_NAME_LEN
    payload = {**_BASE_FILTER, "newTableName": max_name}
    response = client.post("/api/table/filter-single-condition", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]


def test_filter_new_tablename_exceeds_max_length(client, tables_store):
    """
    newTableNameが最大文字数を超えた場合422エラーになる
    """
    over_name = "a" * (_MAX_TABLE_NAME_LEN + 1)
    payload = {**_BASE_FILTER, "newTableName": over_name}
    response = client.post("/api/table/filter-single-condition", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = f"newTableNameは{_MAX_TABLE_NAME_LEN}文字以内で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_filter_new_tablename_leading_trailing_spaces(client, tables_store):
    """
    newTableNameの前後スペースはトリムされ、正常にフィルタできる
    """
    payload = {**_BASE_FILTER, "newTableName": "  FilteredTable  "}
    response = client.post("/api/table/filter-single-condition", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]


def test_filter_new_tablename_japanese(client, tables_store):
    """
    newTableNameに日本語を使った場合、正常にフィルタできる
    """
    payload = {**_BASE_FILTER, "newTableName": "フィルタ結果テーブル"}
    response = client.post("/api/table/filter-single-condition", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]


def test_filter_new_tablename_emoji(client, tables_store):
    """
    newTableNameに絵文字を使った場合、正常にフィルタできる
    """
    payload = {**_BASE_FILTER, "newTableName": "🚀フィルタ結果"}
    response = client.post("/api/table/filter-single-condition", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]


def test_filter_columnname_only_spaces(client, tables_store):
    """
    columnNameがスペースのみの場合、トリム後に空文字になり422エラーになる
    """
    payload = {**_BASE_FILTER, "columnName": "   "}
    response = client.post("/api/table/filter-single-condition", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "columnNameは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_filter_columnname_tab_chars(client, tables_store):
    """
    columnNameがタブ文字のみの場合、トリム後に空文字になり422エラーになる
    """
    payload = {**_BASE_FILTER, "columnName": "\t"}
    response = client.post("/api/table/filter-single-condition", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "columnNameは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_filter_columnname_leading_trailing_spaces(client, tables_store):
    """
    columnNameの前後スペースはトリムされ、正常にフィルタできる
    """
    payload = {**_BASE_FILTER, "columnName": "  A  "}
    response = client.post("/api/table/filter-single-condition", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
