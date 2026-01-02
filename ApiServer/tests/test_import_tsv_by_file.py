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



def test_upload_valid_tsv_file(client, tables_manager):
    """
    有効なTSVファイルをアップロードした場合のテスト
    """
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_csv(
        f'{self.test_dir}/TestDataTab1.tsv', separator='\t')
    test_file = File(open(f'{self.test_dir}/TestDataTab1.tsv',
                          'rb')
    uploaded_file = SimpleUploadedFile('TestDataTab1.tsv',
                                       test_file.read(),
                                       content_type='multipart/form-data')
    response = client.post('/api/import-tsv-by-file',
                                {'file': uploaded_file})
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    # レスポンスデータの検証
    assert 'OK' == response_data['code']
    assert 'TestDataTab1' == response_data['result']['tableName']
    df = tables_manager.get_table('TestDataTab1').table
    assert True == test_data.equals(df


def test_upload_valid_tsv_file_with_txt_extension(client, tables_manager):
    """
    拡張子が.txtの有効なTSVファイルをアップロードした場合のテスト
    """
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_csv(
        f'{self.test_dir}/TestDataTab2.txt', separator='\t')
    test_file = File(open(f'{self.test_dir}/TestDataTab2.txt',
                          'rb')
    uploaded_file = SimpleUploadedFile('TestDataTab2.txt',
                                       test_file.read(),
                                       content_type='multipart/form-data')
    response = client.post('/api/import-tsv-by-file',
                                {'file': uploaded_file})
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    # レスポンスデータの検証
    assert 'OK' == response_data['code']
    assert 'TestDataTab2' == response_data['result']['tableName']
    df = tables_manager.get_table('TestDataTab2').table
    assert True == test_data.equals(df


def test_upload_tsv_with_only_headers(client, tables_manager):
    """
    ヘッダーのみのTSVファイルをアップロードした場合のテスト
    問題なく読み込める
    """
    test_data = pl.DataFrame({
        'col_1': [],
        'col_2': [],
        'col_3': []
    })
    test_data.write_csv(
        f'{self.test_dir}/OnlyHeaderTab.txt', separator='\t')
    test_file = File(open(f'{self.test_dir}/OnlyHeaderTab.txt',
                          'rb')
    uploaded_file = SimpleUploadedFile('OnlyHeaderTab.txt',
                                       test_file.read(),
                                       content_type='multipart/form-data')
    response = client.post('/api/import-tsv-by-file',
                                {'file': uploaded_file})
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_manager.get_table('OnlyHeaderTab').table
    assert True == test_data.equals(df


def test_no_tsv_file_uploaded(client, tables_manager):
    """
    ファイルがアップロードされていない場合のテスト
    """
    response = client.post('/api/import-tsv-by-file')
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert response_data['message'], "No file uploaded.")


def test_upload_non_tsv_file(client, tables_manager):
    """
    TSVではないファイルをアップロードした場合のテスト (拡張子チェック)
    """
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_csv(
        f'{self.test_dir}/TestDataComma.csv', separator=',')
    test_file = File(open(f'{self.test_dir}/TestDataComma.csv',
                          'rb')
    uploaded_file = SimpleUploadedFile('TestDataComma.csv',
                                       test_file.read(),
                                       content_type='multipart/form-data')
    response = client.post('/api/import-tsv-by-file',
                                {'file': uploaded_file})
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "Uploaded file is not a .tsv, .txt file.",
                  response_data['message'])


def test_upload_empty_tsv_file(client, tables_manager):
    """
    空のTSVファイルをアップロードした場合のテスト (Polars NoDataError)
    """
    with open(f'{self.test_dir}/Empty.txt', 'w',
              encoding='utf-8'):
        pass
    test_file = File(open(f'{self.test_dir}/Empty.txt', 'rb')
    uploaded_file = SimpleUploadedFile('Empty.txt', test_file.read(),
                                       content_type='multipart/form-data')
    response = client.post('/api/import-tsv-by-file',
                                {'file': uploaded_file})
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert 
        "Invalid file content type. Allowed types: "
        "text/tab-separated-values, text/plain",
        response_data['message'])
    @unittest.skip("このテストは現在、発生させる方法が不明なためスキップされています。")


def test_upload_malformed_tsv_file(client, tables_manager):
    """
    不正な形式のTSVファイルをアップロードした場合のテスト (Polars PanicExceptionを想定)
    """
    test_file = File(open(f'{self.test_dir}/Error.txt', 'rb')
    uploaded_file = SimpleUploadedFile('Error.txt', test_file.read(),
                                       content_type='multipart/form-data')
    response = client.post('/api/import-tsv-by-file',
                                {'file': uploaded_file})
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "Invalid file content type. Allowed types: "
                  "text/tab-separated-values, text/plain",
                  response_data['message'])
