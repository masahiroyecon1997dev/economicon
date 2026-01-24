import json
import os
import shutil
import tempfile

import polars as pl
import pytest
from analysisapp.services.data.tables_store import TablesStore
from fastapi import status
from fastapi.testclient import TestClient
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


def test_export_parquet_by_path_success(client, prepared_data):
    """
    PARQUETファイルを正常にエクスポートするテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    # APIリクエスト
    request_data = {
        'tableName': 'TestTable',
        'directoryPath': test_output_dir,
        'fileName': 'test_output.parquet'
    }
    response = client.post('/api/data/export-parquet-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    output_path = os.path.join(test_output_dir, 'test_output.parquet')
    assert output_path == response_data['result']['filePath']
    # ファイルが作成されているかチェック
    assert os.path.exists(output_path)
    # 出力されたPARQUETファイルの内容を検証
    exported_data = pl.read_parquet(output_path)
    assert test_data.equals(exported_data)


def test_export_parquet_by_path_table_not_exists(client, prepared_data):
    """
    存在しないテーブル名を指定した場合のテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        'tableName': 'NonExistentTable',
        'directoryPath': test_output_dir,
        'fileName': 'test_output.parquet',
    }
    response = client.post('/api/data/export-parquet-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    message = "tableName 'NonExistentTable' does not exist."
    assert message == response_data['message']


def test_export_parquet_by_path_invalid_output_directory(client,
                                                         prepared_data):
    """
    存在しない出力ディレクトリを指定した場合のテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        'tableName': 'TestTable',
        'directoryPath': '/non/existent/directory',
        'fileName': 'test_output.parquet'
    }
    response = client.post('/api/data/export-parquet-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    message = "Directory does not exist: /non/existent/directory"
    assert message == response_data['message']


def test_export_parquet_by_path_missing_table_name(client, prepared_data):
    """
    tableNameパラメータが未指定の場合のテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        'directoryPath': test_output_dir,
        'fileName': 'test_output.parquet'
    }
    response = client.post('/api/data/export-parquet-by-path',
                           data=json.dumps(request_data))
    # response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    # assert 'NG' == response_data['code']
    # assert "tableName is required" == response_data['message']


def test_export_parquet_by_path_missing_directory_path(client, prepared_data):
    """
    directoryPathパラメータが未指定の場合のテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        'tableName': 'TestTable',
        'fileName': 'test_output.parquet'
    }
    response = client.post('/api/data/export-parquet-by-path',
                           data=json.dumps(request_data))
    # response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    # assert 'NG' == response_data['code']
    # assert "directoryPath is required" == response_data['message']


def test_export_parquet_by_path_missing_file_name(client, prepared_data):
    """
    fileNameパラメータが未指定の場合のテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    request_data = {
        'tableName': 'TestTable',
        'directoryPath': test_output_dir,
    }
    response = client.post('/api/data/export-parquet-by-path',
                           data=json.dumps(request_data))
    # response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    # assert 'NG' == response_data['code']
    # assert "fileName is required" == response_data['message']


def test_export_parquet_by_path_invalid_json(client, prepared_data):
    """
    不正なJSONを送信した場合のテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    response = client.post('/api/data/export-parquet-by-path',
                           data='invalid json')
    # response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    # assert 'NG' == response_data['code']
    # assert "Invalid JSON format" == response_data['message']


def test_export_parquet_by_path_empty_table(client, prepared_data):
    """
    空のテーブルをエクスポートする場合のテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    # 空のテーブルを作成
    empty_data = pl.DataFrame({'col1': [], 'col2': []})
    tables_store.store_table('EmptyTable', empty_data)
    request_data = {
        'tableName': 'EmptyTable',
        'directoryPath': test_output_dir,
        'fileName': 'empty_output.parquet'
    }
    response = client.post('/api/data/export-parquet-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    output_path = os.path.join(test_output_dir, 'empty_output.parquet')
    assert output_path == response_data['result']['filePath']
    # ファイルが作成されているかチェック
    assert os.path.exists(output_path)
    # 出力されたPARQUETファイルの内容を検証（空のデータ）
    exported_data = pl.read_parquet(output_path)
    assert empty_data.equals(exported_data)


def test_export_parquet_by_path_large_table(client, prepared_data):
    """
    大きなテーブルをエクスポートする場合のテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    # 大きなテーブルを作成
    large_data = pl.DataFrame({
        'id': list(range(1000)),
        'value': [f'value_{i}' for i in range(1000)],
        'number': [i * 1.5 for i in range(1000)]
    })
    tables_store.store_table('LargeTable', large_data)
    request_data = {
        'tableName': 'LargeTable',
        'directoryPath': test_output_dir,
        'fileName': 'large_output.parquet'
    }
    response = client.post('/api/data/export-parquet-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    output_path = os.path.join(test_output_dir, 'large_output.parquet')
    assert output_path == response_data['result']['filePath']
    # ファイルが作成されているかチェック
    assert os.path.exists(output_path)
    # 出力されたPARQUETファイルの内容を検証
    exported_data = pl.read_parquet(output_path)
    assert large_data.equals(exported_data)
    assert 1000 == len(exported_data)


def test_export_parquet_by_path_special_characters(client, prepared_data):
    """
    特殊文字を含むデータをエクスポートする場合のテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    # 特殊文字を含むテーブルを作成
    special_data = pl.DataFrame({
        'text': ['Hello, 世界', 'こんにちは', 'αβγ', '123@#$'],
        'numbers': [1.1, 2.2, 3.3, 4.4],
        'unicode': ['🌟', '💻', '🐍', '📊']
    })
    tables_store.store_table('SpecialTable', special_data)
    request_data = {
        'tableName': 'SpecialTable',
        'directoryPath': test_output_dir,
        'fileName': 'special_output.parquet'
    }
    response = client.post('/api/data/export-parquet-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    output_path = os.path.join(test_output_dir, 'special_output.parquet')
    assert output_path == response_data['result']['filePath']
    # ファイルが作成されているかチェック
    assert os.path.exists(output_path)
    # 出力されたPARQUETファイルの内容を検証
    exported_data = pl.read_parquet(output_path)
    assert special_data.equals(exported_data)


def test_export_parquet_by_path_different_data_types(client, prepared_data):
    """
    異なるデータ型を含むテーブルをエクスポートする場合のテスト
    """
    tables_store, test_output_dir, test_data = prepared_data
    # 異なるデータ型を含むテーブルを作成
    mixed_data = pl.DataFrame({
        'integers': [1, 2, 3, 4],
        'floats': [1.1, 2.2, 3.3, 4.4],
        'strings': ['a', 'b', 'c', 'd'],
        'booleans': [True, False, True, False]
    })
    tables_store.store_table('MixedTable', mixed_data)
    request_data = {
        'tableName': 'MixedTable',
        'directoryPath': test_output_dir,
        'fileName': 'mixed_output.parquet'
    }
    response = client.post('/api/data/export-parquet-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    output_path = os.path.join(test_output_dir, 'mixed_output.parquet')
    assert output_path == response_data['result']['filePath']
    # ファイルが作成されているかチェック
    assert os.path.exists(output_path)
    # 出力されたPARQUETファイルの内容を検証
    exported_data = pl.read_parquet(output_path)
    assert mixed_data.equals(exported_data)
