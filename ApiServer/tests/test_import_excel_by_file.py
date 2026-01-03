import pytest
from fastapi.testclient import TestClient
from fastapi import status
import polars as pl
import tempfile
import shutil

from main import app
from analysisapp.services.data.tables_manager import TablesManager

# テスト用の出力ディレクトリ
test_dir = tempfile.mkdtemp()

@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_manager():
    """TablesManagerのフィクスチャ"""
    manager = TablesManager()
    manager.clear_tables()
    # テスト後にテンポラリディレクトリをクリーンアップ
    shutil.rmtree(test_dir, ignore_errors=True)
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
        f'{test_dir}/TestDataXlsx.xlsx')
    with open(f'{test_dir}/TestDataXlsx.xlsx', 'rb') as f:
        response = client.post('/api/import-excel-by-file',
                               files={'file': ('TestDataXlsx.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')})
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    # レスポンスデータの検証
    assert 'OK' == response_data['code']
    assert 'TestDataXlsx' == response_data['result']['tableName']
    df = tables_manager.get_table('TestDataXlsx').table
    assert test_data.equals(df)


@pytest.mark.skip(reason="このテストは現在、xlsが推奨されていないためスキップされています。")
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
        f'{test_dir}/TestDataXls.xls')
    with open(f'{test_dir}/TestDataXls.xls', 'rb') as f:
        response = client.post('/api/import-excel-by-file',
                               files={'file': ('TestDataXls.xls', f, 'application/vnd.ms-excel')})
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    # レスポンスデータの検証
    assert 'OK' == response_data['code']
    assert 'TestDataXls' == response_data['result']['tableName']
    df = tables_manager.get_table('TestDataXls').table
    assert test_data.equals(df)


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
        f'{test_dir}/OnlyHeaderExcel.xlsx')
    with open(f'{test_dir}/OnlyHeaderExcel.xlsx', 'rb') as f:
        response = client.post('/api/import-excel-by-file',
                               files={'file': ('OnlyHeaderExcel.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')})
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_manager.get_table('OnlyHeaderExcel').table
    assert test_data.equals(df)


def test_no_file_uploaded(client, tables_manager):
    """
    ファイルがアップロードされていない場合のテスト。
    """
    response = client.post('/api/import-csv-by-file')
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert response_data['message'] == "No file uploaded."


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
        f'{test_dir}/TestDataComma.csv', separator=',')
    with open(f'{test_dir}/TestDataComma.csv', 'rb') as f:
        response = client.post('/api/import-excel-by-file',
                               files={'file': ('TestDataComma.csv', f, 'multipart/form-data')})
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "Uploaded file is not a .xlsx, .xls file." == response_data['message']


def test_upload_empty_excel_file(client, tables_manager):
    """
    空のEXCELファイルをアップロードした場合のテスト (Polars NoDataError)
    """
    test_data = pl.DataFrame()
    test_data.write_excel(
        f'{test_dir}/Empty.xlsx')
    with open(f'{test_dir}/Empty.xlsx', 'rb') as f:
        response = client.post('/api/import-excel-by-file',
                               files={'file': ('Empty.xlsx', f, 'multipart/form-data')})
    response_data = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response_data['code'] == 'NG'
    assert "The uploaded EXCEL file is empty or contains no valid data." == response_data['message']


@pytest.mark.skip(reason="このテストは現在、発生させる方法が不明なためスキップされています。")
def test_upload_malformed_excel_file(client, tables_manager):
    """
    不正な形式のCSVファイルをアップロードした場合のテスト (Polars PanicExceptionを想定)
    """
    with open('/AnalysisApp/AnalysisApp'
              '/SampleData/Error.xlsx', 'rb') as f:
        response = client.post('/api/import-excel-by-file',
                               files={'file': ('Error.xlsx', f, 'multipart/form-data')})
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "Invalid file content type. Allowed types: pplication/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel, application/CDFV2" == response_data['message']
