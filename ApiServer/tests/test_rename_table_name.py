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
        # テスト用テーブルをセット
        df = pl.DataFrame({
            'A': [1, 2],
            'B': [3, 4]
        })
        manager.store_table('OldTable', df)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()



def test_rename_table_success(client, tables_manager):
    payload = {
        'oldTableName': 'OldTable',
        'newTableName': 'NewTable'
    }
    response = client.post(
        '/api/rename-table-name',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    table_info = tables_manager.get_table('NewTable')
    assert table_info.table_name == 'NewTable'
    assert 'OldTable' not in tables_manager.get_table_name_list()
    df = table_info.table
    assert df['A'].to_list() == [1, 2])
    assert df['B'].to_list() == [3, 4])


def test_rename_table_not_found(client, tables_manager):
    payload = {
        'oldTableName': 'NotExist',
        'newTableName': 'AnyName'
    }
    response = client.post(
        '/api/rename-table-name',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "oldTableName 'NotExist' does not exist." in response_data['message']


def test_rename_table_empty_old_table_name(client, tables_manager):
    # oldTableNameが空
    payload = {
        'oldTableName': '',
        'newTableName': 'NewTable'
    }
    response = client.post(
        '/api/rename-table-name',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "oldTableName is required." in response_data['message']


def test_rename_table_empty_new_table_name(client, tables_manager):
    # newTableNameが空
    payload = {
        'oldTableName': 'OldTable',
        'newTableName': ''
    }
    response = client.post(
        '/api/rename-table-name',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "newTableName is required." in response_data['message']
