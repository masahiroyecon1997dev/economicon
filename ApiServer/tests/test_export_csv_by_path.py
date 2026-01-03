import pytest
from fastapi.testclient import TestClient
from fastapi import status
import polars as pl

from main import app
from analysisapp.services.data.tables_manager import TablesManager


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_manager():
    """TablesManagerのフィクスチャ"""
    manager = TablesManager()
        manager.clear_tables()
        # テスト用のテーブルデータを作成
        self.test_data = pl.DataFrame({
            'col_1': [1, 2, 3],
            'col_2': [10.1, 20.2, 30.3],
            'col_3': ['A', 'B', 'C']
        })
        manager.store_table('TestTable', self.test_data)
        # テスト用の出力ディレクトリ
        self.test_output_dir = tempfile.mkdtemp()
    def tearDown(self):
        # テスト後にテンポラリディレクトリをクリーンアップ
        shutil.rmtree(self.test_output_dir, ignore_errors=True)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()



def test_export_csv_by_path_default_separator(client, tables_manager):
    """
    デフォルトのカンマ区切りでCSVファイルをエクスポートするテスト
    """
    # APIリクエスト
    request_data = {
        'tableName': 'TestTable',
        'directoryPath': self.test_output_dir,
        'fileName': 'test_output.csv'
    }
    response = client.post('/api/export-csv-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    output_path = os.path.join(self.test_output_dir, 'test_output.csv')
    assert output_path == response_data['result']['filePath']
    # ファイルが作成されているかチェック
    assert output_path)
    # 出力されたCSVファイルの内容を検証
    exported_data = pl.read_csv(output_path)
    assert True == self.test_data.equals(exported_data


def test_export_csv_by_path_custom_separator(client, tables_manager):
    """
    タブ区切りでCSVファイルをエクスポートするテスト
    """
    # APIリクエスト
    request_data = {
        'tableName': 'TestTable',
        'directoryPath': self.test_output_dir,
        'fileName': 'test_output_tab.csv',
        'separator': '\t'
    }
    response = client.post('/api/export-csv-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    output_path = os.path.join(self.test_output_dir, 'test_output_tab.csv')
    assert output_path == response_data['result']['filePath']
    # ファイルが作成されているかチェック
    assert os.path.exists(output_path)
    # 出力されたCSVファイルの内容を検証（タブ区切り）
    exported_data = pl.read_csv(output_path, separator='\t')
    assert True == self.test_data.equals(exported_data


def test_export_csv_by_path_semicolon_separator(client, tables_manager):
    """
    セミコロン区切りでCSVファイルをエクスポートするテスト
    """
    # APIリクエスト
    request_data = {
        'tableName': 'TestTable',
        'directoryPath': self.test_output_dir,
        'fileName': 'test_output_semicolon.csv',
        'separator': ';'
    }
    response = client.post('/api/export-csv-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    output_path = os.path.join(self.test_output_dir,
                               'test_output_semicolon.csv')
    assert output_path == response_data['result']['filePath']
    # ファイルが作成されているかチェック
    assert os.path.exists(output_path)
    # 出力されたCSVファイルの内容を検証（セミコロン区切り）
    exported_data = pl.read_csv(output_path, separator=';')
    assert True == self.test_data.equals(exported_data


def test_export_csv_by_path_table_not_exists(client, tables_manager):
    """
    存在しないテーブル名を指定した場合のテスト
    """
    request_data = {
        'tableName': 'NonExistentTable',
        'directoryPath': self.test_output_dir,
        'fileName': 'test_output.csv',
    }
    response = client.post('/api/export-csv-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    assert "tableName 'NonExistentTable' does not exist",
                  response_data['message'])


def test_export_csv_by_path_invalid_output_directory(client, tables_manager):
    """
    存在しない出力ディレクトリを指定した場合のテスト
    """
    request_data = {
        'tableName': 'TestTable',
        'directoryPath': '/non/existent/directory',
        'fileName': 'test_output.csv'
    }
    response = client.post('/api/export-csv-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    assert "Directory does not exist: /non/existent/directory",
                  response_data['message'])


def test_export_csv_by_path_missing_table_name(client, tables_manager):
    """
    tableNameパラメータが未指定の場合のテスト
    """
    request_data = {
        'directoryPath': self.test_output_dir,
        'fileName': 'test_output.csv'
    }
    response = client.post('/api/export-csv-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    assert "tableName is required", response_data['message'])


def test_export_csv_by_path_missing_directory_path(client, tables_manager):
    """
    directoryPathパラメータが未指定の場合のテスト
    """
    request_data = {
        'tableName': 'TestTable',
        'fileName': 'test_output.csv'
    }
    response = client.post('/api/export-csv-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    assert "directoryPath is required", response_data['message'])


def test_export_csv_by_path_missing_file_name(client, tables_manager):
    """
    fileNameパラメータが未指定の場合のテスト
    """
    request_data = {
        'tableName': 'TestTable',
        'directoryPath': self.test_output_dir,
    }
    response = client.post('/api/export-csv-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    assert "fileName is required", response_data['message'])


def test_export_csv_by_path_empty_separator(client, tables_manager):
    """
    空の区切り文字を指定した場合のテスト
    """
    request_data = {
        'tableName': 'TestTable',
        'directoryPath': self.test_output_dir,
        'fileName': 'test_output_empty_separator.csv',
        'separator': ''
    }
    response = client.post('/api/export-csv-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    assert "separator must be at least 1 characters long",
                  response_data['message'])


def test_export_csv_by_path_invalid_json(client, tables_manager):
    """
    不正なJSONを送信した場合のテスト
    """
    response = client.post('/api/export-csv-by-path',
                                data='invalid json',
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    assert "Invalid JSON format", response_data['message'])


def test_export_csv_by_path_empty_table(client, tables_manager):
    """
    空のテーブルをエクスポートする場合のテスト
    """
    # 空のテーブルを作成
    empty_data = pl.DataFrame({'col1': [], 'col2': []})
    tables_manager.store_table('EmptyTable', empty_data)
    request_data = {
        'tableName': 'EmptyTable',
        'directoryPath': self.test_output_dir,
        'fileName': 'empty_output.csv'
    }
    response = client.post('/api/export-csv-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    output_path = os.path.join(self.test_output_dir, 'empty_output.csv')
    assert output_path == response_data['result']['filePath']
    # ファイルが作成されているかチェック
    assert os.path.exists(output_path)
    # 出力されたCSVファイルの内容を検証（空のデータ）
    exported_data = pl.read_csv(output_path)
    assert True == empty_data.equals(exported_data


def test_export_csv_by_path_large_table(client, tables_manager):
    """
    大きなテーブルをエクスポートする場合のテスト
    """
    # 大きなテーブルを作成
    large_data = pl.DataFrame({
        'id': list(range(1000)),
        'value': [f'value_{i}' for i in range(1000)],
        'number': [i * 1.5 for i in range(1000)]
    })
    tables_manager.store_table('LargeTable', large_data)
    request_data = {
        'tableName': 'LargeTable',
        'directoryPath': self.test_output_dir,
        'fileName': 'large_output.csv'
    }
    response = client.post('/api/export-csv-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    output_path = os.path.join(self.test_output_dir, 'large_output.csv')
    assert output_path == response_data['result']['filePath']
    # ファイルが作成されているかチェック
    assert os.path.exists(output_path)
    # 出力されたCSVファイルの内容を検証
    exported_data = pl.read_csv(output_path)
    assert True == large_data.equals(exported_data
    assert 1000 == len(exported_data
