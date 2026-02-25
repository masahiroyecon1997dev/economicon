import os
import stat
import sys
import tempfile

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
    df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
    manager.store_table("TestTable", df)
    yield manager
    manager.clear_tables()


# ========================================
# 正常系テスト
# ========================================


def test_add_column_success(client, tables_store):
    """正常にカラム追加できる"""
    payload = {
        "tableName": "TestTable",
        "newColumnName": "C",
        "addPositionColumn": "A",
    }
    response = client.post("/api/column/add", json=payload)

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["tableName"] == "TestTable"
    assert response_data["result"]["columnName"] == "C"

    df = tables_store.get_table("TestTable").table
    # A の後に C が挿入されている
    assert df.columns == ["A", "C", "B"]
    # 追加カラムはNoneで埋まっている
    assert df["C"].to_list() == [None, None, None]
    # 既存データが保持されている
    assert df["A"].to_list() == [1, 2, 3]
    assert df["B"].to_list() == [4, 5, 6]


def test_add_column_from_csv_with_header_success(client, tables_store):
    """CSV読み込み成功（ヘッダあり）"""
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".csv", encoding="utf-8"
    ) as tmpfile:
        tmpfile.write("ColumnName\n10\n20\n30\n")
        csv_path = tmpfile.name

    try:
        payload = {
            "tableName": "TestTable",
            "newColumnName": "C",
            "addPositionColumn": "B",
            "csvFilePath": csv_path,
            "csvHasHeader": True,
            "csvStrictRowCount": True,
        }
        response = client.post("/api/column/add", json=payload)

        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert response_data["code"] == "OK"

        df = tables_store.get_table("TestTable").table
        # B の後（末尾）に C が挿入されている
        assert df.columns == ["A", "B", "C"]
        assert df["C"].to_list() == [10, 20, 30]
        # 既存データが保持されている
        assert df["A"].to_list() == [1, 2, 3]
        assert df["B"].to_list() == [4, 5, 6]
    finally:
        os.unlink(csv_path)


def test_add_column_from_csv_without_header_success(client, tables_store):
    """CSV読み込み成功（ヘッダなし）"""
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".csv", encoding="utf-8"
    ) as tmpfile:
        tmpfile.write("100\n200\n300\n")
        csv_path = tmpfile.name

    try:
        payload = {
            "tableName": "TestTable",
            "newColumnName": "D",
            "addPositionColumn": "A",
            "csvFilePath": csv_path,
            "csvHasHeader": False,
            "csvStrictRowCount": True,
        }
        response = client.post("/api/column/add", json=payload)

        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert response_data["code"] == "OK"

        df = tables_store.get_table("TestTable").table
        # A の後に D が挿入されている
        assert df.columns == ["A", "D", "B"]
        assert df["D"].to_list() == [100, 200, 300]
        # 既存データが保持されている
        assert df["A"].to_list() == [1, 2, 3]
        assert df["B"].to_list() == [4, 5, 6]
    finally:
        os.unlink(csv_path)


def test_add_column_from_csv_row_count_mismatch_non_strict_truncate(
    client, tables_store
):
    """行数不一致で非厳密モード（超過分を切り捨て）"""
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".csv", encoding="utf-8"
    ) as tmpfile:
        tmpfile.write("ColumnName\n10\n20\n30\n40\n50\n")
        csv_path = tmpfile.name

    try:
        payload = {
            "tableName": "TestTable",
            "newColumnName": "F",
            "addPositionColumn": "A",
            "csvFilePath": csv_path,
            "csvHasHeader": True,
            "csvStrictRowCount": False,
        }
        response = client.post("/api/column/add", json=payload)

        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert response_data["code"] == "OK"

        df = tables_store.get_table("TestTable").table
        # A の後に F が挿入されている
        assert df.columns == ["A", "F", "B"]
        # 超過分は切り捨て（CSVの5行 → テーブルの3行）
        assert df["F"].to_list() == [10, 20, 30]
        # 既存データが保持されている
        assert df["A"].to_list() == [1, 2, 3]
        assert df["B"].to_list() == [4, 5, 6]
    finally:
        os.unlink(csv_path)


def test_add_column_from_csv_row_count_mismatch_non_strict_pad(
    client, tables_store
):
    """行数不一致で非厳密モード（不足分をNoneで埋める）"""
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".csv", encoding="utf-8"
    ) as tmpfile:
        tmpfile.write("ColumnName\n10\n20\n")
        csv_path = tmpfile.name

    try:
        payload = {
            "tableName": "TestTable",
            "newColumnName": "G",
            "addPositionColumn": "A",
            "csvFilePath": csv_path,
            "csvHasHeader": True,
            "csvStrictRowCount": False,
        }
        response = client.post("/api/column/add", json=payload)

        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert response_data["code"] == "OK"

        df = tables_store.get_table("TestTable").table
        # A の後に G が挿入されている
        assert df.columns == ["A", "G", "B"]
        # 不足分は None で埋める（CSVの2行 → テーブルの3行）
        assert df["G"].to_list() == [10, 20, None]
        # 既存データが保持されている
        assert df["A"].to_list() == [1, 2, 3]
        assert df["B"].to_list() == [4, 5, 6]
    finally:
        os.unlink(csv_path)


def test_add_column_new_column_name_max_length(client, tables_store):
    """新カラム名がちょうど128文字の場合（境界値：正常）"""
    long_name = "a" * 128  # ちょうど128文字（NewColumnName の最大値）

    payload = {
        "tableName": "TestTable",
        "newColumnName": long_name,
        "addPositionColumn": "A",
    }
    response = client.post("/api/column/add", json=payload)

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["columnName"] == long_name

    df = tables_store.get_table("TestTable").table
    assert long_name in df.columns
    # A の後に挿入されている
    assert df.columns == ["A", long_name, "B"]


def test_add_column_special_chars_in_column_name(client, tables_store):
    """新カラム名に特殊文字（日本語・記号）が含まれる場合（正常）"""
    special_name = "カラム名@#$%^&*()"

    payload = {
        "tableName": "TestTable",
        "newColumnName": special_name,
        "addPositionColumn": "A",
    }
    response = client.post("/api/column/add", json=payload)

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["columnName"] == special_name

    df = tables_store.get_table("TestTable").table
    assert special_name in df.columns
    assert df.columns == ["A", special_name, "B"]


def test_add_column_csv_with_multiple_columns(client, tables_store):
    """CSVファイルに複数列がある場合（1列目のみ使用）"""
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".csv", encoding="utf-8"
    ) as tmpfile:
        # 3列あるが1列目だけ使われる
        tmpfile.write(
            "10,ignored_a,ignored_b\n"
            "20,ignored_c,ignored_d\n"
            "30,ignored_e,ignored_f\n"
        )
        csv_path = tmpfile.name

    try:
        payload = {
            "tableName": "TestTable",
            "newColumnName": "C",
            "addPositionColumn": "A",
            "csvFilePath": csv_path,
            "csvHasHeader": False,
            "csvStrictRowCount": True,
        }
        response = client.post("/api/column/add", json=payload)

        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert response_data["code"] == "OK"

        df = tables_store.get_table("TestTable").table
        # 1列目 (10, 20, 30) のみ使用される
        assert df["C"].to_list() == [10, 20, 30]
    finally:
        os.unlink(csv_path)


def test_add_column_first_position(client, tables_store):
    """最初の列（A）の直後に追加"""
    payload = {
        "tableName": "TestTable",
        "newColumnName": "C",
        "addPositionColumn": "A",
    }
    response = client.post("/api/column/add", json=payload)

    assert response.status_code == status.HTTP_200_OK

    df = tables_store.get_table("TestTable").table
    # addPositionColumn は「この列の後に追加」なので A の後 → ["A", "C", "B"]
    assert df.columns == ["A", "C", "B"]


def test_add_column_last_position(client, tables_store):
    """最後の列（B）の直後に追加（末尾追加）"""
    payload = {
        "tableName": "TestTable",
        "newColumnName": "C",
        "addPositionColumn": "B",
    }
    response = client.post("/api/column/add", json=payload)

    assert response.status_code == status.HTTP_200_OK

    df = tables_store.get_table("TestTable").table
    # B の後（末尾）に追加 → ["A", "B", "C"]
    assert df.columns == ["A", "B", "C"]


def test_add_column_preserves_other_columns_data(client, tables_store):
    """列追加時に既存の全データが保持されることを確認"""
    df_before = tables_store.get_table("TestTable").table.clone()

    payload = {
        "tableName": "TestTable",
        "newColumnName": "C",
        "addPositionColumn": "A",
    }
    response = client.post("/api/column/add", json=payload)

    assert response.status_code == status.HTTP_200_OK

    df_after = tables_store.get_table("TestTable").table
    # データ内容が保持されている
    assert df_after["A"].to_list() == df_before["A"].to_list()
    assert df_after["B"].to_list() == df_before["B"].to_list()
    # データ型が保持されている
    assert df_after["A"].dtype == df_before["A"].dtype
    assert df_after["B"].dtype == df_before["B"].dtype


# ========================================
# 異常系テスト（Pydanticバリデーション: 422）
# ========================================


def test_add_column_missing_table_name(client, tables_store):
    """tableName が未指定の場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add",
        json={
            "newColumnName": "C",
            "addPositionColumn": "A",
        },
    )

    expected_msg = "tableNameは必須です。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_column_missing_new_column_name(client, tables_store):
    """newColumnName が未指定の場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add",
        json={
            "tableName": "TestTable",
            "addPositionColumn": "A",
        },
    )

    expected_msg = "newColumnNameは必須です。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_column_missing_add_position_column(client, tables_store):
    """addPositionColumn が未指定の場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add",
        json={
            "tableName": "TestTable",
            "newColumnName": "C",
        },
    )

    expected_msg = "addPositionColumnは必須です。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_column_empty_table_name(client, tables_store):
    """tableName がスペースのみ（strip後に空文字）の場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add",
        json={
            "tableName": "   ",
            "newColumnName": "C",
            "addPositionColumn": "A",
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


def test_add_column_empty_new_column_name(client, tables_store):
    """newColumnName が空文字の場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add",
        json={
            "tableName": "TestTable",
            "newColumnName": "",
            "addPositionColumn": "A",
        },
    )

    expected_msg = "newColumnNameは1文字以上で入力してください。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_column_empty_add_position_column(client, tables_store):
    """addPositionColumn が空文字の場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add",
        json={
            "tableName": "TestTable",
            "newColumnName": "C",
            "addPositionColumn": "",
        },
    )

    expected_msg = "addPositionColumnは1文字以上で入力してください。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_column_table_name_is_number(client, tables_store):
    """tableName が数値の場合（strict=True なので型エラー）"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add",
        json={
            "tableName": 123,
            "newColumnName": "C",
            "addPositionColumn": "A",
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


def test_add_column_new_column_name_is_number(client, tables_store):
    """newColumnName が数値の場合（strict=True なので型エラー）"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add",
        json={
            "tableName": "TestTable",
            "newColumnName": 123,
            "addPositionColumn": "A",
        },
    )

    expected_msg = "newColumnNameは文字列で入力してください。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_column_add_position_column_is_number(client, tables_store):
    """addPositionColumn が数値の場合（strict=True なので型エラー）"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add",
        json={
            "tableName": "TestTable",
            "newColumnName": "C",
            "addPositionColumn": 123,
        },
    )

    expected_msg = "addPositionColumnは文字列で入力してください。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_column_new_column_name_too_long(client, tables_store):
    """newColumnName が129文字（最大128文字を超過）の場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add",
        json={
            "tableName": "TestTable",
            "newColumnName": "a" * 129,
            "addPositionColumn": "A",
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


def test_add_column_csv_file_path_too_long(client, tables_store):
    """csvFilePath が1025文字（最大1024文字を超過）の場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add",
        json={
            "tableName": "TestTable",
            "newColumnName": "C",
            "addPositionColumn": "A",
            "csvFilePath": "x" * 1025,
        },
    )

    expected_msg = "csvFilePathは1024文字以内で入力してください。"

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert "message" in response_data
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_column_new_column_name_with_null_char(client, tables_store):
    """newColumnName に Null 文字（\\x00）が含まれる場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add",
        json={
            "tableName": "TestTable",
            "newColumnName": "col\x00name",
            "addPositionColumn": "A",
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


def test_add_column_new_column_name_with_control_char_1f(client, tables_store):
    """newColumnName に制御文字（\\x1f）が含まれる場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add",
        json={
            "tableName": "TestTable",
            "newColumnName": "col\x1fname",
            "addPositionColumn": "A",
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


def test_add_column_new_column_name_with_control_char_7f(client, tables_store):
    """newColumnName に制御文字（\\x7f DEL）が含まれる場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add",
        json={
            "tableName": "TestTable",
            "newColumnName": "col\x7fname",
            "addPositionColumn": "A",
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


def test_add_column_separator_empty(client, tables_store):
    """区切り文字が空文字の場合（最小1文字）"""
    df_before = tables_store.get_table("TestTable").table.clone()

    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".csv", encoding="utf-8"
    ) as tmpfile:
        tmpfile.write("10\n20\n30\n")
        csv_path = tmpfile.name

    try:
        response = client.post(
            "/api/column/add",
            json={
                "tableName": "TestTable",
                "newColumnName": "C",
                "addPositionColumn": "A",
                "csvFilePath": csv_path,
                "separator": "",
            },
        )

        expected_msg = "separatorは1文字以上で入力してください。"

        response_data = response.json()
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        assert response_data["code"] == ErrorCode.VALIDATION_ERROR
        assert "message" in response_data
        assert response_data["message"] == expected_msg
        assert response_data["details"] == [expected_msg]

        df_after = tables_store.get_table("TestTable").table
        assert df_after.equals(df_before)
    finally:
        os.unlink(csv_path)


def test_add_column_separator_too_long(client, tables_store):
    """区切り文字が11文字（最大10文字を超過）の場合"""
    df_before = tables_store.get_table("TestTable").table.clone()

    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".csv", encoding="utf-8"
    ) as tmpfile:
        tmpfile.write("10\n20\n30\n")
        csv_path = tmpfile.name

    try:
        response = client.post(
            "/api/column/add",
            json={
                "tableName": "TestTable",
                "newColumnName": "C",
                "addPositionColumn": "A",
                "csvFilePath": csv_path,
                "separator": "-" * 11,
            },
        )

        expected_msg = "separatorは10文字以内で入力してください。"

        response_data = response.json()
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        assert response_data["code"] == ErrorCode.VALIDATION_ERROR
        assert "message" in response_data
        assert response_data["message"] == expected_msg
        assert response_data["details"] == [expected_msg]

        df_after = tables_store.get_table("TestTable").table
        assert df_after.equals(df_before)
    finally:
        os.unlink(csv_path)


# ========================================
# 異常系テスト（内部バリデーション: 400）
# ========================================


def test_add_column_invalid_table(client, tables_store):
    """存在しないテーブル名"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add",
        json={
            "tableName": "NoTable",
            "newColumnName": "C",
            "addPositionColumn": "A",
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert response_data["message"] == "tableName 'NoTable'は存在しません。"

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_column_duplicate_name(client, tables_store):
    """既存のカラム名と重複"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add",
        json={
            "tableName": "TestTable",
            "newColumnName": "A",
            "addPositionColumn": "A",
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_ALREADY_EXISTS
    assert response_data["message"] == "newColumnName 'A'は既に存在します。"

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_column_invalid_position_column(client, tables_store):
    """追加位置指定カラムが存在しない"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add",
        json={
            "tableName": "TestTable",
            "newColumnName": "C",
            "addPositionColumn": "Z",
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.DATA_NOT_FOUND
    assert response_data["message"] == "addPositionColumn 'Z'は存在しません。"

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


def test_add_column_from_csv_file_not_found(client, tables_store):
    """CSVファイルが存在しない（エラー）"""
    df_before = tables_store.get_table("TestTable").table.clone()

    response = client.post(
        "/api/column/add",
        json={
            "tableName": "TestTable",
            "newColumnName": "H",
            "addPositionColumn": "A",
            "csvFilePath": "/nonexistent/path/to/file.csv",
            "csvHasHeader": True,
            "csvStrictRowCount": True,
        },
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == ErrorCode.PATH_NOT_FOUND
    assert response_data["message"] == (
        "csvFilePath '/nonexistent/path/to/file.csv'は存在しません。"
    )

    df_after = tables_store.get_table("TestTable").table
    assert df_after.equals(df_before)


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Windowsでは os.chmod による読み取り拒否が管理者権限では無効",
)
def test_add_column_from_csv_file_permission_denied(client, tables_store):
    """CSVファイルへのアクセス権がない場合（非Windows）"""
    df_before = tables_store.get_table("TestTable").table.clone()

    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".csv", encoding="utf-8"
    ) as tmpfile:
        tmpfile.write("ColumnName\n10\n20\n30\n")
        csv_path = tmpfile.name

    try:
        # 読み取り権限を削除
        os.chmod(csv_path, stat.S_IWRITE)

        response = client.post(
            "/api/column/add",
            json={
                "tableName": "TestTable",
                "newColumnName": "C",
                "addPositionColumn": "A",
                "csvFilePath": csv_path,
                "csvHasHeader": True,
            },
        )

        response_data = response.json()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response_data["code"] == ErrorCode.PERMISSION_DENIED
        # permission denied メッセージは日本語翻訳あり
        expected_msg = f"csvFilePath '{csv_path}'にはread権限がありません。"
        assert response_data["message"] == expected_msg

        df_after = tables_store.get_table("TestTable").table
        assert df_after.equals(df_before)
    finally:
        # 権限を戻してから削除
        os.chmod(csv_path, stat.S_IWRITE | stat.S_IREAD)
        os.unlink(csv_path)


# ========================================
# 異常系テスト（処理エラー: 500）
# ========================================


def test_add_column_from_csv_row_count_mismatch_strict(client, tables_store):
    """行数不一致で厳密モード（エラー）"""
    df_before = tables_store.get_table("TestTable").table.clone()

    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".csv", encoding="utf-8"
    ) as tmpfile:
        # 5行（テーブルは3行）
        tmpfile.write("ColumnName\n10\n20\n30\n40\n50\n")
        csv_path = tmpfile.name

    try:
        response = client.post(
            "/api/column/add",
            json={
                "tableName": "TestTable",
                "newColumnName": "E",
                "addPositionColumn": "A",
                "csvFilePath": csv_path,
                "csvHasHeader": True,
                "csvStrictRowCount": True,
            },
        )

        response_data = response.json()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response_data["code"] == ErrorCode.ROW_COUNT_MISMATCH
        # row count mismatch メッセージは日本語翻訳あり
        expected_msg = (
            "行数の不一致: CSVには5行ありますが、テーブルには3行あります。"
        )
        assert response_data["message"] == expected_msg

        df_after = tables_store.get_table("TestTable").table
        assert df_after.equals(df_before)
    finally:
        os.unlink(csv_path)


def test_add_column_from_csv_empty_file(client, tables_store):
    """CSVファイルがサイズ0（エラー）"""
    df_before = tables_store.get_table("TestTable").table.clone()

    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".csv", encoding="utf-8"
    ) as tmpfile:
        csv_path = tmpfile.name  # 空ファイル（サイズ0）

    try:
        response = client.post(
            "/api/column/add",
            json={
                "tableName": "TestTable",
                "newColumnName": "I",
                "addPositionColumn": "A",
                "csvFilePath": csv_path,
                "csvHasHeader": False,
                "csvStrictRowCount": True,
            },
        )

        response_data = response.json()
        # サイズ0のファイルはCSV解析前に validate_file_format が
        # EMPTY_FILE(400)で検出
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response_data["code"] == ErrorCode.EMPTY_FILE
        # empty file メッセージは日本語翻訳あり
        expected_msg = f"csvFilePath '{csv_path}'は空です。"
        assert response_data["message"] == expected_msg

        df_after = tables_store.get_table("TestTable").table
        assert df_after.equals(df_before)
    finally:
        os.unlink(csv_path)


def test_add_column_from_csv_header_only(client, tables_store):
    """CSVにヘッダ行のみでデータ行がない場合（エラー）"""
    df_before = tables_store.get_table("TestTable").table.clone()

    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".csv", encoding="utf-8"
    ) as tmpfile:
        tmpfile.write("ColumnName\n")  # ヘッダのみ、データ行なし
        csv_path = tmpfile.name

    try:
        response = client.post(
            "/api/column/add",
            json={
                "tableName": "TestTable",
                "newColumnName": "J",
                "addPositionColumn": "A",
                "csvFilePath": csv_path,
                "csvHasHeader": True,
                "csvStrictRowCount": True,
            },
        )

        response_data = response.json()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response_data["code"] == ErrorCode.EMPTY_CSV_FILE
        expected_msg = (
            "CSVファイルが空であるか、有効なデータが含まれていません。"
        )
        assert response_data["message"] == expected_msg

        df_after = tables_store.get_table("TestTable").table
        assert df_after.equals(df_before)
    finally:
        os.unlink(csv_path)


def test_add_column_from_csv_newlines_only(client, tables_store):
    """CSVの内容が改行のみの場合（Polarsは None 値として読み込む）"""
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".csv", encoding="utf-8"
    ) as tmpfile:
        tmpfile.write("\n\n\n")  # 改行のみ（サイズ > 0）
        csv_path = tmpfile.name

    try:
        response = client.post(
            "/api/column/add",
            json={
                "tableName": "TestTable",
                "newColumnName": "J",
                "addPositionColumn": "A",
                "csvFilePath": csv_path,
                "csvHasHeader": False,
                "csvStrictRowCount": False,  # 非厳密モードで行数不一致を許容
            },
        )

        response_data = response.json()
        # Polars は改行のみを None 値として読み込むため正常として扱われる
        assert response.status_code == status.HTTP_200_OK
        assert response_data["code"] == "OK"

        df = tables_store.get_table("TestTable").table
        # 改行のみのCSVは None 値（String型）として追加される
        assert "J" in df.columns
    finally:
        os.unlink(csv_path)


def test_add_column_from_csv_invalid_encoding(client, tables_store):
    """CSVファイルのエンコーディングが不正（Shift-JISなど非UTF-8）の場合（エラー）"""
    df_before = tables_store.get_table("TestTable").table.clone()

    with tempfile.NamedTemporaryFile(
        mode="wb", delete=False, suffix=".csv"
    ) as tmpfile:
        # Shift-JIS エンコードのバイト列（UTF-8として不正）
        tmpfile.write("あいう\nかきく\nさしす\n".encode("shift_jis"))
        csv_path = tmpfile.name

    try:
        response = client.post(
            "/api/column/add",
            json={
                "tableName": "TestTable",
                "newColumnName": "J",
                "addPositionColumn": "A",
                "csvFilePath": csv_path,
                "csvHasHeader": False,
                "csvStrictRowCount": True,
            },
        )

        response_data = response.json()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response_data["code"] == ErrorCode.CSV_PROCESSING_ERROR
        expected_msg = "CSV処理中に予期しないエラーが発生しました。"
        assert response_data["message"] == expected_msg

        df_after = tables_store.get_table("TestTable").table
        assert df_after.equals(df_before)
    finally:
        os.unlink(csv_path)


# ========================================
# 意地悪な入力テスト (N1-N7: 名前バリエーション)
# ========================================


def test_add_column_japanese_new_column_name(client, tables_store):
    """N1: 日本語の新規列名でも正常に空列が追加される"""
    response = client.post(
        "/api/column/add",
        json={
            "tableName": "TestTable",
            "newColumnName": "増加率",
            "addPositionColumn": "A",
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["columnName"] == "増加率"

    df = tables_store.get_table("TestTable").table
    assert "増加率" in df.columns
    assert df["増加率"].to_list() == [None, None, None]


def test_add_column_japanese_position_column(client, tables_store):
    """N2: addPositionColumn に日本語列名を指定しても正常な位置に挿入される"""
    tables_store.update_table(
        "TestTable",
        pl.DataFrame({"売上①": [1, 2, 3], "B": [4, 5, 6]}),
    )
    response = client.post(
        "/api/column/add",
        json={
            "tableName": "TestTable",
            "newColumnName": "C",
            "addPositionColumn": "売上①",
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table("TestTable").table
    assert df.columns == ["売上①", "C", "B"]


def test_add_column_emoji_new_column_name(client, tables_store):
    """N3: 絵文字のみの新規列名でも正常に空列が追加される"""
    response = client.post(
        "/api/column/add",
        json={
            "tableName": "TestTable",
            "newColumnName": "📈",
            "addPositionColumn": "A",
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["columnName"] == "📈"


def test_add_column_strip_whitespace_position_column(client, tables_store):
    """N4: addPositionColumn の前後スペースは除去されて正常に処理される"""
    response = client.post(
        "/api/column/add",
        json={
            "tableName": "TestTable",
            "newColumnName": "C",
            "addPositionColumn": "  A  ",
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"

    df = tables_store.get_table("TestTable").table
    assert df.columns == ["A", "C", "B"]


def test_add_column_max_length_new_column_name(client, tables_store):
    """N5: 128文字（最大長境界値）の新規列名は正常に空列が追加される"""
    long_name = "x" * 128
    response = client.post(
        "/api/column/add",
        json={
            "tableName": "TestTable",
            "newColumnName": long_name,
            "addPositionColumn": "A",
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["columnName"] == long_name


def test_add_column_too_long_new_column_name(client, tables_store):
    """N6: 129文字（最大長超過）の新規列名は422エラーになる"""
    response = client.post(
        "/api/column/add",
        json={
            "tableName": "TestTable",
            "newColumnName": "x" * 129,
            "addPositionColumn": "A",
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "newColumnNameは128文字以内で入力してください。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


def test_add_column_tab_char_new_column_name(client, tables_store):
    """N7: タブ文字を含む新規列名は422エラーになる"""
    response = client.post(
        "/api/column/add",
        json={
            "tableName": "TestTable",
            "newColumnName": "col	A",
            "addPositionColumn": "A",
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    expected_msg = "newColumnNameに使用できない文字が含まれています。"
    assert response_data["message"] == expected_msg
    assert response_data["details"] == [expected_msg]


# ========================================
# エンコーディングテスト（異常系: 422）
# ========================================

_ENCODING_ERROR = (
    "csvEncodingは次のいずれかである必要があります: "
    "'utf8', 'latin1', 'ascii', 'gbk', 'windows-1252' or 'shift_jis'"
)


def test_add_column_csv_encoding_invalid_value(client, tables_store):
    """csvEncoding に不正な値を指定すると 422 VALIDATION_ERROR"""
    response = client.post(
        "/api/column/add",
        json={
            "tableName": "TestTable",
            "newColumnName": "C",
            "addPositionColumn": "A",
            "csvFilePath": "/dummy/path.csv",
            "csvEncoding": "invalid-enc",
        },
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data["code"] == ErrorCode.VALIDATION_ERROR
    assert response_data["message"] == _ENCODING_ERROR
    assert response_data["details"] == [_ENCODING_ERROR]


# ========================================
# エンコーディングテスト（正常系）
# ========================================


def test_add_column_csv_encoding_shift_jis_success(client, tables_store):
    """Shift-JIS エンコードのCSVをcsvEncoding=shift_jisで正常に読み込める"""
    with tempfile.NamedTemporaryFile(
        mode="wb", delete=False, suffix=".csv"
    ) as tmpfile:
        tmpfile.write("山田\n田中\n鈴木\n".encode("shift_jis"))
        csv_path = tmpfile.name

    try:
        response = client.post(
            "/api/column/add",
            json={
                "tableName": "TestTable",
                "newColumnName": "名前",
                "addPositionColumn": "A",
                "csvFilePath": csv_path,
                "csvHasHeader": False,
                "csvStrictRowCount": True,
                "csvEncoding": "shift_jis",
            },
        )
        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert response_data["code"] == "OK"
        df = tables_store.get_table("TestTable").table
        assert "名前" in df.columns
        assert df["名前"].to_list() == ["山田", "田中", "鈴木"]
    finally:
        os.unlink(csv_path)


def test_add_column_csv_encoding_latin1_success(client, tables_store):
    """latin1 エンコードのCSVをcsvEncoding=latin1で正常に読み込める"""
    with tempfile.NamedTemporaryFile(
        mode="wb", delete=False, suffix=".csv"
    ) as tmpfile:
        tmpfile.write("K\xf6ln\nM\xfcnchen\n\xd6stersund\n".encode("latin1"))
        csv_path = tmpfile.name

    try:
        response = client.post(
            "/api/column/add",
            json={
                "tableName": "TestTable",
                "newColumnName": "都市",
                "addPositionColumn": "A",
                "csvFilePath": csv_path,
                "csvHasHeader": False,
                "csvStrictRowCount": True,
                "csvEncoding": "latin1",
            },
        )
        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert response_data["code"] == "OK"
        df = tables_store.get_table("TestTable").table
        assert "都市" in df.columns
        assert df["都市"].to_list() == ["Köln", "München", "Östersund"]
    finally:
        os.unlink(csv_path)
