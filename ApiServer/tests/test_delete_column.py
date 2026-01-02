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
    """テーブルTablesManagerのフィクスチャ"""
    manager = TablesManager()
    manager.clear_tables()
    # テスト用テーブルをセット
    df = pl.DataFrame({
        'A': [1, 2, 3],
        'B': [4, 5, 6],
        'C': [7, 8, 9]
    })
    manager.store_table('TestTable', df)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()



def test_delete_column_success(client, tables_manager):
    payload = {
        'tableName': 'TestTable',
        'columnName': 'A'
    }
    response = client.post(
        '/api/delete-column',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    df = tables_manager.get_table('TestTable').table
    assert 'A' not in df.columns
    assert 'B' in df.columns
    assert 'C' in df.columns


def test_delete_column_not_found(client, tables_manager):
    payload = {
        'tableName': 'TestTable',
        'columnName': 'Z'
    }
    response = client.post(
        '/api/delete-column',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "columnName 'Z' does not exist." in response_data['message']


def test_delete_column_table_not_found(client, tables_manager):
    payload = {
        'tableName': 'NotExistTable',
        'columnName': 'A'
    }
    response = client.post(
        '/api/delete-column',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "tableName 'NotExistTable' does not exist." in response_data['message']


def test_delete_column_empty_table_name(client, tables_manager):
    payload = {
        'tableName': '',
        'columnName': 'A'
    }
    response = client.post(
        '/api/delete-column',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "tableName is required." in response_data['message']


def test_delete_column_empty_column_name(client, tables_manager):
    payload = {
        'tableName': 'TestTable',
        'columnName': ''
    }
    response = client.post(
        '/api/delete-column',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "columnName is required." in response_data['message']
