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
        self.test_dir = tempfile.mkdtemp()
    def tearDown(self):
        # テスト後にテンポラリディレクトリをクリーンアップ
        shutil.rmtree(self.test_dir, ignore_errors=True)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()



def test_import_excel_by_path_simple(client, tables_manager):
    """
    シンプルなEXCELファイルをパス指定でインポートするテスト
    """
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_excel(
        f'{self.test_dir}/SimpleTest.xlsx')
    # APIリクエスト
    request_data = {
        'filePath': f'{self.test_dir}/SimpleTest.xlsx',
        'tableName': 'TestSimpleExcel'
    }
    response = client.post('/api/import-excel-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    self.assertEqual('TestSimpleExcel',
                     response_data['result']['tableName'])
    # データの検証
    df = tables_manager.get_table('TestSimpleExcel').table
    assert True == test_data.equals(df


def test_import_excel_by_path_large_data(client, tables_manager):
    """
    大きなEXCELファイルをパス指定でインポートするテスト
    """
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
        f'{self.test_dir}/TestDataXlsx.xlsx')
    # APIリクエスト
    request_data = {
        'filePath': f'{self.test_dir}/TestDataXlsx.xlsx',
        'tableName': 'TestLargeExcel'
    }
    response = client.post('/api/import-excel-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    self.assertEqual('TestLargeExcel',
                     response_data['result']['tableName'])
    # データの検証
    df = tables_manager.get_table('TestLargeExcel').table
    assert True == df_sample.equals(df


def test_import_excel_by_path_custom_table_name(client, tables_manager):
    """
    カスタムテーブル名でEXCELファイルをインポートするテスト
    """
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_excel(
        f'{self.test_dir}/SimpleTest.xlsx')
    # APIリクエスト
    request_data = {
        'filePath': f'{self.test_dir}/SimpleTest.xlsx',
        'tableName': 'MyCustomExcelTable'
    }
    response = client.post('/api/import-excel-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    self.assertEqual('MyCustomExcelTable',
                     response_data['result']['tableName'])
    # データの検証
    df = tables_manager.get_table('MyCustomExcelTable').table
    assert True == test_data.equals(df


def test_import_excel_by_path_file_not_exists(client, tables_manager):
    """
    存在しないファイルパスを指定した場合のテスト
    """
    request_data = {
        'filePath': '/non/existent/file.parquet',
        'tableName': 'TestNonExistent'
    }
    response = client.post('/api/import-excel-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    assert "filePath does not exist: /non/existent/file.parquet",
                  response_data['message'])


def test_import_excel_by_path_invalid_file_extension(client, tables_manager):
    """
    EXCEL以外のファイル拡張子を指定した場合のテスト
    """
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_csv(
        f'{self.test_dir}/TestDataComma.csv', separator=',')
    request_data = {
        'filePath': f'{self.test_dir}/TestDataComma.csv',
        'tableName': 'TestInvalidExtension'
    }
    response = client.post('/api/import-excel-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    self.assertEqual(response.status_code,
                     status.HTTP_500_INTERNAL_SERVER_ERROR
    assert 'NG' == response_data['code']
    assert "An unexpected error occurred during "
                  "EXCEL processing",
                  response_data['message'])


def test_import_excel_by_path_missing_file_path(client, tables_manager):
    """
    filePathパラメータが未指定の場合のテスト
    """
    request_data = {
        'tableName': 'TestMissingPath'
    }
    response = client.post('/api/import-parquet-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    assert "filePath is required", response_data['message'])


def test_import_excel_by_path_missing_table_name(client, tables_manager):
    """
    tableNameパラメータが未指定の場合のテスト
    """
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_csv(
        f'{self.test_dir}/TestDataComma.csv', separator=',')
    request_data = {
        'filePath': f'{self.test_dir}/TestDataComma.csv'
    }
    response = client.post('/api/import-excel-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    assert "tableName is required.", response_data['message'])


def test_import_excel_by_path_duplicate_table_name(client, tables_manager):
    """
    既存のテーブル名と重複する場合のテスト
    """
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    test_data.write_excel(
        f'{self.test_dir}/TestDataComma.xlsx')
    # 先にテーブルを作成
    first_request_data = {
        'filePath': f'{self.test_dir}/TestDataComma.xlsx',
        'tableName': 'DuplicateTable'
    }
    client.post('/api/import-excel-by-path',
                     data=json.dumps(first_request_data),
                     )
    # 同じテーブル名で再度作成を試行
    second_request_data = {
        'filePath': f'{self.test_dir}/TestDataComma.xlsx',
        'tableName': 'DuplicateTable'
    }
    response = client.post('/api/import-excel-by-path',
                                data=json.dumps(second_request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    # テーブル名重複エラーメッセージを確認


def test_import_excel_by_path_invalid_json(client, tables_manager):
    """
    不正なJSONを送信した場合のテスト
    """
    response = client.post('/api/import-excel-by-path',
                                data='invalid json',
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    assert "Invalid JSON format", response_data['message'])


def test_import_excel_by_path_with_temporary_file(client, tables_manager):
    """
    一時的なEXCELファイルを作成してインポートするテスト
    """
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
        response = client.post('/api/import-excel-by-path',
                                    data=json.dumps(request_data),
                                    )
        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert 'OK' == response_data['code']
        self.assertEqual('TestTempExcel',
                         response_data['result']['tableName'])
        # データの検証
        df = tables_manager.get_table('TestTempExcel').table
        assert 3 == len(df.columns
        assert 5 == len(df
        assert True == temp_data.equals(df
    finally:
        # 一時ファイルを削除
        os.unlink(temp_path)
