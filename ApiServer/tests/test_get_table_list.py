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
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


def test_get_table_list_empty(client, tables_store):
    """テーブルが0件の場合"""
    response = client.get('/api/table/get-list')
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    assert response_data['result']['tableNameList'] == []


def test_get_table_list_multiple(client, tables_store):
    """テーブルが複数件の場合"""
    table_names = ['table1', 'table2', 'table3']
    for name in table_names:
        df = pl.DataFrame({'col': [1, 2, 3]})
        tables_store.store_table(name, df)
    response = client.get('/api/table/get-list')
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    assert set(response_data['result']['tableNameList']) == set(table_names)


def test_get_table_list_exception(client, tables_store, monkeypatch):
    """例外発生時のテスト"""
    def raise_exception():
        raise Exception("DB error")

    monkeypatch.setattr(tables_store, 'get_table_name_list', raise_exception)
    response = client.get('/api/table/get-list')
    response_data = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response_data['code'] == 'NG'
    expected_message = 'テーブル名リストの取得中に予期しないエラーが発生しました。'
    assert expected_message == response_data['message']
