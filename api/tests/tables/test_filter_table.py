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
_NESTED_CONDITION_ERROR = (
    "conditions.0.conditionは次のいずれかである必要があります: "
    "equals, notEquals, greaterThan, lessThan, "
    "greaterThanOrEquals, lessThanOrEquals"
)
_LOGICAL_OPERATOR_ERROR = (
    "logicalOperatorは次のいずれかである必要があります: and, or"
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


# ---------------------------------------------------------------------------
# 演算子ごとの単一条件テスト
# ---------------------------------------------------------------------------


def test_filter_equals(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "conditions": [
            {
                "columnName": "A",
                "condition": "equals",
                "isCompareColumn": False,
                "compareValue": 2,
            }
        ],
    }
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    expected_row_count = 2  # A==2 の行数
    assert df.shape[0] == expected_row_count
    assert df["A"].to_list() == [2, 2]


def test_filter_greater_than(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "conditions": [
            {
                "columnName": "B",
                "condition": "greaterThan",
                "isCompareColumn": False,
                "compareValue": 10,
            }
        ],
    }
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    expected_row_count = 5  # B>10 の行数
    assert df.shape[0] == expected_row_count
    assert df["B"].to_list() == [11, 12, 30, 40, 40]


def test_filter_not_equals(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "conditions": [
            {
                "columnName": "A",
                "condition": "notEquals",
                "isCompareColumn": False,
                "compareValue": 2,
            }
        ],
    }
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    expected_row_count = 8  # A!=2 の行数
    excluded_value = 2
    assert df.shape[0] == expected_row_count
    assert excluded_value not in df["A"].to_list()


def test_filter_greater_than_or_equals(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "conditions": [
            {
                "columnName": "B",
                "condition": "greaterThanOrEquals",
                "isCompareColumn": False,
                "compareValue": 30,
            }
        ],
    }
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    expected_row_count = 3  # B>=30 の行数
    assert df.shape[0] == expected_row_count
    assert df["B"].to_list() == [30, 40, 40]


def test_filter_less_than(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "conditions": [
            {
                "columnName": "A",
                "condition": "lessThan",
                "isCompareColumn": False,
                "compareValue": 3,
            }
        ],
    }
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    expected_row_count = 4  # A<3 の行数
    assert df.shape[0] == expected_row_count
    assert df["A"].to_list() == [1, 2, 1, 2]


def test_filter_less_than_or_equals(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "conditions": [
            {
                "columnName": "B",
                "condition": "lessThanOrEquals",
                "isCompareColumn": False,
                "compareValue": 12,
            }
        ],
    }
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    expected_row_count = 7  # B<=12 の行数
    assert df.shape[0] == expected_row_count
    assert df["B"].to_list() == [11, 12, 1, 2, 3, 10, 2]


# ---------------------------------------------------------------------------
# isCompareColumn = True（カラム比較）
# ---------------------------------------------------------------------------


def test_filter_equals_compare_column(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "conditions": [
            {
                "columnName": "A",
                "condition": "equals",
                "isCompareColumn": True,
                "compareValue": "C",
            }
        ],
    }
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    expected_row_count = 3  # A==C となる行数
    assert df.shape[0] == expected_row_count
    assert df["A"].to_list() == [1, 6, 7]
    assert df["C"].to_list() == [1, 6, 7]


def test_filter_greater_than_compare_column(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "conditions": [
            {
                "columnName": "A",
                "condition": "greaterThan",
                "isCompareColumn": True,
                "compareValue": "C",
            }
        ],
    }
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    expected_row_count = 3  # A>C となる行数
    assert df.shape[0] == expected_row_count
    assert df["A"].to_list() == [2, 5, 3]
    assert df["C"].to_list() == [1, 4, 2]


def test_filter_less_than_or_equals_compare_column(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "conditions": [
            {
                "columnName": "A",
                "condition": "lessThanOrEquals",
                "isCompareColumn": True,
                "compareValue": "C",
            }
        ],
    }
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    expected_row_count = 7  # A<=C となる行数
    assert df.shape[0] == expected_row_count
    assert df["A"].to_list() == [1, 3, 4, 6, 7, 1, 2]
    assert df["C"].to_list() == [1, 4, 8, 6, 7, 2, 3]


# ---------------------------------------------------------------------------
# AND / OR 多条件テスト
# ---------------------------------------------------------------------------


def test_filter_and_two_conditions(client, tables_store):
    """
    AND: A > 1 かつ B > 10 → A=[3,4,2], B=[30,40,10] の3行
    """
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "logicalOperator": "and",
        "conditions": [
            {
                "columnName": "A",
                "condition": "greaterThan",
                "isCompareColumn": False,
                "compareValue": 1,
            },
            {
                "columnName": "B",
                "condition": "greaterThan",
                "isCompareColumn": False,
                "compareValue": 10,
            },
        ],
    }
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    # A=[2,3,4,5,6,7,2,3] かつ B>10 → B=[11,12,30,40,40]のうちA>1と交差
    # 全行: A  B
    #  idx0: 1  11 → A>1 F
    #  idx1: 2  12 → OK
    #  idx2: 3  30 → OK
    #  idx3: 4  40 → OK
    #  idx4: 5   1 → B>10 F
    #  idx5: 6   2 → B>10 F
    #  idx6: 7   3 → B>10 F
    #  idx7: 1  40 → A>1 F
    #  idx8: 2  10 → B>10 F (10 not > 10)
    #  idx9: 3   2 → B>10 F
    expected_row_count = 3  # A>1 AND B>10 の行数
    assert df.shape[0] == expected_row_count
    assert df["A"].to_list() == [2, 3, 4]
    assert df["B"].to_list() == [12, 30, 40]


def test_filter_or_two_conditions(client, tables_store):
    """
    OR: A == 1 または A == 7 → A=[1,7,1]の3行
    """
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "logicalOperator": "or",
        "conditions": [
            {
                "columnName": "A",
                "condition": "equals",
                "isCompareColumn": False,
                "compareValue": 1,
            },
            {
                "columnName": "A",
                "condition": "equals",
                "isCompareColumn": False,
                "compareValue": 7,
            },
        ],
    }
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    expected_row_count = 3  # A==1 OR A==7 の行数
    assert df.shape[0] == expected_row_count
    assert df["A"].to_list() == [1, 7, 1]


def test_filter_and_default_logical_operator(client, tables_store):
    """
    logicalOperator を省略した場合はデフォルト "and" として動作する
    """
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "conditions": [
            {
                "columnName": "A",
                "condition": "greaterThan",
                "isCompareColumn": False,
                "compareValue": 1,
            },
            {
                "columnName": "B",
                "condition": "greaterThan",
                "isCompareColumn": False,
                "compareValue": 10,
            },
        ],
    }
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    expected_row_count = 3  # A>1 AND B>10（AND デフォルト）の行数
    assert df.shape[0] == expected_row_count


def test_filter_three_conditions_and(client, tables_store):
    """
    AND: A > 1 かつ B > 10 かつ C < 5
    """
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "logicalOperator": "and",
        "conditions": [
            {
                "columnName": "A",
                "condition": "greaterThan",
                "isCompareColumn": False,
                "compareValue": 1,
            },
            {
                "columnName": "B",
                "condition": "greaterThan",
                "isCompareColumn": False,
                "compareValue": 10,
            },
            {
                "columnName": "C",
                "condition": "lessThan",
                "isCompareColumn": False,
                "compareValue": 5,
            },
        ],
    }
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    df = tables_store.get_table("FilteredTable").table
    # A>1 AND B>10 AND C<5 → idx1(A=2,B=12,C=1) のみ
    expected_row_count = 2  # 3条件 AND の行数
    assert df.shape[0] == expected_row_count
    assert df["A"].to_list() == [2, 3]
    assert df["B"].to_list() == [12, 30]
    assert df["C"].to_list() == [1, 4]


# ---------------------------------------------------------------------------
# バリデーションエラー系
# ---------------------------------------------------------------------------


def test_filter_invalid_table(client, tables_store):
    payload = {
        "tableName": "NoTable",
        "newTableName": "FilteredTable",
        "conditions": [
            {
                "columnName": "A",
                "condition": "equals",
                "isCompareColumn": False,
                "compareValue": 1,
            }
        ],
    }
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert "tableName 'NoTable'は存在しません。" == response_data["message"]


def test_filter_invalid_column(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "conditions": [
            {
                "columnName": "Z",
                "condition": "equals",
                "isCompareColumn": False,
                "compareValue": 1,
            }
        ],
    }
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert "columnName 'Z'は存在しません。" == response_data["message"]


def test_filter_invalid_condition(client, tables_store):
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "conditions": [
            {
                "columnName": "A",
                "condition": "invalid_condition",
                "isCompareColumn": False,
                "compareValue": 1,
            }
        ],
    }
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert _NESTED_CONDITION_ERROR == response_data["message"]
    assert [_NESTED_CONDITION_ERROR] == response_data["details"]


def test_filter_invalid_logical_operator(client, tables_store):
    """
    logicalOperator に無効な値が渡された場合は 422 になる
    """
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "logicalOperator": "xor",
        "conditions": [
            {
                "columnName": "A",
                "condition": "equals",
                "isCompareColumn": False,
                "compareValue": 1,
            }
        ],
    }
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert _LOGICAL_OPERATOR_ERROR == response_data["message"]
    assert [_LOGICAL_OPERATOR_ERROR] == response_data["details"]


def test_filter_empty_conditions(client, tables_store):
    """
    conditions が空リストの場合は 422 になる
    """
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
        "conditions": [],
    }
    response = client.post("/api/table/filter", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json()["code"] == ErrorCode.VALIDATION_ERROR


def test_filter_missing_conditions(client, tables_store):
    """
    conditions が欠損している場合は 422 になる
    """
    payload = {
        "tableName": "TestTable",
        "newTableName": "FilteredTable",
    }
    response = client.post("/api/table/filter", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json()["code"] == ErrorCode.VALIDATION_ERROR


# ---------------------------------------------------------------------------
# 必須フィールド欠損テスト
# ---------------------------------------------------------------------------


def test_filter_missing_table_name(client, tables_store):
    """
    tableNameが欠損している場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/table/filter",
        json={
            "newTableName": "FilteredTable",
            "conditions": [
                {
                    "columnName": "A",
                    "condition": "equals",
                    "isCompareColumn": False,
                    "compareValue": 1,
                }
            ],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "tableNameは必須です。" == response_data["message"]
    assert ["tableNameは必須です。"] == response_data["details"]


def test_filter_missing_new_table_name(client, tables_store):
    """
    newTableNameが欠損している場合はバリデーションエラーになる
    """
    response = client.post(
        "/api/table/filter",
        json={
            "tableName": "TestTable",
            "conditions": [
                {
                    "columnName": "A",
                    "condition": "equals",
                    "isCompareColumn": False,
                    "compareValue": 1,
                }
            ],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "newTableNameは必須です。" == response_data["message"]
    assert ["newTableNameは必須です。"] == response_data["details"]


def test_filter_condition_missing_column_name(client, tables_store):
    """
    conditions 内の columnName が欠損している場合はバリデーションエラー
    """
    response = client.post(
        "/api/table/filter",
        json={
            "tableName": "TestTable",
            "newTableName": "FilteredTable",
            "conditions": [
                {
                    "condition": "equals",
                    "isCompareColumn": False,
                    "compareValue": 1,
                }
            ],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "conditions.0.columnNameは必須です。" == response_data["message"]
    assert ["conditions.0.columnNameは必須です。"] == response_data["details"]


def test_filter_condition_missing_condition(client, tables_store):
    """
    conditions 内の condition が欠損している場合はバリデーションエラー
    """
    response = client.post(
        "/api/table/filter",
        json={
            "tableName": "TestTable",
            "newTableName": "FilteredTable",
            "conditions": [
                {
                    "columnName": "A",
                    "isCompareColumn": False,
                    "compareValue": 1,
                }
            ],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "conditions.0.conditionは必須です。" == response_data["message"]
    assert ["conditions.0.conditionは必須です。"] == response_data["details"]


def test_filter_condition_missing_is_compare_column(client, tables_store):
    """
    conditions 内の isCompareColumn が欠損している場合はバリデーションエラー
    """
    response = client.post(
        "/api/table/filter",
        json={
            "tableName": "TestTable",
            "newTableName": "FilteredTable",
            "conditions": [
                {
                    "columnName": "A",
                    "condition": "equals",
                    "compareValue": 1,
                }
            ],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "conditions.0.isCompareColumnは必須です。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_filter_condition_missing_compare_value(client, tables_store):
    """
    conditions 内の compareValue が欠損している場合はバリデーションエラー
    """
    response = client.post(
        "/api/table/filter",
        json={
            "tableName": "TestTable",
            "newTableName": "FilteredTable",
            "conditions": [
                {
                    "columnName": "A",
                    "condition": "equals",
                    "isCompareColumn": False,
                }
            ],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "conditions.0.compareValueは必須です。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


# ---------------------------------------------------------------------------
# 意地悪なリクエストテスト
# ---------------------------------------------------------------------------

_BASE_FILTER = {
    "tableName": "TestTable",
    "newTableName": "FilteredTable",
    "conditions": [
        {
            "columnName": "A",
            "condition": "equals",
            "isCompareColumn": False,
            "compareValue": 1,
        }
    ],
}


def test_filter_tablename_only_spaces(client, tables_store):
    """
    tableNameがスペースのみの場合、トリム後に空文字になり422エラーになる
    """
    payload = {**_BASE_FILTER, "tableName": "   "}
    response = client.post("/api/table/filter", json=payload)
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
    response = client.post("/api/table/filter", json=payload)
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
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]


def test_filter_tablename_japanese(client, tables_store):
    """
    tableNameに日本語を使った場合、型は有効だが存在しないので400になる
    """
    payload = {**_BASE_FILTER, "tableName": "日本語テーブル"}
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert ErrorCode.DATA_NOT_FOUND == response_data["code"]


def test_filter_tablename_emoji(client, tables_store):
    """
    tableNameに絵文字を使った場合、型は有効だが存在しないので400になる
    """
    payload = {**_BASE_FILTER, "tableName": "🚀table"}
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert ErrorCode.DATA_NOT_FOUND == response_data["code"]


def test_filter_new_tablename_only_spaces(client, tables_store):
    """
    newTableNameがスペースのみの場合、トリム後に空文字になり422エラーになる
    """
    payload = {**_BASE_FILTER, "newTableName": "   "}
    response = client.post("/api/table/filter", json=payload)
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
    response = client.post("/api/table/filter", json=payload)
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
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]


def test_filter_new_tablename_exceeds_max_length(client, tables_store):
    """
    newTableNameが最大文字数を超えた場合422エラーになる
    """
    over_name = "a" * (_MAX_TABLE_NAME_LEN + 1)
    payload = {**_BASE_FILTER, "newTableName": over_name}
    response = client.post("/api/table/filter", json=payload)
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
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]


def test_filter_new_tablename_japanese(client, tables_store):
    """
    newTableNameに日本語を使った場合、正常にフィルタできる
    """
    payload = {**_BASE_FILTER, "newTableName": "フィルタ結果テーブル"}
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]


def test_filter_new_tablename_emoji(client, tables_store):
    """
    newTableNameに絵文字を使った場合、正常にフィルタできる
    """
    payload = {**_BASE_FILTER, "newTableName": "🚀フィルタ結果"}
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]


def test_filter_columnname_only_spaces(client, tables_store):
    """
    columnNameがスペースのみの場合、トリム後に空文字になり422エラーになる
    """
    payload = {
        **_BASE_FILTER,
        "conditions": [
            {
                "columnName": "   ",
                "condition": "equals",
                "isCompareColumn": False,
                "compareValue": 1,
            }
        ],
    }
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "conditions.0.columnNameは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_filter_columnname_tab_chars(client, tables_store):
    """
    columnNameがタブ文字のみの場合、トリム後に空文字になり422エラーになる
    """
    payload = {
        **_BASE_FILTER,
        "conditions": [
            {
                "columnName": "\t",
                "condition": "equals",
                "isCompareColumn": False,
                "compareValue": 1,
            }
        ],
    }
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "conditions.0.columnNameは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_filter_columnname_leading_trailing_spaces(client, tables_store):
    """
    columnNameの前後スペースはトリムされ、正常にフィルタできる
    """
    payload = {
        **_BASE_FILTER,
        "conditions": [
            {
                "columnName": "  A  ",
                "condition": "equals",
                "isCompareColumn": False,
                "compareValue": 1,
            }
        ],
    }
    response = client.post("/api/table/filter", json=payload)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
