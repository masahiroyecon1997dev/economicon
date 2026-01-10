import json
import os
import shutil
import tempfile

import polars as pl
import pytest
from analysisapp.services.data.tables_manager import TablesManager
from fastapi import status
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def prepared_data():
    """TablesManagerのフィクスチャ"""
    manager = TablesManager()
    manager.clear_tables()
    # テスト用のテーブルデータを作成
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    manager.store_table('TestTable', test_data)
    # テスト用の出力ディレクトリ
    test_output_dir = tempfile.mkdtemp()
    yield manager, test_output_dir, test_data
    # テスト後のクリーンアップ
    manager.clear_tables()
    # テスト後にテンポラリディレクトリをクリーンアップ
    shutil.rmtree(test_output_dir, ignore_errors=True)


def test_export_csv_by_path_default_separator(client, prepared_data):
    """
    デフォルトのカンマ区切りでCSVファイルをエクスポートするテスト
    """
    tables_manager, test_output_dir, test_data = prepared_data
    # APIリクエスト
    request_data = {
        'tableName': 'TestTable',
        'directoryPath': test_output_dir,
        'fileName': 'test_output.csv'
    }
    response = client.post('/api/data/export-csv-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    output_path = os.path.join(test_output_dir, 'test_output.csv')
    assert output_path == response_data['result']['filePath']
    # ファイルが作成されているかチェック
    assert os.path.exists(output_path)
    # 出力されたCSVファイルの内容を検証
    exported_data = pl.read_csv(output_path)
    assert test_data.equals(exported_data)


def test_export_csv_by_path_custom_separator(client, prepared_data):
    """
    タブ区切りでCSVファイルをエクスポートするテスト
    """
    tables_manager, test_output_dir, test_data = prepared_data
    # APIリクエスト
    request_data = {
        'tableName': 'TestTable',
        'directoryPath': test_output_dir,
        'fileName': 'test_output_tab.csv',
        'separator': '\t'
    }
    response = client.post('/api/data/export-csv-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    output_path = os.path.join(test_output_dir, 'test_output_tab.csv')
    assert output_path == response_data['result']['filePath']
    # ファイルが作成されているかチェック
    assert os.path.exists(output_path)
    # 出力されたCSVファイルの内容を検証（タブ区切り）
    exported_data = pl.read_csv(output_path, separator='\t')
    assert test_data.equals(exported_data)


def test_export_csv_by_path_semicolon_separator(client, prepared_data):
    """
    セミコロン区切りでCSVファイルをエクスポートするテスト
    """
    tables_manager, test_output_dir, test_data = prepared_data
    # APIリクエスト
    request_data = {
        'tableName': 'TestTable',
        'directoryPath': test_output_dir,
        'fileName': 'test_output_semicolon.csv',
        'separator': ';'
    }
    response = client.post('/api/data/export-csv-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    output_path = os.path.join(test_output_dir,
                               'test_output_semicolon.csv')
    assert output_path == response_data['result']['filePath']
    # ファイルが作成されているかチェック
    assert os.path.exists(output_path)
    # 出力されたCSVファイルの内容を検証（セミコロン区切り）
    exported_data = pl.read_csv(output_path, separator=';')
    assert test_data.equals(exported_data)


def test_export_csv_by_path_table_not_exists(client, prepared_data):
    """
    存在しないテーブル名を指定した場合のテスト
    """
    tables_manager, test_output_dir, test_data = prepared_data
    request_data = {
        'tableName': 'NonExistentTable',
        'directoryPath': test_output_dir,
        'fileName': 'test_output.csv',
    }
    response = client.post('/api/data/export-csv-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    message = "tableName 'NonExistentTable' does not exist."
    assert message == response_data['message']


def test_export_csv_by_path_invalid_output_directory(client, prepared_data):
    """
    存在しない出力ディレクトリを指定した場合のテスト
    """
    tables_manager, test_output_dir, test_data = prepared_data
    request_data = {
        'tableName': 'TestTable',
        'directoryPath': '/non/existent/directory',
        'fileName': 'test_output.csv'
    }
    response = client.post('/api/data/export-csv-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    message = "Directory does not exist: /non/existent/directory"
    assert message == response_data['message']


def test_export_csv_by_path_missing_table_name(client, prepared_data):
    """
    tableNameパラメータが未指定の場合のテスト
    """
    tables_manager, test_output_dir, test_data = prepared_data
    request_data = {
        'directoryPath': test_output_dir,
        'fileName': 'test_output.csv'
    }
    response = client.post('/api/data/export-csv-by-path',
                           data=json.dumps(request_data))
    # response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    # assert 'NG' == response_data['code']
    # assert "tableName is required" == response_data['message']


def test_export_csv_by_path_missing_directory_path(client, prepared_data):
    """
    directoryPathパラメータが未指定の場合のテスト
    """
    request_data = {
        'tableName': 'TestTable',
        'fileName': 'test_output.csv'
    }
    response = client.post('/api/data/export-csv-by-path',
                           data=json.dumps(request_data))
    # response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    # assert 'NG' == response_data['code']
    # assert "directoryPath is required" == response_data['message']


def test_export_csv_by_path_missing_file_name(client, prepared_data):
    """
    fileNameパラメータが未指定の場合のテスト
    """
    tables_manager, test_output_dir, test_data = prepared_data
    request_data = {
        'tableName': 'TestTable',
        'directoryPath': test_output_dir,
    }
    response = client.post('/api/data/export-csv-by-path',
                           data=json.dumps(request_data))
    # response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    # assert 'NG' == response_data['code']
    # assert "fileName is required" == response_data['message']


def test_export_csv_by_path_empty_separator(client, prepared_data):
    """
    空の区切り文字を指定した場合のテスト
    """
    tables_manager, test_output_dir, test_data = prepared_data
    request_data = {
        'tableName': 'TestTable',
        'directoryPath': test_output_dir,
        'fileName': 'test_output_empty_separator.csv',
        'separator': ''
    }
    response = client.post('/api/data/export-csv-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    message = "separator must be at least 1 characters long."
    assert message == response_data['message']


def test_export_csv_by_path_invalid_json(client, prepared_data):
    """
    不正なJSONを送信した場合のテスト
    """
    response = client.post('/api/data/export-csv-by-path',
                           data='invalid json')
    # response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    # assert 'NG' == response_data['code']
    # assert "Invalid JSON format" == response_data['message']


def test_export_csv_by_path_empty_table(client, prepared_data):
    """
    空のテーブルをエクスポートする場合のテスト
    """
    tables_manager, test_output_dir, test_data = prepared_data
    # 空のテーブルを作成
    empty_data = pl.DataFrame({'col1': [], 'col2': []})
    tables_manager.store_table('EmptyTable', empty_data)
    request_data = {
        'tableName': 'EmptyTable',
        'directoryPath': test_output_dir,
        'fileName': 'empty_output.csv'
    }
    response = client.post('/api/data/export-csv-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    output_path = os.path.join(test_output_dir, 'empty_output.csv')
    assert output_path == response_data['result']['filePath']
    # ファイルが作成されているかチェック
    assert os.path.exists(output_path)
    # 出力されたCSVファイルの内容を検証（空のデータ）
    exported_data = pl.read_csv(output_path)
    assert empty_data.equals(exported_data)


def test_export_csv_by_path_large_table(client, prepared_data):
    """
    大きなテーブルをエクスポートする場合のテスト
    """
    tables_manager, test_output_dir, test_data = prepared_data
    # 大きなテーブルを作成
    large_data = pl.DataFrame({
        'id': list(range(1000)),
        'value': [f'value_{i}' for i in range(1000)],
        'number': [i * 1.5 for i in range(1000)]
    })
    tables_manager.store_table('LargeTable', large_data)
    request_data = {
        'tableName': 'LargeTable',
        'directoryPath': test_output_dir,
        'fileName': 'large_output.csv'
    }
    response = client.post('/api/data/export-csv-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    output_path = os.path.join(test_output_dir, 'large_output.csv')
    assert output_path == response_data['result']['filePath']
    # ファイルが作成されているかチェック
    assert os.path.exists(output_path)
    # 出力されたCSVファイルの内容を検証
    exported_data = pl.read_csv(output_path)
    assert large_data.equals(exported_data)
    assert 1000 == len(exported_data)
