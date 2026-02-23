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
    # テーブルをクリア
    manager.clear_tables()
    # テスト用テーブルをセット
    df = pl.DataFrame(
        {
            "group": ["A", "A", "A", "B", "B", "B"],
            "time": [1, 2, 3, 1, 2, 3],
            "value": [10, 20, 30, 40, 50, 60],
        }
    )
    manager.store_table("TestTable", df)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


# ========================================
# 正常系テスト
# ========================================


def test_add_lag_column_success_no_group(client, tables_store):
    """グループなしでラグ変数を追加"""
    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "sourceColumn": "value",
            "newColumnName": "value_lag1",
            "addPositionColumn": "value",
            "periods": -1,
            "groupColumns": [],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == "TestTable"
    assert response_data["result"]["columnName"] == "value_lag1"

    df = tables_store.get_table("TestTable").table
    # value の右隣に挿入される
    assert df.columns == ["group", "time", "value", "value_lag1"]
    # 最初の値はNone、以降は前の値
    assert df["value_lag1"].to_list() == [None, 10, 20, 30, 40, 50]
    # 既存データが保持されている
    assert df["value"].to_list() == [10, 20, 30, 40, 50, 60]


def test_add_lead_column_success_no_group(client, tables_store):
    """グループなしでリード変数を追加"""
    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "sourceColumn": "value",
            "newColumnName": "value_lead1",
            "addPositionColumn": "value",
            "periods": 1,
            "groupColumns": [],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == "TestTable"
    assert response_data["result"]["columnName"] == "value_lead1"

    df = tables_store.get_table("TestTable").table
    assert df.columns == ["group", "time", "value", "value_lead1"]
    # 次の値、最後はNone
    assert df["value_lead1"].to_list() == [20, 30, 40, 50, 60, None]
    assert df["value"].to_list() == [10, 20, 30, 40, 50, 60]


def test_add_lag_column_success_with_group(client, tables_store):
    """グループありでラグ変数を追加"""
    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "sourceColumn": "value",
            "newColumnName": "value_lag1_grouped",
            "addPositionColumn": "value",
            "periods": -1,
            "groupColumns": ["group"],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["columnName"] == "value_lag1_grouped"

    df = tables_store.get_table("TestTable").table
    assert df.columns == ["group", "time", "value", "value_lag1_grouped"]
    # 各グループの最初の値はNone
    assert df["value_lag1_grouped"].to_list() == [None, 10, 20, None, 40, 50]


def test_add_lead_column_success_with_group(client, tables_store):
    """グループありでリード変数を追加"""
    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "sourceColumn": "value",
            "newColumnName": "value_lead1_grouped",
            "addPositionColumn": "value",
            "periods": 1,
            "groupColumns": ["group"],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["columnName"] == "value_lead1_grouped"

    df = tables_store.get_table("TestTable").table
    assert df.columns == ["group", "time", "value", "value_lead1_grouped"]
    # 各グループの最後の値はNone
    assert df["value_lead1_grouped"].to_list() == [20, 30, None, 50, 60, None]


# ========================================
# 異常系テスト（Pydanticバリデーション: 422）
# ========================================


def test_add_lag_lead_column_missing_table_name(client, tables_store):
    """tableName が未指定の場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "sourceColumn": "value",
            "newColumnName": "value_lag1",
            "addPositionColumn": "value",
            "periods": -1,
            "groupColumns": [],
        },
    )

    expected_msg = "tableNameは必須項目です。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_lag_lead_column_missing_source_column(client, tables_store):
    """sourceColumn が未指定の場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "newColumnName": "value_lag1",
            "addPositionColumn": "value",
            "periods": -1,
            "groupColumns": [],
        },
    )

    expected_msg = "sourceColumnは必須項目です。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_lag_lead_column_missing_new_column_name(client, tables_store):
    """newColumnName が未指定の場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "sourceColumn": "value",
            "addPositionColumn": "value",
            "periods": -1,
            "groupColumns": [],
        },
    )

    expected_msg = "newColumnNameは必須項目です。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_lag_lead_column_missing_add_position_column(client, tables_store):
    """addPositionColumn が未指定の場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "sourceColumn": "value",
            "newColumnName": "value_lag1",
            "periods": -1,
            "groupColumns": [],
        },
    )

    expected_msg = "addPositionColumnは必須項目です。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_lag_lead_column_missing_periods(client, tables_store):
    """periods が未指定の場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "sourceColumn": "value",
            "newColumnName": "value_lag1",
            "addPositionColumn": "value",
            "groupColumns": [],
        },
    )

    expected_msg = "periodsは必須項目です。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_lag_lead_column_empty_table_name(client, tables_store):
    """tableName がスペースのみ（strip後に空文字）の場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "   ",
            "sourceColumn": "value",
            "newColumnName": "value_lag1",
            "addPositionColumn": "value",
            "periods": -1,
            "groupColumns": [],
        },
    )

    expected_msg = "tableNameは1文字以上で入力してください。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_lag_lead_column_table_name_is_number(client, tables_store):
    """tableName が数値の場合（strict=True なので型エラー）"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": 123,
            "sourceColumn": "value",
            "newColumnName": "value_lag1",
            "addPositionColumn": "value",
            "periods": -1,
            "groupColumns": [],
        },
    )

    expected_msg = "tableNameは文字列で入力してください。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_lag_lead_column_periods_is_string(client, tables_store):
    """periods が文字列の場合（strict=True なので型エラー）"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "sourceColumn": "value",
            "newColumnName": "value_lag1",
            "addPositionColumn": "value",
            "periods": "one",
            "groupColumns": [],
        },
    )

    expected_msg = "periodsは整数で入力してください。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_lag_lead_column_new_column_name_too_long(client, tables_store):
    """newColumnName が129文字（最大128文字を超過）の場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "sourceColumn": "value",
            "newColumnName": "a" * 129,
            "addPositionColumn": "value",
            "periods": -1,
            "groupColumns": [],
        },
    )

    expected_msg = "newColumnNameは128文字以内で入力してください。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_lag_lead_column_new_column_name_with_control_char(
    client, tables_store
):
    """newColumnName に制御文字（\\x00）が含まれる場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "sourceColumn": "value",
            "newColumnName": "col\x00name",
            "addPositionColumn": "value",
            "periods": -1,
            "groupColumns": [],
        },
    )

    expected_msg = "newColumnNameに使用できない文字が含まれています。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


# ========================================
# 異常系テスト（内部バリデーション: 400）
# ========================================


def test_add_lag_lead_column_invalid_table(client, tables_store):
    """存在しないテーブル名"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "NoTable",
            "sourceColumn": "value",
            "newColumnName": "value_lag1",
            "addPositionColumn": "value",
            "periods": -1,
            "groupColumns": [],
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert response_data["message"] == "tableName 'NoTable'は存在しません。"

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_lag_lead_column_invalid_source_column(client, tables_store):
    """存在しないソース列名"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "sourceColumn": "nonexistent",
            "newColumnName": "value_lag1",
            "addPositionColumn": "value",
            "periods": -1,
            "groupColumns": [],
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert (
        response_data["message"]
        == "sourceColumn 'nonexistent'は存在しません。"
    )

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_lag_lead_column_invalid_group_column(client, tables_store):
    """存在しないグループ列名"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "sourceColumn": "value",
            "newColumnName": "value_lag1",
            "addPositionColumn": "value",
            "periods": -1,
            "groupColumns": ["nonexistent"],
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert (
        response_data["message"]
        == "groupColumns 'nonexistent'は存在しません。"
    )

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_lag_lead_column_existing_column_name(client, tables_store):
    """既存の列名を新しい列名として指定"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "sourceColumn": "value",
            "newColumnName": "group",  # 既存の列名
            "addPositionColumn": "value",
            "periods": -1,
            "groupColumns": [],
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_ALREADY_EXISTS
    assert (
        response_data["message"] == "newColumnName 'group'は既に存在します。"
    )

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_lag_lead_column_invalid_position_column(client, tables_store):
    """追加位置指定カラムが存在しない"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "sourceColumn": "value",
            "newColumnName": "value_lag1",
            "addPositionColumn": "no_such_col",
            "periods": -1,
            "groupColumns": [],
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert (
        response_data["message"]
        == "addPositionColumn 'no_such_col'は存在しません。"
    )

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_lag_lead_column_multiple_periods(client, tables_store):
    """2期間ラグを追加"""
    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "sourceColumn": "value",
            "newColumnName": "value_lag2",
            "addPositionColumn": "value",
            "periods": -2,
            "groupColumns": [],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["columnName"] == "value_lag2"

    df = tables_store.get_table("TestTable").table
    assert df.columns == ["group", "time", "value", "value_lag2"]
    # 最初の2つの値はNone
    assert df["value_lag2"].to_list() == [None, None, 10, 20, 30, 40]


# ========================================
# 意地悪な入力テスト (N1-N7: 名前バリエーション)
# ========================================


def test_add_lag_lead_column_japanese_new_column_name(client, tables_store):
    """N1: 日本語の新規列名でも正常にラグ列が追加される"""
    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "sourceColumn": "value",
            "newColumnName": "前期値",
            "addPositionColumn": "value",
            "periods": -1,
            "groupColumns": [],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["columnName"] == "前期値"

    df = tables_store.get_table("TestTable").table
    assert "前期値" in df.columns


def test_add_lag_lead_column_japanese_source_column(client, tables_store):
    """N2: 日本語の元列名を参照しても正常にラグ列が追加される"""
    tables_store.update_table(
        "TestTable",
        pl.DataFrame(
            {
                "group": ["A", "A", "A", "B", "B", "B"],
                "time": [1, 2, 3, 1, 2, 3],
                "売上高": [10, 20, 30, 40, 50, 60],
            }
        ),
    )
    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "sourceColumn": "売上高",
            "newColumnName": "売上高_lag1",
            "addPositionColumn": "売上高",
            "periods": -1,
            "groupColumns": [],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table("TestTable").table
    assert "売上高_lag1" in df.columns


def test_add_lag_lead_column_emoji_new_column_name(client, tables_store):
    """N3: 絵文字のみの新規列名でも正常にラグ列が追加される"""
    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "sourceColumn": "value",
            "newColumnName": "⏮️",
            "addPositionColumn": "value",
            "periods": -1,
            "groupColumns": [],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["columnName"] == "⏮️"


def test_add_lag_lead_column_strip_whitespace_source_column(
    client, tables_store
):
    """N4: sourceColumn の前後スペースは除去されて正常に処理される"""
    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "sourceColumn": "  value  ",
            "newColumnName": "value_lag1",
            "addPositionColumn": "value",
            "periods": -1,
            "groupColumns": [],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"


def test_add_lag_lead_column_max_length_new_column_name(client, tables_store):
    """N5: 128文字（最大長境界値）の新規列名は正常に追加される"""
    long_name = "x" * 128
    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "sourceColumn": "value",
            "newColumnName": long_name,
            "addPositionColumn": "value",
            "periods": -1,
            "groupColumns": [],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["columnName"] == long_name


def test_add_lag_lead_column_too_long_new_column_name(client, tables_store):
    """N6: 129文字（最大長超過）の新規列名は422エラーになる"""
    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "sourceColumn": "value",
            "newColumnName": "x" * 129,
            "addPositionColumn": "value",
            "periods": -1,
            "groupColumns": [],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "newColumnNameは128文字以内で入力してください。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_add_lag_lead_column_tab_char_new_column_name(client, tables_store):
    """N7: タブ文字を含む新規列名は422エラーになる"""
    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "sourceColumn": "value",
            "newColumnName": "col	A",
            "addPositionColumn": "value",
            "periods": -1,
            "groupColumns": [],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "newColumnNameに使用できない文字が含まれています。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


# ========================================
# 意地悪な入力テスト (L1-L3: periods 極端値)
# ========================================


def test_add_lag_lead_column_periods_zero(client, tables_store):
    """L1: periods=0 はシフトなし（元の値と同じ）でも正常に追加される"""
    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "sourceColumn": "value",
            "newColumnName": "value_shift0",
            "addPositionColumn": "value",
            "periods": 0,
            "groupColumns": [],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table("TestTable").table
    # shift=0 → 全行が元の値と同じ
    assert df["value_shift0"].to_list() == [10, 20, 30, 40, 50, 60]


def test_add_lag_lead_column_periods_large_positive(client, tables_store):
    """
    L2:
        periods=10000 はデータ行数を超えるため
        全行 null になるが正常に追加される
    """
    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "sourceColumn": "value",
            "newColumnName": "value_lead_huge",
            "addPositionColumn": "value",
            "periods": 10000,
            "groupColumns": [],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table("TestTable").table
    # 全行 null になる
    assert all(v is None for v in df["value_lead_huge"].to_list())


def test_add_lag_lead_column_periods_large_negative(client, tables_store):
    """
    L3: periods=-10000 はデータ行数を超えるため
    全行 null になるが正常に追加される
    """
    response = client.post(
        "/api/column/add-lag-lead",
        json={
            "tableName": "TestTable",
            "sourceColumn": "value",
            "newColumnName": "value_lag_huge",
            "addPositionColumn": "value",
            "periods": -10000,
            "groupColumns": [],
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table("TestTable").table
    assert all(v is None for v in df["value_lag_huge"].to_list())
