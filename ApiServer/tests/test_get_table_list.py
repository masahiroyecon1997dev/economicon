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
def tables_manager():
    """TablesManagerのフィクスチャ"""
    manager = TablesManager()
    manager.clear_tables()
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


def test_get_table_list_empty(client, tables_manager):
    """テーブルが0件の場合"""
    response = client.get('/api/table/list')
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    assert response_data['result']['tableNameList'] == []


def test_get_table_list_multiple(client, tables_manager):
    """テーブルが複数件の場合"""
    table_names = ['table1', 'table2', 'table3']
    for name in table_names:
        df = pl.DataFrame({'col': [1, 2, 3]})
        tables_manager.store_table(name, df)
    response = client.get('/api/table/list')
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    assert set(response_data['result']['tableNameList']) == set(table_names)


def test_get_table_list_exception(client, tables_manager):
    """例外発生時のテスト"""
    original_method = tables_manager.get_table_name_list

    def raise_exception():
        raise Exception("DB error")

    tables_manager.get_table_name_list = raise_exception
    response = client.get('/api/table/list')
    response_data = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response_data['code'] == 'NG'
    expected_message = 'An unexpected error during getting table name list.'
    assert expected_message == response_data['message']
    # 後始末
    tables_manager.get_table_name_list = original_method
