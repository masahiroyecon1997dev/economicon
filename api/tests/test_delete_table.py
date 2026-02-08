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
    manager.store_table('TestTable1', df)
    df = pl.DataFrame({
        'C': [1, 2],
        'D': [3, 4]
    })
    manager.store_table('TestTable2', df)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


def test_delete_table_success(client, tables_store):
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
    assert 'TestTable2' not in tables_store.get_table_name_list()
    assert len(tables_store.get_table_name_list()) == 1


def test_delete_table_not_found(client, tables_store):
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
    message = "tableName 'NotExistTable'は存在しません。"
    assert message == response_data['message']


def test_delete_table_empty_table_name(client, tables_store):
    payload = {
        'tableName': ''
    }
    response = client.post(
        '/api/table/delete',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response_data['code'] == 'NG'
    assert "tableName は1文字以上である必要があります。" in response_data['message']


# Pydanticバリデーションテスト


def test_delete_table_pydantic_empty_table_name(client, tables_store):
    """
    tableNameが空文字列の場合はバリデーションエラーになる
    """
    payload = {
        'tableName': ''
    }
    response = client.post(
        '/api/table/delete',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert 'NG' == response_data['code']
    assert 'tableName' in response_data['message']


def test_delete_table_pydantic_missing_table_name(client, tables_store):
    """
    tableNameが欠損している場合はバリデーションエラーになる
    """
    payload = {}
    response = client.post(
        '/api/table/delete',
        json=payload,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert 'NG' == response_data['code']
    assert 'tableName' in response_data['message']
