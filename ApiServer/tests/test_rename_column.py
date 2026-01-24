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
    manager.store_table('TestTable', df)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


def test_rename_column_success(client, tables_store):
    payload = {
        'tableName': 'TestTable',
        'oldColumnName': 'A',
        'newColumnName': 'C'
    }
    response = client.post(
        '/api/column/rename',
        json=payload,
    )
    response_data = response.json()
    print(response_data)
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_store.get_table('TestTable').table
    assert 'C' in df.columns
    assert 'A' not in df.columns
    assert df['C'].to_list() == [1, 2]


def test_rename_column_not_found(client, tables_store):
    payload = {
        'tableName': 'TestTable',
        'oldColumnName': 'Z',
        'newColumnName': 'C'
    }
    response = client.post(
        '/api/column/rename',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "oldColumnName 'Z'は存在しません。" in response_data['message']


def test_rename_column_empty_old_column_name(client, tables_store):
    payload = {
        'tableName': 'TestTable',
        'oldColumnName': '',
        'newColumnName': 'C'
    }
    response = client.post(
        '/api/column/rename',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "oldColumnNameは必須です。" in response_data['message']


def test_rename_column_empty_new_column_name(client, tables_store):
    payload = {
        'tableName': 'TestTable',
        'oldColumnName': 'A',
        'newColumnName': ''
    }
    response = client.post(
        '/api/column/rename',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "newColumnNameは必須です。" in response_data['message']


def test_rename_column_table_not_found(client, tables_store):
    # 存在しないテーブル名を指定した場合の異常系
    payload = {
        'tableName': 'NotExistTable',
        'oldColumnName': 'A',
        'newColumnName': 'C'
    }
    response = client.post(
        '/api/column/rename',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    message = "tableName 'NotExistTable'は存在しません。"
    assert message in response_data['message']
