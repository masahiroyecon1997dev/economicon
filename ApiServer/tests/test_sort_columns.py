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
    # テーブルをクリア
    manager.clear_tables()
    # テスト用テーブルをセット
    df = pl.DataFrame({
        'A': [3, 1, 2],
        'B': [6, 4, 5],
        'C': ['c', 'a', 'b']
    })
    manager.store_table('TestTable', df)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()



def test_sort_single_column_ascending(client, tables_manager):
    # 単一列で昇順ソート
    payload = {
        'tableName': 'TestTable',
        'sortColumns': [
            {'columnName': 'A', 'ascending': 'true'}
        ]
    }
    response = client.post(
        '/api/column/sort',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    assert response_data['result']['tableName'] == 'TestTable'
    # ソート結果を確認
    df = tables_manager.get_table('TestTable').table
    assert df['A'].to_list() == [1, 2, 3]
    assert df['B'].to_list() == [4, 5, 6]
    assert df['C'].to_list() == ['a', 'b', 'c']


def test_sort_single_column_descending(client, tables_manager):
    # 単一列で降順ソート
    payload = {
        'tableName': 'TestTable',
        'sortColumns': [
            {'columnName': 'A', 'ascending': 'false'}
        ]
    }
    response = client.post(
        '/api/column/sort',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # ソート結果を確認
    df = tables_manager.get_table('TestTable').table
    assert df['A'].to_list() == [3, 2, 1]
    assert df['B'].to_list() == [6, 5, 4]
    assert df['C'].to_list() == ['c', 'b', 'a']


def test_sort_multiple_columns(client, tables_manager):
    # 複数列でソート（混合順序）
    # より複雑なテストデータを準備
    df_complex = pl.DataFrame({
        'A': [1, 2, 1, 2],
        'B': [4, 3, 2, 1],
        'C': ['d', 'c', 'b', 'a']
    })
    tables_manager.update_table('TestTable', df_complex)
    payload = {
        'tableName': 'TestTable',
        'sortColumns': [
            {'columnName': 'A', 'ascending': 'true'},
            {'columnName': 'B', 'ascending': 'false'}
        ]
    }
    response = client.post(
        '/api/column/sort',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # ソート結果を確認（A昇順、B降順）
    df = tables_manager.get_table('TestTable').table
    assert df['A'].to_list() == [1, 1, 2, 2]
    assert df['B'].to_list() == [4, 2, 3, 1]
    assert df['C'].to_list() == ['d', 'b', 'c', 'a']


def test_sort_invalid_table(client, tables_manager):
    # 存在しないテーブル名
    payload = {
        'tableName': 'NoTable',
        'sortColumns': [
            {'columnName': 'A', 'ascending': 'true'}
        ]
    }
    response = client.post(
        '/api/column/sort',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "tableName 'NoTable' does not exist." == response_data['message']


def test_sort_invalid_column(client, tables_manager):
    # 存在しないカラム名を指定
    payload = {
        'tableName': 'TestTable',
        'sortColumns': [
            {'columnName': 'Z', 'ascending': 'true'}
        ]
    }
    response = client.post(
        '/api/column/sort',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "columnName 'Z' does not exist." == response_data['message']


def test_sort_empty_columns(client, tables_manager):
    # 空のソート列指定
    payload = {
        'tableName': 'TestTable',
        'sortColumns': []
    }
    response = client.post(
        '/api/column/sort',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'


def test_sort_missing_column_name(client, tables_manager):
    # columnNameが欠けている
    payload = {
        'tableName': 'TestTable',
        'sortColumns': [
            {'ascending': True}
        ]
    }
    response = client.post(
        '/api/column/sort',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    # assert response_data['code'] == 'NG'


def test_sort_missing_ascending(client, tables_manager):
    # ascendingが欠けている
    payload = {
        'tableName': 'TestTable',
        'sortColumns': [
            {'columnName': 'A'}
        ]
    }
    response = client.post(
        '/api/column/sort',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'


def test_sort_invalid_ascending_type(client, tables_manager):
    # ascendingがtrue、false以外
    payload = {
        'tableName': 'TestTable',
        'sortColumns': [
            {'columnName': 'A', 'ascending': 'yes'}
        ]
    }
    response = client.post(
        '/api/column/sort',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
