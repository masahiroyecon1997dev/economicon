import json
import os
import shutil
import tempfile

import numpy as np
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
    # テスト用の出力ディレクトリ
    test_dir = tempfile.mkdtemp()
    yield manager, test_dir
    # テスト後のクリーンアップ
    manager.clear_tables()
    # テスト後にテンポラリディレクトリをクリーンアップ
    shutil.rmtree(test_dir, ignore_errors=True)


def test_import_excel_by_path_simple(client, prepared_data):
    """
    シンプルなEXCELファイルをパス指定でインポートするテスト
    """
    tables_store, test_dir = prepared_data
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_excel(
        f'{test_dir}/SimpleTest.xlsx')
    # APIリクエスト
    request_data = {
        'filePath': f'{test_dir}/SimpleTest.xlsx',
        'tableName': 'TestSimpleExcel'
    }
    response = client.post('/api/data/import-excel-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    assert 'TestSimpleExcel' == response_data['result']['tableName']
    # データの検証
    df = tables_store.get_table('TestSimpleExcel').table
    assert test_data.equals(df)


def test_import_excel_by_path_large_data(client, prepared_data):
    """
    大きなEXCELファイルをパス指定でインポートするテスト
    """
    tables_store, test_dir = prepared_data
    N_ROWS = 5000
    N_COLS = 500
    rng = np.random.default_rng(42)
    data = rng.integers(0, 100, size=(N_ROWS, N_COLS), dtype=np.int32)
    column_names = [f"col_{i}" for i in range(N_COLS)]
    df_sample = pl.DataFrame(
        data,
        schema=column_names
    )
    df_sample.write_excel(
        f'{test_dir}/TestDataXlsx.xlsx')
    # APIリクエスト
    request_data = {
        'filePath': f'{test_dir}/TestDataXlsx.xlsx',
        'tableName': 'TestLargeExcel'
    }
    response = client.post('/api/data/import-excel-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    assert 'TestLargeExcel' == response_data['result']['tableName']
    # データの検証
    df = tables_store.get_table('TestLargeExcel').table
    assert df_sample.equals(df)


def test_import_excel_by_path_custom_table_name(client, prepared_data):
    """
    カスタムテーブル名でEXCELファイルをインポートするテスト
    """
    tables_store, test_dir = prepared_data
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_excel(
        f'{test_dir}/SimpleTest.xlsx')
    # APIリクエスト
    request_data = {
        'filePath': f'{test_dir}/SimpleTest.xlsx',
        'tableName': 'MyCustomExcelTable'
    }
    response = client.post('/api/data/import-excel-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    assert 'MyCustomExcelTable' == response_data['result']['tableName']
    # データの検証
    df = tables_store.get_table('MyCustomExcelTable').table
    assert test_data.equals(df)


def test_import_excel_by_path_file_not_exists(client, prepared_data):
    """
    存在しないファイルパスを指定した場合のテスト
    """
    tables_store, test_dir = prepared_data
    request_data = {
        'filePath': '/non/existent/file.parquet',
        'tableName': 'TestNonExistent'
    }
    response = client.post('/api/data/import-excel-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    message = "filePath does not exist: /non/existent/file.parquet"
    assert message == response_data['message']


def test_import_excel_by_path_invalid_file_extension(client, prepared_data):
    """
    EXCEL以外のファイル拡張子を指定した場合のテスト
    """
    tables_store, test_dir = prepared_data
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_csv(
        f'{test_dir}/TestDataComma.csv', separator=',')
    request_data = {
        'filePath': f'{test_dir}/TestDataComma.csv',
        'tableName': 'TestInvalidExtension'
    }
    response = client.post('/api/data/import-excel-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert 'NG' == response_data['code']
    message = "An unexpected error occurred during EXCEL processing"
    assert message == response_data['message']


def test_import_excel_by_path_missing_file_path(client, prepared_data):
    """
    filePathパラメータが未指定の場合のテスト
    """
    tables_store, test_dir = prepared_data
    request_data = {
        'tableName': 'TestMissingPath'
    }
    response = client.post('/api/data/import-parquet-by-path',
                           data=json.dumps(request_data))
    # response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    # assert 'NG' == response_data['code']
    # assert "filePath is required" == response_data['message']


def test_import_excel_by_path_missing_table_name(client, prepared_data):
    """
    tableNameパラメータが未指定の場合のテスト
    """
    tables_store, test_dir = prepared_data
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_csv(
        f'{test_dir}/TestDataComma.csv', separator=',')
    request_data = {
        'filePath': f'{test_dir}/TestDataComma.csv'
    }
    response = client.post('/api/data/import-excel-by-path',
                           data=json.dumps(request_data))
    # response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    # assert 'NG' == response_data['code']
    # assert "tableName is required." == response_data['message']


def test_import_excel_by_path_duplicate_table_name(client, prepared_data):
    """
    既存のテーブル名と重複する場合のテスト
    """
    tables_store, test_dir = prepared_data
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_excel(
        f'{test_dir}/TestDataComma.xlsx')
    # 先にテーブルを作成
    first_request_data = {
        'filePath': f'{test_dir}/TestDataComma.xlsx',
        'tableName': 'DuplicateTable'
    }
    client.post('/api/data/import-excel-by-path',
                data=json.dumps(first_request_data))
    # 同じテーブル名で再度作成を試行
    second_request_data = {
        'filePath': f'{test_dir}/TestDataComma.xlsx',
        'tableName': 'DuplicateTable'
    }
    response = client.post('/api/data/import-excel-by-path',
                           data=json.dumps(second_request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    # テーブル名重複エラーメッセージを確認
    message = "tableName 'DuplicateTable' already exists."
    assert message == response_data['message']


def test_import_excel_by_path_invalid_json(client, prepared_data):
    """
    不正なJSONを送信した場合のテスト
    """
    tables_store, test_dir = prepared_data
    response = client.post('/api/data/import-excel-by-path',
                           data='invalid json')
    # response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    # assert 'NG' == response_data['code']
    # assert "Invalid JSON format" == response_data['message']


def test_import_excel_by_path_with_temporary_file(client, prepared_data):
    """
    一時的なEXCELファイルを作成してインポートするテスト
    """
    tables_store, test_dir = prepared_data
    # 一時的なEXCELファイルを作成
    temp_data = pl.DataFrame({
        'col1': [1, 2, 3, 4, 5],
        'col2': ['A', 'B', 'C', 'D', 'E'],
        'col3': [10.1, 20.2, 30.3, 40.4, 50.5]
    })
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx',
                                     delete=False) as f:
        temp_data.write_excel(f.name)
        temp_path = f.name
    try:
        # APIリクエスト
        request_data = {
            'filePath': temp_path,
            'tableName': 'TestTempExcel'
        }
        response = client.post('/api/data/import-excel-by-path',
                               data=json.dumps(request_data))
        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert 'OK' == response_data['code']
        assert 'TestTempExcel' == response_data['result']['tableName']
        # データの検証
        df = tables_store.get_table('TestTempExcel').table
        assert 3 == len(df.columns)
        assert 5 == len(df)
        assert temp_data.equals(df)
    finally:
        # 一時ファイルを削除
        os.unlink(temp_path)
