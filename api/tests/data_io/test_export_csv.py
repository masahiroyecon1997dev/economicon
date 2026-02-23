import json
import os
import shutil
import tempfile

import polars as pl
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.services.data.tables_store import TablesStore
from main import app

URL = "/api/data/export"


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def prepared_data():
    """TablesStoreのフィクスチャ"""
    manager = TablesStore()
    manager.clear_tables()
    test_data = pl.DataFrame(
        {
            "col_1": [1, 2, 3],
            "col_2": [10.1, 20.2, 30.3],
            "col_3": ["A", "B", "C"],
        }
    )
    manager.store_table("TestTable", test_data)
    test_output_dir = tempfile.mkdtemp()
    yield manager, test_output_dir, test_data
    manager.clear_tables()
    shutil.rmtree(test_output_dir, ignore_errors=True)


def test_export_csv_default_separator(client, prepared_data):
    """
    デフォルトのカンマ区切りで CSV ファイルをエクスポートするテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        "tableName": "TestTable",
        "directoryPath": test_output_dir,
        "fileName": "test_output",
        "format": "csv",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(test_output_dir, "test_output.csv")
    assert output_path == response_data["result"]["filePath"]
    assert os.path.exists(output_path)
    exported_data = pl.read_csv(output_path)
    assert test_data.equals(exported_data)


def test_export_csv_custom_separator(client, prepared_data):
    """
    タブ区切りで CSV ファイルをエクスポートするテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        "tableName": "TestTable",
        "directoryPath": test_output_dir,
        "fileName": "test_output_tab",
        "format": "csv",
        "separator": "\t",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(test_output_dir, "test_output_tab.csv")
    assert output_path == response_data["result"]["filePath"]
    assert os.path.exists(output_path)
    exported_data = pl.read_csv(output_path, separator="\t")
    assert test_data.equals(exported_data)


def test_export_csv_semicolon_separator(client, prepared_data):
    """
    セミコロン区切りで CSV ファイルをエクスポートするテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        "tableName": "TestTable",
        "directoryPath": test_output_dir,
        "fileName": "test_output_semicolon",
        "format": "csv",
        "separator": ";",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(test_output_dir, "test_output_semicolon.csv")
    assert output_path == response_data["result"]["filePath"]
    assert os.path.exists(output_path)
    exported_data = pl.read_csv(output_path, separator=";")
    assert test_data.equals(exported_data)


def test_export_csv_no_header(client, prepared_data):
    """
    ヘッダなしで CSV ファイルをエクスポートするテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        "tableName": "TestTable",
        "directoryPath": test_output_dir,
        "fileName": "test_output_no_header",
        "format": "csv",
        "includeHeader": False,
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(test_output_dir, "test_output_no_header.csv")
    assert output_path == response_data["result"]["filePath"]
    assert os.path.exists(output_path)
    # ヘッダなしで読み込んで行数を検証
    exported_data = pl.read_csv(output_path, has_header=False)
    assert len(test_data) == len(exported_data)


def test_export_csv_encoding_shift_jis(client, prepared_data):
    """
    Shift-JIS エンコーディングで CSV ファイルをエクスポートするテスト
    """
    tables_store, test_output_dir, _ = prepared_data
    # Shift-JIS で扱える日本語データ
    jp_data = pl.DataFrame(
        {
            "名前": ["山田", "田中", "鈴木"],
            "年齢": [30, 25, 40],
        }
    )
    tables_store.store_table("JpTable", jp_data)
    request_data = {
        "tableName": "JpTable",
        "directoryPath": test_output_dir,
        "fileName": "output_sjis",
        "format": "csv",
        "encoding": "shift_jis",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(test_output_dir, "output_sjis.csv")
    assert output_path == response_data["result"]["filePath"]
    assert os.path.exists(output_path)
    # CP932 (Shift-JIS) でデコードしてデータを検証
    with open(output_path, encoding="cp932") as f:
        content = f.read()
    assert "名前" in content
    assert "山田" in content


def test_export_csv_table_not_exists(client, prepared_data):
    """
    存在しないテーブル名を指定した場合のテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        "tableName": "NonExistentTable",
        "directoryPath": test_output_dir,
        "fileName": "test_output",
        "format": "csv",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "tableName" in response_data["message"]


def test_export_csv_invalid_output_directory(client, prepared_data):
    """
    存在しない出力ディレクトリを指定した場合のテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        "tableName": "TestTable",
        "directoryPath": "/non/existent/directory",
        "fileName": "test_output",
        "format": "csv",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "/non/existent/directory" in response_data["message"]


def test_export_csv_missing_table_name(client, prepared_data):
    """
    tableName が未指定の場合のテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        "directoryPath": test_output_dir,
        "fileName": "test_output",
        "format": "csv",
    }
    response = client.post(URL, data=json.dumps(request_data))
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert "tableName" in response_data["message"]


def test_export_csv_missing_directory_path(client, prepared_data):
    """
    directoryPath が未指定の場合のテスト
    """
    request_data = {
        "tableName": "TestTable",
        "fileName": "test_output",
        "format": "csv",
    }
    response = client.post(URL, data=json.dumps(request_data))
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert "directoryPath" in response_data["message"]


def test_export_csv_missing_file_name(client, prepared_data):
    """
    fileName が未指定の場合のテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        "tableName": "TestTable",
        "directoryPath": test_output_dir,
        "format": "csv",
    }
    response = client.post(URL, data=json.dumps(request_data))
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert "fileName" in response_data["message"]


def test_export_csv_missing_format(client, prepared_data):
    """
    format が未指定の場合のテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        "tableName": "TestTable",
        "directoryPath": test_output_dir,
        "fileName": "test_output",
    }
    response = client.post(URL, data=json.dumps(request_data))
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert "format" in response_data["message"]


def test_export_csv_empty_separator(client, prepared_data):
    """
    空の区切り文字を指定した場合はバリデーションエラーになる
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        "tableName": "TestTable",
        "directoryPath": test_output_dir,
        "fileName": "test_output_empty_separator",
        "format": "csv",
        "separator": "",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "separator" in response_data["message"]


def test_export_csv_invalid_json(client, prepared_data):
    """
    不正な JSON を送信した場合のテスト
    """
    response = client.post(URL, data="invalid json")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert "JSON decode error" == response_data["message"]


def test_export_csv_empty_table(client, prepared_data):
    """
    空のテーブルをエクスポートするテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    empty_data = pl.DataFrame({"col1": [], "col2": []})
    tables_store.store_table("EmptyTable", empty_data)
    request_data = {
        "tableName": "EmptyTable",
        "directoryPath": test_output_dir,
        "fileName": "empty_output",
        "format": "csv",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(test_output_dir, "empty_output.csv")
    assert output_path == response_data["result"]["filePath"]
    assert os.path.exists(output_path)
    exported_data = pl.read_csv(output_path)
    assert empty_data.equals(exported_data)


def test_export_csv_large_table(client, prepared_data):
    """
    大きなテーブルをエクスポートするテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    large_data = pl.DataFrame(
        {
            "id": list(range(1000)),
            "value": [f"value_{i}" for i in range(1000)],
            "number": [i * 1.5 for i in range(1000)],
        }
    )
    tables_store.store_table("LargeTable", large_data)
    request_data = {
        "tableName": "LargeTable",
        "directoryPath": test_output_dir,
        "fileName": "large_output",
        "format": "csv",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(test_output_dir, "large_output.csv")
    assert output_path == response_data["result"]["filePath"]
    assert os.path.exists(output_path)
    exported_data = pl.read_csv(output_path)
    assert large_data.equals(exported_data)
    assert 1000 == len(exported_data)


def test_export_csv_empty_table_name(client, prepared_data):
    """
    tableName が空文字列の場合はバリデーションエラーになる
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        "tableName": "",
        "directoryPath": test_output_dir,
        "fileName": "test_output",
        "format": "csv",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "tableName" in response_data["message"]


def test_export_csv_empty_directory_path(client, prepared_data):
    """
    directoryPath が空文字列の場合はバリデーションエラーになる
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        "tableName": "TestTable",
        "directoryPath": "",
        "fileName": "test_output",
        "format": "csv",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "directoryPath" in response_data["message"]


def test_export_csv_empty_file_name(client, prepared_data):
    """
    fileName が空文字列の場合はバリデーションエラーになる
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        "tableName": "TestTable",
        "directoryPath": test_output_dir,
        "fileName": "",
        "format": "csv",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "fileName" in response_data["message"]
