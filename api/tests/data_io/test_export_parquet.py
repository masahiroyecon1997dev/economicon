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


def test_export_parquet_success(client, prepared_data):
    """
    Parquet ファイルを正常にエクスポートするテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        "tableName": "TestTable",
        "directoryPath": test_output_dir,
        "fileName": "test_output",
        "format": "parquet",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(test_output_dir, "test_output.parquet")
    assert output_path == response_data["result"]["filePath"]
    assert os.path.exists(output_path)
    exported_data = pl.read_parquet(output_path)
    assert test_data.equals(exported_data)


def test_export_parquet_table_not_exists(client, prepared_data):
    """
    存在しないテーブル名を指定した場合のテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        "tableName": "NonExistentTable",
        "directoryPath": test_output_dir,
        "fileName": "test_output",
        "format": "parquet",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "tableName" in response_data["message"]


def test_export_parquet_invalid_output_directory(client, prepared_data):
    """
    存在しない出力ディレクトリを指定した場合のテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        "tableName": "TestTable",
        "directoryPath": "/non/existent/directory",
        "fileName": "test_output",
        "format": "parquet",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "/non/existent/directory" in response_data["message"]


def test_export_parquet_missing_table_name(client, prepared_data):
    """
    tableName が未指定の場合のテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        "directoryPath": test_output_dir,
        "fileName": "test_output",
        "format": "parquet",
    }
    response = client.post(URL, data=json.dumps(request_data))
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert "tableName" in response_data["message"]


def test_export_parquet_missing_directory_path(client, prepared_data):
    """
    directoryPath が未指定の場合のテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        "tableName": "TestTable",
        "fileName": "test_output",
        "format": "parquet",
    }
    response = client.post(URL, data=json.dumps(request_data))
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert "directoryPath" in response_data["message"]


def test_export_parquet_missing_file_name(client, prepared_data):
    """
    fileName が未指定の場合のテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        "tableName": "TestTable",
        "directoryPath": test_output_dir,
        "format": "parquet",
    }
    response = client.post(URL, data=json.dumps(request_data))
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert "fileName" in response_data["message"]


def test_export_parquet_missing_format(client, prepared_data):
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


def test_export_parquet_invalid_json(client, prepared_data):
    """
    不正な JSON を送信した場合のテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    response = client.post(URL, data="invalid json")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert "JSON decode error" == response_data["message"]


def test_export_parquet_empty_table(client, prepared_data):
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
        "format": "parquet",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(test_output_dir, "empty_output.parquet")
    assert output_path == response_data["result"]["filePath"]
    assert os.path.exists(output_path)
    exported_data = pl.read_parquet(output_path)
    assert empty_data.equals(exported_data)


def test_export_parquet_large_table(client, prepared_data):
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
        "format": "parquet",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(test_output_dir, "large_output.parquet")
    assert output_path == response_data["result"]["filePath"]
    assert os.path.exists(output_path)
    exported_data = pl.read_parquet(output_path)
    assert large_data.equals(exported_data)
    assert 1000 == len(exported_data)


def test_export_parquet_special_characters(client, prepared_data):
    """
    特殊文字を含むデータをエクスポートするテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    special_data = pl.DataFrame(
        {
            "text": ["Hello, 世界", "こんにちは", "αβγ", "123@#$"],
            "numbers": [1.1, 2.2, 3.3, 4.4],
            "unicode": ["🌟", "💻", "🐍", "📊"],
        }
    )
    tables_store.store_table("SpecialTable", special_data)
    request_data = {
        "tableName": "SpecialTable",
        "directoryPath": test_output_dir,
        "fileName": "special_output",
        "format": "parquet",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(test_output_dir, "special_output.parquet")
    assert output_path == response_data["result"]["filePath"]
    assert os.path.exists(output_path)
    exported_data = pl.read_parquet(output_path)
    assert special_data.equals(exported_data)


def test_export_parquet_different_data_types(client, prepared_data):
    """
    異なるデータ型を含むテーブルをエクスポートするテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    mixed_data = pl.DataFrame(
        {
            "integers": [1, 2, 3, 4],
            "floats": [1.1, 2.2, 3.3, 4.4],
            "strings": ["a", "b", "c", "d"],
            "booleans": [True, False, True, False],
        }
    )
    tables_store.store_table("MixedTable", mixed_data)
    request_data = {
        "tableName": "MixedTable",
        "directoryPath": test_output_dir,
        "fileName": "mixed_output",
        "format": "parquet",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(test_output_dir, "mixed_output.parquet")
    assert output_path == response_data["result"]["filePath"]
    assert os.path.exists(output_path)
    exported_data = pl.read_parquet(output_path)
    assert mixed_data.equals(exported_data)


def test_export_parquet_empty_table_name(client, prepared_data):
    """
    tableName が空文字列の場合はバリデーションエラーになる
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        "tableName": "",
        "directoryPath": test_output_dir,
        "fileName": "test_output",
        "format": "parquet",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "tableName" in response_data["message"]


def test_export_parquet_empty_directory_path(client, prepared_data):
    """
    directoryPath が空文字列の場合はバリデーションエラーになる
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        "tableName": "TestTable",
        "directoryPath": "",
        "fileName": "test_output",
        "format": "parquet",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "directoryPath" in response_data["message"]


def test_export_parquet_empty_file_name(client, prepared_data):
    """
    fileNameが空文字列の場合はバリデーションエラーになる
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        "tableName": "TestTable",
        "directoryPath": test_output_dir,
        "fileName": "",
        "format": "parquet",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "fileName" in response_data["message"]
