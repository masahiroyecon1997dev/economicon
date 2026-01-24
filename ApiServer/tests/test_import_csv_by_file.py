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


def test_upload_valid_csv_file(client, prepared_data):
    """有効なCSVファイルをアップロードした場合のテスト"""
    tables_store, test_dir = prepared_data
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_csv(f'{test_dir}/TestDataComma.csv', separator=',')
    with open(f'{test_dir}/TestDataComma.csv', 'rb') as f:
        response = client.post(
            '/api/data/import-csv-by-file',
            files={'file': ('TestDataComma.csv', f, 'text/csv')}
        )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    # レスポンスデータの検証
    assert 'OK' == response_data['code']
    assert 'TestDataComma' == response_data['result']['tableName']
    df = tables_store.get_table('TestDataComma').table
    assert test_data.equals(df)


def test_upload_csv_with_only_headers(client, prepared_data):
    """
    ヘッダーのみのCSVファイルをアップロードした場合のテスト
    問題なく読み込める
    """
    tables_store, test_dir = prepared_data
    test_data = pl.DataFrame({
        'col_1': [],
        'col_2': [],
        'col_3': []
    })
    test_data.write_csv(f'{test_dir}/OnlyHeaderComma.csv', separator=',')
    with open(f'{test_dir}/OnlyHeaderComma.csv', 'rb') as f:
        response = client.post(
            '/api/data/import-csv-by-file',
            files={'file': ('OnlyHeaderComma.csv', f, 'multipart/form-data')}
        )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_store.get_table('OnlyHeaderComma').table
    assert test_data.equals(df)


def test_no_file_uploaded(client, prepared_data):
    """
    ファイルがアップロードされていない場合のテスト
    FastAPIは必須パラメータがない場合422を返す
    """
    tables_store, test_dir = prepared_data
    response = client.post('/api/data/import-csv-by-file')
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_upload_non_csv_file(client, prepared_data):
    """
    CSVではないファイルをアップロードした場合のテスト (拡張子チェック)
    """
    tables_store, test_dir = prepared_data
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_json(f'{test_dir}/TestDataJson.json')
    with open(f'{test_dir}/TestDataJson.json', 'rb') as f:
        response = client.post(
            '/api/data/import-csv-by-file',
            files={'file': ('TestDataJson.json', f, 'multipart/form-data')}
        )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "CSVファイルである必要があります" == response_data['message']


def test_upload_empty_csv_file(client, prepared_data):
    """
    空のCSVファイルをアップロードした場合のテスト (Polars NoDataError)
    exception_handlerでキャッチされて500エラーとなる
    """
    tables_store, test_dir = prepared_data
    test_data = pl.DataFrame()
    test_data.write_csv(f'{test_dir}/Empty.csv', separator=',')
    with open(f'{test_dir}/Empty.csv', 'rb') as f:
        response = client.post(
            '/api/data/import-csv-by-file',
            files={'file': ('Empty.csv', f, 'text/csv')}
        )
    response_data = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response_data['code'] == 'NG'
    expected_message = (
        "アップロードされたCSVファイルが空、または有効なデータが含まれていません。"
    )
    assert expected_message == response_data['message']


@pytest.mark.skip(
    reason="このテストは現在、発生させる方法が不明なためスキップされています。"
)
def test_upload_malformed_csv_file(client, prepared_data):
    """不正な形式のCSVファイルをアップロードした場合のテスト"""
    tables_store, test_dir = prepared_data
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_parquet(f'{test_dir}/Error.csv')
    with open(f'{test_dir}/Error.csv', 'rb') as f:
        response = client.post(
            '/api/data/import-csv-by-file',
            files={'file': ('Error.csv', f, 'multipart/form-data')}
        )
    response_data = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response_data['code'] == 'NG'
    expected_message = (
        "CSVファイルの解析に失敗しました: 無効なフォーマットまたはエンコーディングです。"
    )
    assert expected_message == response_data['message']
