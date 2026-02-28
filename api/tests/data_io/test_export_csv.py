import os
import shutil
import tempfile
from unittest.mock import MagicMock

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
_ENCODING_ERROR = (
    "encodingは次のいずれかである必要があります: "
    "'utf8', 'latin1', 'ascii', 'gbk', 'windows-1252' or 'shift_jis'"
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
    response = client.post(URL, json=request_data)
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
    response = client.post(URL, json=request_data)
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
    response = client.post(URL, json=request_data)
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
    response = client.post(URL, json=request_data)
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
    response = client.post(URL, json=request_data)
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
    response = client.post(URL, json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert ErrorCode.DATA_NOT_FOUND == response_data["code"]
    msg = "tableName 'NonExistentTable'は存在しません。"
    assert msg == response_data["message"]


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
    response = client.post(URL, json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert ErrorCode.PATH_NOT_FOUND == response_data["code"]
    msg = "directoryPath '/non/existent/directory'は存在しません。"
    assert msg == response_data["message"]


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
    response = client.post(URL, json=request_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "tableNameは必須です。" == response_data["message"]
    assert ["tableNameは必須です。"] == response_data["details"]


def test_export_csv_missing_directory_path(client, prepared_data):
    """
    directoryPath が未指定の場合のテスト
    """
    request_data = {
        "tableName": "TestTable",
        "fileName": "test_output",
        "format": "csv",
    }
    response = client.post(URL, json=request_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "directoryPathは必須です。" == response_data["message"]
    assert ["directoryPathは必須です。"] == response_data["details"]


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
    response = client.post(URL, json=request_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "fileNameは必須です。" == response_data["message"]
    assert ["fileNameは必須です。"] == response_data["details"]


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
    response = client.post(URL, json=request_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert "formatは必須です。" == response_data["message"]
    assert ["formatは必須です。"] == response_data["details"]


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
    response = client.post(URL, json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "separatorは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_export_csv_invalid_json(client, prepared_data):
    """
    不正な JSON を送信した場合のテスト
    """
    response = client.post(
        URL,
        content=b"invalid json",
        headers={"Content-Type": "application/json"},
    )
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
    response = client.post(URL, json=request_data)
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
        "format": "csv",
    }
    response = client.post(URL, json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(test_output_dir, "large_output.csv")
    assert output_path == response_data["result"]["filePath"]
    assert os.path.exists(output_path)
    exported_data = pl.read_csv(output_path)
    assert large_data.equals(exported_data)
    assert _LARGE_TABLE_ROWS == len(exported_data)


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
    response = client.post(URL, json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "tableNameは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


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
    response = client.post(URL, json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "directoryPathは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


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
    response = client.post(URL, json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "fileNameは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_export_csv_tablename_only_spaces(client, prepared_data):
    """
    tableName がスペースのみの場合はバリデーションエラーになる
    """
    tables_store, test_output_dir, _ = prepared_data
    request_data = {
        "tableName": "   ",
        "directoryPath": test_output_dir,
        "fileName": "out",
        "format": "csv",
    }
    response = client.post(URL, json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "tableNameは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_export_csv_tablename_leading_trailing_spaces(client, prepared_data):
    """
    tableName の前後スペースはトリムされて既存テーブル名と一致すれば成功する
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        "tableName": "  TestTable  ",
        "directoryPath": test_output_dir,
        "fileName": "out_trimmed",
        "format": "csv",
    }
    response = client.post(URL, json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(test_output_dir, "out_trimmed.csv")
    assert os.path.exists(output_path)


def test_export_csv_tablename_japanese(client, prepared_data):
    """
    日本語テーブル名でエクスポートできる
    """
    tables_store, test_output_dir, test_data = prepared_data
    tables_store.store_table("日本語テーブル", test_data)
    request_data = {
        "tableName": "日本語テーブル",
        "directoryPath": test_output_dir,
        "fileName": "out_jp_table",
        "format": "csv",
    }
    response = client.post(URL, json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(test_output_dir, "out_jp_table.csv")
    assert os.path.exists(output_path)


def test_export_csv_tablename_emoji(client, prepared_data):
    """
    絵文字を含むテーブル名でエクスポートできる
    """
    tables_store, test_output_dir, test_data = prepared_data
    tables_store.store_table("絵文字🎉テーブル", test_data)
    request_data = {
        "tableName": "絵文字🎉テーブル",
        "directoryPath": test_output_dir,
        "fileName": "out_emoji_table",
        "format": "csv",
    }
    response = client.post(URL, json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(test_output_dir, "out_emoji_table.csv")
    assert os.path.exists(output_path)


def test_export_csv_filename_only_spaces(client, prepared_data):
    """
    fileName がスペースのみの場合はバリデーションエラーになる
    """
    tables_store, test_output_dir, _ = prepared_data
    request_data = {
        "tableName": "TestTable",
        "directoryPath": test_output_dir,
        "fileName": "   ",
        "format": "csv",
    }
    response = client.post(URL, json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "fileNameは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_export_csv_filename_max_length(client, prepared_data):
    """
    fileName が境界値付近（_SAFE_FILE_NAME_LEN 文字）のとき成功する
    """
    tables_store, test_output_dir, _ = prepared_data
    safe_file_name = "a" * _SAFE_FILE_NAME_LEN
    request_data = {
        "tableName": "TestTable",
        "directoryPath": test_output_dir,
        "fileName": safe_file_name,
        "format": "csv",
    }
    response = client.post(URL, json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(test_output_dir, f"{safe_file_name}.csv")
    assert os.path.exists(output_path)


def test_export_csv_filename_exceeds_max_length(client, prepared_data):
    """
    fileName が最大文字数（255文字）を超えた場合はバリデーションエラーになる
    """
    tables_store, test_output_dir, _ = prepared_data
    too_long_file_name = "a" * (_MAX_FILE_NAME_LEN + 1)
    request_data = {
        "tableName": "TestTable",
        "directoryPath": test_output_dir,
        "fileName": too_long_file_name,
        "format": "csv",
    }
    response = client.post(URL, json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "fileNameは255文字以内で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_export_csv_filename_leading_trailing_spaces(client, prepared_data):
    """
    fileName の前後スペースはトリムされてエクスポートできる
    """
    tables_store, test_output_dir, _ = prepared_data
    request_data = {
        "tableName": "TestTable",
        "directoryPath": test_output_dir,
        "fileName": "  out_trimmed_fn  ",
        "format": "csv",
    }
    response = client.post(URL, json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(test_output_dir, "out_trimmed_fn.csv")
    assert os.path.exists(output_path)


def test_export_csv_filename_japanese(client, prepared_data):
    """
    日本語ファイル名でエクスポートできる
    """
    tables_store, test_output_dir, _ = prepared_data
    request_data = {
        "tableName": "TestTable",
        "directoryPath": test_output_dir,
        "fileName": "日本語ファイル",
        "format": "csv",
    }
    response = client.post(URL, json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(test_output_dir, "日本語ファイル.csv")
    assert os.path.exists(output_path)


def test_export_csv_directorypath_only_spaces(client, prepared_data):
    """
    directoryPath がスペースのみの場合はバリデーションエラーになる
    """
    tables_store, test_output_dir, _ = prepared_data
    request_data = {
        "tableName": "TestTable",
        "directoryPath": "   ",
        "fileName": "out",
        "format": "csv",
    }
    response = client.post(URL, json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    msg = "directoryPathは1文字以上で入力してください。"
    assert msg == response_data["message"]
    assert [msg] == response_data["details"]


def test_export_csv_invalid_format(client, prepared_data):
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
    response = client.post(URL, json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert _FORMAT_ERROR == response_data["message"]
    assert [_FORMAT_ERROR] == response_data["details"]


# ─────────────────────────────────────────────────────────────
# エンコーディングテスト（異常系）
# ─────────────────────────────────────────────────────────────


def test_export_csv_invalid_encoding(client, prepared_data):
    """
    無効なエンコーディング文字列を指定した場合は 422 VALIDATION_ERROR になる
    """
    tables_store, test_output_dir, _ = prepared_data
    request_data = {
        "tableName": "TestTable",
        "directoryPath": test_output_dir,
        "fileName": "output_bad_enc",
        "format": "csv",
        "encoding": "invalid-enc",
    }
    response = client.post(URL, json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert ErrorCode.VALIDATION_ERROR == response_data["code"]
    assert _ENCODING_ERROR == response_data["message"]
    assert [_ENCODING_ERROR] == response_data["details"]


# ─────────────────────────────────────────────────────────────
# エンコーディングテスト（正常系）
# ─────────────────────────────────────────────────────────────


def test_export_csv_encoding_utf8_explicit(client, prepared_data):
    """
    encoding: utf8 を明示指定してエクスポートできる（デフォルト値の明示確認）
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        "tableName": "TestTable",
        "directoryPath": test_output_dir,
        "fileName": "output_utf8_explicit",
        "format": "csv",
        "encoding": "utf8",
    }
    response = client.post(URL, json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(test_output_dir, "output_utf8_explicit.csv")
    assert os.path.exists(output_path)
    exported_data = pl.read_csv(output_path, encoding="utf8")
    assert test_data.equals(exported_data)


def test_export_csv_encoding_latin1(client, prepared_data):
    """
    latin1 エンコーディングで CSV ファイルをエクスポートでき、
    西欧文字（ウムラウト等）が正しくデコードできる
    """
    tables_store, test_output_dir, _ = prepared_data
    latin1_data = pl.DataFrame(
        {
            "name": ["M\xfcller", "Dupont"],
            "city": ["K\xf6ln", "Paris"],
        }
    )
    tables_store.store_table("Latin1ExportTable", latin1_data)
    request_data = {
        "tableName": "Latin1ExportTable",
        "directoryPath": test_output_dir,
        "fileName": "output_latin1",
        "format": "csv",
        "encoding": "latin1",
    }
    response = client.post(URL, json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(test_output_dir, "output_latin1.csv")
    assert os.path.exists(output_path)
    with open(output_path, encoding="latin1") as f:
        content = f.read()
    assert "M\xfcller" in content
    assert "K\xf6ln" in content


def test_export_csv_encoding_windows1252(client, prepared_data):
    """
    windows-1252 エンコーディングで CSV ファイルをエクスポートでき、
    フランス語のアクセント付き文字が正しくデコードできる
    """
    tables_store, test_output_dir, _ = prepared_data
    win_data = pl.DataFrame(
        {
            "word": ["r\xe9sum\xe9", "caf\xe9"],
            "meaning": ["CV", "drinks"],
        }
    )
    tables_store.store_table("Win1252ExportTable", win_data)
    request_data = {
        "tableName": "Win1252ExportTable",
        "directoryPath": test_output_dir,
        "fileName": "output_win1252",
        "format": "csv",
        "encoding": "windows-1252",
    }
    response = client.post(URL, json=request_data)
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    output_path = os.path.join(test_output_dir, "output_win1252.csv")
    assert os.path.exists(output_path)
    with open(output_path, encoding="windows-1252") as f:
        content = f.read()
    assert "r\xe9sum\xe9" in content
    assert "caf\xe9" in content


# ─────────────────────────────────────────────────────────────
# OSレイヤーI/Oエラーテスト
# ─────────────────────────────────────────────────────────────


def test_export_csv_permission_denied(client, prepared_data):
    """
    書き込み権限エラーが発生した場合は500 PERMISSION_DENIEDを返す
    """
    tables_store, test_output_dir, _ = prepared_data
    table_info = tables_store.get_table("TestTable")
    original_df = table_info.table
    mock_df = MagicMock()
    mock_df.write_csv.side_effect = PermissionError(
        "Permission denied: read-only location"
    )
    table_info.table = mock_df
    try:
        request_data = {
            "tableName": "TestTable",
            "directoryPath": test_output_dir,
            "fileName": "test_perm_error",
            "format": "csv",
        }
        response = client.post(URL, json=request_data)
        response_data = response.json()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert ErrorCode.PERMISSION_DENIED == response_data["code"]
    finally:
        table_info.table = original_df


def test_export_csv_io_error(client, prepared_data):
    """
    汎用IOErrorが発生した場合は500 CSV_EXPORT_ERRORを返す
    """
    tables_store, test_output_dir, _ = prepared_data
    table_info = tables_store.get_table("TestTable")
    original_df = table_info.table
    mock_df = MagicMock()
    mock_df.write_csv.side_effect = OSError("OS error: file name too long")
    table_info.table = mock_df
    try:
        request_data = {
            "tableName": "TestTable",
            "directoryPath": test_output_dir,
            "fileName": "test_io_error",
            "format": "csv",
        }
        response = client.post(URL, json=request_data)
        response_data = response.json()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert ErrorCode.CSV_EXPORT_ERROR == response_data["code"]
    finally:
        table_info.table = original_df
