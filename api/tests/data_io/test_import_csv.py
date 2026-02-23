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


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def prepared_data():
    """TablesStoreのフィクスチャ"""
    manager = TablesStore()
    manager.clear_tables()
    # テスト用のCSVファイルパス
    test_data = pl.DataFrame(
        {
            "col_1": [1, 2, 3],
            "col_2": [10.1, 20.2, 30.3],
            "col_3": ["A", "B", "C"],
        }
    )
    # テスト用の出力ディレクトリ
    test_dir = tempfile.mkdtemp()
    test_data.write_csv(f"{test_dir}/TestDataComma.csv", separator=",")
    test_data.write_csv(f"{test_dir}/TestDataTab1.tsv", separator="\t")
    with open(f"{test_dir}/Empty.csv", "w", encoding="utf-8"):
        pass
    test_data.write_excel(f"{test_dir}/TestDataXlsx.xlsx")
    yield manager, test_dir
    # テスト後のクリーンアップ
    manager.clear_tables()
    # テスト後にテンポラリディレクトリをクリーンアップ
    shutil.rmtree(test_dir, ignore_errors=True)


def test_import_csv_comma_separator(client, prepared_data):
    """
    カンマ区切りのCSVファイルをパス指定でインポートするテスト
    """
    tables_store, test_dir = prepared_data
    test_csv_comma = f"{test_dir}/TestDataComma.csv"
    # 期待データをPolarsで読み込み
    expected_data = pl.read_csv(test_csv_comma, encoding="utf8")
    # APIリクエスト
    request_data = {
        "filePath": test_csv_comma,
        "tableName": "TestCommaTable",
        "separator": ",",
    }
    response = client.post("/api/data/import", data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert "TestCommaTable" == response_data["result"]["tableName"]
    # データの検証
    df = tables_store.get_table("TestCommaTable").table
    assert expected_data.equals(df)


def test_import_csv_tab_separator(client, prepared_data):
    """
    タブ区切りのファイルをCSVとしてパス指定でインポートするテスト
    """
    tables_store, test_dir = prepared_data
    test_csv_tab = f"{test_dir}/TestDataTab1.tsv"
    # 期待データをPolarsで読み込み
    expected_data = pl.read_csv(test_csv_tab, separator="\t", encoding="utf8")
    # APIリクエスト
    request_data = {
        "filePath": test_csv_tab,
        "tableName": "TestTabTable",
        "separator": "\t",
    }
    response = client.post("/api/data/import", data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert "TestTabTable" == response_data["result"]["tableName"]
    # データの検証
    df = tables_store.get_table("TestTabTable").table
    assert expected_data.equals(df)


def test_import_csv_custom_separator(client, prepared_data):
    """
    セミコロン区切りのCSVファイルのテスト（テストファイルを作成）
    """
    tables_store, test_dir = prepared_data
    # 一時的なセミコロン区切りファイルを作成
    temp_data = "col1;col2;col3\n1;2;3\n4;5;6\n"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False
    ) as f:
        f.write(temp_data)
        temp_path = f.name
    try:
        # APIリクエスト
        request_data = {
            "filePath": temp_path,
            "tableName": "TestSemicolonTable",
            "separator": ";",
        }
        response = client.post(
            "/api/data/import", data=json.dumps(request_data)
        )
        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert "OK" == response_data["code"]
        assert "TestSemicolonTable" == response_data["result"]["tableName"]
        # データの検証
        df = tables_store.get_table("TestSemicolonTable").table
        assert 3 == len(df.columns)
        assert 2 == len(df)
    finally:
        # 一時ファイルを削除
        os.unlink(temp_path)


def test_import_csv_default_separator(client, prepared_data):
    """
    separatorパラメータを省略した場合のテスト（デフォルトはカンマ）
    """
    tables_store, test_dir = prepared_data
    test_csv_comma = f"{test_dir}/TestDataComma.csv"
    # 期待データをPolarsで読み込み
    expected_data = pl.read_csv(test_csv_comma, encoding="utf8")
    # APIリクエスト（separatorを省略）
    request_data = {
        "filePath": test_csv_comma,
        "tableName": "TestDefaultSeparator",
    }
    response = client.post("/api/data/import", data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert "TestDefaultSeparator" == response_data["result"]["tableName"]
    # データの検証
    df = tables_store.get_table("TestDefaultSeparator").table
    assert expected_data.equals(df)


def test_import_csv_file_not_exists(client, prepared_data):
    """
    存在しないファイルパスを指定した場合のテスト
    """
    tables_store, test_dir = prepared_data
    request_data = {
        "filePath": "/non/existent/file.csv",
        "tableName": "TestNonExistent",
        "separator": ",",
    }
    response = client.post("/api/data/import", data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    message = "filePath '/non/existent/file.csv'は存在しません。"
    assert message == response_data["message"]


def test_import_csv_invalid_file_extension(client, prepared_data):
    """
    非対応拡張子（.txt）を指定した場合のテスト
    統合 /import エンドポイントでサポート外拡張子は 500 が返る
    """
    tables_store, test_dir = prepared_data
    # 非対応拡張子のファイルを作成
    txt_path = f"{test_dir}/unsupported.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("col1,col2\n1,2\n")
    request_data = {
        "filePath": txt_path,
        "tableName": "TestInvalidExtension",
    }
    response = client.post("/api/data/import", data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_import_csv_missing_file_path(client, prepared_data):
    """
    filePathパラメータが未指定の場合のテスト
    FastAPIのバリデーションエラーで422が返る
    """
    tables_store, test_dir = prepared_data
    request_data = {"tableName": "TestMissingPath", "separator": ","}
    response = client.post("/api/data/import", data=json.dumps(request_data))
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert "filePathは必須項目です。" == response_data["message"]


def test_import_csv_missing_table_name(client, prepared_data):
    """
    tableNameパラメータが未指定の場合のテスト
    FastAPIのバリデーションエラーで422が返る
    """
    tables_store, test_dir = prepared_data
    test_csv_comma = f"{test_dir}/TestDataComma.csv"
    request_data = {"filePath": test_csv_comma, "separator": ","}
    response = client.post("/api/data/import", data=json.dumps(request_data))
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert "tableNameは必須項目です。" == response_data["message"]


def test_import_csv_duplicate_table_name(client, prepared_data):
    """
    既存のテーブル名と重複する場合のテスト
    """
    tables_store, test_dir = prepared_data
    test_csv_comma = f"{test_dir}/TestDataComma.csv"
    # 先にテーブルを作成
    first_request_data = {
        "filePath": test_csv_comma,
        "tableName": "DuplicateTable",
        "separator": ",",
    }
    client.post("/api/data/import", data=json.dumps(first_request_data))
    # 同じテーブル名で再度作成を試行
    second_request_data = {
        "filePath": test_csv_comma,
        "tableName": "DuplicateTable",
        "separator": ",",
    }
    response = client.post(
        "/api/data/import", data=json.dumps(second_request_data)
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    # テーブル名重複エラーメッセージを確認
    message = "tableName 'DuplicateTable'は既に存在します。"
    assert message == response_data["message"]


def test_import_csv_empty_separator(client, prepared_data):
    """
    空の区切り文字を指定した場合のテスト
    """
    tables_store, test_dir = prepared_data
    test_csv_comma = f"{test_dir}/TestDataComma.csv"
    request_data = {
        "filePath": test_csv_comma,
        "tableName": "TestEmptySeparator",
        "separator": "",
    }
    response = client.post("/api/data/import", data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    message = "separatorは1文字以上で入力してください。"
    assert message == response_data["message"]


def test_import_csv_invalid_json(client, prepared_data):
    """
    不正なJSONを送信した場合のテスト
    FastAPIのバリデーションエラーで422が返る
    """
    response = client.post("/api/data/import", data="invalid json")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert "JSON decode error" == response_data["message"]


@pytest.mark.skip(
    reason="このテストは現在、発生させる方法が不明なためスキップされています。"
)
def test_import_csv_malformed_csv(client, prepared_data):
    """
    不正な形式のCSVファイルを指定した場合のテスト
    """
    # エラーCSVファイルが存在する場合
    request_data = {
        "filePath": "/ECONOMICON/SampleData/Error.csv",
        "tableName": "TestMalformed",
        "separator": ",",
    }
    response = client.post("/api/data/import", data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    message = "Failed to parse CSV file: Invalid format or encoding."
    assert message == response_data["message"]


def test_import_csv_encoding_utf8bom(client, prepared_data):
    """
    UTF-8 BOM エンコーディングの CSV ファイルをインポートするテスト
    （Polars は utf8 エンコーディングで BOM を自動処理する）
    """
    tables_store, test_dir = prepared_data
    bom_path = f"{test_dir}/TestBom.csv"
    with open(bom_path, "w", encoding="utf-8-sig") as f:
        f.write("col_1,col_2\n1,10\n2,20\n")
    request_data = {
        "filePath": bom_path,
        "tableName": "TestBomTable",
        "separator": ",",
        "encoding": "utf8",
    }
    response = client.post("/api/data/import", data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert "TestBomTable" == response_data["result"]["tableName"]
    df = tables_store.get_table("TestBomTable").table
    assert 2 == len(df.columns)
    assert 2 == len(df)


def test_import_csv_invalid_encoding(client, prepared_data):
    """
    無効なエンコーディングを指定した場合はバリデーションエラーになる
    """
    tables_store, test_dir = prepared_data
    test_csv = f"{test_dir}/TestDataComma.csv"
    request_data = {
        "filePath": test_csv,
        "tableName": "TestInvalidEncoding",
        "encoding": "invalid-encoding",
    }
    response = client.post("/api/data/import", data=json.dumps(request_data))
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_import_csv_empty_file_path(client, prepared_data):
    """
    filePathが空文字列の場合はバリデーションエラーになる
    """
    request_data = {"filePath": "", "tableName": "TestTable", "separator": ","}
    response = client.post("/api/data/import", data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "filePath" in response_data["message"]


def test_import_csv_empty_table_name(client, prepared_data):
    """
    tableNameが空文字列の場合はバリデーションエラーになる
    """
    request_data = {
        "filePath": "/some/path/test.csv",
        "tableName": "",
        "separator": ",",
    }
    response = client.post("/api/data/import", data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "tableName" in response_data["message"]
