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
    # テスト用の出力ディレクトリ
    test_dir = tempfile.mkdtemp()
    yield manager, test_dir
    # テスト後のクリーンアップ
    manager.clear_tables()
    # テスト後にテンポラリディレクトリをクリーンアップ
    shutil.rmtree(test_dir, ignore_errors=True)


def test_upload_valid_parquet_file(client, prepared_data):
    """
    有効なParquetファイルをアップロードした場合のテスト
    """
    tables_store, test_dir = prepared_data
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_parquet(
        f'{test_dir}/TestData.parquet')
    with open(f'{test_dir}/TestData.parquet', 'rb') as f:
        response = client.post('/api/data/import-parquet-by-file',
                               files={'file': ('TestData.parquet',
                                               f,
                                               'application/octet-stream')})
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    # レスポンスデータの検証
    assert 'OK' == response_data['code']
    assert 'TestData' == response_data['result']['tableName']
    df = tables_store.get_table('TestData').table
    assert test_data.equals(df)


def test_no_file_uploaded(client, prepared_data):
    """
    ファイルがアップロードされていない場合のテスト。
    """
    tables_store, test_dir = prepared_data
    response = client.post('/api/data/import-parquet-by-file')
    # response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    # assert response_data['code'] == 'NG'
    # assert "No file uploaded." == response_data['message']


def test_upload_non_parquet_file(client, prepared_data):
    """
    Parquet以外のファイルをアップロードした場合のエラーケースをテストする。
    """
    tables_store, test_dir = prepared_data
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_csv(
        f'{test_dir}/TestDataComma.csv', separator=',')
    with open(f'{test_dir}/TestDataComma.csv', 'rb') as f:
        response = client.post('/api/data/import-parquet-by-file',
                               files={'file': ('TestDataComma.csv',
                                               f,
                                               'application/octet-stream')})
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "File must be a Parquet file" == response_data['message']


def test_upload_empty_parquet_file(client, prepared_data):
    """
    空のPARQUETファイルをアップロードした場合のテスト (Polars NoDataError)
    """
    tables_store, test_dir = prepared_data
    # 一時的なPARQUETファイルを作成
    temp_data = pl.DataFrame()
    temp_data.write_parquet(
        f'{test_dir}/Empty.parquet')
    with open(f'{test_dir}/Empty.parquet', 'rb') as f:
        response = client.post('/api/data/import-parquet-by-file',
                               files={'file': ('Empty.parquet',
                                               f,
                                               'application/octet-stream')})
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
