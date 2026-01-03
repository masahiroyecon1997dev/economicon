import pytest
from fastapi.testclient import TestClient
from fastapi import status
import polars as pl
import os
import tempfile
import shutil
import json

from main import app
from analysisapp.services.data.tables_manager import TablesManager

# テスト用の出力ディレクトリ
test_output_dir = tempfile.mkdtemp()
# テスト用のテーブルデータを作成
test_data = pl.DataFrame({
    'col_1': [1, 2, 3],
    'col_2': [10.1, 20.2, 30.3],
    'col_3': ['A', 'B', 'C']
})
@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_manager():
    """TablesManagerのフィクスチャ"""
    manager = TablesManager()
    manager.clear_tables()
    manager.store_table('TestTable', test_data)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()
    # テスト後にテンポラリディレクトリをクリーンアップ
    shutil.rmtree(test_output_dir, ignore_errors=True)


def test_export_excel_by_path_success(client, tables_manager):
    """
    EXCELファイルをエクスポートするテスト
    """
    # APIリクエスト
    request_data = {
        'tableName': 'TestTable',
        'directoryPath': test_output_dir,
        'fileName': 'test_output.xlsx'
    }
    response = client.post('/api/export-excel-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    output_path = os.path.join(test_output_dir, 'test_output.xlsx')
    assert output_path == response_data['result']['filePath']
    # ファイルが作成されているかチェック
    assert os.path.exists(output_path)
    # 出力されたEXCELファイルの内容を検証
    exported_data = pl.read_excel(output_path)
    assert test_data.equals(exported_data)


def test_export_excel_by_path_with_xls_extension(client, tables_manager):
    """
    .xls拡張子でEXCELファイルをエクスポートするテスト
    注意: Polarsは常にXLSX形式で出力するため、拡張子に関わらずXLSX形式のファイルが作成される
    """
    # APIリクエスト
    request_data = {
        'tableName': 'TestTable',
        'directoryPath': test_output_dir,
        'fileName': 'test_output.xls'
    }
    response = client.post('/api/export-excel-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    output_path = os.path.join(test_output_dir, 'test_output.xls')
    assert output_path == response_data['result']['filePath']
    # ファイルが作成されているかチェック
    assert os.path.exists(output_path)
    # Polarsは常にXLSX形式で出力するため、ファイルヘッダーをチェック
    with open(output_path, 'rb') as f:
        header = f.read(4)
        # XLSX形式のZIPヘッダー（PK）をチェック
        assert header[:2] == b'PK'
    # 読み取りのためにファイルを一時的に.xlsx拡張子でコピー
    temp_xlsx_path = output_path + '.xlsx'
    shutil.copy2(output_path, temp_xlsx_path)
    try:
        # 出力されたEXCELファイルの内容を検証（XLSX形式として読み込み）
        exported_data = pl.read_excel(temp_xlsx_path)
        assert test_data.equals(exported_data)
    finally:
        # 一時ファイルを削除
        if os.path.exists(temp_xlsx_path):
            os.unlink(temp_xlsx_path)


def test_export_excel_by_path_table_not_exists(client, tables_manager):
    """
    存在しないテーブル名を指定した場合のテスト
    """
    request_data = {
        'tableName': 'NonExistentTable',
        'directoryPath': test_output_dir,
        'fileName': 'test_output.xlsx',
    }
    response = client.post('/api/export-excel-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    assert "tableName 'NonExistentTable' does not exist" == response_data['message']


def test_export_excel_by_path_invalid_output_directory(client, tables_manager):
    """
    存在しない出力ディレクトリを指定した場合のテスト
    """
    request_data = {
        'tableName': 'TestTable',
        'directoryPath': '/non/existent/directory',
        'fileName': 'test_output.xlsx'
    }
    response = client.post('/api/export-excel-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    assert "Directory does not exist: /non/existent/directory" == response_data['message']



def test_export_excel_by_path_missing_table_name(client, tables_manager):
    """
    tableNameパラメータが未指定の場合のテスト
    """
    request_data = {
        'directoryPath': test_output_dir,
        'fileName': 'test_output.xlsx'
    }
    response = client.post('/api/export-excel-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    assert "tableName is required" == response_data['message']


def test_export_excel_by_path_missing_directory_path(client, tables_manager):
    """
    directoryPathパラメータが未指定の場合のテスト
    """
    request_data = {
        'tableName': 'TestTable',
        'fileName': 'test_output.xlsx'
    }
    response = client.post('/api/export-excel-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    assert "directoryPath is required" == response_data['message']


def test_export_excel_by_path_missing_file_name(client, tables_manager):
    """
    fileNameパラメータが未指定の場合のテスト
    """
    request_data = {
        'tableName': 'TestTable',
        'directoryPath': test_output_dir,
    }
    response = client.post('/api/export-excel-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    assert "fileName is required" == response_data['message']


def test_export_excel_by_path_invalid_json(client, tables_manager):
    """
    不正なJSONを送信した場合のテスト
    """
    response = client.post('/api/export-excel-by-path',
                                data='invalid json',
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    assert "Invalid JSON format" == response_data['message']


def test_export_excel_by_path_empty_table(client, tables_manager):
    """
    空のテーブルをエクスポートする場合のテスト
    """
    # 空のテーブルを作成
    empty_data = pl.DataFrame({'col1': [], 'col2': []})
    tables_manager.store_table('EmptyTable', empty_data)
    request_data = {
        'tableName': 'EmptyTable',
        'directoryPath': test_output_dir,
        'fileName': 'empty_output.xlsx'
    }
    response = client.post('/api/export-excel-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    output_path = os.path.join(test_output_dir, 'empty_output.xlsx')
    assert output_path == response_data['result']['filePath']
    # ファイルが作成されているかチェック
    assert os.path.exists(output_path)
    # 出力されたEXCELファイルの内容を検証（空のデータ）
    exported_data = pl.read_excel(output_path)
    assert empty_data.equals(exported_data)


def test_export_excel_by_path_large_table(client, tables_manager):
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
        'directoryPath': test_output_dir,
        'fileName': 'large_output.xlsx'
    }
    response = client.post('/api/export-excel-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    output_path = os.path.join(test_output_dir, 'large_output.xlsx')
    assert output_path == response_data['result']['filePath']
    # ファイルが作成されているかチェック
    assert os.path.exists(output_path)
    # 出力されたEXCELファイルの内容を検証
    exported_data = pl.read_excel(output_path)
    assert large_data.equals(exported_data)
    assert 1000 == len(exported_data)


def test_export_excel_by_path_special_characters_in_data(client, tables_manager):
    """
    特殊文字を含むデータをエクスポートする場合のテスト
    """
    # 特殊文字を含むテーブルを作成
    special_data = pl.DataFrame({
        'text': ['日本語', 'English', '中文', '한국어'],
        'special': ['@#$%', '&*()[]', '{}|\\', '\'";:'],
        'numbers': [1.23, -4.56, 0.0, 999.999]
    })
    tables_manager.store_table('SpecialTable', special_data)
    request_data = {
        'tableName': 'SpecialTable',
        'directoryPath': test_output_dir,
        'fileName': 'special_output.xlsx'
    }
    response = client.post('/api/export-excel-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    output_path = os.path.join(test_output_dir, 'special_output.xlsx')
    assert output_path == response_data['result']['filePath']
    # ファイルが作成されているかチェック
    assert os.path.exists(output_path)
    # 出力されたEXCELファイルの内容を検証
    exported_data = pl.read_excel(output_path)
    assert special_data.equals(exported_data)
