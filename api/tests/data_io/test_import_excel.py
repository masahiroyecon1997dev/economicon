import os
import shutil
import tempfile
from pathlib import Path

import numpy as np
import polars as pl
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.core.enums import ErrorCode
from economicon.services.data.tables_store import TablesStore
from main import app

# テストデータの定数
_TEMP_N_COLS = 3  # 一時ファイルテストデータの列数
_TEMP_N_ROWS = 5  # 一時ファイルテストデータの行数
_MAX_TABLE_NAME_LEN = 128  # テーブル名の最大文字数


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def prepared_data():
    """TablesStoreのフィクスチャ"""
    manager = TablesStore()
    manager.clear_tables()
    # テスト用の出力ディレクトリ
    test_dir = tempfile.mkdtemp()
    yield manager, test_dir
    # テスト後のクリーンアップ
    manager.clear_tables()
    # テスト後にテンポラリディレクトリをクリーンアップ
    shutil.rmtree(test_dir, ignore_errors=True)


def test_import_excel_simple(client, prepared_data):
    """
    シンプルなEXCELファイルをパス指定でインポートするテスト
    """
    tables_store, test_dir = prepared_data
    test_data = pl.DataFrame(
        {
            "col_1": [1, 2, 3],
            "col_2": [10.1, 20.2, 30.3],
            "col_3": ["A", "B", "C"],
        }
    )
    test_data.write_excel(f"{test_dir}/SimpleTest.xlsx")
    # APIリクエスト
    request_data = {
        "filePath": f"{test_dir}/SimpleTest.xlsx",
        "tableName": "TestSimpleExcel",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert "TestSimpleExcel" == response_data["result"]["tableName"]
    # データの検証
    df = tables_store.get_table("TestSimpleExcel").table
    assert test_data.equals(df)


@pytest.mark.skip(reason="大きなデータのインポートは時間がかかるためスキップ")
def test_import_excel_large_data(client, prepared_data):
    """
    大きなEXCELファイルをパス指定でインポートするテスト
    """
    tables_store, test_dir = prepared_data
    n_rows = 5000
    n_cols = 500
    rng = np.random.default_rng(42)
    data = rng.integers(0, 100, size=(n_rows, n_cols), dtype=np.int32)
    column_names = [f"col_{i}" for i in range(n_cols)]
    df_sample = pl.DataFrame(data, schema=column_names)
    df_sample.write_excel(f"{test_dir}/TestDataXlsx.xlsx")
    # APIリクエスト
    request_data = {
        "filePath": f"{test_dir}/TestDataXlsx.xlsx",
        "tableName": "TestLargeExcel",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert "TestLargeExcel" == response_data["result"]["tableName"]
    # データの検証
    df = tables_store.get_table("TestLargeExcel").table
    assert df_sample.equals(df)


def test_import_excel_custom_table_name(client, prepared_data):
    """
    カスタムテーブル名でEXCELファイルをインポートするテスト
    """
    tables_store, test_dir = prepared_data
    test_data = pl.DataFrame(
        {
            "col_1": [1, 2, 3],
            "col_2": [10.1, 20.2, 30.3],
            "col_3": ["A", "B", "C"],
        }
    )
    test_data.write_excel(f"{test_dir}/SimpleTest.xlsx")
    # APIリクエスト
    request_data = {
        "filePath": f"{test_dir}/SimpleTest.xlsx",
        "tableName": "MyCustomExcelTable",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert "MyCustomExcelTable" == response_data["result"]["tableName"]
    # データの検証
    df = tables_store.get_table("MyCustomExcelTable").table
    assert test_data.equals(df)


def test_import_excel_file_not_exists(client, prepared_data):
    """
    存在しないファイルパスを指定した場合のテスト
    """
    tables_store, test_dir = prepared_data
    request_data = {
        "filePath": "/non/existent/file.parquet",
        "tableName": "TestNonExistent",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert ErrorCode.PATH_NOT_FOUND == response_data["code"]
    message = "filePath '/non/existent/file.parquet'は存在しません。"
    assert message == response_data["message"]


def test_import_excel_invalid_file_extension(client, prepared_data):
    """
    非対応拡張子（.txt）を指定した場合のテスト
    統合 /import エンドポイントでサポート外拡張子は 500 が返る
    """
    tables_store, test_dir = prepared_data
    txt_path = f"{test_dir}/unsupported.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("col1,col2\n1,2\n")
    request_data = {
        "filePath": txt_path,
        "tableName": "TestInvalidExtension",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert ErrorCode.UNSUPPORTED_FILE_TYPE == response_data["code"]


def test_import_excel_missing_file_path(client, prepared_data):
    """
    filePathパラメータが未指定の場合のテスト
    """
    tables_store, test_dir = prepared_data
    request_data = {"tableName": "TestMissingPath"}
    response = client.post("/api/data/import", json=request_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "filePathは必須です。" == response_data["message"]
    assert ["filePathは必須です。"] == response_data["details"]


def test_import_excel_missing_table_name(client, prepared_data):
    """
    tableNameパラメータが未指定の場合のテスト
    """
    tables_store, test_dir = prepared_data
    test_data = pl.DataFrame(
        {
            "col_1": [1, 2, 3],
            "col_2": [10.1, 20.2, 30.3],
            "col_3": ["A", "B", "C"],
        }
    )
    test_data.write_excel(f"{test_dir}/TestDataComma.xlsx")
    request_data = {"filePath": f"{test_dir}/TestDataComma.xlsx"}
    response = client.post("/api/data/import", json=request_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "tableNameは必須です。" == response_data["message"]
    assert ["tableNameは必須です。"] == response_data["details"]


def test_import_excel_duplicate_table_name(client, prepared_data):
    """
    既存のテーブル名と重複する場合のテスト
    """
    tables_store, test_dir = prepared_data
    test_data = pl.DataFrame(
        {
            "col_1": [1, 2, 3],
            "col_2": [10.1, 20.2, 30.3],
            "col_3": ["A", "B", "C"],
        }
    )
    test_data.write_excel(f"{test_dir}/TestDataComma.xlsx")
    # 先にテーブルを作成
    first_request_data = {
        "filePath": f"{test_dir}/TestDataComma.xlsx",
        "tableName": "DuplicateTable",
    }
    client.post("/api/data/import", json=first_request_data)
    # 同じテーブル名で再度作成を試行
    second_request_data = {
        "filePath": f"{test_dir}/TestDataComma.xlsx",
        "tableName": "DuplicateTable",
    }
    response = client.post("/api/data/import", json=second_request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert ErrorCode.DATA_ALREADY_EXISTS == response_data["code"]
    # テーブル名重複エラーメッセージを確認
    message = "tableName 'DuplicateTable'は既に存在します。"
    assert message == response_data["message"]


def test_import_excel_invalid_json(client, prepared_data):
    """
    不正なJSONを送信した場合のテスト
    """
    tables_store, test_dir = prepared_data
    response = client.post(
        "/api/data/import",
        content=b"invalid json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert "JSON decode error" == response_data["message"]


def test_import_excel_with_temporary_file(client, prepared_data):
    """
    一時的なEXCELファイルを作成してインポートするテスト
    """
    tables_store, test_dir = prepared_data
    # 一時的なEXCELファイルを作成
    temp_data = pl.DataFrame(
        {
            "col1": [1, 2, 3, 4, 5],
            "col2": ["A", "B", "C", "D", "E"],
            "col3": [10.1, 20.2, 30.3, 40.4, 50.5],
        }
    )
    with tempfile.NamedTemporaryFile(
        mode="wb", suffix=".xlsx", delete=False
    ) as f:
        temp_data.write_excel(f.name)
        temp_path = f.name
    try:
        # APIリクエスト
        request_data = {"filePath": temp_path, "tableName": "TestTempExcel"}
        response = client.post("/api/data/import", json=request_data)
        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert "OK" == response_data["code"]
        assert "TestTempExcel" == response_data["result"]["tableName"]
        # データの検証
        df = tables_store.get_table("TestTempExcel").table
        assert _TEMP_N_COLS == len(df.columns)
        assert _TEMP_N_ROWS == len(df)
        assert temp_data.equals(df)
    finally:
        # 一時ファイルを削除
        os.unlink(temp_path)


def test_import_excel_empty_file_path(client, prepared_data):
    """
    filePathが空文字列の場合はバリデーションエラーになる
    """
    request_data = {"filePath": "", "tableName": "TestTable"}
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert (
        "filePathは1文字以上で入力してください。" == response_data["message"]
    )
    assert ["filePathは1文字以上で入力してください。"] == response_data[
        "details"
    ]


def test_import_excel_empty_table_name(client, prepared_data):
    """
    tableNameが空文字列の場合はバリデーションエラーになる
    """
    request_data = {"filePath": "/some/path/test.xlsx", "tableName": ""}
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert (
        "tableNameは1文字以上で入力してください。" == response_data["message"]
    )
    assert ["tableNameは1文字以上で入力してください。"] == response_data[
        "details"
    ]


def test_import_excel_tablename_only_spaces(client, prepared_data):
    """
    tableNameがスペースのみの場合はトリムされ空文字列になりエラーになる
    """
    tables_store, test_dir = prepared_data
    request_data = {
        "filePath": "/some/path/test.xlsx",
        "tableName": "   ",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    expected_msg = "tableNameは1文字以上で入力してください。"
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert expected_msg == response_data["message"]
    assert [expected_msg] == response_data["details"]


def test_import_excel_tablename_only_tabs(client, prepared_data):
    """
    tableNameがタブ文字のみの場合はトリムされ空文字列になりエラーになる
    """
    tables_store, test_dir = prepared_data
    request_data = {
        "filePath": "/some/path/test.xlsx",
        "tableName": "\t\t\t",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    expected_msg = "tableNameは1文字以上で入力してください。"
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert expected_msg == response_data["message"]
    assert [expected_msg] == response_data["details"]


def test_import_excel_tablename_embedded_tab(client, prepared_data):
    """
    tableNameにタブ文字が埋め込まれた場合はパターン違反エラーになる
    """
    tables_store, test_dir = prepared_data
    request_data = {
        "filePath": "/some/path/test.xlsx",
        "tableName": "test\ttable",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    expected_msg = "tableNameに使用できない文字が含まれています。"
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert expected_msg == response_data["message"]
    assert [expected_msg] == response_data["details"]


def test_import_excel_tablename_exceeds_max_length(client, prepared_data):
    """
    tableNameが最大文字数（128文字）を超える場合はバリデーションエラーになる
    """
    tables_store, test_dir = prepared_data
    test_data = pl.DataFrame({"col_1": [1, 2, 3]})
    test_data.write_excel(f"{test_dir}/MaxTest.xlsx")
    over_limit = "a" * (_MAX_TABLE_NAME_LEN + 1)
    request_data = {
        "filePath": f"{test_dir}/MaxTest.xlsx",
        "tableName": over_limit,
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    expected_msg = (
        f"tableNameは{_MAX_TABLE_NAME_LEN}文字以内で入力してください。"
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert expected_msg == response_data["message"]
    assert [expected_msg] == response_data["details"]


def test_import_excel_tablename_at_max_length(client, prepared_data):
    """
    tableNameがちょうど最大文字数（128文字）の場合は正常にインポートできる
    """
    tables_store, test_dir = prepared_data
    test_data = pl.DataFrame({"col_1": [1, 2, 3]})
    test_data.write_excel(f"{test_dir}/MaxNameTest.xlsx")
    max_length_name = "a" * _MAX_TABLE_NAME_LEN
    request_data = {
        "filePath": f"{test_dir}/MaxNameTest.xlsx",
        "tableName": max_length_name,
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert max_length_name == response_data["result"]["tableName"]


def test_import_excel_tablename_leading_trailing_spaces(client, prepared_data):
    """
    tableNameの前後にスペースがある場合はトリムされて正常にインポートできる
    """
    tables_store, test_dir = prepared_data
    test_data = pl.DataFrame({"col_1": [1, 2, 3]})
    test_data.write_excel(f"{test_dir}/TrimTest.xlsx")
    request_data = {
        "filePath": f"{test_dir}/TrimTest.xlsx",
        "tableName": "  TrimmedExcelTable  ",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert "TrimmedExcelTable" == response_data["result"]["tableName"]


def test_import_excel_tablename_emoji(client, prepared_data):
    """
    tableNameに絵文字を使った場合は正常にインポートできる
    """
    tables_store, test_dir = prepared_data
    test_data = pl.DataFrame({"col_1": [1, 2, 3]})
    test_data.write_excel(f"{test_dir}/EmojiTest.xlsx")
    request_data = {
        "filePath": f"{test_dir}/EmojiTest.xlsx",
        "tableName": "データ📊テーブル",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert "データ📊テーブル" == response_data["result"]["tableName"]


def test_import_excel_tablename_japanese(client, prepared_data):
    """
    tableNameに日本語を使った場合は正常にインポートできる
    """
    tables_store, test_dir = prepared_data
    test_data = pl.DataFrame({"col_1": [1, 2, 3]})
    test_data.write_excel(f"{test_dir}/JpTest.xlsx")
    request_data = {
        "filePath": f"{test_dir}/JpTest.xlsx",
        "tableName": "人口統計データ",
    }
    response = client.post("/api/data/import", json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert "人口統計データ" == response_data["result"]["tableName"]


def test_import_excel_saves_last_opened_path(
    client, prepared_data, settings_store
):
    """
    Excelインポート成功後に last_opened_path が設定ファイルへ
    保存されるテスト
    """
    tables_store, test_dir = prepared_data
    test_excel = f"{test_dir}/TestLastOpened.xlsx"
    pl.DataFrame({"a": [1, 2]}).write_excel(test_excel)
    request_data = {
        "filePath": test_excel,
        "tableName": "TestLastOpenedExcel",
    }
    response = client.post("/api/data/import", json=request_data)
    assert response.status_code == status.HTTP_200_OK
    # last_opened_path にファイルの親ディレクトリが設定されていることを確認
    expected_path = str(Path(test_excel).parent).replace(os.sep, "/")
    actual_path = settings_store.get_settings().last_opened_path
    assert expected_path == actual_path
