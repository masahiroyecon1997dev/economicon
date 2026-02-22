import os
import tempfile

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
    # テーブルをクリア
    manager.clear_tables()
    # テスト用テーブルをセット
    df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
    manager.store_table("TestTable", df)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


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

    # カラムが追加されているか
    df = tables_store.get_table("TestTable").table
    index_C = df.columns.index("A") + 1
    assert df.columns[index_C] == "C"

    # 追加カラムはNoneで埋まっている
    assert df["C"].to_list() == [None, None, None]


def test_add_column_table_not_found(client, tables_store):
    """テーブル名に入力がない"""
    payload = {
        # テーブル名が存在しない
        "newColumnName": "C",
        "addPositionColumn": "A",
    }
    response = client.post("/api/column/add", json=payload)

    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "details" in response_data


def test_add_column_invalid_table(client, tables_store):
    """存在しないテーブル名"""
    payload = {
        "tableName": "NoTable",
        "newColumnName": "C",
        "addPositionColumn": "A",
    }
    response = client.post("/api/column/add", json=payload)

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "NG"
    assert "tableName 'NoTable'は存在しません。" == response_data["message"]


def test_add_column_duplicate_name(client, tables_store):
    """既存のカラム名と重複"""
    payload = {
        "tableName": "TestTable",
        "newColumnName": "A",  # 既に存在するカラム名
        "addPositionColumn": "A",
    }
    response = client.post("/api/column/add", json=payload)

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "NG"
    assert "newColumnName 'A'は既に存在します。" == response_data["message"]


def test_add_column_invalid_position_column(client, tables_store):
    """追加位置指定カラムが存在しない"""
    payload = {
        "tableName": "TestTable",
        "newColumnName": "C",
        "addPositionColumn": "Z",  # 存在しないカラム名
    }
    response = client.post("/api/column/add", json=payload)

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "NG"
    assert "addPositionColumn 'Z'は存在しません。" == response_data["message"]


def test_add_column_from_csv_with_header_success(client, tables_store):
    """CSV読み込み成功（ヘッダあり）"""
    # 一時CSVファイルを作成
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".csv", encoding="utf-8"
    ) as tmpfile:
        tmpfile.write("ColumnName\n")
        tmpfile.write("10\n")
        tmpfile.write("20\n")
        tmpfile.write("30\n")
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

        # カラムが追加されているか
        df = tables_store.get_table("TestTable").table
        assert "C" in df.columns
        assert df["C"].to_list() == [10, 20, 30]
    finally:
        os.unlink(csv_path)


def test_add_column_from_csv_without_header_success(client, tables_store):
    """CSV読み込み成功（ヘッダなし）"""
    # 一時CSVファイルを作成
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".csv", encoding="utf-8"
    ) as tmpfile:
        tmpfile.write("100\n")
        tmpfile.write("200\n")
        tmpfile.write("300\n")
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

        # カラムが追加されているか
        df = tables_store.get_table("TestTable").table
        assert "D" in df.columns
        assert df["D"].to_list() == [100, 200, 300]
    finally:
        os.unlink(csv_path)


def test_add_column_from_csv_row_count_mismatch_strict(client, tables_store):
    """行数不一致で厳密モード（エラー）"""
    # 一時CSVファイルを作成（行数が5行で不一致）
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".csv", encoding="utf-8"
    ) as tmpfile:
        tmpfile.write("ColumnName\n")
        tmpfile.write("10\n")
        tmpfile.write("20\n")
        tmpfile.write("30\n")
        tmpfile.write("40\n")
        tmpfile.write("50\n")
        csv_path = tmpfile.name

    try:
        payload = {
            "tableName": "TestTable",
            "newColumnName": "E",
            "addPositionColumn": "A",
            "csvFilePath": csv_path,
            "csvHasHeader": True,
            "csvStrictRowCount": True,
        }
        response = client.post("/api/column/add", json=payload)

        response_data = response.json()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response_data["code"] == "NG"
        assert "Row count mismatch" in response_data["message"]
    finally:
        os.unlink(csv_path)


def test_add_column_from_csv_row_count_mismatch_non_strict_truncate(
    client, tables_store
):
    """行数不一致で非厳密モード（超過分を切り捨て）"""
    # 一時CSVファイルを作成（行数が5行で超過）
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".csv", encoding="utf-8"
    ) as tmpfile:
        tmpfile.write("ColumnName\n")
        tmpfile.write("10\n")
        tmpfile.write("20\n")
        tmpfile.write("30\n")
        tmpfile.write("40\n")
        tmpfile.write("50\n")
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

        # カラムが追加されているか（超過分は切り捨て）
        df = tables_store.get_table("TestTable").table
        assert "F" in df.columns
        assert df["F"].to_list() == [10, 20, 30]
    finally:
        os.unlink(csv_path)


def test_add_column_from_csv_row_count_mismatch_non_strict_pad(
    client, tables_store
):
    """行数不一致で非厳密モード（不足分をNoneで埋める）"""
    # 一時CSVファイルを作成（行数が2行で不足）
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".csv", encoding="utf-8"
    ) as tmpfile:
        tmpfile.write("ColumnName\n")
        tmpfile.write("10\n")
        tmpfile.write("20\n")
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

        # カラムが追加されているか（不足分はNoneで埋める）
        df = tables_store.get_table("TestTable").table
        assert "G" in df.columns
        assert df["G"].to_list() == [10, 20, None]
    finally:
        os.unlink(csv_path)


def test_add_column_from_csv_file_not_found(client, tables_store):
    """CSVファイルが存在しない（エラー）"""
    payload = {
        "tableName": "TestTable",
        "newColumnName": "H",
        "addPositionColumn": "A",
        "csvFilePath": "/nonexistent/path/to/file.csv",
        "csvHasHeader": True,
        "csvStrictRowCount": True,
    }
    response = client.post("/api/column/add", json=payload)

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data["code"] == "NG"


def test_add_column_from_csv_empty_file(client, tables_store):
    """CSVファイルが空（エラー）"""
    # 空のCSVファイルを作成
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".csv", encoding="utf-8"
    ) as tmpfile:
        csv_path = tmpfile.name

    try:
        payload = {
            "tableName": "TestTable",
            "newColumnName": "I",
            "addPositionColumn": "A",
            "csvFilePath": csv_path,
            "csvHasHeader": False,
            "csvStrictRowCount": True,
        }
        response = client.post("/api/column/add", json=payload)

        response_data = response.json()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response_data["code"] == "NG"
        # メッセージのチェック（日本語/英語のどちらにも対応）
        assert (
            "空" in response_data["message"]
            or "empty" in response_data["message"].lower()
            or "no valid data" in response_data["message"].lower()
        )
    finally:
        os.unlink(csv_path)
