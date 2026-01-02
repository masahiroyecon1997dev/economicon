"""Add Column APIのテスト - pytest版

unittest.TestCaseからpytestへの移行サンプル
"""
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


def test_add_column_success(client, tables_manager):
    """正常にカラム追加できる"""
    payload = {
        'tableName': 'TestTable',
        'newColumnName': 'C',
        'addPositionColumn': 'A'
    }
    response = client.post(
        '/api/add-column',
        json=payload
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'

    # カラムが追加されているか
    df = tables_manager.get_table('TestTable').table
    index_C = df.columns.index('A') + 1
    assert df.columns[index_C] == 'C'

    # 追加カラムはNoneで埋まっている
    assert df['C'].to_list() == [None, None, None]


def test_add_column_invalid_table(client, tables_manager):
    """存在しないテーブル名"""
    payload = {
        'tableName': 'NoTable',
        'newColumnName': 'C',
        'addPositionColumn': 'A'
    }
    response = client.post(
        '/api/add-column',
        json=payload
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'


def test_add_column_duplicate_name(client, tables_manager):
    """既存のカラム名と重複"""
    payload = {
        'tableName': 'TestTable',
        'newColumnName': 'A',  # 既に存在するカラム名
        'addPositionColumn': 'A'
    }
    response = client.post(
        '/api/add-column',
        json=payload
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
