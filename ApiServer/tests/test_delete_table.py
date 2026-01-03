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
    # テスト用テーブルをセット
    df = pl.DataFrame({
        'A': [1, 2],
        'B': [3, 4]
    })
    manager.store_table('TestTable1', df)
    df = pl.DataFrame({
        'C': [1, 2],
        'D': [3, 4]
    })
    manager.store_table('TestTable2', df)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()



def test_delete_table_success(client, tables_manager):
    payload = {
        'tableName': 'TestTable2'
    }
    response = client.post(
        '/api/table/delete',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    assert 'TestTable2' not in tables_manager.get_table_name_list()
    assert len(tables_manager.get_table_name_list()) == 1


def test_delete_table_not_found(client, tables_manager):
    payload = {
        'tableName': 'NotExistTable'
    }
    response = client.post(
        '/api/table/delete',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "tableName 'NotExistTable' does not exist." in response_data['message']


def test_delete_table_empty_table_name(client, tables_manager):
    payload = {
        'tableName': ''
    }
    response = client.post(
        '/api/table/delete',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "tableName is required." in response_data['message']
