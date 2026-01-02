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



def test_upload_valid_csv_file(client, tables_manager):
    """
    有効なCSVファイルをアップロードした場合のテスト
    """
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_csv(
        f'{self.test_dir}/TestDataComma.csv', separator=',')
    test_file = File(open(f'{self.test_dir}/TestDataComma.csv', 'rb')
    uploaded_file = SimpleUploadedFile('TestDataComma.csv',
                                       test_file.read(),
                                       content_type='multipart/form-data')
    response = client.post('/api/import-csv-by-file',
                                {'file': uploaded_file})
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    # レスポンスデータの検証
    assert 'OK' == response_data['code']
    self.assertEqual('TestDataComma',
                     response_data['result']['tableName'])
    df = tables_manager.get_table('TestDataComma').table
    assert True == test_data.equals(df


def test_upload_csv_with_only_headers(client, tables_manager):
    """
    ヘッダーのみのCSVファイルをアップロードした場合のテスト
    問題なく読み込める
    """
    test_data = pl.DataFrame({
        'col_1': [],
        'col_2': [],
        'col_3': []
    })
    test_data.write_csv(
        f'{self.test_dir}/OnlyHeaderComma.csv', separator=',')
    test_file = File(open(f'{self.test_dir}/OnlyHeaderComma.csv', 'rb')
    uploaded_file = SimpleUploadedFile('OnlyHeaderComma.csv',
                                       test_file.read(),
                                       content_type='multipart/form-data')
    response = client.post('/api/import-csv-by-file',
                                {'file': uploaded_file})
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_manager.get_table('OnlyHeaderComma').table
    assert True == test_data.equals(df


def test_no_file_uploaded(client, tables_manager):
    """
    ファイルがアップロードされていない場合のテスト
    """
    response = client.post('/api/import-csv-by-file')
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert response_data['message'], "No file uploaded.")


def test_upload_non_csv_file(client, tables_manager):
    """
    CSVではないファイルをアップロードした場合のテスト (拡張子チェック)
    """
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_json(
        f'{self.test_dir}/TestDataJson.json')
    test_file = File(open(f'{self.test_dir}/TestDataJson.json', 'rb')
    uploaded_file = SimpleUploadedFile('TestDataJson.json',
                                       test_file.read(),
                                       content_type='multipart/form-data')
    response = client.post('/api/import-csv-by-file',
                                {'file': uploaded_file})
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "Uploaded file is not a .csv file.",
                  response_data['message'])


def test_upload_empty_csv_file(client, tables_manager):
    """
    空のCSVファイルをアップロードした場合のテスト (Polars NoDataError)
    """
    with open(f'{self.test_dir}/Empty.csv', 'w',
              encoding='utf-8'):
        pass
    test_file = File(open(f'{self.test_dir}/Empty.csv', 'rb')
    uploaded_file = SimpleUploadedFile('Empty.csv', test_file.read(),
                                       content_type='multipart/form-data')
    response = client.post('/api/import-csv-by-file',
                                {'file': uploaded_file})
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert 
        "Invalid file content type. Allowed types: text/csv, "
        "application/csv, text/plain",
        response_data['message'])
    @unittest.skip("このテストは現在、発生させる方法が不明なためスキップされています。")


def test_upload_malformed_csv_file(client, tables_manager):
    """
    不正な形式のCSVファイルをアップロードした場合のテスト
    """
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_parquet(
        f'{self.test_dir}/Error.csv')
    test_file = File(open(f'{self.test_dir}/Error.csv', 'rb')
    uploaded_file = SimpleUploadedFile('Error.csv', test_file.read(),
                                       content_type='multipart/form-data')
    response = client.post('/api/import-csv-by-file',
                                {'file': uploaded_file})
    response_data = response.json()
    self.assertEqual(response.status_code,
                     status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response_data['code'] == 'NG'
    assert "Failed to parse CSV file: Invalid format or encoding.",
                  response_data['message'])
