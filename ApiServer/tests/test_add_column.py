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
    # テーブルをクリア
    manager.clear_tables()
    # テスト用テーブルをセット
    df = pl.DataFrame({
        'A': [1, 2, 3],
        'B': [4, 5, 6]
    })
    manager.store_table('TestTable', df)
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()


def test_add_column_success(client, tables_store):
    """正常にカラム追加できる"""
    payload = {
        'tableName': 'TestTable',
        'newColumnName': 'C',
        'addPositionColumn': 'A'
    }
    response = client.post(
        '/api/column/add',
        json=payload
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'

    # カラムが追加されているか
    df = tables_store.get_table('TestTable').table
    index_C = df.columns.index('A') + 1
    assert df.columns[index_C] == 'C'

    # 追加カラムはNoneで埋まっている
    assert df['C'].to_list() == [None, None, None]


def test_add_column_invalid_table(client, tables_store):
    """存在しないテーブル名"""
    payload = {
        'tableName': 'NoTable',
        'newColumnName': 'C',
        'addPositionColumn': 'A'
    }
    response = client.post(
        '/api/column/add',
        json=payload
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "tableName 'NoTable'は存在しません。" == response_data['message']


def test_add_column_duplicate_name(client, tables_store):
    """既存のカラム名と重複"""
    payload = {
        'tableName': 'TestTable',
        'newColumnName': 'A',  # 既に存在するカラム名
        'addPositionColumn': 'A'
    }
    response = client.post(
        '/api/column/add',
        json=payload
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "newColumnName 'A'は既に存在します。" == response_data['message']


def test_add_column_invalid_position_column(client, tables_store):
    """追加位置指定カラムが存在しない"""
    payload = {
        'tableName': 'TestTable',
        'newColumnName': 'C',
        'addPositionColumn': 'Z'  # 存在しないカラム名
    }
    response = client.post(
        '/api/column/add',
        json=payload
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "addPositionColumn 'Z'は存在しません。" == response_data['message']
