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
    # テスト用の出力ディレクトリ
    test_dir = tempfile.mkdtemp()
    yield manager, test_dir
    # テスト後のクリーンアップ
    manager.clear_tables()
    # テスト後にテンポラリディレクトリをクリーンアップ
    shutil.rmtree(test_dir, ignore_errors=True)


def test_upload_valid_tsv_file(client, prepared_data):
    """
    有効なTSVファイルをアップロードした場合のテスト
    """
    tables_manager, test_dir = prepared_data
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    print(test_data)
    test_data.write_csv(
        f'{test_dir}/TestDataTab1.tsv', separator='\t')
    with open(f'{test_dir}/TestDataTab1.tsv', 'rb') as f:
        response = client.post('/api/data/import-tsv-by-file',
                               files={'file': ('TestDataTab1.tsv',
                                               f,
                                               'text/tab-separated-values')})
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    # レスポンスデータの検証
    assert 'OK' == response_data['code']
    assert 'TestDataTab1' == response_data['result']['tableName']
    df = tables_manager.get_table('TestDataTab1').table
    assert test_data.equals(df)


def test_upload_valid_tsv_file_with_txt_extension(client, prepared_data):
    """
    拡張子が.txtの有効なTSVファイルをアップロードした場合のテスト
    """
    tables_manager, test_dir = prepared_data
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_csv(
        f'{test_dir}/TestDataTab2.txt', separator='\t')
    with open(f'{test_dir}/TestDataTab2.txt', 'rb') as f:
        response = client.post('/api/data/import-tsv-by-file',
                               files={'file': ('TestDataTab2.txt',
                                               f,
                                               'text/tab-separated-values')})
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    # レスポンスデータの検証
    assert 'OK' == response_data['code']
    assert 'TestDataTab2' == response_data['result']['tableName']
    df = tables_manager.get_table('TestDataTab2').table
    assert test_data.equals(df)


def test_upload_tsv_with_only_headers(client, prepared_data):
    """
    ヘッダーのみのTSVファイルをアップロードした場合のテスト
    問題なく読み込める
    """
    tables_manager, test_dir = prepared_data
    test_data = pl.DataFrame({
        'col_1': [],
        'col_2': [],
        'col_3': []
    })
    test_data.write_csv(
        f'{test_dir}/OnlyHeaderTab.txt', separator='\t')
    with open(f'{test_dir}/OnlyHeaderTab.txt', 'rb') as f:
        response = client.post('/api/data/import-tsv-by-file',
                               files={'file': ('OnlyHeaderTab.txt',
                                               f,
                                               'text/tab-separated-values')})
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_manager.get_table('OnlyHeaderTab').table
    assert test_data.equals(df)


def test_no_tsv_file_uploaded(client, prepared_data):
    """
    ファイルがアップロードされていない場合のテスト
    """
    tables_manager, test_dir = prepared_data
    response = client.post('/api/data/import-tsv-by-file')
    # response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    # assert response_data['code'] == 'NG'
    # assert response_data['message'] == "No file uploaded."


def test_upload_non_tsv_file(client, prepared_data):
    """
    TSVではないファイルをアップロードした場合のテスト (拡張子チェック)
    """
    tables_manager, test_dir = prepared_data
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_csv(
        f'{test_dir}/TestDataComma.csv', separator=',')
    with open(f'{test_dir}/TestDataComma.csv', 'rb') as f:
        response = client.post('/api/data/import-tsv-by-file',
                               files={'file': ('TestDataComma.csv',
                                               f,
                                               'text/tab-separated-values')})
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "File must be a TSV file" == response_data['message']


def test_upload_empty_tsv_file(client, prepared_data):
    """
    空のTSVファイルをアップロードした場合のテスト (Polars NoDataError)
    """
    tables_manager, test_dir = prepared_data
    with open(f'{test_dir}/Empty.txt', 'w',
              encoding='utf-8'):
        pass
    with open(f'{test_dir}/Empty.txt', 'rb') as f:
        response = client.post('/api/data/import-tsv-by-file',
                               files={'file': ('Empty.txt',
                                               f,
                                               'text/tab-separated-values')})
    response_data = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response_data['code'] == 'NG'


@pytest.mark.skip(reason="このテストは現在、発生させる方法が不明なためスキップされています。")
def test_upload_malformed_tsv_file(client, prepared_data):
    """
    不正な形式のTSVファイルをアップロードした場合のテスト (Polars PanicExceptionを想定)
    """
    tables_manager, test_dir = prepared_data
    with open(f'{test_dir}/Error.txt', 'rb') as f:
        response = client.post('/api/data/import-tsv-by-file',
                               files={'Error.txt',
                                      f,
                                      'text/tab-separated-values'})
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    message = ("Invalid file content type. "
               "Allowed types: text/tab-separated-values, text/plain")
    assert message == response_data['message']
