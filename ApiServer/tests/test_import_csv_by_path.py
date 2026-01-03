import pytest
from fastapi.testclient import TestClient
from fastapi import status
import polars as pl
import tempfile
import shutil
import os
import json

from main import app
from analysisapp.services.data.tables_manager import TablesManager


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def prepared_data():
    """TablesManagerのフィクスチャ"""
    manager = TablesManager()
    manager.clear_tables()
    # テスト用のCSVファイルパス
    test_data = pl.DataFrame({
        'col_1': [1, 2, 3],
        'col_2': [10.1, 20.2, 30.3],
        'col_3': ['A', 'B', 'C']
    })
    # テスト用の出力ディレクトリ
    test_dir = tempfile.mkdtemp()
    test_data.write_csv(
        f'{test_dir}/TestDataComma.csv', separator=',')
    test_data.write_csv(
        f'{test_dir}/TestDataTab1.tsv', separator='\t')
    with open(f'{test_dir}/Empty.csv', 'w', encoding='utf-8'):
        pass
    test_data.write_excel(
        f'{test_dir}/TestDataXlsx.xlsx')
    # テスト後にテンポラリディレクトリをクリーンアップ
    shutil.rmtree(test_dir, ignore_errors=True)
    yield manager, test_dir
    # テスト後のクリーンアップ
    manager.clear_tables()



def test_import_csv_by_path_comma_separator(client, prepared_data):
    """
    カンマ区切りのCSVファイルをパス指定でインポートするテスト
    """
    tables_manager, test_dir = prepared_data
    test_csv_comma = f'{test_dir}/TestDataComma.csv'
    # 期待データをPolarsで読み込み
    expected_data = pl.read_csv(test_csv_comma, encoding='utf8')
    # APIリクエスト
    request_data = {
        'filePath': test_csv_comma,
        'tableName': 'TestCommaTable',
        'separator': ','
    }
    response = client.post('/api/import-csv-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    assert 'TestCommaTable' == response_data['result']['tableName']
    # データの検証
    df = tables_manager.get_table('TestCommaTable').table
    assert expected_data.equals(df)


def test_import_csv_by_path_tab_separator(client, prepared_data):
    """
    タブ区切りのファイルをCSVとしてパス指定でインポートするテスト
    """
    tables_manager, test_dir = prepared_data
    test_csv_tab = f'{test_dir}/TestDataTab1.tsv'
    # 期待データをPolarsで読み込み
    expected_data = pl.read_csv(test_csv_tab, separator='\t',
                                encoding='utf8')
    # APIリクエスト
    request_data = {
        'filePath': test_csv_tab,
        'tableName': 'TestTabTable',
        'separator': '\t'
    }
    response = client.post('/api/import-csv-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    assert 'TestTabTable' == response_data['result']['tableName']
    # データの検証
    df = tables_manager.get_table('TestTabTable').table
    assert expected_data.equals(df)


def test_import_csv_by_path_custom_separator(client, prepared_data):
    """
    セミコロン区切りのCSVファイルのテスト（テストファイルを作成）
    """
    tables_manager, test_dir = prepared_data
    # 一時的なセミコロン区切りファイルを作成
    temp_data = "col1;col2;col3\n1;2;3\n4;5;6\n"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv',
                                     delete=False) as f:
        f.write(temp_data)
        temp_path = f.name
    try:
        # APIリクエスト
        request_data = {
            'filePath': temp_path,
            'tableName': 'TestSemicolonTable',
            'separator': ';'
        }
        response = client.post('/api/import-csv-by-path',
                                data=json.dumps(request_data),
                                )
        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert 'OK' == response_data['code']
        assert 'TestSemicolonTable' == response_data['result']['tableName']
        # データの検証
        df = tables_manager.get_table('TestSemicolonTable').table
        assert 3 == len(df.columns)
        assert 2 == len(df)
    finally:
        # 一時ファイルを削除
        os.unlink(temp_path)


def test_import_csv_by_path_default_separator(client, prepared_data):
    """
    separatorパラメータを省略した場合のテスト（デフォルトはカンマ）
    """
    tables_manager, test_dir = prepared_data
    test_csv_comma = f'{test_dir}/TestDataComma.csv'
    # 期待データをPolarsで読み込み
    expected_data = pl.read_csv(test_csv_comma, encoding='utf8')
    # APIリクエスト（separatorを省略）
    request_data = {
        'filePath': test_csv_comma,
        'tableName': 'TestDefaultSeparator'
    }
    response = client.post('/api/import-csv-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert 'OK' == response_data['code']
    assert 'TestDefaultSeparator' == response_data['result']['tableName']
    # データの検証
    df = tables_manager.get_table('TestDefaultSeparator').table
    assert expected_data.equals(df)


def test_import_csv_by_path_file_not_exists(client, prepared_data):
    """
    存在しないファイルパスを指定した場合のテスト
    """
    tables_manager, test_dir = prepared_data
    request_data = {
        'filePath': '/non/existent/file.csv',
        'tableName': 'TestNonExistent',
        'separator': ','
    }
    response = client.post('/api/import-csv-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    assert "filePath does not exist: /non/existent/file.csv" == response_data['message']



def test_import_csv_by_path_invalid_file_extension(client, prepared_data):
    """
    CSV以外のファイル拡張子を指定した場合のテスト
    """
    tables_manager, test_dir = prepared_data
    request_data = {
        'filePath': f'{test_dir}/TestDataXlsx.xlsx',
        'tableName': 'TestInvalidExtension',
        'separator': ','
    }
    response = client.post('/api/import-csv-by-path',
                           data=json.dumps(request_data))
    response_data = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert 'NG' == response_data['code']
    assert "Failed to parse CSV file: Invalid format or encoding." == response_data['message']

def test_import_csv_by_path_missing_file_path(client, prepared_data):
    """
    filePathパラメータが未指定の場合のテスト
    """
    tables_manager, test_dir = prepared_data
    request_data = {
        'tableName': 'TestMissingPath',
        'separator': ','
    }
    response = client.post('/api/import-csv-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    assert "filePath is required" == response_data['message']


def test_import_csv_by_path_missing_table_name(client, prepared_data):
    """
    tableNameパラメータが未指定の場合のテスト
    """
    tables_manager, test_dir = prepared_data
    test_csv_comma = f'{test_dir}/TestDataComma.csv'
    request_data = {
        'filePath': test_csv_comma,
        'separator': ','
    }
    response = client.post('/api/import-csv-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    assert "tableName is required." == response_data['message']


def test_import_csv_by_path_duplicate_table_name(client, prepared_data):
    """
    既存のテーブル名と重複する場合のテスト
    """
    tables_manager, test_dir = prepared_data
    test_csv_comma = f'{test_dir}/TestDataComma.csv'
    # 先にテーブルを作成
    first_request_data = {
        'filePath': test_csv_comma,
        'tableName': 'DuplicateTable',
        'separator': ','
    }
    client.post('/api/import-csv-by-path',
                     data=json.dumps(first_request_data),
                     )
    # 同じテーブル名で再度作成を試行
    second_request_data = {
        'filePath': test_csv_comma,
        'tableName': 'DuplicateTable',
        'separator': ','
    }
    response = client.post('/api/import-csv-by-path',
                                data=json.dumps(second_request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    # テーブル名重複エラーメッセージを確認


def test_import_csv_by_path_empty_separator(client, prepared_data):
    """
    空の区切り文字を指定した場合のテスト
    """
    tables_manager, test_dir = prepared_data
    test_csv_comma = f'{test_dir}/TestDataComma.csv'
    request_data = {
        'filePath': test_csv_comma,
        'tableName': 'TestEmptySeparator',
        'separator': ''
    }
    response = client.post('/api/import-csv-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    assert "separator must be at least 1 characters long." == response_data['message']


def test_import_csv_by_path_invalid_json(client, prepared_data):
    """
    不正なJSONを送信した場合のテスト
    """
    response = client.post('/api/import-csv-by-path',
                                data='invalid json',
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'NG' == response_data['code']
    assert "Invalid JSON format" == response_data['message']


@pytest.mark.skip(reason="このテストは現在、発生させる方法が不明なためスキップされています。")
def test_import_csv_by_path_malformed_csv(client, prepared_data):
    """
    不正な形式のCSVファイルを指定した場合のテスト
    """
    # エラーCSVファイルが存在する場合
    request_data = {
        'filePath': '/AnalysisApp/AnalysisApp/SampleData/Error.csv',
        'tableName': 'TestMalformed',
        'separator': ','
    }
    response = client.post('/api/import-csv-by-path',
                                data=json.dumps(request_data),
                                )
    response_data = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert 'NG' == response_data['code']
    assert "Failed to parse CSV file: Invalid format or encoding." == response_data['message']
