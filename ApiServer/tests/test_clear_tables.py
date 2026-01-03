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
    # テスト用テーブルを複数セット
    df1 = pl.DataFrame({
        'A': [1, 2, 3],
        'B': [4, 5, 6]
    })
    df2 = pl.DataFrame({
        'X': [10, 20],
        'Y': [30, 40]
    })
    manager.store_table('TestTable1', df1)
    manager.store_table('TestTable2', df2)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()



def test_clear_tables_success(client, tables_manager):
    # テーブルが存在することを確認
    table_names = tables_manager.get_table_name_list()
    assert len(table_names) == 2
    assert 'TestTable1' in table_names
    assert 'TestTable2' in table_names
    # テーブルをクリア
    response = client.delete('/api/clear-tables')
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # テーブルが空になっていることを確認
    table_names = tables_manager.get_table_name_list()
    assert len(table_names) == 0


def test_clear_tables_empty(client, tables_manager):
    # 既にテーブルをクリア
    tables_manager.clear_tables()
    # テーブルが空であることを確認
    table_names = tables_manager.get_table_name_list()
    assert len(table_names) == 0
    # 空の状態でクリアを実行
    response = client.delete('/api/clear-tables')
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # テーブルが空のままであることを確認
    table_names = tables_manager.get_table_name_list()
    assert len(table_names) == 0
