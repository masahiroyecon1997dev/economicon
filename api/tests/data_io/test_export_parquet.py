import json
import os
import shutil
import tempfile

import polars as pl
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.core.enums import ErrorCode
from economicon.services.data.tables_store import TablesStore
from main import app

URL = "/api/data/export"

# テストデータの定数
_LARGE_TABLE_ROWS = 1000  # 大規模テーブルの行数
_MAX_FILE_NAME_LEN = 255  # ファイル名の最大文字数（Pydantic型上の制限）
_SAFE_FILE_NAME_LEN = 100  # OSファイルパス長制限を考慮した安全なテスト用長さ
_FORMAT_ERROR = (
    "formatは次のいずれかである必要があります: 'csv', 'excel' or 'parquet'"
)


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
    assert ErrorCode.DATA_NOT_FOUND == response_data["code"]
    msg = "tableName 'NonExistentTable'は存在しません。"
    assert msg == response_data["message"]


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
    assert ErrorCode.PATH_NOT_FOUND == response_data["code"]
    msg = "directoryPath '/non/existent/directory'は存在しません。"
    assert msg == response_data["message"]


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
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "tableNameは必須項目です。" == response_data["message"]
    assert ["tableNameは必須項目です。"] == response_data["details"]


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
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "directoryPathは必須項目です。" == response_data["message"]
    assert ["directoryPathは必須項目です。"] == response_data["details"]


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
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "fileNameは必須項目です。" == response_data["message"]
    assert ["fileNameは必須項目です。"] == response_data["details"]


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
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "formatは必須項目です。" == response_data["message"]
    assert ["formatは必須項目です。"] == response_data["details"]


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
            "id": list(range(_LARGE_TABLE_ROWS)),
            "value": [f"value_{i}" for i in range(_LARGE_TABLE_ROWS)],
            "number": [i * 1.5 for i in range(_LARGE_TABLE_ROWS)],
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
    assert _LARGE_TABLE_ROWS == len(exported_data)


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
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "tableNameは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


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
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "directoryPathは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


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
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "fileNameは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_export_parquet_tablename_only_spaces(client, prepared_data):
    """
    tableName がスペースのみの場合はバリデーションエラーになる
    """
    tables_store, test_output_dir, _ = prepared_data
    request_data = {
        "tableName": "   ",
        "directoryPath": test_output_dir,
        "fileName": "out",
        "format": "parquet",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "tableNameは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_export_parquet_tablename_leading_trailing_spaces(
    client, prepared_data
):
    """
    tableName の前後スペースはトリムされて既存テーブル名と一致すれば成功する
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        "tableName": "  TestTable  ",
        "directoryPath": test_output_dir,
        "fileName": "out_trimmed",
        "format": "parquet",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(test_output_dir, "out_trimmed.parquet")
    assert os.path.exists(output_path)


def test_export_parquet_tablename_japanese(client, prepared_data):
    """
    日本語テーブル名でエクスポートできる
    """
    tables_store, test_output_dir, test_data = prepared_data
    tables_store.store_table("日本語テーブル", test_data)
    request_data = {
        "tableName": "日本語テーブル",
        "directoryPath": test_output_dir,
        "fileName": "out_jp_table",
        "format": "parquet",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(test_output_dir, "out_jp_table.parquet")
    assert os.path.exists(output_path)


def test_export_parquet_tablename_emoji(client, prepared_data):
    """
    絵文字を含むテーブル名でエクスポートできる
    """
    tables_store, test_output_dir, test_data = prepared_data
    tables_store.store_table("絵文字🎉テーブル", test_data)
    request_data = {
        "tableName": "絵文字🎉テーブル",
        "directoryPath": test_output_dir,
        "fileName": "out_emoji_table",
        "format": "parquet",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(test_output_dir, "out_emoji_table.parquet")
    assert os.path.exists(output_path)


def test_export_parquet_filename_only_spaces(client, prepared_data):
    """
    fileName がスペースのみの場合はバリデーションエラーになる
    """
    tables_store, test_output_dir, _ = prepared_data
    request_data = {
        "tableName": "TestTable",
        "directoryPath": test_output_dir,
        "fileName": "   ",
        "format": "parquet",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "fileNameは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_export_parquet_filename_max_length(client, prepared_data):
    """
    fileName が境界値付近（_SAFE_FILE_NAME_LEN 文字）のとき成功する
    """
    tables_store, test_output_dir, _ = prepared_data
    safe_file_name = "a" * _SAFE_FILE_NAME_LEN
    request_data = {
        "tableName": "TestTable",
        "directoryPath": test_output_dir,
        "fileName": safe_file_name,
        "format": "parquet",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(
        test_output_dir, f"{safe_file_name}.parquet"
    )
    assert os.path.exists(output_path)


def test_export_parquet_filename_exceeds_max_length(client, prepared_data):
    """
    fileName が最大文字数（255文字）を超えた場合はバリデーションエラーになる
    """
    tables_store, test_output_dir, _ = prepared_data
    too_long_file_name = "a" * (_MAX_FILE_NAME_LEN + 1)
    request_data = {
        "tableName": "TestTable",
        "directoryPath": test_output_dir,
        "fileName": too_long_file_name,
        "format": "parquet",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "fileNameは255文字以内で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_export_parquet_directorypath_only_spaces(client, prepared_data):
    """
    directoryPath がスペースのみの場合はバリデーションエラーになる
    """
    tables_store, test_output_dir, _ = prepared_data
    request_data = {
        "tableName": "TestTable",
        "directoryPath": "   ",
        "fileName": "out",
        "format": "parquet",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "directoryPathは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_export_parquet_invalid_format(client, prepared_data):
    """
    format に無効な値を指定した場合はバリデーションエラーになる
    """
    tables_store, test_output_dir, _ = prepared_data
    request_data = {
        "tableName": "TestTable",
        "directoryPath": test_output_dir,
        "fileName": "out",
        "format": "xml",
    }
    response = client.post(URL, data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert _FORMAT_ERROR == response_data["message"]
    assert [_FORMAT_ERROR] == response_data["details"]
