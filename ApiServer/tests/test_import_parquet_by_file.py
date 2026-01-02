import pytest
from fastapi.testclient import TestClient
from fastapi import status
import polars as pl

from main import app
from analysisapp.api.services.data.tables_manager import TablesManager


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_manager():
    """TablesManagerのフィクスチャ"""
    manager = TablesManager()
        manager.clear_tables()
        # テスト用の出力ディレクトリ
        self.test_dir = tempfile.mkdtemp()
    def tearDown(self):
        # テスト後にテンポラリディレクトリをクリーンアップ
        shutil.rmtree(self.test_dir, ignore_errors=True)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()



def test_upload_valid_parquet_file(client, tables_manager):
    """
    有効なParquetファイルをアップロードした場合のテスト
    """
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_parquet(
        f'{self.test_dir}/TestData.parquet')
    test_file = File(open(f'{self.test_dir}/TestData.parquet',
                          'rb')
    uploaded_file = SimpleUploadedFile('TestData.parquet',
                                       test_file.read(),
                                       content_type='multipart/form-data')
    response = client.post('/api/import-parquet-by-file',
                                {'file': uploaded_file})
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    # レスポンスデータの検証
    assert 'OK' == response_data['code']
    self.assertEqual('TestData',
                     response_data['result']['tableName'])
    df = tables_manager.get_table('TestData').table
    assert True == test_data.equals(df


def test_no_file_uploaded(client, tables_manager):
    """
    ファイルがアップロードされていない場合のテスト。
    """
    response = client.post('/api/import-parquet-by-file')
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert response_data['message'], "No file uploaded.")


def test_upload_non_parquet_file(client, tables_manager):
    """
    Parquet以外のファイルをアップロードした場合のエラーケースをテストする。
    """
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_csv(
        f'{self.test_dir}/TestDataComma.csv', separator=',')
    uploaded_file = SimpleUploadedFile('TestDataComma.csv',
                                       open(f'{self.test_dir}/'
                                            'TestDataComma.csv', 'rb'
                                            ).read(),
                                       content_type='multipart/form-data')
    response = client.post('/api/import-parquet-by-file',
                                {'file': uploaded_file},
                                format='multipart')
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "Uploaded file is not a .parquet file.",
                  response_data['message'])


def test_upload_empty_parquet_file(client, tables_manager):
    """
    空のPARQUETファイルをアップロードした場合のテスト (Polars NoDataError)
    """
    # 一時的なPARQUETファイルを作成
    temp_data = pl.DataFrame()
    temp_data.write_parquet(
        f'{self.test_dir}/Empty.parquet')
    test_file = File(open(f'{self.test_dir}/Empty.parquet', 'rb')
    uploaded_file = SimpleUploadedFile('Empty.parquet',
                                       test_file.read(),
                                       content_type='multipart/'
                                       'form-data')
    response = client.post('/api/import-parquet-by-file',
                                {'file': uploaded_file})
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
