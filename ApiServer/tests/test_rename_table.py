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
def tables_store():
    """TablesStoreのフィクスチャ"""
    manager = TablesStore()
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


def test_rename_table_success(client, tables_store):
    payload = {
        'oldTableName': 'OldTable',
        'newTableName': 'NewTable'
    }
    response = client.post(
        '/api/table/rename',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    table_info = tables_store.get_table('NewTable')
    assert table_info.table_name == 'NewTable'
    assert 'OldTable' not in tables_store.get_table_name_list()
    df = table_info.table
    assert df['A'].to_list() == [1, 2]
    assert df['B'].to_list() == [3, 4]


def test_rename_table_not_found(client, tables_store):
    payload = {
        'oldTableName': 'NotExist',
        'newTableName': 'AnyName'
    }
    response = client.post(
        '/api/table/rename',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    message = "oldTableName 'NotExist' does not exist."
    assert message == response_data['message']


def test_rename_table_empty_old_table_name(client, tables_store):
    # oldTableNameが空
    payload = {
        'oldTableName': '',
        'newTableName': 'NewTable'
    }
    response = client.post(
        '/api/table/rename',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "oldTableName is required." == response_data['message']


def test_rename_table_empty_new_table_name(client, tables_store):
    # newTableNameが空
    payload = {
        'oldTableName': 'OldTable',
        'newTableName': ''
    }
    response = client.post(
        '/api/table/rename',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "newTableName is required." == response_data['message']
