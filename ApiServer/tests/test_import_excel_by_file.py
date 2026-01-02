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



def test_upload_valid_excel_file(client, tables_manager):
    """
    有効なExcel(xlsx)ファイルをアップロードした場合のテスト
    """
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_excel(
        f'{self.test_dir}/TestDataXlsx.xlsx')
    test_file = File(open(f'{self.test_dir}/TestDataXlsx.xlsx',
                          'rb')
    uploaded_file = SimpleUploadedFile(f'{self.test_dir}/'
                                       'TestDataXlsx.xlsx',
                                       test_file.read(),
                                       content_type='multipart/form-data')
    response = client.post('/api/import-excel-by-file',
                                {'file': uploaded_file})
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    # レスポンスデータの検証
    assert 'OK' == response_data['code']
    self.assertEqual('TestDataXlsx',
                     response_data['result']['tableName'])
    df = tables_manager.get_table('TestDataXlsx').table
    assert True == test_data.equals(df
    @unittest.skip("このテストは現在、xlsが推奨されていないためスキップされています。")


def test_upload_valid_excel_file_with_extension_xls(client, tables_manager):
    """
    有効なExcel(xls)ファイルをアップロードした場合のテスト
    """
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_excel(
        f'{self.test_dir}/TestDataXls.xls')
    test_file = File(open(f'{self.test_dir}/TestDataXls.xls',
                          'rb')
    uploaded_file = SimpleUploadedFile('TestDataXls.xls',
                                       test_file.read(),
                                       content_type='multipart/form-data')
    response = client.post('/api/import-excel-by-file',
                                {'file': uploaded_file})
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    # レスポンスデータの検証
    assert 'OK' == response_data['code']
    assert 'TestDataXls' == response_data['result']['tableName']
    df = tables_manager.get_table('TestDataXls').table
    assert True == test_data.equals(df


def test_upload_excel_with_only_headers(client, tables_manager):
    """
    ヘッダーのみのEXCELファイルをアップロードした場合のテスト
    問題なく読み込める
    """
    test_data = pl.DataFrame({
        'col_1': [],
        'col_2': [],
        'col_3': []
    })
    test_data.write_excel(
        f'{self.test_dir}/OnlyHeaderExcel.xlsx')
    test_file = File(open(f'{self.test_dir}/OnlyHeaderExcel.xlsx',
                          'rb')
    uploaded_file = SimpleUploadedFile(f'{self.test_dir}/'
                                       'OnlyHeaderExcel.xlsx',
                                       test_file.read(),
                                       content_type='multipart/form-data')
    response = client.post('/api/import-excel-by-file',
                                {'file': uploaded_file})
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_manager.get_table('OnlyHeaderExcel').table
    assert True == test_data.equals(df


def test_no_file_uploaded(client, tables_manager):
    """
    ファイルがアップロードされていない場合のテスト。
    """
    response = client.post('/api/import-csv-by-file')
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert response_data['message'], "No file uploaded.")


def test_upload_non_excel_file(client, tables_manager):
    """
    Excel以外のファイルをアップロードした場合のエラーケースをテストする。
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
    uploaded_file = SimpleUploadedFile(f'{self.test_dir}/'
                                       'TestDataComma.csv',
                                       test_file.read(),
                                       content_type='multipart/form-data')
    response = client.post('/api/import-excel-by-file',
                                {'file': uploaded_file},
                                format='multipart')
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "Uploaded file is not a .xlsx, .xls file.",
                  response_data['message'])


def test_upload_empty_excel_file(client, tables_manager):
    """
    空のEXCELファイルをアップロードした場合のテスト (Polars NoDataError)
    """
    test_data = pl.DataFrame()
    test_data.write_excel(
        f'{self.test_dir}/Empty.xlsx')
    test_file = File(open(f'{self.test_dir}/Empty.xlsx', 'rb')
    uploaded_file = SimpleUploadedFile(f'{self.test_dir}/'
                                       'Empty.xlsx',
                                       test_file.read(),
                                       content_type='multipart/form-data')
    response = client.post('/api/import-excel-by-file',
                                {'file': uploaded_file})
    response_data = response.json()
    self.assertEqual(response.status_code,
                     status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response_data['code'] == 'NG'
    assert 
        "The uploaded EXCEL file is empty or contains no valid data.",
        response_data['message'])
    @unittest.skip("このテストは現在、発生させる方法が不明なためスキップされています。")


def test_upload_malformed_excel_file(client, tables_manager):
    """
    不正な形式のCSVファイルをアップロードした場合のテスト (Polars PanicExceptionを想定)
    """
    test_file = File(open('/AnalysisApp/AnalysisApp'
                          '/SampleData/Error.xlsx', 'rb')
    uploaded_file = SimpleUploadedFile('Error.xlsx', test_file.read(),
                                       content_type='multipart/form-data')
    response = client.post('/api/import-excel-by-file',
                                {'file': uploaded_file})
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "Invalid file content type. Allowed types: "
                  "application/vnd.openxmlformats-officedocument."
                  "spreadsheetml.sheet, application/vnd.ms-excel, "
                  "application/CDFV2",
                  response_data['message'])
