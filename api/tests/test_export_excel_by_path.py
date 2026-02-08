import json
import os
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
    # テスト用のテーブルデータを作成
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    manager.store_table('TestTable', test_data)
    # テスト用の出力ディレクトリ
    test_dir = tempfile.mkdtemp()
    yield manager, test_dir, test_data
    # テスト後のクリーンアップ
    manager.clear_tables()
    # テスト後にテンポラリディレクトリをクリーンアップ
    shutil.rmtree(test_dir, ignore_errors=True)


def test_export_excel_by_path_success(client, prepared_data):
    """
    EXCELファイルをエクスポートするテスト
    """
    tables_store, test_dir, test_data = prepared_data
    # APIリクエスト
    request_data = {
        'tableName': 'TestTable',
        'directoryPath': test_dir,
        'fileName': 'test_output.xlsx'
    }
    response = client.post('/api/data/export-excel-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    output_path = os.path.join(test_dir, 'test_output.xlsx')
    assert output_path == response_data['result']['filePath']
    # ファイルが作成されているかチェック
    assert os.path.exists(output_path)
    # 出力されたEXCELファイルの内容を検証
    exported_data = pl.read_excel(output_path)
    assert test_data.equals(exported_data)


def test_export_excel_by_path_with_xls_extension(client, prepared_data):
    """
    .xls拡張子でEXCELファイルをエクスポートするテスト
    注意: Polarsは常にXLSX形式で出力するため、拡張子に関わらずXLSX形式のファイルが作成される
    """
    tables_store, test_dir, test_data = prepared_data
    # APIリクエスト
    request_data = {
        'tableName': 'TestTable',
        'directoryPath': test_dir,
        'fileName': 'test_output.xls'
    }
    response = client.post('/api/data/export-excel-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    output_path = os.path.join(test_dir, 'test_output.xls')
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


def test_export_excel_by_path_table_not_exists(client, prepared_data):
    """
    存在しないテーブル名を指定した場合のテスト
    """
    tables_store, test_dir, _ = prepared_data
    request_data = {
        'tableName': 'NonExistentTable',
        'directoryPath': test_dir,
        'fileName': 'test_output.xlsx',
    }
    response = client.post('/api/data/export-excel-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    message = "tableName 'NonExistentTable'は存在しません。"
    assert message == response_data['message']


def test_export_excel_by_path_invalid_output_directory(client, prepared_data):
    """
    存在しない出力ディレクトリを指定した場合のテスト
    """
    tables_store, test_output_dir, _ = prepared_data
    request_data = {
        'tableName': 'TestTable',
        'directoryPath': '/non/existent/directory',
        'fileName': 'test_output.xlsx'
    }
    response = client.post('/api/data/export-excel-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    message = "ディレクトリが存在しません: /non/existent/directory"
    assert message == response_data['message']


def test_export_excel_by_path_missing_table_name(client, prepared_data):
    """
    tableNameパラメータが未指定の場合のテスト
    """
    tables_store, test_dir, test_data = prepared_data
    request_data = {
        'directoryPath': test_dir,
        'fileName': 'test_output.xlsx'
    }
    response = client.post('/api/data/export-excel-by-path',
                           data=json.dumps(request_data))
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert 'NG' == response_data['code']
    assert "tableName は必須です。" == response_data['message']


def test_export_excel_by_path_missing_directory_path(client, prepared_data):
    """
    directoryPathパラメータが未指定の場合のテスト
    """
    tables_store, test_dir, test_data = prepared_data
    request_data = {
        'tableName': 'TestTable',
        'fileName': 'test_output.xlsx'
    }
    response = client.post('/api/data/export-excel-by-path',
                           data=json.dumps(request_data))
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert 'NG' == response_data['code']
    assert "directoryPath は必須です。" == response_data['message']


def test_export_excel_by_path_missing_file_name(client, prepared_data):
    """
    fileNameパラメータが未指定の場合のテスト
    """
    tables_store, test_dir, test_data = prepared_data
    request_data = {
        'tableName': 'TestTable',
        'directoryPath': test_dir,
    }
    response = client.post('/api/data/export-excel-by-path',
                           data=json.dumps(request_data))
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert 'NG' == response_data['code']
    assert "fileName は必須です。" == response_data['message']


def test_export_excel_by_path_invalid_json(client, prepared_data):
    """
    不正なJSONを送信した場合のテスト
    """
    tables_store, test_dir, test_data = prepared_data
    response = client.post('/api/data/export-excel-by-path',
                           data='invalid json')
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert 'NG' == response_data['code']
    assert "JSON decode error" == response_data['message']


def test_export_excel_by_path_empty_table(client, prepared_data):
    """
    空のテーブルをエクスポートする場合のテスト
    """
    tables_store, test_dir, _ = prepared_data
    # 空のテーブルを作成
    empty_data = pl.DataFrame({'col1': [], 'col2': []})
    tables_store.store_table('EmptyTable', empty_data)
    request_data = {
        'tableName': 'EmptyTable',
        'directoryPath': test_dir,
        'fileName': 'empty_output.xlsx'
    }
    response = client.post('/api/data/export-excel-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    output_path = os.path.join(test_dir, 'empty_output.xlsx')
    assert output_path == response_data['result']['filePath']
    # ファイルが作成されているかチェック
    assert os.path.exists(output_path)
    # 出力されたEXCELファイルの内容を検証（空のデータ）
    exported_data = pl.read_excel(output_path)
    assert empty_data.equals(exported_data)


def test_export_excel_by_path_large_table(client, prepared_data):
    """
    大きなテーブルをエクスポートする場合のテスト
    """
    tables_store, test_dir, _ = prepared_data
    # 大きなテーブルを作成
    large_data = pl.DataFrame({
        'id': list(range(1000)),
        'value': [f'value_{i}' for i in range(1000)],
        'number': [i * 1.5 for i in range(1000)]
    })
    tables_store.store_table('LargeTable', large_data)
    request_data = {
        'tableName': 'LargeTable',
        'directoryPath': test_dir,
        'fileName': 'large_output.xlsx'
    }
    response = client.post('/api/data/export-excel-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    output_path = os.path.join(test_dir, 'large_output.xlsx')
    assert output_path == response_data['result']['filePath']
    # ファイルが作成されているかチェック
    assert os.path.exists(output_path)
    # 出力されたEXCELファイルの内容を検証
    exported_data = pl.read_excel(output_path)
    assert large_data.equals(exported_data)
    assert 1000 == len(exported_data)


def test_export_excel_by_path_special_characters_in_data(client,
                                                         prepared_data):
    """
    特殊文字を含むデータをエクスポートする場合のテスト
    """
    tables_store, test_output_dir, _ = prepared_data
    # 特殊文字を含むテーブルを作成
    special_data = pl.DataFrame({
        'text': ['日本語', 'English', '中文', '한국어'],
        'special': ['@#$%', '&*()[]', '{}|\\', '\'";:'],
        'numbers': [1.23, -4.56, 0.0, 999.999]
    })
    tables_store.store_table('SpecialTable', special_data)
    request_data = {
        'tableName': 'SpecialTable',
        'directoryPath': test_output_dir,
        'fileName': 'special_output.xlsx'
    }
    response = client.post('/api/data/export-excel-by-path',
                           data=json.dumps(request_data))
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


def test_export_excel_by_path_empty_table_name(client, prepared_data):
    """
    tableNameが空文字列の場合はバリデーションエラーになる
    """
    tables_store, test_dir, test_data = prepared_data
    request_data = {
        'tableName': '',
        'directoryPath': test_dir,
        'fileName': 'test_output.xlsx'
    }
    response = client.post('/api/data/export-excel-by-path',
                          data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert 'NG' == response_data['code']
    assert 'tableName' in response_data['message']


def test_export_excel_by_path_empty_directory_path(client, prepared_data):
    """
    directoryPathが空文字列の場合はバリデーションエラーになる
    """
    tables_store, test_dir, test_data = prepared_data
    request_data = {
        'tableName': 'TestTable',
        'directoryPath': '',
        'fileName': 'test_output.xlsx'
    }
    response = client.post('/api/data/export-excel-by-path',
                          data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert 'NG' == response_data['code']
    assert 'directoryPath' in response_data['message']


def test_export_excel_by_path_empty_file_name(client, prepared_data):
    """
    fileNameが空文字列の場合はバリデーションエラーになる
    """
    tables_store, test_dir, test_data = prepared_data
    request_data = {
        'tableName': 'TestTable',
        'directoryPath': test_dir,
        'fileName': ''
    }
    response = client.post('/api/data/export-excel-by-path',
                          data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert 'NG' == response_data['code']
    assert 'fileName' in response_data['message']
