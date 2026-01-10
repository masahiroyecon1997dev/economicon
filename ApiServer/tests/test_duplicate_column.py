import polars as pl
import pytest
from analysisapp.services.data.tables_manager import TablesManager
from fastapi import status
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def prepared_data():
    """TablesManagerのフィクスチャ"""
    manager = TablesManager()
    # テーブルをクリア
    manager.clear_tables()
    # テスト用テーブルをセット
    df = pl.DataFrame({
        'A': [1, 2, 3],
        'B': [4, 5, 6],
        'C': ['x', 'y', 'z']
    })
    manager.store_table('TestTable', df)
    yield manager, df
    # テスト後のクリーンアップ
    manager.clear_tables()


def test_duplicate_column_success(client, prepared_data):
    tables_manager, df = prepared_data
    # 正常に列複製できる
    payload = {
        'tableName': 'TestTable',
        'sourceColumnName': 'A',
        'newColumnName': 'A_Copy'
    }
    response = client.post(
        '/api/column/duplicate',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    assert response_data['result']['tableName'] == 'TestTable'
    assert response_data['result']['columnName'] == 'A_Copy'
    # 列が複製されているか確認
    df = tables_manager.get_table('TestTable').table
    expected_columns = ['A', 'A_Copy', 'B', 'C']
    assert df.columns == expected_columns
    # 複製された列の値が元の列と同じか確認
    assert df['A'].to_list() == df['A_Copy'].to_list()
    assert df['A_Copy'].to_list() == [1, 2, 3]


def test_duplicate_column_success_middle_column(client, prepared_data):
    tables_manager, df = prepared_data
    # 中間の列を複製する場合
    payload = {
        'tableName': 'TestTable',
        'sourceColumnName': 'B',
        'newColumnName': 'B_Duplicate'
    }
    response = client.post(
        '/api/column/duplicate',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # 列の順序が正しいか確認（B の右隣に B_Duplicate が挿入される）
    df = tables_manager.get_table('TestTable').table
    expected_columns = ['A', 'B', 'B_Duplicate', 'C']
    assert df.columns == expected_columns
    # 複製された列の値が元の列と同じか確認
    assert df['B'].to_list() == df['B_Duplicate'].to_list()
    assert df['B_Duplicate'].to_list() == [4, 5, 6]


def test_duplicate_column_success_string_column(client, prepared_data):
    tables_manager, df = prepared_data
    # 文字列列の複製
    payload = {
        'tableName': 'TestTable',
        'sourceColumnName': 'C',
        'newColumnName': 'C_Clone'
    }
    response = client.post(
        '/api/column/duplicate',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    assert response_data['result']['tableName'] == 'TestTable'
    assert response_data['result']['columnName'] == 'C_Clone'
    # 複製された文字列列の値が正しいか確認
    df = tables_manager.get_table('TestTable').table
    assert df['C'].to_list() == df['C_Clone'].to_list()
    assert df['C_Clone'].to_list() == ['x', 'y', 'z']


def test_duplicate_column_invalid_table(client, prepared_data):
    tables_manager, df = prepared_data
    # 存在しないテーブル名
    payload = {
        'tableName': 'NoTable',
        'sourceColumnName': 'A',
        'newColumnName': 'A_Copy'
    }
    response = client.post(
        '/api/column/duplicate',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "tableName 'NoTable' does not exist." == response_data['message']


def test_duplicate_column_invalid_source_column(client, prepared_data):
    tables_manager, df = prepared_data
    # 存在しないソース列名を指定
    payload = {
        'tableName': 'TestTable',
        'sourceColumnName': 'Z',
        'newColumnName': 'Z_Copy'
    }
    response = client.post(
        '/api/column/duplicate',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "sourceColumnName 'Z' does not exist." == response_data['message']


def test_duplicate_column_duplicate_new_column_name(client, prepared_data):
    tables_manager, df = prepared_data
    # 既存の列名と同じ新列名を指定
    payload = {
        'tableName': 'TestTable',
        'sourceColumnName': 'A',
        'newColumnName': 'B'  # 既存の列名
    }
    response = client.post(
        '/api/column/duplicate',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    print(response_data['message'])
    assert "newColumnName 'B' already exists." == response_data['message']
